# 📘 [GCP] 폐쇄망 Kubernetes 인프라 구축 완벽 가이드

이 문서는 **Windows WSL2(Ubuntu)** 환경에서 **Google Cloud Platform(GCP)** 상에
**완전 폐쇄망(Air-gapped)** 기반의 고가용성(HA) 인프라를 구축하는 매뉴얼입니다.

> **구성 목표:** Bastion(1대) + Master(3대) + Worker(3대) + DB(3대) = **총 10대**
> **주의:** 신규 계정은 vCPU 제한(12개)이 있어, **반드시 할당량 상향 요청(Step 3)**을 먼저 수행해야 합니다.

---

## 🚀 1단계: 필수 도구 설치

GCP와 통신하기 위한 최신 도구를 설치합니다.

### 1. Terraform 설치

```bash
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common

wget -O- https://apt.releases.hashicorp.com/gpg | \
gpg --dearmor | \
sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null

echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
sudo tee /etc/apt/sources.list.d/hashicorp.list

sudo apt-get update && sudo apt-get install terraform

```

### 2. Google Cloud SDK (gcloud CLI) 설치

```bash
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

sudo apt-get update && sudo apt-get install google-cloud-cli

```

---

## 🚀 2단계: GCP 인증 및 사전 준비

이 과정을 건너뛰면 `403 Forbidden` 에러가 발생합니다.

### 1. 로그인 및 ADC 설정

```bash
# 브라우저 로그인 (계정 권한 획득)
gcloud auth login

# Terraform용 인증 토큰 생성 (필수 과정)
gcloud auth application-default login

```

### 2. 프로젝트 연결 및 API 활성화

본인의 프로젝트 ID를 정확히 입력하세요.

```bash
# [수정] 본인의 프로젝트 ID로 변경
export MY_PROJECT_ID="rocky-k8s-airgap" 

# 프로젝트 지정
gcloud config set project $MY_PROJECT_ID

# Compute Engine API 활성화 (가상머신 생성 권한 켜기)
gcloud services enable compute.googleapis.com

```

### 3. SSH 키 생성

```bash
# 엔터만 계속 눌러서 기본 경로(~/.ssh/gcp_key)에 생성
ssh-keygen -t rsa -f ~/.ssh/gcp_key -C "rocky"

```

---

## 🚀 3단계: vCPU 할당량(Quota) 상향 요청 (★ 필수)

본 가이드의 3중화 구성은 **약 19 vCPU**가 필요합니다.
하지만 신규 계정의 기본 한도는 **12 vCPU**이므로, 배포 전 반드시 한도를 늘려야 합니다.

### 📊 필요 자원 계산

- Bastion (e2-micro): **약 1 vCPU**
- Master 3대 (e2-standard-2): 2 * 3 = **6 vCPU**
- Worker 3대 (e2-standard-2): 2 * 3 = **6 vCPU**
- DB 3대 (e2-standard-2): 2 * 3 = **6 vCPU**
- **총합: 19 vCPU 필요** (여유 있게 **24** 이상으로 요청 권장)

### 🛠️ 상향 요청 방법 (웹 콘솔)

1. [GCP 콘솔 - 할당량(Quotas) 페이지](https://console.cloud.google.com/iam-admin/quotas)
로 이동합니다.
2. 필터 창에 `CPUS_ALL_REGIONS`라고 입력합니다.
3. 서비스가 **Compute Engine API**인 항목(`CPUS-ALL-REGIONS-per-project`)을 찾아 체크박스를 선택합니다.
4. 상단의 **[할당량 수정 (EDIT QUOTAS)]** 버튼을 클릭합니다.
5. 새 한도 입력 칸에 **24** (또는 32)를 입력합니다.
6. 요청 사유에 `Kubernetes HA Cluster Test` 라고 적고 제출합니다.
    - *승인은 보통 몇 분 내로 완료되지만, 신규 계정 검토로 인해 최대 1~2일이 걸릴 수도 있습니다.*
    - *승인 메일을 받으면 4단계로 넘어가세요.*

---

## 🚀 4단계: Terraform 코드 작성

### 1. 파일 생성

```bash
mkdir ~/gcp-k8s-airgap && cd ~/gcp-k8s-airgap
nano main.tf

```

### 2. `main.tf` 내용 작성

생성할 자원들 구성은 아래와 같습니다.

![main.tf 구성도](../images/terraform-with-gcp.png)

**`project` 값은 반드시 본인 ID로 수정**하세요.

```hcl
provider "google" {
  # ★ 본인의 프로젝트 ID로 반드시 수정하세요!
  project = "rocky-k8s-airgap"
  region  = "asia-northeast3"    # 서울 리전
}

# SSH 키 프로젝트 전체 등록
resource "google_compute_project_metadata" "ssh_keys" {
  metadata = {
    ssh-keys = "rocky:${file("~/.ssh/gcp_key.pub")}"
  }
}

# 1. VPC 네트워크 (폐쇄망)
resource "google_compute_network" "vpc" {
  name                    = "k8s-airgap-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "public_subnet" {
  name          = "public-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = "asia-northeast3"
  network       = google_compute_network.vpc.id
}

resource "google_compute_subnetwork" "private_subnet" {
  name                     = "private-subnet"
  ip_cidr_range            = "10.0.2.0/24"
  region                   = "asia-northeast3"
  network                  = google_compute_network.vpc.id
  private_ip_google_access = false # 완전 폐쇄 (인터넷 불가)
}

# 2. 방화벽 규칙
resource "google_compute_firewall" "allow_ssh_bastion" {
  name    = "allow-ssh-bastion"
  network = google_compute_network.vpc.id
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["bastion"]
}

resource "google_compute_firewall" "allow_internal" {
  name    = "allow-internal"
  network = google_compute_network.vpc.id
  allow { protocol = "all" }
  source_tags = ["internal-node", "bastion"]
  target_tags = ["internal-node", "bastion"]
}

# 3. VM 인스턴스
resource "google_compute_instance" "bastion" {
  name         = "bastion-host"
  machine_type = "e2-micro"
  zone         = "asia-northeast3-a"
  tags         = ["bastion"]
  
  boot_disk {
    initialize_params {
      image = "rocky-linux-cloud/rocky-linux-9"
    }
  }
  
  network_interface {
    subnetwork = google_compute_subnetwork.public_subnet.id
    access_config {} # 공인 IP 할당
  }
}

resource "google_compute_instance" "k8s_masters" {
  count        = 3
  name         = "k8s-master-${count.index + 1}"
  machine_type = "e2-standard-2" # 2 vCPU, 8GB Ram
  zone         = "asia-northeast3-a"
  tags         = ["k8s-master", "internal-node"]
  
  boot_disk {
    initialize_params {
      image = "rocky-linux-cloud/rocky-linux-9"
      size  = 30
    }
  }
  
  network_interface {
    subnetwork = google_compute_subnetwork.private_subnet.id
  }
}

resource "google_compute_instance" "k8s_workers" {
  count        = 3
  name         = "k8s-worker-${count.index + 1}"
  machine_type = "e2-standard-2"
  zone         = "asia-northeast3-a"
  tags         = ["k8s-worker", "internal-node"]
  
  boot_disk {
    initialize_params {
      image = "rocky-linux-cloud/rocky-linux-9"
      size  = 30
    }
  }
  
  network_interface {
    subnetwork = google_compute_subnetwork.private_subnet.id
  }
}

resource "google_compute_instance" "db_nodes" {
  count        = 3
  name         = "mariadb-node-${count.index + 1}"
  machine_type = "e2-standard-2"
  zone         = "asia-northeast3-a"
  tags         = ["db-node", "internal-node"]
  
  boot_disk {
    initialize_params {
      image = "rocky-linux-cloud/rocky-linux-9"
      size  = 30
    }
  }
  
  network_interface {
    subnetwork = google_compute_subnetwork.private_subnet.id
  }
}

output "bastion_ip" {
  value = google_compute_instance.bastion.network_interface.0.access_config.0.nat_ip
}

```

---

## 🚀 5단계: 배포 및 접속 설정

### 1. 인프라 배포

```bash
terraform init
terraform plan
terraform apply
# (내용 확인 후 yes 입력)

```

> **참고:** 할당량 상향이 아직 안 되었다면 여기서 에러가 발생합니다.

### 2. 접속 편의성 설정 (`~/.ssh/config`)

배포 후 출력된 **`bastion_ip`**를 사용하여 설정 파일을 수정합니다.

```bash
nano ~/.ssh/config

```

**[붙여넣을 내용]**

```text
# 1. Bastion Host
Host bastion
    HostName 34.xx.xx.xx        # ★ Terraform Output의 Bastion IP로 수정하세요!
    User rocky
    IdentityFile ~/.ssh/gcp_key

# 2. 내부 폐쇄망 노드 (자동 점프)
Host 10.0.2.*
    User rocky
    IdentityFile ~/.ssh/gcp_key
    ProxyJump bastion             # Bastion을 거쳐서 접속
    StrictHostKeyChecking no      # (테스트용) 지문 변경 경고 무시
    UserKnownHostsFile /dev/null

```

---

## 🚀 6단계: 접속 테스트 및 운영

### A. 접속 테스트

내 PC(WSL) 터미널에서 바로 내부 IP를 입력하여 접속합니다.

```bash
# Bastion을 거쳐 마스터 1번 노드로 바로 접속
ssh 10.0.2.2

```

> `[rocky@k8s-master-1 ~]$` 프롬프트가 뜨면 성공입니다.

### B. 파일 전송 (SCP)

```bash
# 로컬 파일 -> 내부 서버 전송
scp my-file.tar.gz 10.0.2.2:/home/rocky/

```

---

## 🚀 7단계: 자원 삭제 (Clean Up)

비용 발생을 막기 위해 테스트가 끝나면 반드시 자원을 정리해야 합니다.

```bash
terraform destroy
# (yes 입력)

```
