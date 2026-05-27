# 🐧 Rocky Linux 9.6 Vagrant 기반 VMware 템플릿 생성 가이드 (v3.0)

이 문서는 **Rocky Linux 9.6 Vagrant VMware 이미지**를 기반으로 vCenter 배포를 위한 공식 인프라 템플릿으로 마이그레이션하고, VM 생성 시 cloud-init을 통해 IP/라우팅 및 루트 디스크 자동 확장이 한 오차도 없이 안정적으로 동작하도록 제작하는 절차예요.

---

## 📌 핵심 기본 전제

템플릿 빌드 시 무조건 확보되어야 하는 핵심 요구사항 항목이에요.
*   OS 네트워크 제어 엔진은 **NetworkManager**를 사용해요.
*   cloud-init의 메타데이터 탐색 datasource는 **`VMware`** 및 **`OVF`**로 한정 제한해요.
*   자동 용량 증설을 완벽하게 대응하도록 **`cloud-utils-growpart`**를 빌드 단계에서 확실히 적재해 주어야 해요.
*   최종 템플릿 변환 직전에는 `cloud-init clean --logs --machine-id` 명령으로 고유 ID와 캐시를 지워 **완전한 첫 부팅(First Boot)** 상태를 강제해야 해요.

---

## 1. 이미지 준비 및 OVF 변환 절차

### 1.1 Rocky Linux Vagrant 이미지 다운로드
Rocky Linux 아카이브 스토리지에서 VMware 가상화용 최신 Box를 직접 내려받아요.
*   **다운로드 경로**: [Rocky Linux Vault - x86_64 이미지](https://dl.rockylinux.org/vault/rocky/9.6/images/x86_64/)
*   **다운로드 대상 파일**: `Rocky-9-Vagrant-VMware.latest.x86_64.box`

### 1.2 Vagrant Box 압축 해제 및 확인
Box 파일은 실질적으로 tar 압축 파일이에요. 확장자를 변경하여 안에 들어있는 `.vmx` 설정을 추출해요.
```bash
# 확장자 명칭 변경
mv Rocky-9-Vagrant-VMware.latest.x86_64.box Rocky-9-Vagrant-VMware.latest.x86_64.tar.gz

# tar 압축 해제
tar xvf Rocky-9-Vagrant-VMware.latest.x86_64.tar.gz

# vmx 가상 머신 설정 파일 확보 검증
ls -al *.vmx
```

### 1.3 OVF 변환 도구 설치
VMware 가상 머신 구성을 OVF 구조로 컨버전하기 위해 Broadcom 포털에서 **`ovftool`**을 획득하여 터미널에 설치해요.
*   **도구 획득 경로**: [Broadcom OVF Tool 다운로드 링크](https://developer.broadcom.com/tools/open-virtualization-format-ovf-tool/latest)

### 1.4 OVF 포맷 변환 기동
변환 툴을 이용하여 vmx 구조를 업로드용 OVF 구조로 트랜스폼해요.
```bash
ovftool "Rocky-9-Vagrant-VMware-9.6-20250531.0.x86_64.vmx" "Rocky-9-Template.ovf"
```

---

## 2. vCenter 업로드 및 하드웨어 구성 조정

### 2.1 OVF 템플릿 배포 및 등록
vCenter 관리 콘솔의 **OVF 템플릿 배포** 메뉴를 실행하여 방금 빌드한 `Rocky-9-Template.ovf` 리소스를 업로드해요.

### 2.2 가상 하드웨어 환경 편집
1.  **네트워크 어댑터**: 신규 어댑터를 추가하고, 드라이버 방식을 예측 가능하고 고성능인 **VMXNET3** 유형으로 변경해요.
2.  **부팅 사양**: 하드웨어 가상 펌웨어 구동 설정을 **BIOS** 부팅 방식으로 지정해요.
3.  **CPU/메모리/디스크**: 타겟 인프라 요건에 따라 사양을 조정해요.

> [!NOTE]
> 자동 볼륨 리사이징은 루트 파티션이 대상 디스크의 **가장 뒤쪽(연속된 공간)**에 배정되어 있을 때 오류 없이 매끄럽게 동작해요. LVM(논리 볼륨) 기반인 가이드가 요구될 때는 수동 `pvresize`, `lvextend -r` 절차를 태워야 할 수 있어요.

---

## 3. 서비스 설치 및 cloud-init 환경 튜닝

### 3.1 부팅 및 최초 권한 획득
가상 머신 구동 후 Vagrant 기본 계정을 사용해 루트 셸을 확보해요.
*   **기본 사용자 계정**: `vagrant`
*   **기본 비밀번호**: `vagrant`

구동 직후 필수 데몬 가동 현황을 파악해요.
```bash
systemctl status cloud-init
systemctl status vmtoolsd
```

### 3.2 임시 네트워크 인터페이스 구성
필수 모듈의 DNF 팩 다운로드를 위해 `nmcli` 명령으로 일시 인터넷 접속 경로를 셋업해요.
```bash
# 디바이스 명칭 스캔
sudo nmcli connection show

# "Wired connection 1" 명칭 확인 시, static IP 및 게이트웨이 강제 적용
sudo nmcli connection modify "Wired connection 1" \
  ipv4.addresses x.x.x.x/x \
  ipv4.gateway x.x.x.x \
  ipv4.dns x.x.x.x \
  ipv4.method manual

# 인터페이스 적용 및 핑 검증
sudo nmcli connection up "Wired connection 1"
ping -c 3 8.8.8.8
ping -c 3 dl.rockylinux.org
```

### 3.3 핵심 패키지 주입
가상화 드라이브 안정화와 디스크 리사이즈를 완벽하게 구동하는 패키지를 dnf로 적재해요.
```bash
sudo dnf install -y \
  cloud-init \
  cloud-utils-growpart \
  open-vm-tools \
  NetworkManager \
  openssh-server \
  xfsprogs
```

*   **패키지별 요약**:
    *   `cloud-init`: VM 부팅 시 메타데이터 매핑 및 파티션 자동 리사이즈 수행.
    *   `cloud-utils-growpart`: `/` 파티션 강제 볼륨 할당용 `growpart` 쉘 유틸리티 제공.
    *   `open-vm-tools`: 게스트 커스터마이제이션 지원.
    *   `NetworkManager`: 클라우드 메타데이터 네트워크 렌더링.
    *   `xfsprogs`: XFS 파일시스템 확장 도구(`xfs_growfs`) 제공.

설치 완료 검사:
```bash
rpm -q cloud-init cloud-utils-growpart open-vm-tools NetworkManager openssh-server xfsprogs
command -v growpart
command -v xfs_growfs
```

### 3.4 cloud-init 렌더러 `NetworkManager` 강제 지정
네트워크 제어가 충돌 없이 NetworkManager 프로토콜로 작동되게 렌더러 설정을 드롭인 경로에 작성해 주어요. (YAML 들여쓰기 정렬 철저 준수)
```bash
sudo tee /etc/cloud/cloud.cfg.d/99-network-renderer.cfg >/dev/null <<'EOF'
system_info:
  network:
    renderers: ['network-manager']
EOF
```

### 3.5 VMware 전용 Datasource 제한 설정
VMware Guest OS Customization 및 vCenter GuestInfo의 cloud-init 정보 주입 방식을 타도록 datasource 경로를 구성해요.
```bash
sudo tee /etc/cloud/cloud.cfg.d/99_vmware.cfg >/dev/null <<'EOF'
datasource_list: [ VMware, OVF, None ]
datasource:
  VMware:
    allow_raw_data: true
    allow_update_network: true
    network_config:
      encoding: base64
      variable: network
EOF
```

### 3.6 디스크 자동 팽창(`growpart` & `resizefs`) 세부 설정
디스크 1의 확장이 일어났을 때, 마운트 지점(`/`)과 파티션 공간을 100% 동기화해 주도록 관련 드롭인 스크립트를 작성하고 불필요한 비활성화 파일을 차단해요.
```bash
sudo tee /etc/cloud/cloud.cfg.d/98-growpart-resizefs.cfg >/dev/null <<'EOF'
growpart:
  mode: auto
  devices: ['/']
  ignore_growroot_disabled: true
resize_rootfs: true
EOF

# 혹시 남아있을 비활성화 식별 태그 제거
sudo rm -f /etc/growroot-disabled
```

설정 파일의 무결성을 화면에 표시하여 육안 확인해요.
```bash
sudo cat /etc/cloud/cloud.cfg.d/98-growpart-resizefs.cfg
```

### 3.7 모듈 활성화 수준 확인 및 스키마 검증
/etc/cloud/cloud.cfg 내부에 해당 컴포넌트 모듈들이 적절히 할당되어 있는지 그랩하여 점검하고 스키마 문법 유효성을 최종 체크해요.
```bash
# 모듈 할당 체크
sudo grep -nE 'growpart|resizefs' /etc/cloud/cloud.cfg
```
*   **정상 출력 스냅샷**:
    ```text
    cloud_init_modules:
     - growpart
     - resizefs
    ```

*   **스키마 구조적 유효성 검증**:
    ```bash
    # 전체 시스템 환경 구성 검증
    sudo cloud-init schema --system

    # 방금 추가한 디스크 조절 스크립트만 정밀 유효성 스캔
    sudo cloud-init schema --config-file /etc/cloud/cloud.cfg.d/98-growpart-resizefs.cfg --annotate
    ```

### 3.8 필수 프로세스 활성화 등록
인프라의 주요 백그라운드 프로세스들을 부팅 시 구동되게 활성화 조치해요.
```bash
sudo systemctl enable --now cloud-init
sudo systemctl enable --now vmtoolsd
sudo systemctl enable --now NetworkManager
sudo systemctl enable --now sshd
```

---

## 4. 모니터링 에이전트(Node Exporter) 주입

인프라 통합 수집 시스템과의 지표 연동을 위해 **Node Exporter 1.7.0**을 사전 탑재시켜 주어요.
1.  가상 머신 내부로 `node_exporter-1.7.0.tar.gz` 바이너리를 파일 업로드해요.
2.  아래 순서로 수동 빌드를 기동하여 서비스 파일 등록까지 마치도록 설정해요.
    ```bash
    tar xvfz node_exporter-1.7.0.tar.gz
    cd node_exporter-1.7.0
    sudo ./install.sh
    ```
3.  서비스 상태와 메트릭 포트(9100) 리스닝 현황을 교차 검증해요.
    ```bash
    sudo systemctl status node_exporter.service
    
    # 로컬에서 메트릭 수집 가능 유무 점검
    curl http://localhost:9100/metrics | head -n 10
    ```

---

## 5. 네트워크 인터페이스 예측 가능 명칭 고정 (`eth0`)

vCenter 및 CMP에서 고정 IP를 할당할 때 인터페이스명이 유동적으로 흔들리지 않도록 `eth0`, `eth1` 등의 일관성 있는 이름 체계를 커널 파라미터 수준에서 하드 코딩해 주어요.

### 5.1 커널 파라미터 옵션 튜닝
`/etc/default/grub` 파일의 `GRUB_CMDLINE_LINUX` 지시어 마지막 줄 우측 끝에 아래 옵션을 공백 하나 뒤에 이어 붙여 수동 적용해요.
*   **추가 옵션**: `net.ifnames=0 biosdevname=0`

그 다음 커널 명령어 실행 툴인 `grubby`를 이용해 가동 중인 전체 부팅 환경 커널에 반영을 선언해요.
```bash
sudo grubby --update-kernel=ALL --args="net.ifnames=0 biosdevname=0"
```

### 5.2 Grub 환경 파일 재생성 (부팅 정보 동기화)
서버 부팅 유형(BIOS vs UEFI)에 맞춰 적절한 타겟 디렉토리에 빌드를 수행해요.
```bash
# BIOS 구동 환경인 경우
sudo grub2-mkconfig -o /boot/grub2/grub.cfg

# UEFI 구동 환경인 경우
sudo grub2-mkconfig -o /boot/efi/EFI/rocky/grub.cfg
```

### 5.3 변경 후 재부팅 확인
```bash
sudo reboot

# 재구동 후 디바이스 명칭 스냅샷 확인
ip addr show
```
> [!NOTE]
> 명령 결과에 `eth0`, `eth1` 형태의 예측 가능한 명칭이 매핑되어 출력되는 것을 눈으로 검증해야 해요.

---

## 6. 시스템 초기화 및 최종 템플릿 잠금 단계

배포 템플릿의 잔여 캐시 정보로 인해 중복 IP 할당, 호스트 고유 ID 오버랩 에러 등이 발생하는 참사를 막기 위한 **극도로 엄격한 청소 스크립트 절차**예요.

```bash
# 6.1 임시 임베디드 네트워크 바인딩 연결 파일의 원천 제거
sudo rm -f /etc/NetworkManager/system-connections/*.nmconnection
sudo rm -f /etc/netplan/*
sudo systemctl restart NetworkManager

# 6.2 cloud-init 로그, 로컬 machine-id 지문, 저널로그 청소
sudo cloud-init clean --logs --machine-id
sudo rm -rf /var/lib/cloud/*
sudo truncate -s 0 /etc/machine-id
sudo rm -f /var/lib/dbus/machine-id
sudo rm -f /etc/NetworkManager/system-connections/*.nmconnection
sudo journalctl --vacuum-time=0
sudo rm -rf /tmp/*

# 6.3 쉘 실행 이력 흔적 말소
history -c && history -w

# 6.4 가상 머신 즉각 종료
sudo poweroff
```

가상 머신이 파워오프 상태가 되면, vCenter 콘솔에서 해당 VM을 우클릭하고 **템플릿으로 변환**을 실행하면 최종적으로 패키징이 끝나요.

---

## 7. 템플릿 가동 후 자동 볼륨 증가 확인 디버깅 가이드

해당 템플릿으로 최종 프로비저닝된 신규 가상 머신을 켜고 디스크 1이 늘어난 하드웨어 크기를 인식했는지 확인해요.

```bash
# 1. cloud-init 구동 성공 대기
sudo cloud-init status --wait
sudo cloud-init status --long

# 2. 파일시스템 크기 비교 점검
lsblk -f
df -hT /
findmnt -no SOURCE,FSTYPE,SIZE,USED,AVAIL /

# 3. cloud-init 실행 로그 내 리사이저 동작 패턴 조사
sudo grep -Ei 'growpart|resizefs|resize_rootfs|growroot|NOCHANGE|FAILED|ERROR|WARN' \
  /var/log/cloud-init.log /var/log/cloud-init-output.log
```

### 🚨 트러블슈팅 대표 유형

#### Q. 디스크 크기는 확대되었는데 파티션(`/dev/sda5` 등) 용량이 이전 템플릿 수준에 머물러 있어요.
*   **원인 1**: `cloud-utils-growpart` 패키지가 템플릿 제작 단계에서 설치 누락된 경우예요.
    *   *조치*: `sudo dnf install -y cloud-utils-growpart` 실행 후 수동 리사이즈를 기동해 봐요.
        ```bash
        # sda의 5번 파티션 공간을 우선 확장
        sudo growpart /dev/sda 5
        # XFS 파일시스템을 파티션 크기에 맞춰 동기화
        sudo xfs_growfs /
        ```
*   **원인 2**: 확장하고자 하는 루트 파티션 뒤쪽에 다른 고정 파티션(예: Swap 파티션 등)이 달라붙어 있어, 디스크의 연속된 Free Space 공간 팽창을 막고 있는 경우예요.
    *   *확인*: `sudo parted /dev/sda unit MiB print free` 실행 시, `/dev/sda5` 바로 옆 뒤쪽 구간에 `Free Space` 영역이 표시되는지 대조해요. 만약 비연속 공간이라면 디스크 파티션 구조를 앞단으로 다시 조정하는 템플릿 재설계가 필요해요.
*   **원인 3**: 새 VM 배포 후 1회 구동(first boot) 인식이 되지 않아 작동이 멈춘 상태예요.
    *   *조치*: 템플릿 변환 종료 스크립트 실행 시 `cloud-init clean --logs --machine-id` 단계가 정상적으로 돌았는지 이력을 면밀히 되짚어봐요.
