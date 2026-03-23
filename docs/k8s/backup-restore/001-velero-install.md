# 🚀 Velero 오프라인 설치 가이드 (MinIO 통합형)

폐쇄망 환경에서 전용 MinIO 저장소를 포함하여 Velero 백업 체계를 구축하고 데이터를 복구하는 절차를 설명합니다.

## 전제 조건

- Kubernetes 클러스터 구성 완료
- Helm v3.14.0 설치 완료
- `kubectl` CLI 사용 가능
- Harbor 레지스트리 접근 가능 (`<NODE_IP>:30002`)

## 1단계: CLI 설치 및 이미지 업로드

### 1.1 Velero CLI 설치

인터넷 환경에서 다운로드한 바이너리를 실행 경로로 이동합니다.

```bash
tar -xvf velero-v1.14.1-linux-amd64.tar.gz
sudo mv velero-v1.14.1-linux-amd64/velero /usr/local/bin/
velero version --client-only
```

### 1.2 Harbor에 이미지 업로드

모든 작업은 컴포넌트 루트 디렉토리에서 실행합니다.

```bash
# images/upload_images_to_harbor_v3-lite.sh 상단 Config 수정
# HARBOR_REGISTRY: <NODE_IP>:30002

./images/upload_images_to_harbor_v3-lite.sh
```

## 2단계: 설치 실행

`scripts/install.sh` 파일 상단의 `HARBOR_IP`를 수정한 뒤 실행합니다.

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

스크립트 자동 처리 항목:
- 네임스페이스(`velero`) 생성
- MinIO 설치 및 버킷(`velero`) 생성
- Velero 서버 설치 및 MinIO 연동
- BackupStorageLocation 생성

## 3단계: 설치 확인

```bash
# 파드 및 저장소 상태 확인
kubectl get pods -n velero
velero backup-location get
```

- **MinIO 콘솔 접속**: `http://minio-velero.devops.internal` (ID/PW: `minioadmin` / `minioadmin`)

## 4단계: 백업 및 복구 테스트

### 4.1 백업 실행 (Backup)

```bash
# 전체 백업 생성
velero backup create cluster-full-backup --include-namespaces '*'

# 백업 목록 확인
velero backup get
```

### 4.2 복구 실행 (Restore)

```bash
# 전체 복구 실행
velero restore create --from-backup cluster-full-backup

# 복구 상태 확인
velero restore get
```

## 디렉토리 구조 (Standard Structure)

| 경로 | 설명 |
| :--- | :--- |
| `charts/` | Velero 및 MinIO Helm 차트 |
| `images/` | 컨테이너 이미지 및 업로드 스크립트 |
| `manifests/` | BackupLocation, Secret 등 설정 파일 |
| `scripts/` | 설치/삭제/다운로드 자동화 스크립트 |

## 삭제

```bash
./scripts/uninstall.sh
```
