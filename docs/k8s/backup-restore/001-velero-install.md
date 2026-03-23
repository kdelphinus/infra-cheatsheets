# 🚀 Velero v1.14.1 오프라인 설치 가이드 (MinIO 통합형)

본 문서는 폐쇄망 Kubernetes 환경에서 **MinIO 전용 저장소**를 포함하여 Velero 백업 체계를 구축하고, 클러스터 데이터를 보호 및 복구하는 절차를 정의합니다.

## 📋 구성 명세

| 항목 | 버전 | 용도 |
| :--- | :--- | :--- |
| **Velero CLI** | **v1.14.1** | 백업 및 복구 명령 도구 |
| **Velero Chart** | **v7.2.1** | Velero 서버 (Helm) |
| **MinIO** | **RELEASE.2024-12-18** | S3 호환 백업 스토리지 |
| **MinIO Client (mc)** | **RELEASE.2024-11-21** | 스토리지 관리 도구 |

---

## 🛠️ 설치 전제 조건

- Kubernetes 클러스터 구성 완료
- Helm v3.x 설치 완료
- Harbor 레지스트리 접근 가능 (`<NODE_IP>:30002`)

---

## 1단계: CLI 설치 및 이미지 업로드

### 1.1 Velero CLI 설치

```bash
# 바이너리 압축 해제 및 실행 경로 이동
tar -xvf velero-v1.14.1-linux-amd64.tar.gz
sudo mv velero-v1.14.1-linux-amd64/velero /usr/local/bin/
velero version --client-only
```

### 1.2 Harbor에 이미지 업로드

컴포넌트 루트 디렉토리의 `images/upload_images_to_harbor_v3-lite.sh` 파일을 사용합니다.

```bash
# HARBOR_REGISTRY: <NODE_IP>:30002
chmod +x images/upload_images_to_harbor_v3-lite.sh
./images/upload_images_to_harbor_v3-lite.sh
```

---

## 2단계: 설치 실행

컴포넌트 루트의 `scripts/install.sh` 파일의 설정을 확인한 후 실행합니다.

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

**스크립트 자동 처리 항목:**
- 네임스페이스 (`velero`) 생성
- MinIO 설치 및 전용 버킷 (`velero`) 자동 생성
- Velero 서버 배포 및 MinIO 백업 저장소 연동
- 백업 상태 확인용 `BackupStorageLocation` 등록

---

## 3단계: 설치 확인 및 웹 접속

### 3.1 서비스 상태 확인

```bash
# Pod 상태 및 저장소 연동 상태 확인 (Phase: Available 확인 필수)
kubectl get pods -n velero
velero backup-location get
```

### 3.2 MinIO 웹 콘솔 접속

백업된 데이터 파일을 시각적으로 확인하기 위해 MinIO 웹 인터페이스에 접속할 수 있습니다.

- **주소**: `http://minio-velero.devops.internal`
- **계정/비밀번호**: `minioadmin` / `minioadmin`

---

## 4단계: 백업 및 복구 실무 테스트

### 4.1 백업 생성 (Backup)

```bash
# 전체 클러스터 백업
velero backup create full-cluster-backup --include-namespaces '*'

# 특정 네임스페이스(예: monitoring) 백업
velero backup create monitoring-backup --include-namespaces monitoring

# 백업 목록 및 상태 확인
velero backup get
```

### 4.2 데이터 복구 (Restore)

```bash
# 1. 전체 복구 실행
velero restore create --from-backup full-cluster-backup

# 2. 특정 네임스페이스만 선택 복구
velero restore create --from-backup monitoring-backup --include-namespaces monitoring

# 3. 복구 프로세스 상태 확인
velero restore get
velero restore describe <복구명>
```

---

## 🗑️ 삭제 (Uninstall)

```bash
./scripts/uninstall.sh
```
