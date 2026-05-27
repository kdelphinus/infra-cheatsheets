# 🛠️ VMware VM 템플릿 일반 제작 표준 가이드 (v4.0)

이 문서는 **Linux Server**, **Ubuntu Desktop**, **Windows Server** 환경의 VMware 가상 머신(VM) 템플릿을 생성하고 자동 디스크 확장 및 초기 네트워크 셋업을 완벽히 수행하기 위한 표준 운영 가이드라인이에요.

---

## 📌 공통 핵심 전제

템플릿 가상 머신을 템플릿으로 변환하기 전 반드시 확보되어야 하는 핵심 요구사항이에요.

*   **Linux 계열 VM**:
    *   **cloud-init**을 활용하여 VM 부팅 시 초기 사용자 데이터 주입, 네트워크 렌더링, 루트 디스크 확장을 수행해요.
    *   네트워크 관리 서비스는 기본적으로 **NetworkManager**를 사용해요.
    *   cloud-init의 메타데이터 소스는 **VMware datasource**(`VMware`, `OVF`)를 허용하도록 설정해요.
    *   디스크 확장 시 파티션 크기 조정을 위해 `growpart` 및 `resizefs` 명령어가 내장되어 있어야 해요.
*   **Windows 계열 VM**:
    *   cloud-init을 사용하지 않고, VMware의 **CustomizationSysprep** 메커니즘을 사용해 호스트명, 비밀번호, 네트워크를 자동 주입해요.
*   **공통 관리**:
    *   템플릿 변환 직전에는 OS 고유 식별자(machine-id), 네트워크 연결 정보, 로그 및 임시 파일을 깨끗이 정리(Clean)해야 해요.

---

## 🐧 1. Linux Server 템플릿 기본 생성 절차

### 1.1 가상 머신 생성 및 이미지 준비
1.  vCenter 콘솔을 통해 설치하려는 OS 이미지(ISO) 또는 이미 배포 준비가 된 OVF 파일을 업로드해요.
2.  vCenter 콘솔의 **OVF 템플릿 배포** 기능을 사용하여 가상 머신을 생성하고, 웹 콘솔에 접속하여 기본 네트워크 및 OS 설치를 마쳐요.

### 1.2 필수 서비스 상태 확인
최초 OS 설치 직후 아래 명령어로 관련 데몬의 활성화 여부를 점검해요.
```bash
systemctl status cloud-init
systemctl status vmtoolsd
```
> [!NOTE]
> 만약 서비스가 없거나 비활성화되어 있더라도 아래의 필수 패키지 설치 단계에서 함께 활성화 처리를 진행하게 돼요.

### 1.3 필수 구성 패키지 설치
RHEL, Rocky Linux 등 RedHat 계열 배포판의 경우 아래 패키지들을 반드시 설치해 주어야 해요.
```bash
sudo dnf install -y \
  cloud-init \
  cloud-utils-growpart \
  open-vm-tools \
  NetworkManager \
  openssh-server \
  xfsprogs
```

*   **패키지별 역할 요약**:
    *   **`cloud-init`**: VM 첫 부팅 시 메타데이터 수집, 사용자 계정/네트워크/디스크 자동 확장 수행.
    *   **`cloud-utils-growpart`**: 디스크 크기 증가 시 루트 파티션을 확장하는 핵심 바이너리(`growpart`) 제공.
    *   **`open-vm-tools`**: VMware 하이퍼바이저와 게스트 OS 간 Customization 및 통합 지원.
    *   **`NetworkManager`**: cloud-init이 작성하는 네트워크 구성의 기본 렌더링 엔진.
    *   **`xfsprogs`**: RHEL 계열에서 많이 사용되는 XFS 파일시스템 확장 도구(`xfs_growfs`) 제공.

> [!IMPORTANT]
> **`cloud-utils-growpart`** 패키지가 누락되면 cloud-init 설정에 아무리 growpart를 지정해도 디스크가 늘어나지 않고 `/var/log/cloud-init.log`에 `growpart unable to find resizer for 'auto': No resizers available` 에러가 남게 되니 주의해 주세요!

설치 후 정상 동작 여부를 아래 명령어로 교차 검증해요.
```bash
# 설치 검증
rpm -q cloud-init cloud-utils-growpart open-vm-tools NetworkManager openssh-server xfsprogs

# 명령어 검증
command -v growpart
command -v xfs_growfs
```

---

## 🖥️ 2. Ubuntu Desktop 템플릿 구성 절차 (22.04 / 24.04)

Ubuntu Desktop 환경은 일반 Server 버전과 달리 cloud-init과 openssh-server가 기본적으로 설치되어 있지 않아요. 따라서 CMP(클라우드 관리 플랫폼)에서 IP 주입이나 계정 생성 등이 정상 적용되게 하려면 아래 수동 조치를 명시적으로 진행해야 해요.

### 2.1 가상 머신 생성
*   Ubuntu Desktop ISO 파일을 사용하여 VM을 생성하고 설치를 완료해요.
*   OS 설치 화면에서 **최소 설치 (Minimal installation)** 옵션을 체크하면 불필요한 데스크톱 유틸리티 패키지를 줄이고 최적화된 용량의 템플릿을 빌드할 수 있어요.

### 2.2 필수 패키지 수동 설치
데스크톱 환경에 인터넷을 임시로 연결한 뒤 아래 패키지들을 구성해요.
```bash
sudo apt update
sudo apt install -y \
  cloud-init \
  cloud-guest-utils \
  open-vm-tools \
  openssh-server \
  network-manager \
  xfsprogs

# ext4 파일시스템 확장을 위해 e2fsprogs가 없을 시 추가 설치
sudo apt install -y e2fsprogs
```
> [!NOTE]
> Ubuntu(Debian) 계열에서는 growpart 명령어를 제공하는 패키지명이 `cloud-utils-growpart`가 아닌 **`cloud-guest-utils`** 임에 주의해 주세요.

설치 완료 확인 명령어:
```bash
dpkg -l cloud-init cloud-guest-utils open-vm-tools openssh-server network-manager xfsprogs e2fsprogs
command -v growpart
command -v resize2fs || true
```

---

## 🪟 3. Windows Server 템플릿 구성 절차 (2019 / 2022)

Windows 가상 머신은 cloud-init 메커니즘을 타지 않고, VMware 고유의 **CustomizationSysprep**을 활용하므로 빌드 방식이 완전히 달라요.

### 3.1 OS 및 VMware Tools 설치
1.  Windows Server ISO 이미지로 가상 머신을 만들고 설치 유형은 필요에 따라 **Desktop Experience** 또는 **Server Core**를 선택해요.
2.  vCenter 콘솔에서 해당 가상 머신 우클릭 -> **게스트 OS** -> **VMware Tools 설치**를 선택한 후, 탐색기 `D:\setup64.exe` 또는 `setup.exe`를 실행하여 도구를 설치해요.
3.  만약 자동 마운트가 되지 않는다면, 수동으로 VMware Tools ISO 파일을 VM 내부로 복사하거나 업로드하여 **Typical** 유형으로 설치 완료한 뒤 재부팅해요.
4.  PowerShell에서 서비스가 원활히 구동 중인지 검증해요.
    ```powershell
    Get-Service -Name VMTools
    ```

### 3.2 원격 데스크톱(RDP) 및 방화벽 활성화
CMP 배포 후 원격 관리가 가능하도록 RDP를 승인하고 포트(3389) 방화벽 규칙을 개방해요. (관리자 권한 PowerShell 실행)
```powershell
# RDP 연결 허용
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0

# 방화벽 허용 규칙 적용
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"

# 원격 제어 서비스 동작 상태 체크
Get-Service -Name TermService
```

### 3.3 Windows Update 실행
가장 최신 보안 패치를 템플릿 빌드 단계에서 미리 적용해 주어야 배포 시간이 줄어들어요.
```powershell
Install-Module PSWindowsUpdate -Force
Get-WindowsUpdate -Install -AcceptAll -AutoReboot
```

### 3.4 Sysprep 일반화(Generalization) 구성 규칙
Windows VM은 복제 시 고유 SID를 재생성하기 위해 Sysprep 일반화 단계를 만족시켜야 해요.

> [!CAUTION]
> 템플릿 제작 단계에서 직접 Sysprep 실행 파일을 마구 구동하면 안 돼요. 템플릿 상태에서는 **Sysprep 실행이 원활히 가능한 대기 상태(Rearm count 남음 등)**만 확보해 두어야 하며, 최종 배포 단계에서 VMware CustomizationSpec이 스스로 Sysprep 명령을 기동하도록 설계해야 해요.

*   **Rearm 횟수 진단**: 남은 초기화 제한 횟수를 확인하기 위해 아래 명령어를 구동해요.
    ```cmd
    slmgr /dlv
    ```
*   **IaC용 프로비저닝 차단**: 클라우드 가상화 플랫폼과의 시너지를 위해 `Cloudbase-init`과 같은 별도 에이전트는 구성하지 않는 것을 원칙으로 해요.
*   **Sysprep 수동 강제 스케줄러 (동작 장애 대비 대체제)**:
    만약 배포 중 정상적인 초기화가 되지 않는 돌발 상황이 우려된다면, 디렉토리 생성 후 부팅 시 1회 강제 실행되도록 CMD 스케줄러를 등록할 수도 있어요.
    1.  `C:\sysprep` 폴더를 생성해요.
    2.  `C:\sysprep\run-sysprep.cmd` 스크립트를 작성해요.
        ```cmd
        @echo off
        echo Running sysprep...
        schtasks /delete /tn "ForceSysprep" /f
        C:\Windows\System32\Sysprep\sysprep.exe /generalize /oobe /reboot /unattend:C:\sysprep\sysprep.xml
        ```
    3.  PowerShell에서 시스템 시작 스케줄 작업으로 연동해요.
        ```cmd
        schtasks /create /tn "ForceSysprep" /sc onstart /ru SYSTEM /tr "C:\sysprep\run-sysprep.cmd"
        ```

---

## 📋 4. 필수 구성 요소 및 카탈로그 등록 요약

### 4.1 핵심 OS 구성 매트릭스

| 구성 요소 | Linux Server | Ubuntu Desktop | Windows Server |
| :--- | :--- | :--- | :--- |
| **VMware Tools** | `open-vm-tools` (필수) | `open-vm-tools` (필수) | VMware Tools Windows 패키지 |
| **cloud-init** | **필수** | **필수** | 불필요 |
| **DataSourceVMware** | **필수** (`VMware`, `OVF`) | **필수** (`VMware`, `OVF`) | 불필요 |
| **자동 디스크 확장** | `growpart`, `resize_rootfs` | `growpart`, `resize_rootfs` | 해당 없음 (Sysprep 자동 연동) |
| **growpart 패키지** | `cloud-utils-growpart` | `cloud-guest-utils` | 해당 없음 |
| **openssh-server** | **필수** | **필수** | 선택 |
| **Node Exporter** | **필수** (9100 메트릭 수집용) | **필수** (9100 메트릭 수집용) | 해당 없음 |
| **NIC 이름 고정** | 권장 (`eth0`, `eth1` 순서) | 권장 (`eth0`, `eth1` 순서) | 해당 없음 |
| **Sysprep 상태** | 해당 없음 | 해당 없음 | **필수** (Rearm 잔여 횟수 확보) |
| **네트워크 관리** | `NetworkManager` | `NetworkManager` | Windows Network Service |

### 4.2 CMP 카탈로그 등록 시 OS 유형 가이드라인
가상 머신 템플릿을 이미지 카탈로그 상품으로 올릴 때 `osGroup`과 `osVersion` 값을 정확하게 바인딩해 주어야 해요. 잘못 입력하면 초기화 스크립트가 잘못 렌더링되거나 오작동이 일어나요.

*   **`osGroup` 값 설정 매핑**:
    *   `ubuntu`, `centos`, `rhel`, `rocky` 등: cloud-init 방식을 채택하며, 네트워크 환경은 기본적으로 `gateway4` 구문을 사용해요.
    *   `ubuntu-desktop`: cloud-init 기반이며 렌더러로 `NetworkManager`를 필수로 요구하고, `routes` 구문 렌더링이 강제돼요.
    *   `windows`: CustomizationSysprep을 타게 되며 cloud-init 설정은 전부 우회되고 RDP 기본 허용으로 처리돼요.
*   **`osVersion` 및 24.04 주의사항**:
    *   **Ubuntu 24.04 이상** 버전(Server 포함)부터는 클라우드 표준에 맞춰 기존 구식 지시어인 `gateway4`가 완전 제거되었어요. 따라서 해당 사양에서는 반드시 `routes` 구문으로 자동 번역되어 렌더링되게끔 처리돼요.
