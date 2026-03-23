# 3. 폐쇄망에서 Helm, Harbor, Envoy(Ingress는 비권장) 설치

- **가이드 환경**
  - **OS**: Rocky Linux 9.6
  - **kubelet**: v1.30.14
- 폐쇄망용 K8s 설치 파일이 준비되어 있어야 합니다.
- [설치 파일 위치 (Google Drive)](https://drive.google.com/drive/folders/1joMQRpZPWzKgU9BBsdxy3b0qzJMWpBC8?usp=sharing)

---

## 🚀 Phase 1: Helm 설치 (Master-1 Only)

Helm은 마스터 노드에서 명령어를 내리는 도구이므로, **마스터 노드 1대**에만 설치하면 됩니다.

**[실행 위치: K8s-Master-Node-1]**

```bash
# 1. 바이너리 폴더로 이동
cd ~/k8s-1.30/k8s/binaries

# 2. 압축 해제
tar -zxvf helm-v3.14.0-linux-amd64.tar.gz

# 3. 실행 파일을 시스템 경로로 이동
sudo mv linux-amd64/helm /usr/local/bin/helm

# 4. 설치 확인
helm version
```

---

## 🚀 Phase 2: Envoy 설치

2026년 3월부터 `Ingress Nginx`에 대한 공식 지원이 종료됨에 따라, Kubernetes 표준인 **Gateway API**와 **Envoy** 사용을 강력히 권장합니다.

### 0. 아키텍처 개요 (Standard Architecture)

- **Network Mode**: `hostNetwork: false` (K8s 내부망 사용, 노드망과 격리)
- **Service Type**: `LoadBalancer` 또는 `NodePort`
- **Traffic Flow**:
  `Client` → `LB/VIP (80/443)` → `Envoy Pod (30080/30443)` → `Backend Pod`

### 1. 이미지 로드 및 설치 실행

**[전체 노드]**

```bash
cd ./envoy-1.36.3
sudo bash ./images/upload_images.sh
```

**[Master-1 노드]**

```bash
sudo bash install_envoy-gateway.sh
```

**설치 시 주요 선택 사항:**

- **LB vs NodePort**: 환경에 맞는 진입점 선택.
- **노드 고정**: 성능 최적화를 위해 특정 노드에 Envoy Proxy 배치 가능.
- **전역 정책**: `policy-global.yaml` 적용 시 헤더 보안 및 트래픽 정책이 자동 반영됩니다.

### 2. 배포 후 상태 확인 및 네트워크 연동

#### 🛠️ [Case C] LoadBalancer 수동 할당 (MetalLB 미사용 시)

서비스가 `<pending>` 상태인 경우 워커 노드 IP를 수동으로 바인딩합니다.

```bash
SVC_NAME=$(kubectl get svc -n envoy-gateway-system -o jsonpath='{.items[?(@.spec.type=="LoadBalancer")].metadata.name}')

# 워커 노드 IP들로 패치
kubectl patch svc -n envoy-gateway-system $SVC_NAME -p '{"spec":{"externalIPs":["10.10.10.73","10.10.10.74"]}}'
```

#### 🛠️ [Case D] NodePort 연동 (VIP/L4 사용 시)

NodePort 설치 시 HTTP **30080**, HTTPS **30443** 포트가 고정 사용됩니다.

- **하드웨어 L4**: 워커 노드 IP와 포트(30080, 30443)를 Real Server로 등록.
- **소프트웨어 LB (HAProxy)**: 80/443 포트 트래픽을 워커 노드 포트로 중계.
- **운영 팁**: `externalTrafficPolicy: Local` 설정을 통해 클라이언트 원본 IP를 보존할 수 있습니다.

### 3. 운영 및 로그 확인

Envoy Gateway는 동적 관리를 위해 파드 이름이 계속 변경되므로 **Label Selector(`-l`)** 사용이 필수입니다.

```bash
# Envoy Proxy(트래픽 처리) 로그 확인
kubectl logs -n envoy-gateway-system -f -l gateway.envoyproxy.io/owning-gateway-name=cmp-gateway

# Gateway Controller(설치/배포) 로그 확인
kubectl logs -n envoy-gateway-system -f -l app.kubernetes.io/name=envoy-gateway
```

---

## 🚀 Phase 3: Harbor 설치

### 0. Local Path Provisioner (영구 저장소)

**[Master-1 노드]**

```bash
cd ~/k8s-1.30/k8s/utils
kubectl apply -f local-path-storage.yaml

# 기본 스토리지 클래스로 지정 (Harbor 자동 할당용)
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

### 1. Harbor 배포

**[Harbor를 배치할 특정 워커 노드]**

```bash
cd harbor-images-upload/
sudo bash upload_images.sh

sudo mkdir -p /data/harbor && sudo chmod -R 777 /data/harbor
```

**[Master-1 노드]**
`harbor_install_offline.sh`에서 `EXTERNAL_HOSTNAME`, `SAVE_PATH`, `NODE_NAME` 등을 수정 후 실행합니다.

```bash
sudo bash harbor_install_offline.sh
```

### 2. Containerd 연동 (Insecure Registry 설정)

HTTP 통신이나 사설 인증서 사용 시 모든 워커 노드에서 아래 설정이 필요합니다.

```bash
# Harbor 도메인/IP에 대한 인증 설정 (예: 10.10.10.73:30002)
sudo mkdir -p /etc/containerd/certs.d/<HARBOR_IP>:30002/

cat <<EOF | sudo tee /etc/containerd/certs.d/<HARBOR_IP>:30002/hosts.toml
server = "http://<HARBOR_IP>:30002"
[host."http://<HARBOR_IP>:30002"]
  capabilities = ["pull", "resolve"]
  skip_verify = true
EOF

sudo systemctl restart containerd
```

---

## 🚀 Phase 4: 접속 테스트 및 이미지 관리

1. **PC 설정**: `/etc/hosts` 파일에 Harbor 도메인과 할당된 IP를 등록합니다.
2. **이미지 푸시**: `sudo ctr -n k8s.io images push --plain-http ...` 명령어로 Harbor에 등록합니다.
3. **이미지 풀**: 워커 노드에서 정상적으로 이미지가 내려받아지는지 확인합니다.
