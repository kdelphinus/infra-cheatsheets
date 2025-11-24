# 🖥️ GPU Passthrough를 위한 OS 사전 설정 가이드

이 가이드는 OpenStack Compute 노드에서 GPU를 가상 머신(VM)에 직접 할당(Passthrough)하기 위해 필요한 **커널 및 드라이버 설정** 절차입니다.

## 📝 변수 정의 (치환 필요)

- `<VENDOR_ID>` : GPU 제조사 ID (예: NVIDIA의 경우 `10de`)
- `<PRODUCT_ID>` : GPU 모델 ID (예: `20b7`)

-----

## 1단계: IOMMU 활성화 (Grub 설정)

CPU의 가상화 기능을 활성화하고, 호스트 OS가 GPU를 점유하지 않도록 설정합니다.

### 1. 설정 파일 수정 (공통)

`/etc/default/grub` 파일을 열어 `GRUB_CMDLINE_LINUX` 라인을 수정합니다.

```bash
# 인텔 CPU 기준 설정 (AMD의 경우 intel_iommu 대신 amd_iommu=on 사용)
# 기존 라인 뒤에 아래 옵션들을 추가합니다.
# nouveau, nvidia 드라이버가 로드되지 않도록 blacklist 처리합니다.
GRUB_CMDLINE_LINUX="... intel_iommu=on iommu=pt modprobe.blacklist=nouveau,nvidia,nvidia_drm"
```

### 2. Grub 적용 및 재부팅 (OS별 선택)

**🅰️ Ubuntu 22.04:**

```bash
sudo update-grub
sudo reboot
```

**🅱️ Rocky Linux:**

```bash
# BIOS 모드일 경우
sudo grub2-mkconfig -o /boot/grub2/grub.cfg
# UEFI 모드일 경우 (대부분의 최신 서버)
sudo grub2-mkconfig -o /boot/efi/EFI/rocky/grub.cfg

sudo reboot
```

### 3. IOMMU 활성화 확인

재부팅 후 설정이 적용되었는지 확인합니다.

```bash
cat /proc/cmdline
# 출력 결과에 intel_iommu=on 등이 포함되어 있어야 함
```

-----

## 2단계: GPU 장치 ID 확인 및 변수 확보

시스템에 장착된 GPU의 PCI ID를 식별합니다.

```bash
# NVIDIA GPU 검색 예시
lspci -nn | grep -i NVIDIA
```

**출력 예시:**
`03:00.0 3D controller [0302]: NVIDIA Corporation ... [10de:20b7] ...`

- 위 예시에서 `<VENDOR_ID>`는 `10de`, `<PRODUCT_ID>`는 `20b7`입니다.

-----

## 3단계: VFIO 모듈 로드 설정

GPU를 호스트 OS 대신 VM이 사용할 수 있도록 VFIO 드라이버를 로드합니다.

### 1. 수동 로드 (테스트용)

```bash
sudo modprobe vfio
sudo modprobe vfio_iommu_type1
sudo modprobe vfio-pci
```

### 2. 영구 적용 설정 (OS별 선택)

부팅 시 자동으로 모듈이 로드되도록 설정합니다.

**🅰️ Ubuntu 22.04:**

```bash
# /etc/modules 파일 편집
sudo vi /etc/modules

# 아래 내용 추가
vfio
vfio_iommu_type1
vfio_pci
```

**🅱️ Rocky Linux:**

```bash
# /etc/modules-load.d/vfio.conf 파일 생성
sudo vi /etc/modules-load.d/vfio.conf

# 아래 내용 추가
vfio
vfio_iommu_type1
vfio-pci
```

-----

## 4단계: GPU 장치 바인딩 (Driver Binding)

식별한 GPU ID를 VFIO 드라이버에 바인딩하여 호스트가 사용하지 못하게 합니다.

### 1. 바인딩 설정 파일 생성 (공통)

```bash
# /etc/modprobe.d/vfio.conf 파일 생성 또는 수정
sudo vi /etc/modprobe.d/vfio.conf

# 아래 내용 추가 (변수 치환 필요)
options vfio-pci ids=<VENDOR_ID>:<PRODUCT_ID>
```

### 2. 램디스크(Ramdisk) 업데이트 및 재부팅 (OS별 선택)

설정 내용을 초기 부팅 이미지에 반영합니다.

**🅰️ Ubuntu 22.04:**

```bash
sudo update-initramfs -u
sudo reboot
```

**🅱️ Rocky Linux:**

```bash
sudo dracut -f
sudo reboot
```

-----

## 5단계: 최종 검증

재부팅 후 GPU가 `vfio-pci` 드라이버를 사용 중인지 확인합니다.

### 1. 드라이버 확인

```bash
# Kernel driver in use가 vfio-pci로 되어 있어야 성공
lspci -nnk -d <VENDOR_ID>:<PRODUCT_ID>
```

### 2. (트러블슈팅) 바인딩이 안 된 경우 강제 적용

만약 위 단계 후에도 드라이버가 잡히지 않는다면 아래 명령어로 강제 바인딩을 시도합니다.

```bash
echo "<VENDOR_ID> <PRODUCT_ID>" | sudo tee /sys/bus/pci/drivers/vfio-pci/new_id
```

이후 다시 `lspci -nnk` 명령어로 확인합니다.

-----

### 💡 DevOps 엔지니어의 다음 단계

이제 OS 레벨의 준비는 모두 끝났습니다. 다음 단계는 OpenStack 설정 파일(`nova.conf` 등)을 수정하여 이 GPU를 Compute 서비스에 등록하는 것입니다.
