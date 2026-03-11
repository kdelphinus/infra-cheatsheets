# 2. 폐쇄망에서 ArgoCD 설치

1. **가이드 환경**
    - OS: Rocky Linux 9.6
    - K8s Version: 1.30.x
    - ArgoCD: v2.12.1 (Helm Chart 7.4.1)

2. **전제 조건**
    - Kubernetes 클러스터가 정상 동작 중이어야 합니다 (`kubectl get nodes` → Ready).
    - Harbor가 설치되어 있어야 합니다.
    - (도메인 접속 사용 시) Envoy Gateway가 설치되어 있어야 합니다.
    - 이 가이드는 마스터 노드의 `~/argocd-2.12.1` 경로에 설치 파일이 준비되어 있다고 가정합니다.

---

## 🚀 Phase 1: 이미지 업로드

Harbor에 ArgoCD 이미지를 업로드합니다.

**[실행 위치: Master 1]**

`scripts/upload_images.sh` 상단 Config를 현재 환경에 맞게 수정합니다.

```bash
HARBOR_REGISTRY="<HARBOR_IP>:30002"
HARBOR_PROJECT="<PROJECT>"
HARBOR_USER="admin"
HARBOR_PASSWORD="<PASSWORD>"
```

수정 후 실행합니다.

```bash
cd ~/argocd-2.12.1/scripts
chmod +x upload_images.sh
./upload_images.sh
```

---

## 🚀 Phase 2: 데이터 영속성 구성 (스토리지 설정)

ArgoCD의 Redis 및 Repo 서버 캐시를 저장할 스토리지를 구성합니다.
`hostPath` 또는 NAS(NFS) 중 선택합니다.

### hostPath 사용 시

데이터가 저장될 디렉토리를 노드에 생성합니다.

```bash
# Redis 데이터
sudo mkdir -p /data/argocd/redis

# Repo 서버 캐시
sudo mkdir -p /data/argocd/repo-cache

sudo chmod -R 777 /data/argocd
```

### NAS(NFS) 사용 시

모든 노드에 NFS 클라이언트가 설치되어 있어야 합니다.
`nas-pv.yaml`의 NFS 서버 주소와 경로를 실제 환경에 맞게 수정한 후 적용합니다.

```bash
kubectl apply -f ~/argocd-2.12.1/nas-pv.yaml
```

---

## 🚀 Phase 3: ArgoCD 설치

`install-argocd.sh` 상단 Config 블록만 수정하면 됩니다.

```bash
# ==================== Config ====================
# Harbor Registry
HARBOR_REGISTRY="<HARBOR_IP>:30002"
HARBOR_PROJECT="<PROJECT>"

# Storage: "none" | "nas" | "hostpath"
STORAGE_TYPE="hostpath"

# NAS (NFS) Settings - STORAGE_TYPE="nas" 일 때 사용
NAS_SERVER="192.168.1.50"
NAS_REDIS_PATH="/nas/argocd/redis"
NAS_REPO_PATH="/nas/argocd/repo"

# hostPath Settings - STORAGE_TYPE="hostpath" 일 때 사용
HOSTPATH_REDIS="/data/argocd/redis"
HOSTPATH_REPO="/data/argocd/repo-cache"

# Networking
NODEPORT="30001"                    # NodePort 번호
DOMAIN="argocd.devops.internal"     # HTTPRoute 도메인, "" 이면 HTTPRoute 미생성 및 CoreDNS 등록 건너뜀
TLS_ENABLED="false"                 # "true" | "false" — https/http 결정
GATEWAY_NAME="cmp-gateway"
GATEWAY_NAMESPACE="envoy-gateway-system"
# ================================================
```

설정 후 실행합니다.

```bash
chmod +x ~/argocd-2.12.1/install-argocd.sh
./install-argocd.sh
```

스크립트가 자동으로 처리하는 항목:

- namespace 생성 (`argocd`)
- NAS PV/PVC 적용 (nas 선택 시)
- Helm 설치 (Harbor 이미지 경로 + 스토리지 설정 반영)
- NodePort 서비스 생성
- HTTPRoute 생성 (`DOMAIN` 설정 시)
- CoreDNS에 도메인 등록 (`DOMAIN` 설정 시)

`DOMAIN`이 설정된 경우 스크립트 실행 중 DNS 서버 등록 여부를 묻습니다.

- DNS 서버에 이미 등록된 경우 → CoreDNS 등록을 건너뜁니다.
- 미등록(hosts 방식) → 클러스터 내부 CoreDNS에 자동 등록합니다.

> **클라이언트 PC hosts 등록은 별도로 필요합니다.** 스크립트 완료 시 안내 문구가 출력됩니다.

---

## 🚀 Phase 4: 설치 확인 및 접속

### 1. Pod 상태 확인

```bash
watch kubectl get pods -n argocd
```

`argocd-server`, `argocd-repo-server`, `argocd-application-controller`, `argocd-redis` 등이 모두 `Running`이 되면 정상입니다.

### 2. 초기 비밀번호 확인

초기 ID는 `admin`이며, 비밀번호는 아래 명령으로 확인합니다.

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
```

> **주의:** 초기 로그인 후 반드시 비밀번호를 변경하고, 아래 명령으로 secret을 삭제하세요.
>
> ```bash
> kubectl delete secret argocd-initial-admin-secret -n argocd
> ```

### 3. 접속 방법

| 방법 | 주소 |
| :--- | :--- |
| NodePort | `http://<NODE_IP>:30001` |
| 도메인 | `http://argocd.devops.internal` (DNS/hosts 등록 필요) |
| 포트 포워딩 (임시) | `kubectl port-forward svc/argocd-server -n argocd 8080:80` → `http://localhost:8080` |

도메인 접속 시 hosts 파일 또는 DNS에 아래 항목을 추가합니다.

```text
<GATEWAY_IP>  argocd.devops.internal
```

### 4. 서비스 확인

```bash
kubectl get svc -n argocd
kubectl get httproute -n argocd   # 도메인 설정 시
```
