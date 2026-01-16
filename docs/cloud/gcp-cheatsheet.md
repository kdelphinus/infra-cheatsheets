# 📘 Google Cloud SDK (`gcloud`) 치트시트

GCP 리소스 관리를 위한 필수 명령어 모음입니다.

> **범례**:
>
> - `<값>` : 필수 입력 값 (예: 인스턴스명, 프로젝트ID)
> - `[옵션]` : 선택 입력 값

## 0. 환경 설정 및 인증 (필수)

GCP CLI를 사용하기 위해 계정을 연동하고 프로젝트를 설정합니다.

```bash
# 1. 브라우저를 통한 인증 (초기 설정)
gcloud auth login

# 2. 프로젝트 설정 (작업 대상 프로젝트 지정)
gcloud config set project <프로젝트_ID>

# 3. 기본 리전/존 설정 (매번 입력하기 귀찮을 때)
gcloud config set compute/region asia-northeast3  # 서울 리전
gcloud config set compute/zone asia-northeast3-a  # 서울 A존

# 4. 설정 확인
gcloud config list

```

> **💡 팁: 다중 계정/환경 관리 (Configuration)**
> OpenStack의 `source rc` 파일 교체와 비슷하게, GCP는 config 구성을 스위칭할 수 있습니다.
>
> ```bash
> # 새 프로필 생성
> gcloud config configurations create <새_프로필명>
> # 프로필 전환
> gcloud config configurations activate <프로필명>
> ```

---

## 1. 인스턴스 (Compute Engine) 관리

VM 인스턴스(GCE)의 생명주기를 관리합니다.

| 작업 | 명령어 | 설명 |
| --- | --- | --- |
| **목록 조회** | `gcloud compute instances list` | 현재 프로젝트의 모든 VM 조회 |
| **상세 조회** | `gcloud compute instances describe <VM이름>` | 특정 VM의 상세 스펙/상태 조회 (YAML 출력) |
| **생성** | `gcloud compute instances create <VM이름> --image-family <OS계열> --machine-type <타입>` | 기본 VM 생성 |
| **삭제** | `gcloud compute instances delete <VM이름>` | VM 삭제 (디스크 유지 옵션 가능) |
| **시리얼 포트** | `gcloud compute instances get-serial-port-output <VM이름>` | 부팅 로그 확인 (디버깅용) |
| **SSH 접속** | `gcloud compute ssh <VM이름>` | **(강추)** 키 관리 없이 바로 SSH 접속 |

### ⚡ 전원 및 상태 관리

```bash
# VM 시작 (Start)
gcloud compute instances start <VM이름>

# VM 중지 (Stop - 과금 중단, 디스크 비용은 발생)
gcloud compute instances stop <VM이름>

# VM 재설정 (Reset - 강제 재부팅 효과)
gcloud compute instances reset <VM이름>

# 실행 중인 VM의 머신 타입 변경 (중지 후 실행 필요)
gcloud compute instances set-machine-type <VM이름> --machine-type e2-standard-4

```

---

## 2. 이미지 (Image) 관리

부팅 디스크용 OS 이미지 관련 명령어입니다.

| 작업 | 명령어 | 설명 |
| --- | --- | --- |
| **목록 조회** | `gcloud compute images list` | 사용 가능한 공용/사설 이미지 목록 |
| **상세 조회** | `gcloud compute images describe <이미지명> --project <프로젝트ID>` | 이미지 상세 정보 확인 |
| **이미지 생성** | `gcloud compute images create <이미지명> --source-disk <원본디스크> --source-disk-zone <존>` | 디스크로부터 커스텀 이미지 생성 |
| **삭제** | `gcloud compute images delete <이미지명>` | 커스텀 이미지 삭제 |

### 🔧 OS 이미지 찾기 (필터링)

```bash
# Rocky Linux 9 계열 이미지 찾기
gcloud compute images list --project rocky-linux-cloud --filter="name ~ rocky-linux-9"

# 특정 OS의 최신 버전 Family 확인
gcloud compute images describe-from-family rocky-linux-9 --project rocky-linux-cloud

# --show-deprecated 옵션을 통해 예전 이미지도 확인 가능
gcloud compute images list \
  --project rocky-linux-cloud \
  --show-deprecated \
  --sort-by="~creationTimestamp"
```

---

## 3. 머신 타입 (Flavor) 조회

GCP는 사용자가 Flavor를 직접 만들기보다, 미리 정의된 **Machine Type**을 조회하여 사용합니다.

| 작업 | 명령어 |
| --- | --- |
| **목록 조회** | `gcloud compute machine-types list` |
| **필터링 조회** | `gcloud compute machine-types list --filter="name ~ e2-standard"` |
| **상세 스펙** | `gcloud compute machine-types describe <타입명>` |

### 🎮 GPU 인스턴스 생성 예시

GCP에서 GPU를 붙일 때는 `--accelerator` 옵션을 사용합니다.

```bash
# T4 GPU 1개를 부착한 인스턴스 생성
gcloud compute instances create <VM이름> \
    --machine-type n1-standard-4 \
    --accelerator type=nvidia-tesla-t4,count=1 \
    --maintenance-policy TERMINATE \
    --image-family common-cu113 \
    --image-project deeplearning-platform-release

```

---

## 4. 네트워크 (VPC) 관리

VPC 네트워크 및 방화벽 규칙 관리입니다.

| 작업 | 명령어 | 설명 |
| --- | --- | --- |
| **네트워크 목록** | `gcloud compute networks list` | VPC 목록 조회 |
| **서브넷 목록** | `gcloud compute networks subnets list` | 서브넷 IP 대역 확인 |
| **방화벽 목록** | `gcloud compute firewall-rules list` | 적용된 방화벽 규칙 확인 |
| **방화벽 생성** | `gcloud compute firewall-rules create <규칙명> --allow tcp:80,tcp:443` | 포트 개방 |
| **방화벽 삭제** | `gcloud compute firewall-rules delete <규칙명>` | 규칙 삭제 |

### 🌐 고정 IP (Static External IP)

OpenStack의 Floating IP에 해당합니다.

```bash
# 고정 IP 예약 (생성)
gcloud compute addresses create <IP이름> --region <리전>

# 예약된 IP 목록 확인 (실제 IP 주소 확인)
gcloud compute addresses list

# 인스턴스 생성 시 고정 IP 할당
gcloud compute instances create <VM이름> --address <IP주소_또는_IP이름>

```

---

## 5. 스토리지 (Disk & Bucket) 관리

블록 스토리지(Persistent Disk)와 객체 스토리지(GCS) 관리입니다.

### 💾 영구 디스크 (Persistent Disk) - Cinder 대응

| 작업 | 명령어 |
| --- | --- |
| **목록 조회** | `gcloud compute disks list` |
| **생성** | `gcloud compute disks create <디스크명> --size 100GB --type pd-ssd` |
| **크기 확장** | `gcloud compute disks resize <디스크명> --size 200GB` |
| **VM 부착** | `gcloud compute instances attach-disk <VM이름> --disk <디스크명>` |
| **스냅샷** | `gcloud compute disks snapshot <디스크명> --snapshot-names <스냅샷명>` |

### 📦 GCS 버킷 (Object Storage) - Swift/S3 대응

`gcloud storage` 또는 구형 `gsutil` 명령어를 사용합니다. (최신 버전은 `gcloud storage` 권장)

```bash
# 버킷 목록 조회
gcloud storage buckets list

# 파일 업로드 (로컬 -> 버킷)
gcloud storage cp <로컬파일> gs://<버킷명>/

# 파일 다운로드 (버킷 -> 로컬)
gcloud storage cp gs://<버킷명>/<파일> <로컬경로>

```

---

## 6. Kubernetes (GKE) 관리

GCP의 핵심인 관리형 쿠버네티스 엔진 명령어입니다.

| 작업 | 명령어 | 설명 |
| --- | --- | --- |
| **클러스터 목록** | `gcloud container clusters list` | GKE 클러스터 상태 확인 |
| **클러스터 생성** | `gcloud container clusters create <이름> --num-nodes 3` | 기본 클러스터 생성 |
| **자격증명 가져오기** | `gcloud container clusters get-credentials <이름>` | **(필수)** `kubectl` 사용을 위한 kubeconfig 자동 설정 |
| **노드풀 관리** | `gcloud container node-pools list --cluster <클러스터명>` | 노드 그룹 확인 |

---

## 7. IAM 및 프로젝트 관리

권한 및 프로젝트 설정입니다.

| 작업 | 명령어 | 설명 |
| --- | --- | --- |
| **프로젝트 목록** | `gcloud projects list` | 접근 가능한 프로젝트 ID 확인 |
| **현재 설정** | `gcloud config list` | 현재 활성화된 계정/프로젝트/리전 확인 |
| **IAM 정책 조회** | `gcloud projects get-iam-policy <프로젝트ID>` | 누구에게 어떤 권한이 있는지 확인 |
| **서비스 계정 키** | `gcloud iam service-accounts keys create key.json --iam-account <계정메일>` | API 키 파일(JSON) 다운로드 |

---

### 💡 팁: 출력 포맷팅 (스크립트용)

OpenStack의 `-c`, `-f` 옵션과 유사하게 GCP는 `--format` 플래그가 매우 강력합니다.

```bash
# 1. 테이블에서 특정 컬럼만 보기
gcloud compute instances list --format="table(name, status, networkInterfaces[0].networkIP)"

# 2. JSON 형태로 전체 보기
gcloud compute instances describe <VM이름> --format="json"

# 3. 특정 값만 딱 뽑아내기 (스크립트 변수 할당용)
# 예: 특정 VM의 외부 IP(NAT IP)만 추출
gcloud compute instances describe <VM이름> \
  --format="value(networkInterfaces[0].accessConfigs[0].natIP)"

# 4. 필터 및 정렬
# 예: 생성된 시간에 따라 정렬
gcloud compute images list \
  --project rocky-linux-cloud \
  --sort-by="~creationTimestamp"

```
