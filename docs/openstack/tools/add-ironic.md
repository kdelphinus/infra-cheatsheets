# 🟥 OpenStack Ironic 베어메탈 구축 가이드 (Final Master)

**작성일:** 2026-01-14
**아키텍처:** Controller-Network 분리형 (Ironic 서비스 전체를 Network Node로 이동)
**대상 장비:**

- **Controller (`cstation`):** 제어(API), DB, 메시지큐 (기존 유지)
- **Network Node (`cstrato1`):** Ironic 서비스, OVS, 물리 연결(`eno4`)
- **Baremetal (`HP G8`):** 타겟 장비 (2대)

---

## 1. [Controller] 잔여 설정 확인 (충돌 방지)

**`[Controller Node - cstation]`**에서 수행

Network Node로 역할을 넘기기 전, Controller에 혹시 남아있을 수 있는 설정을 정리합니다.

```bash
# 1. Controller에 br-ironic이 없어야 정상
ip addr show br-ironic
# -> 만약 있다면: sudo ip link delete br-ironic

# 2. Netplan에서 eno4 IP가 없는지 확인
cat /etc/netplan/50-cloud-init.yaml

# 3. Systemd 잔여 확인
ls /etc/systemd/system/setup-br-ironic.service
# -> 만약 있다면: sudo rm /etc/systemd/system/setup-br-ironic.service && sudo systemctl daemon-reload
```

---

## 2. [Baremetal] 사전 준비 (Target Node) - 방법 선택

베어메탈 노드(HP G8)의 BIOS와 iLO를 설정합니다. 아래 두 가지 방법 중 하나를 선택하세요.

### ✅ [옵션 A] 현장 작업 (모니터/키보드 연결)

서버실에 들어가서 직접 모니터를 보고 작업하는 경우입니다.

1. iLO IP 설정: 부팅 시 F8 진입 → IP 10.10.10.69 (Node1) / 10.10.10.70 (Node2) 설정.
2. BIOS 설정: 부팅 시 F9 진입.
    - Boot Mode: Legacy BIOS Mode (필수)
    - Network Boot Options: NIC 1을 1순위로.
    - Power Management: Static High Performance.
3. MAC 확인: OS 진입 후 ip link show eno1 또는 BIOS 메뉴에서 확인.

### ✅ [옵션 B] 원격 작업 (SSH & Text Console)

서버실에 가지 않고, 현재 설치된 OS(Ubuntu 등)에 SSH로 접속해 작업하는 경우입니다.

#### Step 1: OS에서 iLO IP 설정 및 MAC 확인

```Bash
# (Baremetal OS 터미널에서 수행)
# 1. MAC 주소 기록
ip link show eno1 | grep ether
# 예: ac:16:2d:77:93:94

# 2. ipmitool 설치
sudo apt update && sudo apt install ipmitool -y
sudo modprobe ipmi_devintf && sudo modprobe ipmi_si

# [중요] 2-1. IPMI 드라이버 정상 동작 확인
# 아래 명령어를 쳤을 때 제조사 정보(Device ID, Manufacturer 등)가 떠야 정상입니다.
# 만약 "Could not open device..." 에러가 나면 하드웨어 지원 문제거나 재부팅 필요.
sudo ipmitool mc info

# [중요] 2-2. 올바른 LAN 채널 번호 찾기 (1번 또는 2번, 드물게 8번)
# 보통 HPE는 2번, Dell은 1번입니다.
# 아래 명령어를 하나씩 입력해서 "IP Address" 등의 정보가 뜨는 채널이 정답입니다.

echo "--- Channel 1 확인 ---"
sudo ipmitool lan print 1

echo "--- Channel 2 확인 ---"
sudo ipmitool lan print 2

# (Tip: "Invalid channel" 이라고 뜨면 그 번호는 아닙니다.)
# (HPE G8/G9/G10은 대부분 '2번'이 정답입니다.)

# 3. iLO IP 설정 (예: Node 1)
sudo ipmitool lan set 2 ipsrc static
sudo ipmitool lan set 2 ipaddr 10.10.10.69
sudo ipmitool lan set 2 netmask 255.255.255.0
sudo ipmitool lan set 2 defgw ipaddr 10.10.10.1

# 4. iLO 계정 설정
sudo ipmitool user set password 2 "FVQBAQ2Q"
sudo ipmitool user enable 2
```

설정이 적용되었는지 확인합니다.

```bash
# 채널 2번(HP Dedicated iLO Port)의 설정값 출력
sudo ipmitool lan print 2

# 결과 예시
# IP Address Source: Static Address (중요)
# IP Address: 10.10.10.69
# Subnet Mask: 255.255.255.0
# Default Gateway IP: 10.10.10.1
```

```bash
# 사용자 활성화 확인
sudo ipmitool user list 2

# 결과 예시
# ID  Name             Callin  Link Auth  IPMI Msg   Channel Priv Limit
# 1   Administrator    true    false      true       ADMINISTRATOR
# 2   admin            true    false      true       ADMINISTRATOR
```

`iLO Advanced` 라이센스 유무에 따라 둘 중 하나를 택해서 진행합니다.

#### Step 2-1: 서버실 이동(iLO Advanced 라이센스 X)

아래 설정만 직접 해줍니다.

1. BIOS 설정: 부팅 시 F9 진입.
    - Boot Mode: Legacy BIOS Mode (필수)
    - Network Boot Options: NIC 1을 1순위로.

#### Step 2-2: iLO 원격 콘솔로 BIOS 설정(iLO Advanced 라이센스 필요)

아래 작업은 `iLO Advanced` 라이센스가 필요합니다. 또한 아래 iLO 포트가 연결되어야 합니다.

```Bash
# (내 PC 또는 Controller에서 수행)
# 1. iLO SSH 접속
ssh Administrator@10.10.10.69
# (비밀번호: FVQBAQ2Q)

# 2. 텍스트 콘솔 실행
hpiLO-> TEXTCONS

# 3. 재부팅 및 F9 진입
# (다른 터미널에서 서버를 reboot 하거나, iLO에서 power reset)
# 화면에 "Press F9"가 나오면 [F9] 키 연타 (안 되면 [Esc]+[9])

# 4. BIOS 설정 (방향키 사용)
# - System Options -> Boot Mode -> Legacy BIOS Mode
# - Network Options -> Network Boot -> NIC 1 (1st)
# - Power Management -> Static High Performance
# - [F10] 저장 및 종료
```

---

## 3. [물리 작업] 케이블 연결

서버실에 들어가서 물리 포트 위치를 변경해줍니다.
환경에 따라 연결할 포트, 스위치 등이 다를 수 있으니 환경에 맞춰 진행합니다.

```text
+-------------------------+              +-------------------------+
| Network Node (cstrato1) |              | Baremetal Node (HP G8)  |
|                         |              |                         |
|      [eno4] (New)       |              |      [NIC 1] (Data)     |
+---------+---------------+              +------------+------------+
          |                                           |
          |                                           |
          v                                           v
+------------------------------------------------------------------+
|               Unmanaged Switch (Provisioning Net)                |
|           (DO NOT CONNECT TO OFFICE NETWORK / INTERNET)          |
|                 subnet: 172.20.50.0/24                           |
+------------------------------------------------------------------+


--------------------------------------------------------------------


+-------------------------+              +-------------------------+
|     Intranet Switch     |              | Baremetal Node (HP G8)  |
|   (Office Network)      |              |                         |
|   subnet: 10.10.10.x    +------------->|       [iLO] (Mgmt)      |
+-------------------------+              +-------------------------+
```

포트 작업 완료 후, 컨트롤 노드에서 아래 작업을 수행하여 정상 동작을 확인합니다.

**`[Controller Node - cstation]`**에서 수행

```bash
# 1. 핑 테스트 (네트워크 연결 확인)
ping -c 3 10.10.10.69

# 2. 실제 로그인 및 전원 상태 확인 (비밀번호 검증)
# (비밀번호 'FVQBAQ2Q'는 예시입니다. 실제 설정한 값을 넣으세요)
ipmitool -I lanplus -H 10.10.10.69 -U Administrator -P 'FVQBAQ2Q' power status
```

---

## 4. [Network Node] 네트워크 및 OVS 설정

**`[Network Node - cstrato1]`** 에서 수행

### 4-1. Netplan 수정 (IP 제거)

```bash
sudo nano /etc/netplan/50-cloud-init.yaml
# 아래 내용을 추가 혹은 수정
...
    eno4:
      dhcp4: false
      dhcp6: false
      optional: true
```

수정했으면 아래 명령어로 적용합니다.

```bash
sudo netplan apply
```

### 4-2. 브리지 생성 및 IP 할당 스크립트

Ironic이 이 노드에 있으므로, **Gateway IP(172.20.50.1)** 를 여기서 할당합니다.

```bash
sudo tee /usr/local/bin/setup-br-ironic.sh << 'EOF'
#!/bin/bash
set -e
if ! docker ps | grep -q openvswitch_vswitchd; then
    echo "❌ OVS 컨테이너 없음. Network Node 확인 요망"
    exit 1
fi

# 1. 브리지 및 포트 연결
docker exec openvswitch_vswitchd ovs-vsctl --may-exist add-br br-ironic
docker exec openvswitch_vswitchd ovs-vsctl --may-exist add-port br-ironic eno4

# 2. [필수] Gateway IP 할당
sudo ip link set br-ironic up
sudo ip addr flush dev br-ironic 2>/dev/null || true
sudo ip addr add 172.20.50.1/24 dev br-ironic

# 3. 물리 포트 정리
sudo ip addr flush dev eno4 2>/dev/null || true

echo "✅ br-ironic (172.20.50.1) 설정 완료"
EOF

sudo chmod +x /usr/local/bin/setup-br-ironic.sh
sudo /usr/local/bin/setup-br-ironic.sh

```

### 4-3. 재부팅 대비 (Systemd 등록)

배포 도중 재부팅되어도 설정이 유지되도록 미리 등록합니다.

```bash
sudo tee /etc/systemd/system/setup-br-ironic.service << 'EOF'
[Unit]
Description=Setup OVS br-ironic bridge for Ironic
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStartPre=/bin/sleep 30
ExecStart=/usr/local/bin/setup-br-ironic.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable setup-br-ironic.service

```

---

## 5. [Controller] Kolla 설정 및 배포

**`[Controller Node - cstation]`** 에서 수행

### 5-1. Inventory 수정 (핵심)

Ironic 서비스를 Network Node 그룹으로 이동합니다.

```bash
sudo nano /etc/kolla/inventory/multinode

```

```ini
# [수정 전]
# [ironic:children]
# control

# [수정 후] 기존 control을 지우고 network로 변경
[ironic:children]
network

```

### 5-2. globals.yml 수정

```bash
sudo nano /etc/kolla/globals.yml

```

```yaml
enable_ironic: "yes"
enable_ironic_neutron_agent: "yes"
enable_ironic_pxe: "yes"
enable_ironic_ipxe: "yes"

# [중요] Network Node의 브리지 이름 지정
ironic_dnsmasq_interface: "br-ironic"

# DHCP 범위
ironic_dnsmasq_dhcp_ranges:
  - range: "172.20.50.10,172.20.50.50"
    routers: "172.20.50.1"

# 초기엔 none
ironic_cleaning: "none"

neutron_ml2_flat_networks: "physnet1,physnet_ironic"

# Ironic API가 Network Node에 있으므로, 해당 노드의 IP를 지정
ironic_internal_fqdn: "10.10.10.61"
ironic_external_fqdn: "10.10.10.61"
ironic_api_port: "6385"
```

### 5-3. Neutron Config Override

```bash
sudo mkdir -p /etc/kolla/config/neutron
sudo tee /etc/kolla/config/neutron/openvswitch_agent.ini << 'EOF'
[ovs]
bridge_mappings = physnet1:br-ex,physnet_ironic:br-ironic
EOF

sudo tee /etc/kolla/config/neutron/ml2_conf.ini << 'EOF'
[ml2_type_flat]
flat_networks = physnet1,physnet_ironic
EOF

```

### 5-4. 서비스 배포

```bash
# 1. Ironic 배포 (cstrato1에 설치됨)
kolla-ansible deploy -i multinode --tags ironic

# 2. Neutron 설정 갱신 (매핑 적용)
kolla-ansible reconfigure -i multinode --tags neutron

# 3. Nova 설정 갱신 (Driver 인식)
kolla-ansible reconfigure -i multinode --tags nova

```

---

## 6. [Controller] 리소스 생성

**`[Controller Node - cstation]`**에서 수행

### 6-1. 네트워크 생성

```bash
openstack network create --share --provider-network-type flat \
  --provider-physical-network physnet_ironic provisioning-net

# Gateway는 Network Node에 할당한 IP(172.20.50.1)와 일치해야 함
openstack subnet create --network provisioning-net \
  --subnet-range 172.20.50.0/24 \
  --gateway 172.20.50.1 \
  --allocation-pool start=172.20.50.10,end=172.20.50.50 \
  --dns-nameserver 8.8.8.8 provisioning-subnet

```

### 6-2. [추가] Cleaning 활성화

네트워크가 생성되었으므로 Cleaning을 켭니다.

```bash
sudo nano /etc/kolla/globals.yml
# ironic_cleaning: "metadata"
# ironic_cleaning_network: "provisioning-net"

# 설정 적용
kolla-ansible reconfigure -i multinode --tags ironic

```

### 6-3. 이미지 및 Flavor 생성

```bash
# 작업 디렉토리
mkdir -p ~/ironic_images && cd ~/ironic_images

# IPA 이미지 다운로드
wget https://tarballs.opendev.org/openstack/ironic-python-agent/dib/files/ipa-centos9-master.kernel
wget https://tarballs.opendev.org/openstack/ironic-python-agent/dib/files/ipa-centos9-master.initramfs

# IPA 이미지 등록
openstack image create --file ipa-centos9-master.kernel \
  --public --container-format aki --disk-format aki deploy-kernel
openstack image create --file ipa-centos9-master.initramfs \
  --public --container-format ari --disk-format ari deploy-ramdisk

# OS 이미지 다운로드 및 등록
wget https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img
openstack image create --file jammy-server-cloudimg-amd64.img \
  --disk-format qcow2 --container-format bare \
  --property hypervisor_type=ironic \
  --public ubuntu-22.04

# Flavor 생성
openstack flavor create --ram 65536 --vcpus 24 --disk 500 \
  --property resources:VCPU=0 \
  --property resources:MEMORY_MB=0 \
  --property resources:DISK_GB=0 \
  --property resources:CUSTOM_BAREMETAL_HP_G8=1 \
  bm.hp-g8
```

### 6-4. 노드 등록 (2대)

만약 `Ironic` 플러그인이 없다면 먼저 설치합니다.

```bash
# 1. Ironic 클라이언트 플러그인 설치
pip install python-ironicclient

# 2. 설치가 잘 됐는지 확인 (이제 명령어가 먹혀야 합니다)
openstack baremetal list
```

아래 node1을 등록하듯이, 값만 바꿔서 여러 노드를 등록할 수 있습니다.

```bash
KERNEL_ID=$(openstack image show deploy-kernel -f value -c id)
RAMDISK_ID=$(openstack image show deploy-ramdisk -f value -c id)
ILO_PASS="FVQBAQ2Q"

# Node 1 등록
openstack baremetal node create --driver ipmi --name hp-g8-01 \
  --driver-info ipmi_address=10.10.10.69 \
  --driver-info ipmi_username=Administrator \
  --driver-info ipmi_password=$ILO_PASS \
  --driver-info deploy_kernel=$KERNEL_ID \
  --driver-info deploy_ramdisk=$RAMDISK_ID \
  --resource-class BAREMETAL_HP_G8 \
  --network-interface flat \
  --property cpus=24 --property memory_mb=65536 --property local_gb=500

# 생성된 baremetal node의 uuid 확인
openstack baremetal node list | grep hp-g8-01

# 등록
openstack baremetal port create --node <hp-g8-01의 uuid> "ac:16:2d:77:93:94"
```

---

## 7. [Controller] 최종 검증

**`[Controller Node - cstation]`**에서 수행

```bash
# 1. 관리 모드 전환 (Ironic -> iLO 연결 테스트)
openstack baremetal node manage hp-g8-01

# 2. 상태 확인 (manageable)
watch -n 5 "openstack baremetal node list"

# 3. 사용 가능 모드 전환 (Cleaning 수행됨 -> 전원 켜짐/꺼짐 반복)
openstack baremetal node provide hp-g8-01

# 4. Keypair 생성
openstack keypair create --public-key ~/.ssh/id_rsa.pub mykey 2>/dev/null || true

# 5. 인스턴스 생성 (available 상태가 된 후)
openstack server create --flavor bm.hp-g8 --image ubuntu-22.04 --network provisioning-net --key-name mykey test-bm

# 6. 상태 확인
watch openstack server list

```

---

## 8. 트러블슈팅

- **IPMI 에러:**

  ```bash
  # Controller에서 실행
  ipmitool -I lanplus -H 10.10.10.69 -U Administrator -P 'FVQBAQ2Q' power status
  ```

- **OVS 확인:**

  ```bash
  # Network Node에서
  docker exec openvswitch_vswitchd ovs-vsctl show
  ```

- **Ironic 로그:**

  ```bash
  # Network Node에서
  docker logs ironic_conductor --tail 100
  ```

- **PXE 패킷:**

  ```bash
  # Network Node에서
  sudo tcpdump -i br-ironic -n port 67 or port 68
  ```

- **Node 에러:**

  ```bash
  # Controller에서 실행
  openstack baremetal node show hp-g8-01 -f json | jq '.last_error'
  ```

---

## 📋 최종 체크리스트

- [ ] 1. Controller 잔여 설정 확인/삭제
- [ ] 2. Baremetal BIOS(Legacy) 및 iLO 설정
- [ ] 3. 물리 케이블 연결 (Network Node)
- [ ] 4. Network Node 설정 (Netplan, Script, Systemd)
- [ ] 5. Inventory 수정 (`[ironic] -> network`)
- [ ] 6. 서비스 배포 (deploy -> reconfigure)
- [ ] 7. 리소스 생성 (Network, Cleaning활성화, Image, Node)
- [ ] 8. 검증 (Manage -> Provide -> Create)
