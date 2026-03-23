# 📘 OpenStack CLI 치트시트 (Cheat Sheet)

OpenStack 운영 및 관리를 위한 필수 명령어 모음입니다.

> **범례**:
>
> - `<값>` : 필수 입력 값 (예: ID, 이름)
> - `[옵션]` : 선택 입력 값

## 0. 환경 설정 (필수)

명령어를 실행하기 전, 반드시 인증 정보를 로드해야 합니다.

```bash
# 인증 파일 로드
source admin-openrc.sh

# 토큰 잘 받아졌는지 확인
openstack token issue
```

-----

## 1. 인스턴스 (Server) 관리

가상머신(VM)의 생명주기를 관리합니다.

| 작업 | 명령어 | 설명 |
| :--- | :--- | :--- |
| **목록 조회** | `openstack server list --all-projects` | 모든 프로젝트의 VM 목록 조회 |
| **상세 조회** | `openstack server show <인스턴스_ID>` | 특정 VM의 상세 정보(IP, 호스트, 상태) 조회 |
| **로그 확인** | `openstack console log show <인스턴스_ID>` | 부팅 로그(Console Log) 확인 (디버깅용) |
| **콘솔 URL** | `openstack console url show <인스턴스_ID>` | 웹 VNC 접속 주소 확인 |
| **생성** | `openstack server create --image <이미지> --flavor <플레이버> --network <네트워크> <VM이름>` | 인스턴스 생성 |
| **삭제** | `openstack server delete <인스턴스_ID>` | 인스턴스 삭제 |

### ⚡ 전원 관리 (중요)

```bash
# 부드러운 재부팅 (OS 레벨 재부팅)
openstack server reboot <인스턴스_ID>

# 강제 재부팅 (전원 껐다 켜기 - GPU 오류 시 필수)
openstack server reboot --hard <인스턴스_ID>

# 인스턴스 일시 정지 해제 (Paused 상태 풀기)
openstack server unpause <인스턴스_ID>
```

-----

## 2. 이미지 (Image) 관리

Glance 서비스 관련 명령어입니다.

| 작업 | 명령어 |
| :--- | :--- |
| **목록 조회** | `openstack image list` |
| **상세 조회** | `openstack image show <이미지_ID>` |
| **이미지 등록** | `openstack image create "<이름>" --file <파일경로> --disk-format qcow2 --container-format bare --public` |
| **속성 수정** | `openstack image set --property <키>=<값> <이미지_ID>` |
| **삭제** | `openstack image delete <이미지_ID>` |

### 🔧 GPU/가상화 관련 속성 설정 (필수)

```bash
# 머신 타입 Q35 설정 (PCIe Passthrough 필수)
openstack image set --property hw_machine_type=q35 <이미지_ID>

# 하이퍼바이저 숨기기 (RTX 계열 필수)
openstack image set --property hw:kvm_hidden=true <이미지_ID>

# Guest Agent 활성화 (IP 확인용)
openstack image set --property hw_qemu_guest_agent=yes <이미지_ID>
```

-----

## 3. 플레이버 (Flavor) 관리

인스턴스의 사양(CPU, RAM, Disk)을 정의합니다.

| 작업 | 명령어 |
| :--- | :--- |
| **목록 조회** | `openstack flavor list` |
| **생성** | `openstack flavor create --ram <MB> --disk <GB> --vcpus <개수> <플레이버_이름>` |
| **삭제** | `openstack flavor delete <플레이버_ID>` |

### 🔧 플레이버 속성 (Extra Specs)

```bash
# 속성 설정 (GPU용)
openstack flavor set --property hw:pci_numa_affinity_policy=required <플레이버_ID>

# 속성 확인
openstack flavor show <플레이버_ID>
```

-----

## 4. 네트워크 (Network) 관리

Neutron 서비스 관련 명령어입니다.

| 작업 | 명령어 | 설명 |
| :--- | :--- | :--- |
| **네트워크 목록** | `openstack network list` | 내부/외부 네트워크 목록 |
| **서브넷 목록** | `openstack subnet list` | IP 대역 확인 |
| **보안그룹 목록** | `openstack security group list` | 방화벽 그룹 확인 |
| **규칙 추가** | `openstack security group rule create --proto tcp --dst-port <포트> <그룹ID>` | 포트 개방 (예: 22, 80) |

### 🌐 Floating IP (공인 IP)

```bash
# Floating IP 목록 조회
openstack floating ip list

# 새 IP 생성 (할당)
openstack floating ip create <외부_네트워크_이름>

# 인스턴스에 연결
openstack server add floating ip <인스턴스_ID> <IP주소>
```

-----

## 5. 시스템 및 하이퍼바이저 관리 (Admin 전용)

운영자(Operator)가 클러스터 상태를 점검할 때 씁니다.

| 작업 | 명령어 | 설명 |
| :--- | :--- | :--- |
| **하이퍼바이저 상태** | `openstack hypervisor list` | 각 노드의 UP/DOWN 상태 확인 |
| **컴퓨트 서비스** | `openstack compute service list` | nova-compute 서비스 상태 확인 |
| **자원 사용량** | `openstack hypervisor stats show` | 전체 클러스터 자원 통계 |
| **노드 상세 정보** | `openstack hypervisor show <호스트명>` | 특정 노드의 CPU/RAM 상세 스펙 |

-----

## 6. 볼륨 (Volume) 관리

Cinder 서비스 관련 명령어입니다.

| 작업 | 명령어 |
| :--- | :--- |
| **목록 조회** | `openstack volume list` |
| **생성** | `openstack volume create --size <GB> <볼륨이름>` |
| **연결** | `openstack server add volume <인스턴스_ID> <볼륨_ID>` |
| **해제** | `openstack server remove volume <인스턴스_ID> <볼륨_ID>` |

-----

## 7. Placement (Resource) 관리

Placement 서비스 관련 명령어로, 물리 노드 및 GPU 같은 특수 자원의 재고(Inventory)와 할당(Allocation) 상태를 확인합니다.

| 작업 | 명령어 | 설명 |
| :--- | :--- | :--- |
| **RP 목록 조회** | `openstack resource provider list` | 등록된 모든 자원 제공자(Compute Node, GPU 등) 목록 |
| **재고(Inventory) 확인** | `openstack resource provider inventory list <RP_UUID>` | 특정 노드의 CPU, RAM, GPU **총량 및 여유분** 조회 |
| **사용량(Usage) 확인** | `openstack resource provider usage show <RP_UUID>` | 특정 노드의 자원별 **실제 사용량** 조회 |
| **할당(Allocation) 확인** | `openstack resource provider allocation show <RP_UUID>` | 어떤 인스턴스가 이 노드의 자원을 점유 중인지 확인 |
| **트레이트(Trait) 조회** | `openstack resource provider trait list <RP_UUID>` | 노드의 특성 태그(예: `HW_CPU_X86_AVX512`) 조회 |
| **이름 변경** | `openstack resource provider set --name <새이름> <RP_UUID>` | 리소스 프로바이더 이름 변경 |
| **RP 삭제** | `openstack resource provider delete <RP_UUID>` | (주의) 자원 제공자 삭제 (좀비 레코드 정리 시 사용) |

### 🔍 자원 스케줄링 디버깅 (Allocation Candidates)

"내 VM이 왜 생성이 안 되지? (No Valid Host)" 에러가 날 때, 스케줄러 입장에서 **"배포 가능한 후보지"**가 있는지 미리 조회해보는 명령어입니다.

```bash
# 스펙에 맞는 후보 호스트 조회 (예: CPU 1개, 메모리 512MB)
openstack allocation candidate list --resource VCPU=1 --resource MEMORY_MB=512

# GPU가 포함된 후보 호스트 조회 (예: GPU 1개 필요)
# (사용자 환경에 따라 클래스 이름이 VGPU 또는 PCI_DEVICE 등으로 다를 수 있음)
openstack allocation candidate list --resource VCPU=4 --resource CUSTOM_GPU_RTX3060=1
```

-----

### 💡 Resource Class (자원 클래스) 참고

명령어 사용 시 자주 보이는 자원 이름(Class)들입니다.

- **`VCPU`**: 가상 CPU 코어 수
- **`MEMORY_MB`**: 메모리 용량 (MB)
- **`DISK_GB`**: 로컬 디스크 용량 (GB)
- **`PCI_DEVICE`** 또는 **`CUSTOM_...`**: GPU 같은 특수 장치

**예시: 특정 컴퓨트 노드(`openstack22`)의 GPU 재고 확인하기**

```bash
# 1. 목록에서 openstack22의 UUID 찾기
openstack resource provider list --name openstack22

# 2. 해당 UUID로 재고 확인 (GPU 개수 확인용)
openstack resource provider inventory list <openstack22_UUID>
```

-----

### 💡 팁: 출력 포맷 예쁘게 보기

명령어 뒤에 `-c` (컬럼 선택)와 `-f` (포맷) 옵션을 쓰면 필요한 정보만 깔끔하게 볼 수 있습니다.

```bash
# ID와 이름, 상태만 보고 싶을 때 (테이블 형식)
openstack server list -c ID -c Name -c Status

# 값만 뽑아서 스크립트에 쓰고 싶을 때 (Value 형식)
openstack server show <ID> -c status -f value
```
