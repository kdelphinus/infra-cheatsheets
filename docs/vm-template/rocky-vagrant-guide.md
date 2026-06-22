# VMware Rocky 9.6 템플릿 생성 가이드 v3.1

이 문서는 Rocky Linux 9.6 Vagrant VMware 이미지를 vCenter 템플릿으로 변환하고, 신규 VM 생성 시 cloud-init을 통해 네트워크 설정 및 LVM 기반 루트 디스크 자동 확장이 정상 적용되도록 구성하는 절차를 안내합니다.

---

## 📌 핵심 전제 사항

*   **네트워크 관리**: `NetworkManager`를 사용하여 네트워크 설정을 제어합니다.
*   **Datasource 허용**: VMware datasource로 `VMware` 및 `OVF`를 허용하도록 제한합니다.
*   **디스크 파티션 구조**: 루트 디스크 구조는 `/dev/sda3` LVM PV 위에 `/dev/mapper/rl-root`가 마운트된 구성을 기준으로 합니다.
*   **파티션 확장**: cloud-init `growpart` 모듈이 LVM PV 파티션(/dev/sda3) 확장을 담당합니다.
*   **LVM 확장 서비스**: `resize-lvm-root.service`를 구성하여 LVM PV/LV 및 `/` 파일시스템 확장을 담당합니다.
*   **첫 부팅(First Boot) 보장**: 템플릿 변환 직전에 `cloud-init clean --logs --machine-id` 명령과 machine-id 초기화를 수행하여 새 VM이 최초 부팅 상태로 정상 인식되도록 합니다.
*   **네트워크 잔재 정리**: 템플릿 생성 과정에서 생성된 NetworkManager connection 정보를 삭제하여, 새 VM이 템플릿 VM의 IP 설정을 그대로 물고 올라오는 문제를 방지합니다.

---

## 1. OVF 이미지 준비 및 변환

### 1.1 이미지 다운로드
인터넷이 가능한 환경에서 Rocky Linux 아카이브 스토리지로부터 VMware 가상화용 최신 Box를 다운로드합니다.
*   **다운로드 경로**: [Rocky Linux Vault - x86_64 이미지](https://dl.rockylinux.org/vault/rocky/9.6/images/x86_64/)
*   **대상 파일**: `Rocky-9-Vagrant-VMware.latest.x86_64.box`

### 1.2 압축 해제
Vagrant Box는 tar 압축 파일 형식을 취하고 있습니다. 확장자를 변경하여 내부에 포함된 가상 머신 구성 파일(`.vmx`)을 추출합니다.
```bash
mv Rocky-9-Vagrant-VMware.latest.x86_64.box Rocky-9-Vagrant-VMware.latest.x86_64.tar.gz
tar xvf Rocky-9-Vagrant-VMware.latest.x86_64.tar.gz
ls -al *.vmx
```

### 1.3 변환 도구 설치
vmx 파일을 vCenter 업로드에 필요한 OVF 형식으로 변환하기 위해 Broadcom 개발자 사이트에서 **`ovftool`**을 다운로드하여 설치합니다.
*   **도구 획득 경로**: [Broadcom OVF Tool 다운로드 링크](https://developer.broadcom.com/tools/open-virtualization-format-ovf-tool/latest)

### 1.4 OVF 변환
터미널에서 아래 명령을 실행하여 vmx 구성 파일을 ovf 파일로 변환합니다.
```bash
ovftool "Rocky-9-Vagrant-VMware-9.6-20250531.0.x86_64.vmx" "Rocky-9-Template.ovf"
```

---

## 2. vCenter 업로드 및 하드웨어 설정

### 2.1 템플릿 업로드
vCenter 관리 콘솔에서 **OVF 템플릿 배포** 기능을 사용하여 생성된 `Rocky-9-Template.ovf` 파일을 업로드합니다.

### 2.2 설정 편집
운영 기준 및 용도에 맞게 하드웨어 가상화 스펙을 조정합니다.
1.  **네트워크 어댑터**: 추가 후 어댑터 유형을 고성능 드라이버 방식인 **`VMXNET3`**으로 변경합니다.
2.  **부팅 옵션**: 가상 펌웨어 부팅 옵션을 **`BIOS`**로 변경합니다.
3.  **CPU, 메모리, 디스크**: 타겟 운영 기준에 맞게 조정합니다.

> [!WARNING]
> **루트 디스크 파티션 위치 주의**
> 디스크 자동 확장은 확장 대상 루트 PV 파티션이 대상 디스크의 **마지막 파티션(연속된 디스크 공간 바로 앞)**에 위치해야 안정적으로 동작합니다.

이 가이드는 아래의 디스크 레이아웃 구조를 기준으로 설명합니다.
```text
/dev/sda
├─ sda1 /boot/efi
├─ sda2 /boot
└─ sda3 LVM PV
 ├─ /dev/mapper/rl-root /
 └─ /dev/mapper/rl-swap swap
```

---

## 3. VM 전원 켜기 및 기본 접속

가상 머신의 전원을 켜고 기본 Vagrant 계정을 사용하여 로그인합니다.
*   **사용자**: `vagrant`
*   **비밀번호**: `vagrant`

구동 직후 필수 서비스들의 가동 상태를 확인합니다.
```bash
systemctl status cloud-init
systemctl status vmtoolsd
```
*서비스가 설치되어 있지 않거나 비활성화되어 있더라도 아래 필수 패키지 설치 및 활성화 단계에서 정리되므로 계속 진행합니다.*

---

## 4. 임시 네트워크 설정

필수 패키지 다운로드를 위해 외부 인터넷 접속 또는 내부 RPM 미러 저장소 접근이 가능한 임시 네트워크를 nmcli 명령어로 구성합니다.
```bash
sudo nmcli connection show

# 연결 이름이 "Wired connection 1"인 경우 IP/Gateway/DNS 수동 지정 예시
sudo nmcli connection modify "Wired connection 1" \
  ipv4.addresses x.x.x.x/x \
  ipv4.gateway x.x.x.x \
  ipv4.dns x.x.x.x \
  ipv4.method manual

sudo nmcli connection up "Wired connection 1"
```

인터넷 또는 내부망 접근성을 검증합니다.
```bash
ping -c 3 8.8.8.8
ping -c 3 dl.rockylinux.org

# 폐쇄망 환경에서 내부 저장소만 사용하는 경우 아래 명령으로 확인
dnf repolist
```

---

## 5. 필수 패키지 설치

VMware 템플릿 기동, cloud-init 통합 및 LVM 루트 확장에 필요한 핵심 패키지들을 설치합니다.
```bash
sudo dnf install -y \
  cloud-init \
  cloud-utils-growpart \
  open-vm-tools \
  NetworkManager \
  openssh-server \
  xfsprogs \
  lvm2
```

### 패키지 역할 요약
*   **`cloud-init`**: VM 최초 부팅 시 user-data, network-config, disk resize 설정을 자동 반영합니다.
*   **`cloud-utils-growpart`**: 디스크 크기 증가 시 해당 파티션을 확장하는 `growpart` 도구를 제공합니다.
*   **`open-vm-tools`**: VMware guest integration 및 OS Customization을 원활하게 지원합니다.
*   **`NetworkManager`**: cloud-init 네트워크 설정을 파싱 및 렌더링하는 대상입니다.
*   **`openssh-server`**: 배포 후 원격 SSH 접속을 지원합니다.
*   **`xfsprogs`**: XFS 파일시스템 온라인 확장 도구(`xfs_growfs`)를 제공합니다.
*   **`lvm2`**: LVM 볼륨 그룹(VG) 및 논리 볼륨(LV) 제어 도구를 제공합니다.

설치 완료 후 필수 명령어 파일들의 확보 상태를 교차 검사합니다.
```bash
rpm -q cloud-init cloud-utils-growpart open-vm-tools NetworkManager openssh-server xfsprogs lvm2
command -v growpart
command -v pvresize
command -v lvextend
command -v xfs_growfs
```
*`cloud-utils-growpart`가 유실된 경우 cloud-init 로그에 `growpart unable to find resizer for 'auto': No resizers available` 오류가 발생하며 디스크 파티션 확장이 실패하게 됩니다.*

---

## 6. 디스크 구조 확인

현재 Rocky 템플릿의 디스크 파티션 레이아웃 상태를 파악합니다.
```bash
lsblk
df -hT /
sudo pvs
sudo vgs
sudo lvs
sudo parted /dev/sda unit MiB print free
```

### 정상 디스크 조건 기준
1.  `/dev/sda3` (또는 실제 대상 파티션)가 LVM PV로 잡혀 있어야 합니다.
2.  `/dev/mapper/rl-root` 논리 볼륨이 `/` 경로에 마운트되어 있어야 합니다.
3.  루트 LVM PV 파티션이 대상 디스크 `/dev/sda`의 **가장 마지막 물리 파티션**이어야 합니다.
4.  새 VM 배포 시 가상 디스크 크기를 키웠을 때, LVM PV 파티션 바로 뒤쪽에 `Free Space` 연속 공간이 유입될 수 있는 파티션 구조여야 합니다.

---

## 7. cloud-init NetworkManager renderer 지정

cloud-init이 감지한 네트워크 설정 구성을 시스템의 NetworkManager 형식으로 렌더링하도록 드롭인 설정 파일을 작성합니다.
```bash
sudo tee /etc/cloud/cloud.cfg.d/99-network-renderer.cfg >/dev/null <<'EOF'
system_info:
  network:
    renderers: ['network-manager']
EOF
```

---

## 8. VMware datasource 설정

VMware Guest OS Customization 또는 vCenter GuestInfo 인터페이스를 통해 전달받는 cloud-init 데이터를 처리할 수 있도록 datasource 목록을 구성합니다.
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

---

## 9. cloud-init growpart 설정

LVM 구조에서는 cloud-init이 `/` 파일시스템 자체를 곧바로 리사이즈할 수 없습니다. 따라서 LVM PV가 올라간 하부의 물리 파티션인 `/dev/sda3`를 1차적으로 팽창시키도록 드롭인 파일에 타겟 디바이스를 명시합니다.

!!! warning "루트 파티션 장치명 확인 및 가변 대응 필수"
    본 표준 가이드는 `/dev/sda3`가 LVM PV 파티션인 구성을 기본 모델로 작성되었습니다. 하지만 배포 환경에 따라 루트 PV 파티션 명칭이 `sda3`가 아닌 `sda4` 또는 `sdb1` 등 다를 수 있습니다.
    
    반드시 `sudo parted /dev/sda unit MiB print free` 명령어로 **본인 환경의 루트 LVM PV 물리 파티션 번호(예: sda3, sda4 등)를 직접 검증**하신 뒤, 아래 설정 파일의 `devices: ['/dev/sda3']` 설정값과 이후 단계의 리사이즈 쉘 스크립트 내부 파티션 경로를 환경에 맞춰 변경하십시오.

```bash
sudo tee /etc/cloud/cloud.cfg.d/98-growpart-resizefs.cfg >/dev/null <<'EOF'
growpart:
  mode: auto
  devices: ['/dev/sda3']
  ignore_growroot_disabled: true
resize_rootfs: true
EOF
```

혹시 기존 이미지에 growroot 비활성화 태그 파일이 남아있을 경우 수동 제거합니다.
```bash
sudo rm -f /etc/growroot-disabled
```

작성된 드롭인 설정을 확인합니다.
```bash
sudo cat /etc/cloud/cloud.cfg.d/98-growpart-resizefs.cfg
```

> **참고**: 이전 버전 안내서에서는 `devices: ['/']` 형식으로 마운트 루트 기준 확장을 진행했습니다. LVM을 거치지 않는 일반 단일 파티션 루트 구성이라면 해당 방식으로 충분하지만, `/` 경로가 LVM Logical Volume인 가이드 기준 환경에서는 **물리 파티션 확장(growpart)** 단계와 **LVM 확장** 단계를 완전히 분리하여 수동 조치하는 편이 훨씬 명확하고 확실합니다.

---

## 10. LVM 루트 확장 스크립트 추가

물리 파티션 팽창 직후 LVM의 물리 볼륨(PV)을 감지하고, 볼륨 그룹(VG) 및 논리 볼륨(LV)을 최대로 늘려 XFS 파일시스템 용량까지 일괄적으로 팽창시켜 주는 확장 자동화 스크립트를 작성합니다.

```bash
sudo tee /usr/local/sbin/resize-lvm-root.sh >/dev/null <<'EOF'
#!/bin/bash
set -euo pipefail

# 1. 대상 물리 파티션(sda 3)을 잔여 디스크 크기만큼 확장 (실제 디스크 환경에 맞게 파티션 번호 조정 필수)
growpart /dev/sda 3 || true

# 2. LVM 물리 볼륨 크기 정보 갱신
pvresize /dev/sda3

# 3. / 경로가 올라간 논리 볼륨을 잔여 VG 공간의 100%만큼 늘리고 파일시스템 온라인 확장(-r) 실행
lvextend -r -l +100%FREE /dev/mapper/rl-root || true

# 4. 실행 완료 상태 보존 파일 생성
touch /var/lib/resize-lvm-root.done
EOF

sudo chmod 0755 /usr/local/sbin/resize-lvm-root.sh
```

### 실행 프로세스 흐름
`/dev/sda` 가상 디스크 용량 증가
➡️ `growpart /dev/sda 3` 실행으로 물리 파티션 증가
➡️ `pvresize /dev/sda3` 실행으로 LVM PV 공간 팽창
➡️ `lvextend -r -l +100%FREE /dev/mapper/rl-root` 실행으로 LV 팽창 및 `/` 파일시스템 크기 동기화 완료
➡️ 완료 플래그 파일(`/var/lib/resize-lvm-root.done`) 생성

---

## 11. 첫 부팅용 systemd 서비스 추가

새로운 가상 머신 배포 시 최초 1회(First Boot)만 상기 LVM 리사이즈 스크립트가 호출되도록 systemd 일시 가동(oneshot) 서비스 유닛 파일을 등록합니다.

```bash
sudo tee /etc/systemd/system/resize-lvm-root.service >/dev/null <<'EOF'
[Unit]
Description=Resize LVM root filesystem on first boot
After=local-fs.target
ConditionPathExists=!/var/lib/resize-lvm-root.done

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/resize-lvm-root.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
```

systemd 데몬을 재로드하고 작성한 리사이즈 서비스를 부팅 기본 동작으로 활성화합니다.
```bash
sudo systemctl daemon-reload
sudo systemctl enable resize-lvm-root.service
```

> ⚠️ **주의 사항**:
> 서비스 실행 순서 지정 시 `After=cloud-init.target` 이나 `Wants=cloud-init.target` 같은 cloud-init에 대한 직접적인 종속성을 강제 지정하지 마십시오. 실제 부팅 파이프라인에서 예기치 못한 순환 참조 교착 상태(ordering cycle)가 발생하여 서비스 기동이 정지될 수 있으므로, 단순하고 명확하게 `After=local-fs.target` 시점에 돌도록 고정합니다.

---

## 12. 이전 버전 runcmd 설정 정리

이전 빌드 절차에서 사용했던 cloud-init 내부 `runcmd` 기반의 LVM 루트 디스크 리사이즈 드롭인 파일이 남아 있을 경우, 중복 호출 및 충돌 방지를 위해 사전에 깔끔히 삭제합니다.
```bash
sudo rm -f /etc/cloud/cloud.cfg.d/99-lvm-root-resize.cfg
```

---

## 13. cloud-init 모듈 및 설정 검증

`/etc/cloud/cloud.cfg` 기본 본체 파일 안에 `growpart`와 `resizefs` 모듈 키워드가 정상 등록되어 작동 가능한지 그랩하여 체크합니다.
```bash
sudo grep -nE 'growpart|resizefs' /etc/cloud/cloud.cfg
```

### 정상 출력 스냅샷 예시
```text
cloud_init_modules:
 - growpart
 - resizefs
```

추가한 드롭인 설정의 문법 및 YAML 포맷 유효성에 대해 cloud-init 스키마 검증 도구로 무결성을 스캔합니다.
```bash
sudo cloud-init schema --system
sudo cloud-init schema --config-file /etc/cloud/cloud.cfg.d/98-growpart-resizefs.cfg --annotate
```
*`cloud-init schema --system`은 현재 가상 머신의 로컬에 보관된 user-data 및 network-config 등을 참조하여 분석합니다.*

---

## 14. 필수 서비스 최종 활성화

부팅 시 기동되어야 하는 코어 데몬 및 가상화 관리 툴들을 모두 활성화하고 동작 상태를 확인합니다.
```bash
sudo systemctl enable --now cloud-init
sudo systemctl enable --now vmtoolsd
sudo systemctl enable --now NetworkManager
sudo systemctl enable --now sshd

systemctl status cloud-init vmtoolsd NetworkManager sshd --no-pager
```

---

## 15. 모니터링 에이전트 (Node Exporter) 설치

통합 성능 지표 모니터링 관리를 위해 대상 템플릿에 **Node Exporter**를 탑재합니다.

1.  대상 장비에 SSH 접속 후 `node_exporter-1.7.0.tar.gz` 설치 자산을 업로드합니다.
2.  압축을 풀고 패키지에 동봉된 자동 설치 스크립트를 관리자 권한으로 가동합니다.
    ```bash
    tar xvfz node_exporter-1.7.0.tar.gz
    cd node_exporter-1.7.0
    sudo ./install.sh
    ```
3.  설치 스크립트가 systemd 유닛 파일 등록 및 서비스 구동까지 마쳤는지 최종적으로 검사합니다.
    ```bash
    sudo systemctl status node_exporter.service
    ```
4.  로컬 포트 포워딩 또는 curl 조회를 통해 9100 메트릭 노출 포트 응답을 확인합니다.
    ```bash
    curl http://localhost:9100/metrics | head -n 10
    ```

---

## 16. 네트워크 인터페이스 명칭 고정

vCenter 게스트 커스터마이제이션 및 CMP 솔루션에서 대상 VM으로 예측 가능한 IP 주입 제어를 수행할 수 있도록, 디바이스 명칭을 `eth0`, `eth1` 등의 순차적 고정 규칙으로 강제 매핑합니다.

### 16.1 grub 커널 부팅 명령행 파라미터 튜닝
`/etc/default/grub` 파일의 `GRUB_CMDLINE_LINUX` 지시어 마지막 우측 끝부분에 `net.ifnames=0 biosdevname=0` 파라미터를 추가하여 수동 기입합니다. (기존 설정값이 있다면 지우지 말고 맨 뒤에 스페이스 공백으로 이어서 기입합니다.)

설정에 맞춰 `grubby` 도구를 가동해 실행 커널 설정에 한 번 더 주입합니다.
```bash
sudo grubby --update-kernel=ALL --args="net.ifnames=0 biosdevname=0"
```

### 16.2 GRUB 환경 부팅 설정 파일 재빌드
가상 머신의 부팅 모드 방식(BIOS vs UEFI)을 점검한 뒤 알맞은 타겟 위치로 GRUB 설정을 컴파일 빌드합니다.

*   **BIOS(Legacy) 부팅 방식인 경우:**
    ```bash
    sudo grub2-mkconfig -o /boot/grub2/grub.cfg
    ```
*   **UEFI 부팅 방식인 경우:**
    ```bash
    sudo grub2-mkconfig -o /boot/efi/EFI/rocky/grub.cfg
    ```

변경 사항 조치를 위해 가상 머신을 1회 재부팅합니다.
```bash
sudo reboot
```

재기동이 완료된 후, 물리 어댑터 명칭이 예측한 규칙대로 매핑되었는지 질의합니다.
```bash
ip addr show
```
*출력 결과에 `eth0` 등의 장치가 정상적으로 표시되는지 파악합니다.*

---

## 17. 템플릿 변환 전 최종 점검

가상 머신 템플릿 락을 걸기 전 디바이스, 설정, 리사이즈 서비스 가동 상태를 교차 체킹합니다.

```bash
# 1. 필수 패키지 및 명령어 파일 확인
rpm -q cloud-init cloud-utils-growpart open-vm-tools NetworkManager openssh-server xfsprogs lvm2
command -v growpart && command -v pvresize && command -v lvextend && command -v xfs_growfs

# 2. cloud-init 렌더러 및 datasource 설정 스캔
sudo grep -RniE 'datasource_list|VMware|growpart|resize_rootfs|network-manager' \
  /etc/cloud/cloud.cfg /etc/cloud/cloud.cfg.d

# 3. LVM 리사이즈 서비스 정상 등록 상태 점검
sudo systemctl is-enabled resize-lvm-root.service
sudo ls -l /usr/local/sbin/resize-lvm-root.sh
sudo find /etc/systemd/system -lname '*resize-lvm-root.service' -ls
```

### 템플릿 변환 완료 기준
*   `resize-lvm-root.service`의 상태가 `enabled` 여야 합니다.
*   `multi-user.target.wants` 경로 하위에 심볼릭 링크가 존재해야 합니다.
*   `/usr/local/sbin/resize-lvm-root.sh` 파일에 실행 권한(`0755`)이 주어져 있어야 합니다.
*   **[중요]** 테스트 중 생성되었을 수 있는 완료 태그 플래그 파일인 `/var/lib/resize-lvm-root.done`가 **존재하지 않는 깨끗한 상태**여야 합니다. (태그 파일이 있으면 실제 배포 후 첫 부팅 시 리사이즈 스크립트 실행이 생략됩니다.)

```bash
# 혹시 테스트로 인해 임시 생성된 done 파일이 있다면 원천 삭제
sudo rm -f /var/lib/resize-lvm-root.done
```

---

## 18. nmcli connection 정리

가상 머신 내부에 네트워크 매핑 흔적(`UUID` 및 고정 IP 정보 등)이 커넥션 프로파일에 남아있으면, 배포 후 새 VM이 템플릿 VM의 네트워크 정보와 충돌하거나 꼬이는 원인이 됩니다. 따라서 변환 직전 NM 관리 프로파일들을 모조리 정리 소거합니다.

```bash
# 1. 현재 매핑된 NM 연결 프로파일 확인
sudo nmcli connection show

# 2. 확인된 기존 접속 프로파일 일괄 제거 (대상 명칭에 맞춰 순차적 삭제)
sudo nmcli connection delete "cloud-init eth0" 2>/dev/null
sudo nmcli connection delete "System eth0" 2>/dev/null
sudo nmcli connection delete "System ens34" 2>/dev/null
sudo nmcli connection delete "1" 2>/dev/null
sudo nmcli connection delete "temp-eth1" 2>/dev/null
sudo nmcli connection delete "Wired connection 1" 2>/dev/null

# 3. 물리적인 NetworkManager 연결 설정 구성 프로파일 파일들까지 확실하게 영구 소거
sudo rm -f /etc/NetworkManager/system-connections/*.nmconnection
sudo rm -f /run/NetworkManager/system-connections/*.nmconnection

# 4. 서비스 재기동을 통한 메모리 상태 초기화
sudo systemctl restart NetworkManager
```

---

## 19. 템플릿 초기화 및 종료

새 VM 배포 시 cloud-init이 오차 없이 완전한 최초 구동 단계로 인식하여 metadata/network-config 초기 동작을 보장받도록, 시스템 사용 흔적과 캐시, 고유 머신 식별자(machine-id) 정보를 완전하게 말소한 뒤 즉각 종료를 수행합니다.

```bash
# 1. 최종 디스크 리사이즈 스크립트 실행 태그 파일 확인 및 소거
sudo rm -f /var/lib/resize-lvm-root.done

# 2. cloud-init 캐시 로그 지우고 머신 고유 ID 초기화 트리거 실행
sudo cloud-init clean --logs --machine-id

# 3. 로컬 cloud 라이브러리 캐싱 데이터 지우기
sudo rm -rf /var/lib/cloud/*

# 4. machine-id 내용물 비우기 (파일 자체는 존재하나 크기는 0으로 유지)
sudo truncate -s 0 /etc/machine-id
sudo rm -f /var/lib/dbus/machine-id

# 5. 마지막 한 번 더 잔여 네트워크 커넥션 프로파일 소거 확인
sudo rm -f /etc/NetworkManager/system-connections/*.nmconnection

# 6. 시스템 저널 로그 및 임시 temp 영역 청소
sudo journalctl --vacuum-time=0
sudo rm -rf /tmp/*

# 7. 본 초기화 세션의 쉘 실행 흔적 말소 후 전원 오프
history -c
history -w
sudo poweroff
```

가상 머신의 전원이 완전히 꺼지면, vCenter 웹 콘솔로 이동하여 해당 VM 항목을 우클릭하고 **`템플릿 -> 템플릿으로 변환(Convert to Template)`**을 적용하여 패키지 포맷 락을 완료합니다.

---

## 20. 새 VM 배포 후 동작 검증

본 템플릿을 소스로 삼아 신규 가상 머신을 프로비저닝할 때, **가상 디스크 1 용량을 기본 이미지 크기보다 더 큰 크기(예: 110G 또는 120G)로 임의 지정하여 생성**합니다.

부팅이 시작되면 cloud-init이 프로비저닝 완료 상태가 될 때까지 쉘 프롬프트 대기 명령어로 관찰합니다.
```bash
sudo cloud-init status --wait
sudo cloud-init status --long
```

가이드 프로세스에 따라 디스크 파티션, LVM, 물리 및 논리 볼륨 그룹 및 파일시스템 크기가 정상 증설 완료되었는지 최종 진단합니다.
```bash
# 1. 마운트 및 물리 디바이스 용량 팽창 검사
lsblk
df -hT /
findmnt -no SOURCE,FSTYPE,SIZE,USED,AVAIL /
sudo pvs
sudo vgs
sudo lvs

# 2. 신설한 리사이즈 systemd 서비스 가동 로그 검사
sudo systemctl status resize-lvm-root.service --no-pager
sudo journalctl -u resize-lvm-root.service -b --no-pager

# 3. growpart 및 파일시스템 리사이저 내부 구동 패턴 로그 정밀 점검
sudo grep -Ei 'growpart|resizefs|resize_rootfs|growroot|NOCHANGE|FAILED|ERROR|WARN' \
  /var/log/cloud-init.log /var/log/cloud-init-output.log
```

### 정상 실행 흐름 시나리오 확인
가상 디스크 sda 용량 확장 감색 감지
➡️ sda3 (또는 설정 타겟 파티션) 파티션 영역 확장
➡️ LVM 물리 볼륨 영역 확장 (`pvresize /dev/sda3`)
➡️ 논리 볼륨 및 파일시스템 확장 (`lvextend -r -l +100%FREE /dev/mapper/rl-root`)
➡️ `/var/lib/resize-lvm-root.done` 플래그 파일 자동 생성 완료 확인

---

## 21. 문제 해결 (Troubleshooting)

### 21.1 디스크 1 공간은 늘어났으나 / 경로 마운트 용량이 이전 크기 그대로인 경우
먼저 물리 디스크 가상 장치 뒤쪽에 Free Space 영역이 확보되어 들어와 있는지 확인합니다.
```bash
sudo parted /dev/sda unit MiB print free
```

`/dev/sda3` (루트 LVM PV) 뒤에 Free Space 여유 공간이 잡혀있는데도 LVM 볼륨 확장이 멈춰 있다면, 아래 필수 도구 명령어가 시스템 내부에 누락되었는지 다시 체크하십시오.
```bash
rpm -q cloud-utils-growpart lvm2 xfsprogs
command -v growpart && command -v pvresize && command -v lvextend && command -v xfs_growfs
```

누락 사항을 확인한 후, 가동 중인 새 VM 상태에서 아래 수동 리사이즈 파이프라인 명령을 순차 실행하여 정상 복구시킵니다.
```bash
# 1. 물리 파티션 공간 팽창
sudo growpart /dev/sda 3

# 2. PV 정보 갱신
sudo pvresize /dev/sda3

# 3. LV 및 XFS 파일시스템 갱신
sudo lvextend -r -l +100%FREE /dev/mapper/rl-root

# 4. 검증
lsblk && df -hT / && sudo pvs && sudo vgs && sudo lvs
```

### 21.2 growpart unable to find resizer for 'auto': No resizers available 오류 발생 시
해당 오류는 파티션을 강제 조절해 주는 핵심 쉘 유틸리티가 빌드 시 유실되었을 때 발생합니다. DNF 도구를 가동해 해당 팩을 주입하십시오.
```bash
sudo dnf install -y cloud-utils-growpart
```

### 21.3 새 VM 기동 시 cloud-init이 동작하지 않는 경우
템플릿 변환 직전 단계에서 machine-id 청소 및 cloud-init 캐시 리셋 명령어를 정상 실행하지 않아 이미 부팅이 한 차례 이루어진 장비라고 게스트 OS가 인지했기 때문일 가능성이 큽니다.
```bash
# 템플릿 변환 직전 machine-id 및 cloud-init 캐시를 강제 리셋했는지 검사하십시오.
sudo cloud-init clean --logs --machine-id
sudo rm -rf /var/lib/cloud/*
sudo truncate -s 0 /etc/machine-id
sudo rm -f /var/lib/dbus/machine-id
```

### 21.4 루트 PV 파티션이 디스크의 마지막 파티션 영역이 아닌 경우
`growpart`는 볼륨 팽창 대상 파티션 **바로 뒷단**에 어떠한 방해 물리 파티션도 없이 물리적 연속 Free Space 공간이 달라붙어 있어야 안전하게 늘어납니다.
```bash
sudo parted /dev/sda unit MiB print free
```
만약 확장하고자 하는 루트 LVM PV 파티션 뒤에 Swap 파티션 등 다른 구조적 파티션이 꼬리를 물고 있다면 파티션 확장이 불가하므로, 템플릿 VM의 물리 디바이스 파티션 구조를 앞단으로 다시 조정하거나 Swap 볼륨을 lvm 볼륨 안으로 이관하는 템플릿 재구성 작업이 수반되어야 합니다.

### 21.5 새로 배포한 VM이 템플릿용 VM의 IP 주소를 그대로 가져가는 경우
템플릿화 잠금 직전 단계에서 NetworkManager connection 정보와 잔존 `nmconnection` 파일들을 완벽히 삭제하지 못해 캐싱 프로파일이 상속되어 기동되었을 가능성이 큽니다.
```bash
sudo nmcli connection show
sudo ls -al /etc/NetworkManager/system-connections/
sudo ls -al /run/NetworkManager/system-connections/
```
남아있는 프로파일 정보가 식별될 시 이를 제거하고, `cloud-init clean` 리셋 후 전원을 끄고 템플릿 락을 다시 거는 절차를 반복합니다.

---

## 22. 핵심 요약 결론

1.  **`cloud-init growpart`** ➡️ 물리 파티션 영역 확장 수행 (LVM PV 파티션 `/dev/sda3` 타겟팅)
2.  **`resize-lvm-root.service`** ➡️ LVM 물리 볼륨, 볼륨 그룹, 논리 볼륨 및 XFS 파일시스템 확장 수행
3.  **`nmcli connection 삭제`** ➡️ 템플릿 네트워크 바인딩 흔적 소거로 IP 꼬임 및 충돌 방지
4.  **`cloud-init clean + machine-id 초기화`** ➡️ 배포 시 신규 VM이 오차 없이 최초 부팅 상태로 진입하도록 보장

---

## 23. 참고 문서 및 정보 링크

*   **cloud-init growpart 모듈**: [growpart 모듈 공식 사양](https://docs.cloud-init.io/en/latest/reference/modules.html#growpart)
*   **cloud-init resizefs 모듈**: [resizefs 모듈 공식 사양](https://docs.cloud-init.io/en/latest/reference/modules.html#resizefs)
*   **cloud-init 파티션 및 파일시스템 확장 구성 예시**: [disk_setup 팽창 템플릿 가이드](https://cloudinit.readthedocs.io/en/stable/reference/yaml_examples/disk_setup.html#resize-partitions-and-filesystems)
*   **cloud-init VMware datasource 레퍼런스**: [VMware datasource 상세 명세](https://docs.cloud-init.io/en/latest/reference/datasources/vmware.html)
