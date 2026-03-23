# 🚀 Nexus Repository 오프라인 설치 가이드

폐쇄망 환경에서 Nexus Repository Manager (Nexus3)를 Kubernetes 위에 Helm으로 설치하는 절차를 안내합니다.

## 전제 조건

- Kubernetes 클러스터 구성 완료
- Helm v3.14.0 설치 완료
- `kubectl` CLI 사용 가능
- Harbor 레지스트리 접근 가능 (`<NODE_IP>:30002`)

## 1단계: 이미지 Harbor 업로드

모든 작업은 컴포넌트 루트 디렉토리에서 실행합니다.

```bash
# upload_images_to_harbor_v3-lite.sh 상단 Config 수정
# IMAGE_DIR      : ./images (현재 디렉터리의 이미지 폴더 지정)
# HARBOR_REGISTRY: <NODE_IP>:30002

chmod +x images/upload_images_to_harbor_v3-lite.sh
./images/upload_images_to_harbor_v3-lite.sh
```

## 2단계: 설치 실행

루트 디렉토리의 `values.yaml`을 환경에 맞게 수정한 뒤 실행합니다.

```bash
# 헬름 설치
chmod +x scripts/install.sh
./scripts/install.sh
```

스크립트 자동 처리 항목:
- 네임스페이스(`nexus`) 생성
- Helm 배포 (Harbor 이미지 경로 반영)

## 3단계: 초기 비밀번호 확인

설치 완료 후 파드가 `Running` 상태가 되면 아래 명령어로 초기 `admin` 비밀번호를 확인합니다.

```bash
kubectl exec -it nexus-0 -n nexus -- cat /nexus-data/admin.password
```

| 항목 | 기본값 | 비고 |
| :--- | :--- | :--- |
| **관리자 ID** | `admin` | 초기 계정 |
| **초기 비밀번호** | 위 명령으로 확인 | 최초 로그인 후 변경 필요 |
| **접속 주소** | `http://<NODE_IP>:30004` | NodePort 기본값 |

## 디렉토리 구조 (Standard Structure)

| 경로 | 설명 |
| :--- | :--- |
| `charts/` | Nexus3 Helm 차트 |
| `images/` | 컨테이너 이미지 및 업로드 스크립트 |
| `manifests/` | PV/PVC 정의 등 K8s 리소스 |
| `scripts/` | 설치/삭제 자동화 스크립트 |

## 삭제

```bash
./scripts/uninstall.sh
```
