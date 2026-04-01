# 2. 폐쇄망에서 Kubernetes와 Helm 설치

본 문서는 폐쇄망 환경에서 **kubeadm**을 사용하여 Kubernetes v1.30.x 클러스터를 구축하는 절차를 정의합니다.

- **가이드 환경**
  - **OS**: Rocky Linux 9.6 (추천) / Ubuntu 22.04+
  - **K8s Version**: v1.30.14
  - **Container Runtime**: containerd v2.x
- [설치 파일 위치 (Google Drive)](https://drive.google.com/drive/folders/1joMQRpZPWzKgU9BBsdxy3b0qzJMWpBC8?usp=sharing)

!!! note "네트워크 전제 조건"
    폐쇄망 환경이라도 각 노드 간의 통신은 전면 허용되어야 하며, `169.254.169.254/32` (cloud-init 메타데이터 IP)에 대한 80포트 아웃바운드 규칙이 허용되어야 정상적인 노드 초기화가 가능합니다.

---

## 📦 Phase 0: 설치 파일 배포

마스터-1 노드에 준비된 설치 파일(`k8s-1.30.tar.gz`)을 모든 워커 및 추가 마스터 노드에 배포합니다.

```bash
# 배포 대상 노드 IP 목록 (환경에 맞게 수정)
NODES=("10.10.10.71" "10.10.10.72" "10.10.10.73" "10.10.10.74")

for IP in "${NODES[@]}"; do
    echo "Sending to $IP..."
    scp ~/k8s-1.30.tar.gz rocky@$IP:~/
done

# 모든 노드에서 압축 해제
tar -zxvf ~/k8s-1.30.tar.gz
```

---

## 🚀 Phase 1: 로컬 패키지 설치 및 OS 설정

모든 노드(Master, Worker 공통)에서 수행합니다.

### 1.1 패키지 설치 (dnf localinstall)

```bash
cd ~/k8s-1.30
# Repo 설정을 무시하고 로컬 RPM 파일을 일괄 설치합니다.
sudo dnf localinstall -y --disablerepo='*' common/rpms/*.rpm k8s/rpms/*.rpm

# 설치 확인
rpm -qa | grep -E "kubelet|containerd|haproxy"
```

### 1.2 OS 커널 및 보안 설정

```bash
# 1. Swap 비활성화
sudo swapoff -a
sudo sed -i '/swap/d' /etc/fstab

# 2. SELinux Permissive 모드 (Rocky Linux 필수)
sudo setenforce 0
sudo sed -i 's/^SELINUX=enforcing$/SELINUX=permissive/' /etc/selinux/config

# 3. 커널 모듈 로드 및 sysctl 설정
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter

cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
sudo sysctl --system
```

### 1.3 hosts 파일 설정

```bash
sudo tee -a /etc/hosts <<EOF
10.10.10.70 master1
10.10.10.71 master2
10.10.10.72 master3
10.10.10.73 worker1
EOF
```

### 1.4 Containerd 설정 (Harbor 연동 대비)

```bash
# 1. 기본 설정 생성
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml > /dev/null

# 2. SystemdCgroup 활성화 (필수!)
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

# 3. Pause 이미지 버전 고정 (폐쇄망 반입 이미지와 일치)
sudo sed -i 's/pause:3.10.1/pause:3.9/g' /etc/containerd/config.toml

# 4. Harbor 사설 인증서 경로 설정
sudo sed -i "s|config_path = '/etc/containerd/certs.d:/etc/docker/certs.d'|config_path = '/etc/containerd/certs.d'|g" /etc/containerd/config.toml

# 5. 서비스 시작
sudo systemctl enable --now containerd
sudo systemctl enable --now kubelet
```

#### SystemdCgroup 설정 검증

서비스 재시작 후에도 kubelet이 간헐적으로 오류가 나는 경우, `SystemdCgroup = true` 가 실제로 적용되었는지 확인합니다.

```bash
grep SystemdCgroup /etc/containerd/config.toml
```

값이 없거나 `false` 라면 아래 위치에 직접 추가합니다.

```ini
[plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.runc.options]
  SystemdCgroup = true  # 이 줄 추가
```

추가 후 서비스를 재시작합니다.

```bash
sudo systemctl restart containerd
sudo systemctl restart kubelet
```

#### (선택) 컨테이너 이미지 저장 위치 변경

데이터 디스크를 별도로 마운트한 경우(`/app` 등), 심볼릭 링크로 저장 경로를 변경합니다.

```bash
sudo systemctl stop containerd kubelet

sudo mkdir -p /app/containerd_data
if [ -d "/var/lib/containerd" ]; then
    sudo mv /var/lib/containerd/* /app/containerd_data/
    sudo rmdir /var/lib/containerd
fi
sudo ln -s /app/containerd_data /var/lib/containerd

# 확인 (화살표가 보여야 함)
ls -ld /var/lib/containerd

sudo systemctl start containerd kubelet
```

---

## 🚀 Phase 2: 이미지 로드 (전체 노드)

폐쇄망이므로 `docker pull` 대신 로컬 이미지를 `ctr` 명령어로 로드합니다.

```bash
cd ~/k8s-1.30/k8s/images

# k8s.io 네임스페이스에 이미지 로드
for img in *.tar; do
    echo "Loading $img..."
    sudo ctr -n k8s.io images import "$img"
done

# 로드 확인
sudo ctr -n k8s.io images list | grep kube-apiserver
```

---

## 🚀 Phase 3: 로드밸런서(LB) 구성 (HA 3중화 시에만)

마스터 3대 구성 시 API Server의 고가용성을 위해 LB를 구성합니다.
**단일 마스터 구성이면 Phase 4로 넘어갑니다.**

### 옵션 A: VIP 방식 (Keepalived + HAProxy - 권장)

- **전제**: 마스터 노드 3대 및 가상 IP(VIP: `10.10.10.200`) 필요.
- **커널 설정**: VIP 바인딩 허용

  ```bash
  cat <<EOF | sudo tee /etc/sysctl.d/haproxy.conf
  net.ipv4.ip_nonlocal_bind = 1
  EOF
  sudo sysctl --system
  ```

#### 1) HAProxy 설정 (전체 마스터 노드)

```bash
sudo cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.bak

cat <<EOF | sudo tee /etc/haproxy/haproxy.cfg
global
    log         127.0.0.1 local2
    maxconn     4000
    daemon

defaults
    mode                    tcp
    log                     global
    option                  tcplog
    timeout connect         10s
    timeout client          1m
    timeout server          1m

frontend k8s-api
    bind 10.10.10.200:6443
    mode tcp
    option tcplog
    default_backend k8s-masters

backend k8s-masters
    mode tcp
    balance roundrobin
    option tcp-check
    server master1 10.10.10.70:6443 check fall 3 rise 2
    server master2 10.10.10.71:6443 check fall 3 rise 2
    server master3 10.10.10.72:6443 check fall 3 rise 2
EOF
```

!!! note "포트 충돌 방지"
    `bind`를 `*:6443` 대신 VIP로 지정하는 이유는 API 서버(노드 IP 바인딩)와의 포트 충돌을 방지하기 위함입니다.

#### 2) Keepalived 설정 (전체 마스터 노드)

각 노드별 `state`, `priority`, `interface` 값을 아래 표에 따라 다르게 설정합니다.

| 노드 | state | priority |
| :--- | :--- | :--- |
| Master-1 | `MASTER` | `101` |
| Master-2 | `BACKUP` | `100` |
| Master-3 | `BACKUP` | `99` |

```bash
# Master-1 기준 예시 (Master-2, 3은 state/priority 값 수정)
cat <<EOF | sudo tee /etc/keepalived/keepalived.conf
global_defs {
    router_id LVS_DEVEL
}

vrrp_script check_haproxy {
    script "/usr/bin/killall -0 haproxy"
    interval 3
    weight -2
    fall 10
    rise 2
}

vrrp_instance VI_1 {
    state MASTER              # Master-2, 3은 BACKUP
    interface eth0            # 본인 네트워크 인터페이스명으로 변경 필수
    virtual_router_id 51
    priority 101              # M1: 101, M2: 100, M3: 99
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass 42          # 모든 노드 동일하게 설정
    }

    virtual_ipaddress {
        10.10.10.200          # VIP 주소
    }

    track_script {
        check_haproxy
    }
}
EOF
```

#### 3) 서비스 시작 및 VIP 확인

```bash
sudo systemctl enable --now haproxy
sudo systemctl enable --now keepalived

# VIP 활성화 확인 (Master-1에서 VIP가 보여야 함)
ip addr show eth0 | grep 10.10.10.200
```

---

### 옵션 B: Localhost LB 방식 (VIP 불가 환경)

VIP 사용이 어려운 경우 각 노드(마스터/워커 전체)에 HAProxy를 설치하고 `127.0.0.1:8443`을 통해 마스터로 통신하게 합니다.

```bash
sudo cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.bak

cat <<EOF | sudo tee /etc/haproxy/haproxy.cfg
global
    maxconn     4000
    daemon

defaults
    mode                    tcp
    timeout connect         10s
    timeout client          1m
    timeout server          1m

frontend k8s-api-proxy
    bind 127.0.0.1:8443
    default_backend k8s-masters

backend k8s-masters
    balance roundrobin
    option tcp-check
    server master1 10.10.10.70:6443 check
    server master2 10.10.10.71:6443 check
    server master3 10.10.10.72:6443 check
EOF

sudo systemctl enable --now haproxy
```

---

## 🚀 Phase 4: 마스터 초기화 (Master-1)

### 🅰️ HA 구성 (VIP 사용) 초기화

RHEL/Rocky 9 계열은 SAN 검증이 엄격하므로 모든 마스터 IP를 명시해야 합니다.

```bash
sudo kubeadm init \
  --control-plane-endpoint "10.10.10.200:6443" \
  --upload-certs \
  --apiserver-cert-extra-sans="10.10.10.200,10.10.10.70,10.10.10.71,10.10.10.72,127.0.0.1" \
  --pod-network-cidr=192.168.0.0/16 \
  --service-cidr=10.96.0.0/12 \
  --kubernetes-version v1.30.0
```

!!! warning "포트 충돌 방지 (중요)"
    HAProxy가 VIP의 6443을 점유하고 있으므로, 초기화 후 **kube-apiserver의 bind-address를 실제 IP로 수정**해야 합니다.
    `/etc/kubernetes/manifests/kube-apiserver.yaml` 의 `spec.containers[].command` 섹션에 추가:

    ```yaml
    - --bind-address=10.10.10.70   # 각 마스터의 실제 IP
    ```

### 🅱️ 단일 마스터 구성 초기화

```bash
sudo kubeadm init \
  --control-plane-endpoint "10.10.10.70:6443" \
  --pod-network-cidr=192.168.0.0/16 \
  --service-cidr=10.96.0.0/12 \
  --kubernetes-version v1.30.0
```

### kubeconfig 설정 (컨트롤 플레인 공통)

초기화 성공 후 아래 명령어로 kubeconfig를 설정합니다.

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

---

## 🚀 Phase 4-1: 추가 마스터 노드 조인 (Master-2, 3 — HA 구성 시에만)

Master-1 초기화 출력에서 **`--control-plane`** 조인 명령을 복사하여 실행합니다.

```bash
sudo kubeadm join 10.10.10.200:6443 --token <TOKEN> \
    --discovery-token-ca-cert-hash sha256:<HASH> \
    --control-plane --certificate-key <CERT_KEY>
```

조인 완료 후 **즉시** 해당 노드의 IP로 bind-address를 수정합니다.

```bash
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Master-2: - --bind-address=10.10.10.71
# Master-3: - --bind-address=10.10.10.72
```

kubeconfig도 각 노드에 설정합니다.

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

---

## 🚀 Phase 5: CNI 및 추가 작업

### 5.1 Calico CNI 설치

```bash
kubectl apply -f ~/k8s-1.30/k8s/utils/calico.yaml

# Calico Pod가 Running이 될 때까지 대기
watch kubectl get nodes
```

!!! note "Calico CIDR 일치 확인"
    `calico.yaml` 내부의 `CALICO_IPV4POOL_CIDR` 값이 `--pod-network-cidr`(`192.168.0.0/16`)과 반드시 일치해야 합니다.

Calico가 배포되지 않을 경우 kubelet 오류일 가능성이 높습니다. Phase 6의 재설치 절차로 초기화 후 `kubeadm init`을 재실행합니다.

### 5.2 Helm 설치

```bash
cd ~/k8s-1.30/k8s/binaries
tar -xzvf helm-v3.14.0-linux-amd64.tar.gz
sudo mv linux-amd64/helm /usr/local/bin/helm
helm version
```

### 5.3 워커 노드 조인

Master-1 초기화 결과로 나온 `kubeadm join` 명령어를 각 워커 노드에서 실행합니다.
Phase 4에서 선택한 LB 방식에 따라 접속 대상이 다릅니다.

#### 옵션 A (HA - VIP 사용)

```bash
sudo kubeadm join 10.10.10.200:6443 --token <TOKEN> \
    --discovery-token-ca-cert-hash sha256:<HASH>
```

#### 옵션 B (HA - Localhost LB 사용)

각 워커 노드에도 HAProxy가 `8443` 포트로 떠 있어야 합니다.

```bash
sudo kubeadm join 127.0.0.1:8443 --token <TOKEN> \
    --discovery-token-ca-cert-hash sha256:<HASH>
```

#### 옵션 C (단일 마스터)

```bash
sudo kubeadm join 10.10.10.70:6443 --token <TOKEN> \
    --discovery-token-ca-cert-hash sha256:<HASH>
```

#### 트러블슈팅: 호스트네임 오류

조인 시 `hostname "k8s-worker-node-1.novalocal" could not be reached` 오류가 발생하면 `/etc/hosts`에 FQDN을 추가합니다.

```bash
# /etc/hosts 예시
10.10.10.70 master1
10.10.10.73 worker1 worker1.novalocal
10.10.10.74 worker2 worker2.novalocal
```

### 5.4 설치 확인

```bash
kubectl get nodes
kubectl get pods -n kube-system
```

모든 노드가 `Ready` 상태이고 kube-system Pod들이 `Running`이면 설치 완료입니다.

#### CIDR 설정 확인

```bash
# kube-controller-manager에서 CIDR 확인
kubectl get pod -n kube-system -l component=kube-controller-manager -o yaml | grep cluster

# Calico IP Pool 확인
kubectl get ippools -o yaml
```

---

## 🧹 재설치 시 초기화 절차

설치 중 오류가 발생하여 처음부터 다시 시작해야 하는 경우 다음 명령어를 순서대로 실행합니다.

```bash
# 1. kubeadm 리셋
sudo kubeadm reset -f

# 2. 잔여 설정 및 데이터 삭제
sudo rm -rf /etc/cni/net.d
rm -rf $HOME/.kube
sudo rm -rf /root/.kube
sudo rm -rf /var/lib/etcd /var/lib/kubelet

# 3. 네트워크 규칙 초기화
sudo iptables -F && sudo iptables -t nat -F && sudo iptables -t mangle -F && sudo iptables -X

# 4. 런타임 재시작
sudo systemctl restart containerd
```

재실행 전 Swap이 다시 활성화되지 않았는지 확인합니다.

```bash
sudo swapoff -a
```
