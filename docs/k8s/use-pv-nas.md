# NFS Provisioner v4.0.2 오프라인 설치 가이드

폐쇄망 환경의 Kubernetes 클러스터에 NFS 동적 스토리지 프로비저닝(NFS Subdir External Provisioner)을 구성하는 절차를 안내합니다.

## 전제 조건

- Kubernetes 클러스터 구성 완료
- `kubectl` CLI 사용 가능
- NFS 서버로 사용할 노드 또는 외부 NAS 준비

---

## Phase 1: OS 패키지 설치 (NFS 클라이언트)

모든 워커 노드에서 실행하여 `mount.nfs` 기능을 활성화합니다.

```bash
# Ubuntu의 경우
cd scripts/ubuntu
chmod +x install.sh
./install.sh

# RHEL / Rocky Linux의 경우
cd scripts/rhel_rocky
chmod +x install.sh
./install.sh
```

## Phase 2: 컨테이너 이미지 로드

```bash
# images/load_image.sh 실행 (ctr을 사용하여 로컬 로드)
chmod +x images/load_image.sh
./images/load_image.sh
```

대상 이미지: `registry.k8s.io/sig-storage/nfs-subdir-external-provisioner:v4.0.2`

## Phase 3: 매니페스트 수정 및 배포

`manifests/nfs-provisioner.yaml` 파일에서 아래 항목을 환경에 맞게 수정합니다.

| 항목 | 설명 | 예시 |
| :--- | :--- | :--- |
| `image` | 내부 레지스트리 이미지 주소 | `<NODE_IP>:30002/library/nfs-subdir-external-provisioner:v4.0.2` |
| `NFS_SERVER` | NFS 서버 IP | `192.168.1.100` |
| `NFS_PATH` | NFS 공유 디렉토리 경로 | `/data/nfs-share` |

수정 후 배포합니다.

```bash
kubectl apply -f manifests/nfs-provisioner.yaml
```

## Phase 4: 설치 확인

```bash
# 파드 및 스토리지 클래스 확인
kubectl get pods -n nfs-provisioner
kubectl get storageclass
```

---

## 💡 운영 참고 사항

- **StorageClass 설정**: `archiveOnDelete: "false"` 설정은 PVC 삭제 시 실제 데이터를 삭제합니다. 데이터 보호가 필요하면 `true` 로 변경하세요.
- **방화벽 확인**: 노드 간 **TCP/UDP 2049(NFS), 111(RPC)** 포트가 열려 있어야 정상적으로 마운트됩니다.

## 디렉토리 구조 (Standard Structure)

| 경로 | 설명 |
| :--- | :--- |
| `images/` | 컨테이너 이미지 `.tar` 및 로드 스크립트 |
| `manifests/` | Deployment, StorageClass, RBAC 정의 |
| `scripts/` | OS별 NFS 패키지 설치/삭제 스크립트 |

## 삭제

```bash
# 각 OS 환경에 맞는 스크립트 실행
./scripts/ubuntu/uninstall.sh
```
