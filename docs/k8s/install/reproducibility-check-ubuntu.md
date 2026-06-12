# Kubernetes v1.33.11 (Ubuntu 24.04) 오프라인 빌더 재현성 검증 보고서

이 문서는 기존 정적 설치 번들 `k8s-1.33.11-ubuntu24.04`를 기준으로, 동적 오프라인 빌더(`k8s-offline-builder`) 도구가 동일한 수준의 에어갭 설치 패키지를 재현할 수 있는지 비교 검증한 결과입니다.

---

## 1. 기준 산출물 요약

| 구분 | 기존 정적 번들 | builder 생성 경로 | 재현 상태 |
| --- | --- | --- | --- |
| **DEB 패키지** | 109개 | `k8s/debs` | 재현 가능 |
| **바이너리 tarball** | 2개 (`helm`, `nerdctl`) | `k8s/binaries` | 재현 가능 |
| **컨테이너 이미지** | 16개 (K8s Core + Calico) | `k8s/images` | Calico 기준 재현 가능 |
| **유틸 YAML 매니페스트** | 4개 (`calico.yaml`, `local-path` 등) | `k8s/utils` | 재현 가능 |
| **Cilium Helm chart** | 외부 컴포넌트 호출 방식 | `k8s/charts` | builder에서 내부 포함으로 확장 |

### 기존 이미지 기준 목록 (16개)
- `kube-apiserver-v1.33.11.tar`
- `kube-controller-manager-v1.33.11.tar`
- `kube-scheduler-v1.33.11.tar`
- `kube-proxy-v1.33.11.tar`
- `etcd-3.5.24-0.tar`
- `coredns-coredns-v1.12.0.tar`
- `pause-3.10.tar`
- `tigera-operator-v1.40.0.tar`
- `calico-cni-v3.31.0.tar`
- `calico-node-v3.31.0.tar`
- `calico-kube-controllers-v3.31.0.tar`
- `calico-typha-v3.31.0.tar`
- `calico-pod2daemon-flexvol-v3.31.0.tar`
- `calico-csi-v3.31.0.tar`
- `calico-node-driver-registrar-v3.31.0.tar`
- `calico-apiserver-v3.31.0.tar`

---

## 2. 디렉터리 구조 비교

| 항목 | 기존 정적 번들 | builder 생성 번들 | 판정 / 보완 사항 |
| --- | --- | --- | --- |
| `k8s/debs` | 포함 | 포함 | **일치** (수집 패키지 목록 동일) |
| `k8s/binaries` | 포함 | 포함 | **일치** (`helm` 및 `nerdctl` 수집) |
| `k8s/images` | 포함 | 포함 | **일치** (Calico 및 Core 이미지 동일) |
| `k8s/utils` | 포함 | 포함 | **일치** (`calico.yaml`, `local-path-storage.yaml`) |
| `k8s/charts` | 없음 | 포함 | **확장** (Cilium의 에어갭 내장 설치 지원을 위한 확장) |
| `scripts/install.sh` | 포함 | 템플릿 기반 생성 | **재현 가능** (설정값 기반 템플릿 렌더링) |
| `scripts/uninstall.sh` | 포함 | 템플릿 기반 생성 | **재현 가능** |
| `scripts/wsl2_prep.sh` | 포함 | 템플릿 기반 생성 | **재현 가능** |
| `install-guide*.md` | 번들 내 포함 | 빌더 공통 문서 중심 | 번들 내부 가이드는 빌더 공통 문서로 흡수 |
| `reboot-guide.md` | 포함 | 미생성 | 후속 결정 (번들별 템플릿 README 반영 예정) |

---

## 3. 설정 및 설치 기능 비교

### 설정 매개변수 정책
- **K8s 버전/OS 지정**: 기존 번들은 스크립트 내 하드코딩되었으나, 빌더는 `install.conf` 및 compatibility 정책을 기반으로 동작하여 유연성이 개선되었습니다.
- **Cilium 추가 설정**: `ENABLE_HUBBLE`, `MTU_VALUE` 설정을 빌더 번들 설정 내에 포함하여 통합 관리하도록 향상되었습니다.
- **인터페이스 & 엔드포인트**: `CONTROL_PLANE_ENDPOINT`, `CRI_SOCKET` 설정 및 대화형 입력을 통한 제어 기능은 기존과 동일하게 유지됩니다.

### 설치 기능 명세
*   **시스템 감지**: WSL2/VM 환경 감지 및 WSL2 systemd 활성화 확인 기능 일치.
*   **환경 설정**: swap 영구 비활성화, 시간 동기화(Chrony) 상태 확인, 커널 모듈/sysctl 설정, limits.d/systemd override limits 설정 일치.
*   **컨테이너 및 K8s 기동**: containerd cgroup driver 설정, 에어갭 이미지 pre-load, `kubeadm init/join` (worker 및 추가 master의 HA 합류) 처리 흐름 일치.
*   **CNI 설치 제어**: Calico manifest 설치 및 Tigera operator 설치 모드 완벽 재현.
*   **Cilium 통합**: 기존의 외부 컴포넌트 디렉터리 호출 방식에서 번들 내 내장된 chart/image를 직접 사용하는 구조로 개선되었습니다.

---

## 4. 자산 수집(download) 로직 비교

- **APT 리포지토리 제어**: 기존에는 `v1.33` 대역으로 고정되어 있었으나, 빌더는 `K8S_VERSION` 패치 버전을 파싱하여 minor 리포지토리 경로를 동적으로 계산합니다.
- **containerd.io 패키지**: OS 타겟에 맞춘 패키지 수집 및 `auto` 지정 시 Rocky 9.6 기준 v2.1.x 정규화 지원.
- **의존성 유틸**: `socat`, `conntrack`, `ebtables`, `ipset`, `jq`, `chrony`, `haproxy`, `keepalived`, `psmisc` 등 필수 패키지 목록 동일 수집.
- **YAML 및 이미지 동적 추출**: `kubeadm config images list`를 활용한 코어 이미지 수집 및 Tigera Operator YAML 내의 이미지 태그를 정규식으로 자동 파싱하여 수집하는 고도화된 스크립트 적용.

---

## 5. 의도적인 차이점 및 후속 결정 사항

1. **Envoy Gateway 자동 연동 제외**
   * **기존**: Calico 설치 완료 후 스크립트 내부에서 `../envoy-1.37.2/scripts/install.sh`를 체인 호출하여 강제 기동했습니다.
   * **빌더**: Kubernetes 및 CNI 기반 설치 기능 범위에 집중하기 위해 외부 컴포넌트 자동 호출 체인을 제외했습니다. (엔보이 게이트웨이는 별도 인프라 오케스트레이션 단계에서 순차 적용을 권장합니다.)
2. **Cilium 설치 구조 최적화**
   * **기존**: 외부 디렉터리에 위치한 Cilium 설치 자산을 호출하여 구동했습니다.
   * **빌더**: 번들 내부 `k8s/charts/` 디렉터리에 tgz 차트와 이미지를 포함하여 독립적인 단일 번들 구조를 완성했습니다.
3. **실제 수집 정합성 검증**
   * 빌더가 에어갭 외부망 환경에서 실행될 때, 실제 다운로드된 `k8s/debs/*.deb` 파일 개수가 기존 수동 구성본(약 109개 수준)과 완전히 부합하는지 교차 확인이 필요합니다.

---

## 6. 에어갭 수집 상태 검수 스크립트

외부망 호스트에서 수집 및 번들 빌드를 마친 후, 아래 스크립트를 사용하여 번들 파일의 문법 및 자산 정합성을 수동으로 검증합니다.

```bash
# 1. 쉘 스크립트 문법 검사
bash -n bundles/k8s-v1.33.11-ubuntu24.04/scripts/install.sh
bash -n bundles/k8s-v1.33.11-ubuntu24.04/scripts/uninstall.sh
bash -n bundles/k8s-v1.33.11-ubuntu24.04/scripts/wsl2_prep.sh

# 2. 필수 바이너리 및 아카이브 존재 확인
ls -la bundles/k8s-v1.33.11-ubuntu24.04/k8s/binaries/helm-v3.20.2-linux-amd64.tar.gz
ls -la bundles/k8s-v1.33.11-ubuntu24.04/k8s/binaries/nerdctl-full-2.2.2-linux-amd64.tar.gz

# 3. CNI 매니페스트 및 패키지 수량 점검
ls -l bundles/k8s-v1.33.11-ubuntu24.04/k8s/debs/ | wc -l
ls -la bundles/k8s-v1.33.11-ubuntu24.04/k8s/utils/calico.yaml
ls -la bundles/k8s-v1.33.11-ubuntu24.04/k8s/utils/tigera-operator.yaml
```
