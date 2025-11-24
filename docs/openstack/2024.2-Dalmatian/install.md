안녕하세요, ⚙️ **DevOps 엔지니어**입니다.

요청하신 대로 두 운영체제(**Ubuntu 22.04**, **Rocky Linux**) 모두 **OpenStack 2024.2 (Stable)** 버전을 기준으로 설치할 수 있도록 가이드를 통합 및 재구성했습니다.

환경에 따라 변경되는 값(IP, 계정명 등)은 `< >` 형태의 변수로 치환하여, 어떤 환경에서도 헷갈리지 않고 적용할 수 있도록 작성했습니다.

-----

# 🏛️ 통합 OpenStack 설치 가이드 (Ver. 2024.2)

이 가이드는 **Kolla-Ansible**을 사용하여 **OpenStack 2024.2** 버전을 설치하는 표준 절차입니다.
아래의 **변수 정의**를 먼저 확인하고 본인의 환경에 맞춰 대입하여 진행해 주세요.

### 📝 변수 정의 (치환 필요)

  * `<USER_ID>` : 서버 접속 계정 (예: strato)
  * `<PASSWORD>` : 접속 비밀번호 (예: strt0103\!)
  * `<MASTER_IP>` : 마스터(Control) 노드 IP (예: 10.10.10.60)
  * `<TARGET_NODE_IP>` : 배포 대상(Compute) 노드 IP

-----

## 1단계: 기본 시스템 설정 (공통)

[cite\_start]한국 표준시(KST) 설정은 모든 노드(Master, Compute 등)에서 수행합니다. [cite: 2, 4]

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
[cite_start]sudo apt install net-tools -y [cite: 1]

# 2. 개발 도구 및 라이브러리 설치
# OpenStack 2024.2 구동을 위한 필수 라이브러리 포함
[cite_start]sudo apt install git python3-dev libffi-dev gcc libssl-dev -y [cite: 2]

# 3. 파이썬 가상환경 관리도구 설치
[cite_start]sudo apt install python3-venv -y [cite: 2]
```

### 🅱️ Rocky Linux 사용자

```bash
# 1. 패키지 최신 업데이트 및 필수 도구 설치
sudo dnf update -y
[cite_start]sudo dnf install net-tools -y [cite: 4]

# 2. 개발 도구 및 라이브러리 설치 (Python 3.11 사용)
[cite_start]sudo dnf install git python3.11 python3.11-devel libffi-devel gcc openssl-devel python3-libselinux net-tools -y [cite: 4]

# 3. 파이썬 가상환경 관리도구 설치 (pip)
[cite_start]sudo dnf install python3-pip -y [cite: 4]
```

-----

## 3단계: 가상환경(Venv) 구성 및 Ansible 설치 (통합)

OpenStack 2024.2 버전을 위한 가상환경을 구성하고, 호환되는 Ansible Core 버전을 설치합니다.

### 1\. 가상환경 생성 및 활성화

**Ubuntu:**

```bash
python3 -m venv $HOME/venv
[cite_start]source $HOME/venv/bin/activate [cite: 2]
```

**Rocky Linux:**

```bash
python3.11 -m venv $HOME/venv
[cite_start]source $HOME/venv/bin/activate [cite: 4]
```

### 2\. Pip, Ansible, Kolla-Ansible 설치 (공통)

*가상환경이 활성화된 상태(`(venv)` 표시 확인)에서 진행해야 합니다.*

```bash
# 1. pip 패키지를 최신버전으로 업그레이드
[cite_start]pip install -U pip [cite: 2, 4]

# 2. ansible-core 설치 (2024.2 버전 호환성 고려)
# 2.16 이상 2.17 미만 버전 권장
[cite_start]pip install 'ansible-core>=2.16,<2.17' [cite: 4]

# 3. kolla-ansible 다운로드 (2024.2 Stable 버전)
[cite_start]pip install git+https://opendev.org/openstack/kolla-ansible@stable/2024.2 [cite: 4]
```

-----

## 4단계: 설정 파일 구성 (공통)

Kolla-Ansible 구동에 필요한 설정 파일들을 복사하고 디렉토리 권한을 수정합니다.

```bash
# 1. /etc/kolla 디렉토리 생성 및 소유자 변경
sudo mkdir -p /etc/kolla
[cite_start]sudo chown $USER:$USER /etc/kolla [cite: 2, 4]

# 2. 기본 설정 파일(globals.yml, password.yaml) 복사
[cite_start]cp -r $HOME/venv/share/kolla-ansible/etc_examples/kolla/* /etc/kolla [cite: 2, 5]

# 3. 인벤토리 파일(all-in-one, multinode) 복사
[cite_start]cp $HOME/venv/share/kolla-ansible/ansible/inventory/* . [cite: 2, 5]

# 4. Kolla-Ansible 프로젝트 의존성(Galaxy Role 등) 설치
[cite_start]kolla-ansible install-deps [cite: 3, 6]

# 5. 패스워드 파일 생성
[cite_start]kolla-genpwd [cite: 3, 6]

# 6. Ansible 설정 저장 디렉토리 생성
sudo mkdir -p /etc/ansible
[cite_start]sudo chown $USER:$USER /etc/ansible [cite: 3, 6]
```

-----

## 5단계: 멀티노드 통신 설정 (Master 노드 전용)

Master 노드에서 Compute 노드 등으로 비밀번호 없이 SSH 접속이 가능하도록 설정합니다.

```bash
# 1. SSH 공개 키를 배포 대상 서버에 복사 (각 노드 IP별로 반복 수행)
[cite_start]ssh-copy-id -i ~/.ssh/id_rsa.pub <USER_ID>@<TARGET_NODE_IP> [cite: 3, 7]

# 2. 접속 테스트 (암호 없이 로그인 되면 성공)
[cite_start]ssh <USER_ID>@<TARGET_NODE_IP> [cite: 3, 7]
```

### 인벤토리 파일 수정

`multinode` 파일을 열어 배포 대상 서버 정보를 입력합니다.

```bash
# 3. 인벤토리 수정
[cite_start]sudo vi multinode [cite: 3, 7]
```

**파일 내용 수정 예시:**

```ini
[control]
<MASTER_IP>

[network]
<MASTER_IP>

[compute]
# Compute 노드 IP와 계정 정보를 기입
[cite_start]<TARGET_NODE_IP> ansible_user=<USER_ID> ansible_become=true [cite: 3, 7]
```

### 통신 확인

```bash
# 4. Ansible Ping 테스트
[cite_start]ansible -i multinode all -m ping [cite: 3, 7]
```

-----

## 6단계: OpenStack 배포 (Master 노드 전용)

설정이 완료되면 실제 배포를 진행합니다.

```bash
# 1. 서버 부트스트랩 (Docker 설치 및 기본 설정)
[cite_start]kolla-ansible bootstrap-servers -i ./multinode [cite: 3]

# 2. 사전 점검 (Prechecks)
[cite_start]kolla-ansible prechecks -i ./multinode [cite: 3]

# 3. 배포 (Deploy)
[cite_start]kolla-ansible deploy -i ./multinode [cite: 3]

# (참고) 설정 변경 시 재배포 (Reconfigure)
# [cite_start]kolla-ansible reconfigure -i ./multinode [cite: 3, 7]
```

-----

### 💡 DevOps 엔지니어의 팁

  * **IP 설정 주의**: `globals.yml` 파일 수정 시 `network_interface`와 `neutron_external_interface`가 실제 서버의 인터페이스 명(예: `eth0`, `ens3` 등)과 일치하는지 반드시 확인해야 합니다.
  * **가상환경 필수**: 모든 `kolla-ansible` 및 `ansible` 명령어는 `source $HOME/venv/bin/activate` 명령어로 가상환경이 활성화된 상태에서 실행해야 오류가 발생하지 않습니다.

추가적으로 `globals.yml` 내부 네트워크 설정에 대해 상세한 가이드가 필요하시면 말씀해 주세요.