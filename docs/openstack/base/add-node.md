# ➕ OpenStack 신규 노드 추가 가이드 (Kolla-Ansible)

기존에 운영 중인 Kolla-Ansible 기반 OpenStack 클러스터에 새로운 노드(주로 컴퓨트 노드)를 추가하는 방법을 정리했어요.

이 가이드는 기존 서비스에 영향을 주지 않으면서 안전하게 신규 컴퓨트 노드를 추가하는 과정을 기준으로 설명해요.

---

## ⚙️ 1. 신규 노드 OS 및 인프라 사전 준비

신규로 추가할 서버에 OS 설치를 마친 후, 아래 사전 작업을 진행해야 해요. 기존 노드들과 동일한 OS 환경(Ubuntu 또는 Rocky Linux)을 사용하는 것을 권장해요.

### 🌐 1.1 IP 설정 및 Hosts 등록
모든 OpenStack 노드는 서로 통신할 수 있어야 해요.
배포 노드를 포함한 **모든 기존 노드**와 **신규 노드**의 `/etc/hosts` 파일에 신규 노드의 IP와 호스트명을 추가해 주세요.

```bash
# /etc/hosts 예시
10.10.10.60  cstation
10.10.10.68  compute01
210.217.178.198  compute02  # <-- 신규 노드 추가
```

### 🔑 1.2 SSH 키 복사 (Passwordless SSH)
Kolla-Ansible은 배포 노드에서 각 대상 노드로 SSH 접속을 통해 컨테이너를 배포해요.
배포 노드에서 신규 노드의 접속 계정으로 비밀번호 없이 접속이 가능하도록 SSH 키를 복사해요.

```bash
# 배포 노드에서 실행 (접속 사용자 계정이 strato인 경우)
ssh-copy-id strato@210.217.178.198

# 패스워드 입력창 없이 바로 로그인되는지 최종 확인
ssh strato@210.217.178.198
```

### 🔓 1.3 일반 사용자 계정 Sudo 권한 부여 (root 미사용 시)
`root` 계정이 아닌 일반 유저 계정(예: `strato`)으로 Ansible을 구동하는 경우, 비밀번호 없이 `sudo` 명령을 내릴 수 있도록 권한을 설정해야 해요.

```bash
# [신규 노드에서 실행]
echo "strato ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/strato
sudo chmod 0440 /etc/sudoers.d/strato
```

---

## 📝 2. 배포 노드 설정 수정

Kolla-Ansible이 신규 노드를 인식하고 배포 대상을 구분할 수 있도록 인벤토리 파일을 수정해요.

### 🗂️ 2.1 인벤토리 파일 수정 (`multinode`)
배포 시 사용 중인 인벤토리 파일(일반적으로 `/etc/kolla/multinode`)을 엽니다.
`[compute]` 그룹 또는 신규 노드가 맡을 역할의 그룹 아래에 신규 노드 정보를 추가해요.

```ini
# /etc/kolla/multinode 예시
[compute]
10.10.10.68 ansible_user=strato ansible_become=true
210.217.178.198 ansible_user=strato ansible_become=true  # <-- 신규 노드 추가
```

---

## 🚀 3. Kolla-Ansible 배포 실행 (노드 한정)

전체 클러스터에 영향을 주지 않고 신규 노드만 타겟팅하기 위해 **`--limit` 옵션을 사용하는 것이 핵심**이에요. 

또한, 기존 노드들과의 교차 검증 중 발생할 수 있는 SSH 키 에러를 우회하기 위해 **`ANSIBLE_HOST_KEY_CHECKING=False`** 변수를 붙여 실행하는 것을 권장해요.

```bash
# 1. 신규 노드 부트스트랩 (Docker 및 기본 패키지 자동 설치)
ANSIBLE_HOST_KEY_CHECKING=False kolla-ansible bootstrap-servers -i multinode --limit 210.217.178.198

# 2. 사전 환경 검사 (Prechecks)
ANSIBLE_HOST_KEY_CHECKING=False kolla-ansible prechecks -i multinode --limit 210.217.178.198

# 3. 오픈스택 서비스 컨테이너 배포 (Deploy)
ANSIBLE_HOST_KEY_CHECKING=False kolla-ansible deploy -i multinode --limit 210.217.178.198
```

!!! warning
    `--limit` 옵션 없이 배포하게 되면 클러스터 내 전체 서비스 컨테이너의 헬스체크 및 롤링 업데이트가 일어나므로 많은 시간이 소요되고 운영 중인 서비스에 영향을 줄 수 있어요. 반드시 추가할 노드명/IP만 `--limit`에 지정해 주세요.

---

## 🔍 4. 배포 완료 확인 및 사후 작업

배포 프로세스가 완료되면 컨트롤러 노드에서 클라이언트를 사용하여 새 노드가 성공적으로 활성화되었는지 확인해요.

### 🔄 4.1 Cell 호스트 디스커버리 (필수)
Nova 스케줄러가 새 컴퓨트 노드를 인지하고 인스턴스를 스케줄링할 수 있게 하기 위해, Nova Cell 데이터베이스에 호스트를 등록해 주어야 해요. 컨트롤러 노드에서 아래 명령을 수행해요.

```bash
# nova_api 컨테이너 내에서 cell v2 discover 실행
docker exec -it nova_api nova-manage cell_v2 discover_hosts --verbose
```

### 📊 4.2 하이퍼바이저 및 서비스 상태 확인
CLI 환경 변수(`admin-openrc.sh`)를 로드한 상태에서 하이퍼바이저 목록을 확인해요.

```bash
# 1. OpenStack admin 계정 환경 변수 로드
source /etc/kolla/admin-openrc.sh

# 2. 하이퍼바이저 목록 조회
openstack hypervisor list

# 3. Nova 컴퓨트 서비스 상태 확인 (State가 up인지 확인)
openstack compute service list --service nova-compute

# 4. Neutron 네트워크 에이전트 동작 확인 (Alive가 웃는 얼굴 :-) 인지 확인)
openstack network agent list
```

---

## 💡 실무 트러블슈팅 가이드

### 1. `kolla_address` 필터 플러그인 에러 (랜카드 이름 불일치)
*   **증상**: `bootstrap-servers`나 `deploy` 중 `The filter plugin 'kolla_address' failed: Interface 'eno1' not present on host` 와 같은 에러 발생.
*   **원인**: 기존 노드들이 사용하는 관리망 랜카드 이름(예: `eno1`)과 신규 노드의 실제 랜카드 이름(예: `enp5s0`)이 달라 발생하는 호환성 문제입니다.
*   **해결책**: 인벤토리 파일(`multinode`)에서 신규 노드 IP 뒷부분에 개별적으로 **`api_interface`** 및 **`tunnel_interface`** 변수를 지정해 줍니다. 이때, 반드시 **실제 IP가 할당되어 사용 중인 인터페이스 이름**을 지정해야 합니다.

```ini
# /etc/kolla/multinode 수정 예시
210.217.178.198 ansible_user=strato ansible_become=true api_interface=enp5s0 tunnel_interface=enp5s0 neutron_external_interface=enp6s0
```

### 2. SSH Host key verification failed 에러
*   **증상**: 팩트 수집(`Gather facts`) 단계 등에서 타 노드로 SSH 대행 연결 시 `Host key verification failed.` 발생.
*   **원인**: 배포 노드의 SSH `known_hosts` 파일에 대상 노드들의 지문이 없어서 확인 대기 상태로 머물다 끊어지는 현상입니다.
*   **해결책**: 명령어 맨 앞에 `ANSIBLE_HOST_KEY_CHECKING=False` 환경 변수를 추가하여 호스트 키 검증을 무시하도록 강제합니다.
