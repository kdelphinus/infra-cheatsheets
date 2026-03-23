# 🚀 NFS Provisioner v4.0.2 오프라인 설치 가이드

본 문서는 폐쇄망 Kubernetes 환경에서 **NFS 동적 스토리지 프로비저닝(Dynamic Provisioning)**을 구성하여, 애플리케이션이 자동으로 볼륨을 할당받을 수 있도록 하는 절차를 정의합니다.

## 📋 구성 명세

| 항목 | 버전 | 용도 |
| :--- | :--- | :--- |
| **NFS Subdir Provisioner** | **v4.0.2** | NFS 동적 할당 컨트롤러 |
| **StorageClass** | `nfs-client` | 기본 스토리지 클래스 명칭 |
| **대상 OS** | Rocky Linux / Ubuntu | 클러스터 워커 노드 공통 |

---

## 🛠️ 설치 전제 조건

- Kubernetes 클러스터 구성 완료
- NFS 서버로 사용할 노드 또는 외부 NAS 준비
- Harbor 레지스트리 접근 가능 (`<NODE_IP>:30002`)

---

## 1단계: OS 패키지 설치 (NFS 클라이언트)

모든 워커 노드에서 실행하여 `mount.nfs` 기능을 활성화해야 합니다.

```bash
# Ubuntu의 경우
chmod +x scripts/ubuntu/install.sh
./scripts/ubuntu/install.sh

# RHEL / Rocky Linux의 경우
chmod +x scripts/rhel_rocky/install.sh
./scripts/rhel_rocky/install.sh
```

---

## 2단계: 이미지 Harbor 업로드

컴포넌트 루트 디렉토리에서 실행합니다.

```bash
# 1. 이미지 로드 (ctr 사용)
sudo ctr -n k8s.io images import images/nfs-provisioner.tar

# 2. Harbor 업로드 (upload_images_to_harbor_v3-lite.sh 사용)
# HARBOR_REGISTRY: <NODE_IP>:30002
./images/upload_images_to_harbor_v3-lite.sh
```

---

## 3단계: 매니페스트 수정 및 배포

`manifests/nfs-provisioner.yaml` 파일의 설정을 사용자 환경에 맞게 수정합니다.

| 항목 | 설명 | 예시 |
| :--- | :--- | :--- |
| **`image`** | 내부 레지스트리 이미지 주소 | `<NODE_IP>:30002/library/nfs-subdir-external-provisioner:v4.0.2` |
| **`NFS_SERVER`** | NFS 서버 IP 주소 | `192.168.1.100` |
| **`NFS_PATH`** | NFS 공유 디렉토리 절대 경로 | `/data/nfs-share` |

수정 완료 후 배포를 실행합니다.

```bash
kubectl apply -f manifests/nfs-provisioner.yaml
```

---

## 4단계: 설치 확인 및 테스트

### 4.1 설치 상태 확인

```bash
# 컨트롤러 파드 상태 확인
kubectl get pods -n nfs-provisioner

# StorageClass 생성 확인
kubectl get storageclass
```

### 4.2 동적 할당 테스트 (PVC 생성)

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-nfs-pvc
spec:
  storageClassName: nfs-client
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 1Gi
```

```bash
kubectl apply -f test-pvc.yaml
kubectl get pvc test-nfs-pvc # Status가 Bound인지 확인
```

---

## 💡 운영 참고 사항

- **네트워크 포트**: 노드 간 **TCP/UDP 2049(NFS)** 및 **111(RPC)** 포트가 개방되어 있어야 합니다.
- **데이터 보존 정책**: `StorageClass`의 `archiveOnDelete: "false"` 설정은 PVC 삭제 시 실제 데이터를 삭제합니다. 데이터 보존이 필요하면 `true`로 설정하십시오.
- **노드 고정**: NFS 서버와의 통신 지연을 줄이기 위해 프로비저너를 특정 노드에 고정 배포하는 것을 권장합니다.

---

## 🗑️ 삭제 (Uninstall)

```bash
# OS별 스크립트 실행 (패키지 제거 및 매니페스트 삭제)
./scripts/ubuntu/uninstall.sh
# 또는
./scripts/rhel_rocky/uninstall.sh
```
