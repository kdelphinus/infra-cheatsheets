# 2. 폐쇄망에서 Kubernetes와 Helm 설치

본 문서는 폐쇄망 환경에서 **kubeadm**을 사용하여 Kubernetes v1.30.x 클러스터를 구축하는 절차를 정의합니다.

- **가이드 환경**
  - **OS**: Rocky Linux 9.6 (추천) / Ubuntu 22.04+
  - **K8s Version**: v1.30.14
  - **Container Runtime**: containerd v2.x
- [설치 파일 위치 (Google Drive)](https://drive.google.com/drive/folders/1joMQRpZPWzKgU9BBsdxy3b0qzJMWpBC8?usp=sharing)

> !!! note "네트워크 전제 조건"
> 폐쇄망 환경이라도 각 노드 간의 통신은 전면 허용되어야 하며, `169.254.169.254/32` (cloud-init 메타데이터 IP)에 대한 80포트 아웃바운드 규칙이 허용되어야 정상적인 노드 초기화가 가능합니다.

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

### 1.3 Containerd 설정 (Harbor 연동 대비)

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

### 옵션 A: VIP 방식 (Keepalived + HAProxy - 권장)

- **전제**: 마스터 노드 3대 및 가상 IP(VIP: `10.10.10.200`) 필요.
- **커널 설정**: VIP 바인딩 허용
  ```bash
  echo "net.ipv4.ip_nonlocal_bind = 1" | sudo tee /etc/sysctl.d/haproxy.conf
  sudo sysctl --system
  ```

#### 1) HAProxy 설정 (`/etc/haproxy/haproxy.cfg`)
```bash
frontend k8s-api
    bind 10.10.10.200:6443 # VIP로 바인딩하여 API 서버와 포트 충돌 방지
    default_backend k8s-masters

backend k8s-masters
    balance roundrobin
    server master1 10.10.10.70:6443 check
    server master2 10.10.10.71:6443 check
    server master3 10.10.10.72:6443 check
```

#### 2) Keepalived 설정 (`/etc/keepalived/keepalived.conf`)
- Master-1은 `state MASTER`, `priority 101`. 나머지는 `BACKUP`, `100/99`로 설정합니다.

### 옵션 B: Localhost LB 방식 (VIP 불가 환경)

VIP 사용이 어려운 경우 각 노드(마스터/워커 전체)에 HAProxy를 설치하고 `127.0.0.1:8443`을 통해 마스터로 통신하게 합니다.

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

> !!! warning "포트 충돌 방지 (중요)"
> HAProxy가 VIP의 6443을 점유하고 있으므로, 초기화 후 **kube-apiserver의 bind-address를 실제 IP로 수정**해야 합니다.
> `/etc/kubernetes/manifests/kube-apiserver.yaml` 수정:
> `- --bind-address=10.10.10.70` (각 마스터의 실제 IP)

---

## 🚀 Phase 5: CNI 및 추가 작업

### 5.1 Calico CNI 설치
```bash
kubectl apply -f ~/k8s-1.30/k8s/utils/calico.yaml
```

### 5.2 Helm 설치
```bash
sudo mv ~/k8s-1.30/k8s/binaries/helm /usr/local/bin/helm
chmod +x /usr/local/bin/helm
```

### 5.3 워커 노드 조인
Master-1 초기화 결과로 나온 `kubeadm join` 명령어를 각 워커 노드에서 실행합니다.

---

## 🧹 재설치 시 초기화 절차

설치 중 오류가 발생하여 처음부터 다시 시작해야 하는 경우 다음 명령어를 순서대로 실행합니다.

```bash
# 1. kubeadm 리셋
sudo kubeadm reset -f

# 2. 잔여 설정 및 데이터 삭제
sudo rm -rf /etc/cni/net.d $HOME/.kube /var/lib/etcd /var/lib/kubelet

# 3. 네트워크 규칙 초기화
sudo iptables -F && sudo iptables -t nat -F && sudo iptables -t mangle -F && sudo iptables -X

# 4. 런타임 재시작
sudo systemctl restart containerd
```
