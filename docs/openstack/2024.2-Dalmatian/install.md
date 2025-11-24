# 🏛️ 통합 OpenStack 설치 가이드 (Ver. 2024.2)

이 가이드는 **Kolla-Ansible**을 사용하여 **OpenStack 2024.2** 버전을 설치하는 표준 절차입니다.
아래의 **변수 정의**를 먼저 확인하고 본인의 환경에 맞춰 대입하여 진행해 주세요.

## 📝 변수 정의 (치환 필요)

- `<USER_ID>` : 서버 접속 계정 (예: strato)
- `<PASSWORD>` : 접속 비밀번호 (예: strt0103\!)
- `<MASTER_IP>` : 마스터(Control) 노드 IP (예: 10.10.10.60)
- `<TARGET_NODE_IP>` : 배포 대상(Compute) 노드 IP

-----

## 1단계: 기본 시스템 설정 (공통)

한국 표준시(KST) 설정은 모든 노드(Master, Compute 등)에서 수행합니다.

```bash
# 한국 시간으로 변경
sudo timedatectl set-timezone Asia/Seoul
```

-----

## 2단계: 패키지 업데이트 및 의존성 설치 (OS별 선택)

사용 중인 OS에 맞는 명령어를 선택하여 실행하세요. Ubuntu 환경도 2024.2 버전에 맞게 의존성을 구성했습니다.

### 🅰️ Ubuntu 22.04 사용자

```bash
# 1. 패키지 최신 업데이트 및 필수 도구 설치
sudo apt update
sudo apt install net-tools -y

# 2. 개발 도구 및 라이브러리 설치
# OpenStack 2024.2 구동을 위한 필수 라이브러리 포함
sudo apt install git python3-dev libffi-dev gcc libssl-dev -y

# 3. 파이썬 가상환경 관리도구 설치
sudo apt install python3-venv -y
```

### 🅱️ Rocky Linux 사용자

```bash
# 1. 패키지 최신 업데이트 및 필수 도구 설치
sudo dnf update -y
sudo dnf install net-tools -y

# 2. 개발 도구 및 라이브러리 설치 (Python 3.11 사용)
sudo dnf install git python3.11 python3.11-devel libffi-devel gcc openssl-devel python3-libselinux net-tools -y

# 3. 파이썬 가상환경 관리도구 설치 (pip)
sudo dnf install python3-pip -y
```

-----

## 3단계: 가상환경(Venv) 구성 및 Ansible 설치 (통합)

OpenStack 2024.2 버전을 위한 가상환경을 구성하고, 호환되는 Ansible Core 버전을 설치합니다.

### 1. 가상환경 생성 및 활성화

**Ubuntu:**

```bash
python3 -m venv $HOME/venv
source $HOME/venv/bin/activate
```

**Rocky Linux:**

```bash
python3.11 -m venv $HOME/venv
source $HOME/venv/bin/activate
```

### 2. Pip, Ansible, Kolla-Ansible 설치 (공통)

*가상환경이 활성화된 상태(`(venv)` 표시 확인)에서 진행해야 합니다.*

```bash
# 1. pip 패키지를 최신버전으로 업그레이드
pip install -U pip

# 2. ansible-core 설치 (2024.2 버전 호환성 고려)
# 2.16 이상 2.17 미만 버전 권장
pip install 'ansible-core>=2.16,<2.17'

# 3. kolla-ansible 다운로드 (2024.2 Stable 버전)
pip install git+https://opendev.org/openstack/kolla-ansible@stable/2024.2
```

-----

## 4단계: 설정 파일 구성 (공통)

Kolla-Ansible 구동에 필요한 설정 파일들을 복사하고 디렉토리 권한을 수정합니다.

```bash
# 1. /etc/kolla 디렉토리 생성 및 소유자 변경
sudo mkdir -p /etc/kolla
sudo chown $USER:$USER /etc/kolla

# 2. 기본 설정 파일(globals.yml, password.yaml) 복사
cp -r $HOME/venv/share/kolla-ansible/etc_examples/kolla/* /etc/kolla

# 3. 인벤토리 파일(all-in-one, multinode) 복사
cp $HOME/venv/share/kolla-ansible/ansible/inventory/* .

# 4. Kolla-Ansible 프로젝트 의존성(Galaxy Role 등) 설치
kolla-ansible install-deps

# 5. 패스워드 파일 생성
kolla-genpwd

# 6. Ansible 설정 저장 디렉토리 생성
sudo mkdir -p /etc/ansible
sudo chown $USER:$USER /etc/ansible
```

-----

## 5단계: 멀티노드 통신 설정 (Master 노드 전용)

Master 노드에서 Compute 노드 등으로 비밀번호 없이 SSH 접속이 가능하도록 설정합니다.

```bash
# 1. SSH 공개 키를 배포 대상 서버에 복사 (각 노드 IP별로 반복 수행)
ssh-copy-id -i ~/.ssh/id_rsa.pub <USER_ID>@<TARGET_NODE_IP>

# 2. 접속 테스트 (암호 없이 로그인 되면 성공)
ssh <USER_ID>@<TARGET_NODE_IP>
```

### 인벤토리 파일 수정

`multinode` 파일을 열어 배포 대상 서버 정보를 입력합니다.

```bash
# 3. 인벤토리 수정
sudo vi multinode
```

**파일 내용 수정 예시:**

```ini
[control]
<MASTER_IP>

[network]
<MASTER_IP>

[compute]
# Compute 노드 IP와 계정 정보를 기입
<TARGET_NODE_IP> ansible_user=<USER_ID> ansible_become=true
```

### 통신 확인

```bash
# 4. Ansible Ping 테스트
ansible -i multinode all -m ping
```

-----

## 6단계: OpenStack 배포 (Master 노드 전용)

설정이 완료되면 실제 배포를 진행합니다.

```bash
# 1. 서버 부트스트랩 (Docker 설치 및 기본 설정)
kolla-ansible bootstrap-servers -i ./multinode

# 2. 사전 점검 (Prechecks)
kolla-ansible prechecks -i ./multinode

# 3. 배포 (Deploy)
kolla-ansible deploy -i ./multinode

# (참고) 설정 변경 시 재배포 (Reconfigure)
# kolla-ansible reconfigure -i ./multinode
```

-----

### 💡 DevOps 엔지니어의 팁

- **IP 설정 주의**: `globals.yml` 파일 수정 시 `network_interface`와 `neutron_external_interface`가 실제 서버의 인터페이스 명(예: `eth0`, `ens3` 등)과 일치하는지 반드시 확인해야 합니다.
- **가상환경 필수**: 모든 `kolla-ansible` 및 `ansible` 명령어는 `source $HOME/venv/bin/activate` 명령어로 가상환경이 활성화된 상태에서 실행해야 오류가 발생하지 않습니다.
