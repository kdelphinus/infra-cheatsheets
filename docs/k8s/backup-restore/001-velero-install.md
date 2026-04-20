# Velero v1.18.0 오프라인 설치 가이드 (MinIO 통합형)

폐쇄망 Kubernetes 환경에서 **MinIO 전용 저장소**를 포함하여 Velero 백업 체계를 구축하고, 클러스터 데이터를 보호 및 복구하는 절차를 정의합니다.

## 구성 명세

| 항목 | 버전 | 용도 |
| :--- | :--- | :--- |
| **Velero CLI** | **v1.18.0** | 백업 및 복구 명령 도구 |
| **Velero Chart** | **v12.0.0** | Velero 서버 (Helm) |
| **velero-plugin-for-aws** | **v1.14.0** | S3 호환 스토리지 연동 플러그인 |
| **MinIO** | **RELEASE.2024-12-18** | S3 호환 백업 스토리지 |
| **MinIO Client (mc)** | **RELEASE.2024-11-21** | 스토리지 관리 도구 |

---

## 사전 조건

- Kubernetes 클러스터 구성 완료
- Helm v3.x 설치 완료
- Harbor 레지스트리 접근 가능 (`<NODE_IP>:30002`)

---

## 1단계: 에셋 준비 (인터넷 가능 환경)

```bash
chmod +x scripts/download_assets.sh
./scripts/download_assets.sh
# 생성된 파일들을 폐쇄망 서버의 velero-1.18.0/ 폴더로 복사
```

---

## 2단계: CLI 설치 및 이미지 업로드 (폐쇄망 환경)

### 2.1 Velero CLI 설치

```bash
tar -xvf velero-v1.18.0-linux-amd64.tar.gz
sudo mv velero-v1.18.0-linux-amd64/velero /usr/local/bin/
velero version --client-only
```

### 2.2 Harbor에 이미지 업로드

```bash
./images/upload_images_to_harbor_v3-lite.sh
```

---

## 3단계: 설치 실행

```bash
./scripts/install.sh
```

스크립트를 실행하면 아래 항목을 대화형으로 입력합니다.

### 이미지 소스 선택

```
이미지 소스를 선택하세요:
  1) Harbor 레지스트리 사용  ← 권장
  2) 로컬 tar 직접 import
```

### 스토리지 타입 선택

MinIO 데이터 볼륨 위치를 선택합니다.

```
MinIO 스토리지 타입을 선택하세요:
  1) HostPath  — 로컬 노드 디렉토리 (단일 노드 환경 권장)
  2) NAS/NFS   — 네트워크 공유 스토리지
```

| 타입 | 특징 |
| :--- | :--- |
| HostPath | 노드 로컬 디렉토리 사용. 기본 경로 `/data/minio` (변경 가능) |
| NFS | NFS 서버 주소 + 공유 경로 입력. 사전에 서버에서 export 필요 |

입력한 설정은 **`install.conf`에 자동 저장**되어 다음 업그레이드 시 재사용됩니다.

---

## 4단계: 설치 확인

```bash
# Pod 및 백업 저장소 상태 확인 (Phase: Available 필수)
kubectl get pods -n velero
velero backup-location get

# 자동 스케줄 확인 (매일 새벽 1시, 30일 보관)
kubectl get schedule -n velero
```

MinIO 웹 콘솔: `http://minio-velero.devops.internal` (계정: `minioadmin` / `minioadmin`)

---

## 5단계: 업그레이드 / 재설치 / 초기화

설치된 상태에서 `install.sh`를 재실행하면 메뉴가 나타납니다.

```
동작을 선택하세요:
  1) 업그레이드   — 저장된 설정 유지, Helm upgrade --install
  2) 재설치       — 설정 재입력, MinIO 데이터 삭제 여부 선택
  3) 초기화(리셋) — 모든 리소스 + 데이터 + install.conf 완전 삭제 후 재설치
  4) 취소
```

| 선택 | PVC/PV | install.conf |
| :--- | :--- | :--- |
| 업그레이드 | 유지 | 유지 |
| 재설치 | 선택 삭제 | 재작성 |
| 초기화 | 삭제 | 삭제 |

> 업그레이드 시 PV/PVC를 변경하지 않으므로 기존 백업 데이터가 보존됩니다.

---

## 6단계: 백업 및 복구

### 6.1 백업 생성

```bash
# 전체 클러스터 백업
velero backup create cluster-full-backup --include-namespaces '*'

# 특정 네임스페이스 백업
velero backup create monitoring-backup --include-namespaces monitoring

# 백업 목록 확인
velero backup get
```

### 6.2 복구

```bash
# 전체 복구
velero restore create --from-backup cluster-full-backup

# 특정 네임스페이스만 복구
velero restore create --from-backup monitoring-backup --include-namespaces monitoring

# 복구 상태 확인
velero restore get
velero restore describe <복구명>
```

---

## 7단계: 삭제

```bash
./scripts/uninstall.sh
```

삭제 시 MinIO 백업 데이터(PVC/PV) 및 `install.conf` 보존 여부를 각각 확인합니다.

> 실제 호스트/NFS 볼륨의 파일은 스크립트가 삭제하지 않습니다. 필요 시 수동으로 제거하세요.

---

## install.conf 참고

`install.sh` 실행 시 자동 생성/갱신됩니다. 직접 편집도 가능합니다.

```bash
IMAGE_SOURCE="harbor"
HARBOR_REGISTRY="192.168.1.10:30002"
HARBOR_PROJECT="oss"
STORAGE_TYPE="hostpath"   # hostpath | nfs
HOSTPATH_DIR="/data/minio"
NFS_SERVER=""
NFS_PATH=""
STORAGE_SIZE="50Gi"
INSTALLED_VERSION="v1.18.0"
```

| 상황 | 동작 |
| :--- | :--- |
| install.conf 있음 + 미설치 | 저장된 설정으로 **프롬프트 없이 자동 설치** |
| install.conf 있음 + 설치됨 | 업그레이드/재설치/초기화 메뉴 표시 |
| install.conf 없음 | 모든 설정을 대화형으로 입력 |

새 노드에 동일 구성을 배포할 때 `install.conf`를 미리 복사해두면 무인 설치가 가능합니다.
