# 🚀 OpenStack Flamingo (2025.2) 통합 설치 가이드

## ⚙️ 0. OS 사전 준비

### 📝 0.0 옵션: 기존 설정 백업

만약 기존 환경을 업그레이드 한다면 아래 내용은 백업해두면 좋습니다.

```bash
echo "=== HOSTNAME ===" > server_info.txt
hostname >> server_info.txt

echo -e "\n=== IP & MAC ===" >> server_info.txt
ip -c addr >> server_info.txt

echo -e "\n=== ROUTE ===" >> server_info.txt
ip route >> server_info.txt

echo -e "\n=== DISK INFO (Serial Check) ===" >> server_info.txt
lsblk -o NAME,MODEL,SERIAL,SIZE,TYPE,FSTYPE >> server_info.txt

echo -e "\n=== LVM INFO ===" >> server_info.txt
sudo vgs >> server_info.txt

echo -e "\n=== PCI (GPU) ===" >> server_info.txt
lspci -nn | grep NVIDIA >> server_info.txt

echo -e "\n=== KERNEL BOOT PARAM ===" >> server_info.txt
cat /proc/cmdline >> server_info.txt

echo "Done. Check server_info.txt"
```

### 💾 0.1 Cinder 관련 볼륨 설정

`multinode` 에서 `[Storage]` 항목에 있는 노드들은 아래 작업을 수행해야 합니다.
만약 `/dev/sdb` 를 cinder로 사용한다면 os 설치 시 `/dev/sdb` 는 **Leave unformatted** 상태로 남아있어야 합니다.

```bash
# 1. 물리 볼륨(PV) 생성
# 주의: /dev/sdb의 모든 데이터가 날아갑니다.
sudo pvcreate /dev/sdb

# 2. 볼륨 그룹(VG) 생성 ★이름 중요★
# globals.yml에 적은 이름(cinder-volumes)과 철자 하나라도 틀리면 안 됩니다.
sudo vgcreate cinder-volumes /dev/sdb

# 3. 확인
sudo vgs
# 결과에 cinder-volumes가 보이고 Free 사이즈가 넉넉하면 성공!
```

### 🌐 0.2 네트워크 관련 설정

```yaml
# /etc/netplan/00-installer-config.yaml
network:
  version: 2
  ethernets:
    eno1:  # 관리망 (Management & VXLAN Tunnel)
      dhcp4: false
      addresses:
        - 10.10.10.XX/24  # <--- [중요] 각 서버의 원래 IP로 변경 (예: 60, 62 등)
      routes:
        - to: default
          via: 10.10.10.1 # <--- [중요] ip 대역보고 변경 필요(172.16.11.243 서버는 172.16.11.1로 설정)
      nameservers:
        addresses: [8.8.8.8] # 또는 사내 DNS
    eno2:  # 외부망 (Provider Network)
      dhcp4: false
      # IP를 넣지 않습니다. OpenStack(OVS)이 브리지로 가져가서 쓸 것입니다.
      # 링크만 Up 상태로 만듭니다.
      optional: true
```

```bash
sudo netplan apply
ip addr  # IP가 제대로 들어왔는지 확인
```

### 🕛 0.3 서버 시간 설정

한국 표준시(KST) 설정은 모든 노드에서 수행합니다.

```bash
# 한국 시간으로 변경
sudo timedatectl set-timezone Asia/Seoul
```

### 🟠 [Rocky Linux] 필수 설정 (SELinux 해제)

RedHat 계열은 SELinux가 켜져 있으면 Kolla 배포 시 권한 문제로 실패합니다.

> 보안 정책 상 SELinux 비활성화가 불가능한 환경에서는, Kolla-Ansible SELinux 대응 가이드를 별도로 참고해야 합니다.

```bash
# 1. SELinux를 Permissive 모드로 변경 (일시적)
sudo setenforce 0

# 2. 영구 설정 (재부팅 후에도 유지되도록)
sudo sed -i 's/^SELINUX=.*/SELINUX=disabled/g' /etc/selinux/config

# 3. EPEL 저장소 추가 (필수 패키지 설치용)
sudo dnf install -y epel-release
sudo dnf update -y
```

### 🟣 [Ubuntu] 필수 설정

Ubuntu는 패키지 업데이트만 하면 됩니다.

```bash
sudo apt update && sudo apt upgrade -y
```

-----

## 🛠️ 1. 의존성 패키지 설치 (Install Dependencies)

Python 가상환경을 만들기 위한 기초 도구들을 설치합니다.

### 🟠 [Rocky Linux]

```bash
# 개발 도구 및 파이썬 라이브러리 설치
sudo dnf install -y git python3-devel libffi-devel gcc openssl-devel python3-libselinux python3-pip python3-libselinux-devel
```

### 🟣 [Ubuntu]

```bash
# 개발 도구 및 파이썬 라이브러리 설치
sudo apt install -y git python3-dev libffi-dev gcc libssl-dev python3-venv libdbus-glib-1-dev python3-dbus
```

-----

## 🐍 2. 가상환경 구성 (Virtual Environment) - [공통]

여기서부터는 OS 상관없이 동일합니다. **시스템 파이썬을 더럽히지 않기 위해 가상환경 사용이 필수**입니다.

```bash
# 1. 가상환경 생성 (홈 디렉터리에 venv 생성)
python3 -m venv ~/venv

# 2. 가상환경 활성화 ★(작업할 때마다 매번 실행 필수)★
source ~/venv/bin/activate

# (프롬프트 앞에 (venv)가 떴는지 확인하세요)

# 3. pip 최신화 (오류 방지)
pip install -U pip
```

-----

## 📦 3. Kolla-Ansible 설치 (Install) - [공통]

```bash
# 1. Kolla-Ansible Flamingo 버전 설치 (master 브랜치)
pip install git+https://opendev.org/openstack/kolla-ansible@master

# 버전 지정
pip install git+https://opendev.org/openstack/kolla-ansible@stable/2025.2

# 2. 설정 디렉터리 생성 및 권한 부여
sudo mkdir -p /etc/kolla
sudo chown $USER:$USER /etc/kolla

# 3. 설정 파일 복사 (globals.yml, passwords.yml)
cp -r ~/venv/share/kolla-ansible/etc_examples/kolla/* /etc/kolla/

# 4. 인벤토리 파일 복사 (멀티노드용)
cp ~/venv/share/kolla-ansible/ansible/inventory/multinode .
```

-----

## ⚙️ 4. 설정 파일 수정 (`globals.yml`) - [OS별 차이점]

`vi /etc/kolla/globals.yml`을 열어서 수정합니다. OS에 따라 **`kolla_base_distro`** 값을 다르게 줘야 합니다.

```yaml
---
# [중요] OS에 따라 선택하세요
# Ubuntu 사용 시:
kolla_base_distro: "ubuntu"
# Rocky Linux 사용 시:
# kolla_base_distro: "rocky"

# [공통] 오픈스택 버전 (Flamingo 대응)
# openstack_release: "master"  <-- 주석 그대로 두거나, Docker 태그 명시

# [공통] 네트워크 설정 (사용자 환경에 맞춰서 수정할 것)
# eno2에는 IP를 설정하지 말고, 스위치에 외부망 VLAN/Untaged 연결 필수
network_interface: "eno1"           # 관리망 (IP 10.10.10.60)
neutron_external_interface: "eno2"  # 외부망 (IP 없음)

# [공통] VIP 주소 (관리망 대역 내 미사용 IP, 같은 IP 사용 시 HAProxy 충돌 발생 가능성 높음)
kolla_internal_vip_address: "10.10.10.60"  # HAProxy를 사용할 경우, 빈 IP 할당 필요

# [공통] 주요 서비스 활성화
enable_cinder: "yes"
enable_cinder_backend_lvm: "yes"
cinder_volume_group: "cinder-volumes" # Cinder volume group 이름 확인 필요
enable_heat: "yes"
enable_horizon: "yes"
# enable_prometheus: "yes" # 모니터링 필요 시
```

위 설정은 `vip_address` 는 기본적으로 현재 ip와 다른 ip를 사용하는 것이 정석이지만, 빈 ip가 없거나 동일한 ip를 사용해야 한다면 `haproxy` , `keepalived` 와 `tls` 설정을 꺼야 합니다.

```yml
kolla_internal_vip_address: "10.10.10.60"  # Control 노드의 실제 IP
enable_haproxy: "no"                       # HAProxy 끔
enable_keepalived: "no"                    # Keepalived 끔

kolla_enable_tls_internal: "no" 
kolla_enable_tls_external: "no"
```

-----

## 📝 5. 인벤토리 및 비밀번호 설정 - [공통]

### 5.1 비밀번호 생성

```bash
kolla-genpwd
# 생성 후 Horizon Admin 비밀번호 확인해두기
grep keystone_admin_password /etc/kolla/passwords.yml
```

### 5.2 SSH 접속 허용

Master 노드에서 Compute 노드 등으로 비밀번호 없이 SSH 접속이 가능하도록 설정합니다.

```bash
# 1. SSH 공개 키를 배포 대상 서버에 복사 (각 노드 IP별로 반복 수행)
ssh-copy-id -i ~/.ssh/id_rsa.pub <USER_ID>@<TARGET_NODE_IP>

# 2. 접속 테스트 (암호 없이 로그인 되면 성공)
ssh <USER_ID>@<TARGET_NODE_IP>
```

### 5.3 인벤토리 수정 (`vi multinode`)

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

타켓 IP에 입력한 ID로 접속하여 sudo 권한을 얻겠다는 의미입니다.

### 5.4 통신 확인

```bash
# 4. Ansible Ping 테스트
ansible -i multinode all -m ping
```

### 5.5 Ansible 의존성 설치 (필수)

```bash
kolla-ansible install-deps
```

### 5.6 그 외

```bash
# 타임싱크 확인
timedatectl

# 호스트명 확인
hostname

# /etc/hosts에 모든 노드 등록 권장
vi /etc/hosts
```

-----

## 🚀 6. 배포 실행 (Deploy) - [공통]

이제 실제 설치를 진행합니다.

```bash
# 1. Bootstrap (기초 공사: Docker 설치 등)
kolla-ansible bootstrap-servers -i ./multinode

# 2. Prechecks (사전 검사: 설정 오류 확인)
kolla-ansible prechecks -i ./multinode
# -> 여기서 "SUCCESS"가 떠야만 다음으로 넘어갑니다.

# 3. Deploy (본 게임: 컨테이너 배포)
kolla-ansible deploy -i ./multinode
```

-----

## ✅ 7. 클라이언트 설정 (Post-Deploy) - [공통]

배포가 끝나면 OpenStack 명령어를 쓰기 위한 도구를 세팅합니다.

```bash
# 1. OpenStack 클라이언트 설치
pip install python-openstackclient

# 2. 관리자 인증 파일 생성 (admin-openrc.sh)
kolla-ansible post-deploy -i multinode

# 3. 인증 로드 및 테스트
source /etc/kolla/admin-openrc.sh
openstack service list

# 4. Nova와 Compute 등록 확인
openstack hypervisor list
openstack compute service list
```

## 🌐 8. 네트워크 생성

### `init-runonce` 사용(자동)

아래 항목을 수정 후, 배포합니다.

```ini
# 1. 파일 열기
vi ~/venv/share/kolla-ansible/init-runonce

# 2. 아래 변수들을 찾아 사내망 환경에 맞게 수정
EXT_NET_CIDR='10.10.10.0/24'       # 외부망 전체 대역 (예시)
EXT_NET_RANGE='start=10.10.10.100,end=10.10.10.200' # Floating IP로 쓸 범위
EXT_NET_GATEWAY='10.10.10.1'       # 외부망 게이트웨이
```

배포가 끝나면 해당 파일을 실행하여 네트워크를 생성합니다.

```bash
# home 폴더 기준
./venv/share/kolla-ansible/init-runonce
```

### `CLI` 사용(수동)

네트워크 생성은 아래와 같이 진행합니다. IP 대역 등은 실제 환경에 맞춰 수정해야 합니다.

#### 내부망 생성

```bash
# 1. 내부망 생성
openstack network create --provider-network-type vxlan internal

# 2. 내부망 서브넷 생성
openstack subnet create --network internal \
  --subnet-range 1.1.1.0/24 \
  --gateway 1.1.1.1 \
  --dns-nameserver 8.8.8.8 \
  --dhcp \
  internal_subnet
```

#### 외부망 생성

```bash
# 1. 외부망(provider network) 생성
# 이름: external (사진과 일치)
openstack network create --external \
  --provider-physical-network physnet1 \
  --provider-network-type flat \
  external

# 2. 서브넷 생성
# 네트워크 연결: external (위에서 만든 네트워크)
# DHCP: 끄기 (사진과 일치)
openstack subnet create --network external \
  --allocation-pool start=10.10.10.70,end=10.10.10.108 \
  --dns-nameserver 8.8.8.8 \
  --gateway 10.10.10.1 \
  --subnet-range 10.10.10.0/24 \
  --no-dhcp \
  external_subnet
```

#### 라우터 생성

```bash
# 1. 라우터 이름: route
openstack router create route

# 2. 외부망 연결
openstack router set --external-gateway external --enable-snat route

# 3. 내부망 연결
openstack router add subnet route internal_subnet
```

#### Octavia 로드밸런서 관리망 생성 및 연결

```bash
# 1. 네트워크 생성
openstack network create lb-mgmt-net

# 2. 서브넷 생성 (20.0.0.0/24 대역, 게이트웨이 20.0.0.1)
# globals.yml 설정과 100% 일치시킴
openstack subnet create --network lb-mgmt-net \
  --subnet-range 20.0.0.0/24 \
  --gateway 20.0.0.1 \
  --dns-nameserver 8.8.8.8 \
  --dhcp \
  lb-mgmt-subnet

# 3. 라우터에 연결 (이걸 수행하면 사진처럼 20.0.0.1 포트가 생깁니다)
openstack router add subnet route lb-mgmt-subnet
```

-----

## 💡 DevOps 엔지니어의 조언: Ubuntu vs Rocky 선택 가이드

- **Ubuntu 24.04:**
  - **장점:** OpenStack 커뮤니티의 **표준(De-facto)** 입니다. 트러블슈팅 자료가 제일 많고, `apt`가 빠릅니다.
  - **추천:** 특별한 이유가 없다면 Ubuntu로 가세요.
- **Rocky Linux 9/10:**
  - **장점:** RHEL(RedHat) 기반이라 엔터프라이즈 환경에서 선호됩니다. 안정성이 높습니다.
  - **단점:** SELinux 때문에 초기 설정이 귀찮고, 패키지 이름이 Ubuntu랑 달라서 가끔 헷갈립니다.
  - **추천:** 사내 정책상 RHEL 계열을 써야만 할 때 선택하세요.
