# Kubernetes 오프라인 빌더 (k8s-offline-builder) 사용 가이드

이 문서는 Kubernetes 오프라인 설치 번들을 동적으로 생성하기 위한 빌더 도구의 사용 절차를 다룹니다.

---

## 1. 전제 조건

- 온라인 Ubuntu 24.04 또는 Rocky Linux 9.6 호스트
- `root` 또는 `sudo` 권한
- 외부 인터넷 접근 가능
- `curl`, `tar`, `bash`, `apt-get` 사용 가능

> [!NOTE]
> Rocky/RHEL 계열은 현재 `rocky9.6`을 1차 검증 대상으로 지원합니다.

---

## 2. 설정 파일 구성

빌더의 수집 및 릴리스 설정은 `install.conf` 파일에 저장하여 관리합니다.

```bash
cd k8s-offline-builder
vi install.conf
```

### 주요 설정 매개변수 정책

| 항목 | 설명 |
| --- | --- |
| `K8S_VERSION` | 생성할 Kubernetes patch 버전 (예: `v1.33.11`) |
| `TARGET_OS` | 대상 OS 식별자 (`ubuntu24.04` 또는 `rocky9.6` 등) |
| `CONTAINER_RUNTIME` | 컨테이너 런타임 (현재 `containerd` 고정) |
| `CONTAINERD_VERSION` | containerd 버전 정책. Ubuntu/Rocky는 `auto` 입력 시 `2.1.*` 라인으로 자동 정규화 |
| `CNI_CHOICE` | 설치할 CNI 선택 (`calico` 또는 `cilium`) |
| `CALICO_VERSION` | Calico 버전 |
| `CALICO_INSTALL_METHOD` | Calico 설치 방식 (`manifest` 또는 `operator`) |
| `CILIUM_VERSION` | Cilium 버전 |
| `ENABLE_HUBBLE` | Cilium Hubble 활성화 여부 |
| `MTU_VALUE` | CNI(Cilium 등) 설치 시 적용할 MTU 설정값 |
| `BUNDLE_OUTPUT_DIR` | 생성된 아카이브 산출물이 저장될 루트 디렉터리 경로 |

---

## 3. 온라인 자산 수집 (Download Phase)

외부망과 연동되는 호스트에서 아래 명령어를 실행하여 오프라인 설치에 필요한 모든 패키지 및 이미지를 수집합니다.

```bash
sudo ./scripts/download.sh
```

### 내부 수행 작업
- Kubernetes minor 리포지토리 주소 자동 계산 및 등록
- `kubeadm`, `kubelet`, `kubectl` 패키지와 종속성 패키지 수집
- 컨테이너 런타임 패키지 수집 (Rocky 9.6의 경우, Kubernetes v1.33 호환성 기준인 `containerd.io-2.1.*` 라인 적용)
- `kubeadm` 설정 기준 핵심 컨트롤 플레인 이미지 목록 생성 및 `.tar` 파일로 Export
- 선택된 CNI 매니페스트, Helm chart, 이미지 수집
- 번들 패키징을 위한 staging 디렉터리 구성

> [!IMPORTANT]
> 이 단계는 외부 네트워크와의 통신 및 시스템 APT/DNF 리포지토리 등록 과정이 포함되므로 반드시 `sudo` 권한으로 실행해야 합니다.

### 설정값 및 호환성 검증
`scripts/download.sh` 및 `scripts/build_bundle.sh` 실행 시, 공통 함수 모듈(`scripts/lib/common.sh`)을 통해 설정 파라미터 유효성 검사 및 버정 호환성 정책 검증을 우선 수행합니다.

- **설정값 유효성 검사**: `K8S_VERSION` 포맷 자동 교정(v 누락 시 자동 보정), `TARGET_OS`, `ARCH`, `CNI_CHOICE` 파라미터 적합 여부 확인.
- **호환성 정책 검증 (`manifests/compatibility.yaml`)**: Kubernetes 공식 호환성 기준(Version Skew Policy) 및 각 컴포넌트(containerd, Calico, Cilium)의 OS별/K8s 버전별 공식 검증 매트릭스 정보를 기준으로 대조 작업을 선행합니다. 정의되지 않은 조합의 수집 요청은 실행 전 차단됩니다.

---

## 4. 오프라인 설치 번들 빌드

자산 수집이 완료되면 에어갭(폐쇄망) 환경에서 사용 가능한 단일 압축 번들을 생성합니다.

```bash
./scripts/build_bundle.sh
```

### 실행 옵션 및 산출물
*   **Dry-run 모드 (경로 및 빌드 정보 확인)**:
    ```bash
    ./scripts/build_bundle.sh --dry-run
    ```
*   **빌드 수행 (Staging 디렉터리 구성 및 tar.gz 아카이브 생성)**:
    ```bash
    ./scripts/build_bundle.sh
    ```

### 예상 산출물 구조
```text
bundles/
├── k8s-v1.33.11-ubuntu24.04/         # 폐쇄망 노드 배포용 staging 폴더
├── k8s-v1.33.11-ubuntu24.04.tar.gz   # 폐쇄망 노드로 전송할 압축 번들 파일
├── k8s-v1.33.11-rocky9.6/
└── k8s-v1.33.11-rocky9.6.tar.gz
```

---

## 5. 폐쇄망 설치 진행

빌드된 `tar.gz` 파일을 폐쇄망 환경의 대상 노드로 전송하고 압축을 해제한 뒤, 내부의 설치 진입 스크립트를 사용하여 설치를 진행합니다.

```bash
# 압축 해제 후 번들 내부로 진입
tar -zxvf k8s-v1.33.11-ubuntu24.04.tar.gz
cd k8s-v1.33.11-ubuntu24.04

# 설치 스크립트 가동 (Master-1 기준)
sudo ./scripts/install.sh
```

### 번들 내부 설치 스크립트 주요 처리 범위
- OS 환경 확인 (WSL2 여부 및 가상머신 감지)
- 오프라인 DEB/RPM 패키지 설치 및 Kernel 모듈/sysctl 최적화
- 파일 디스크립터(FD) 및 systemd limits override 설정 적용
- containerd 컨테이너 런타임 오프라인 설정 및 활성화
- 수집된 핵심 컨테이너 이미지 사전 로드 (`ctr` 이미지 임포트)
- `kubeadm init` 및 `kubeadm join` 자동화 제어
- CNI 설치 (`Calico manifest`, `Calico Tigera operator`, `Cilium Helm` 중 설정된 방식 적용)
- WSL2 환경 대상 systemd 활성화 및 iptables-legacy 사전 설정 보조

> [!WARNING]
> 빌더 패키지 루트 디렉터리에 존재하는 `scripts/install.sh`는 오프라인 설치 작업을 수행하지 않으며, 혼선을 막기 위한 안내문 진입점 역할만 수행합니다. 실제 에어갭 설치는 반드시 빌드된 **`bundles/` 하위 번들 폴더 내부의 `scripts/install.sh`**를 통해 가동해야 합니다.

---

## 6. 수동 점검 및 유지보수

빌더 자체는 설치 도구 패키징 역할을 하므로, `helm`이나 `kubectl` 서비스 형태로 클러스터에 배포되지 않습니다. 빌더 도구의 문법 및 수동 점검 사항은 아래 명령으로 검증합니다.

```bash
# 쉘 스크립트 정적 구문 분석 검증
bash -n scripts/download.sh
bash -n scripts/build_bundle.sh

# 생성될 빌드 정보 및 타겟 경로 정합성 검증
./scripts/build_bundle.sh --dry-run
```
