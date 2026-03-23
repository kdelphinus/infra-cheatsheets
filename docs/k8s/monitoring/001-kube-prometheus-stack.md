# 🚀 Monitoring 오프라인 설치 가이드 (kube-prometheus-stack)

폐쇄망 환경에서 `kube-prometheus-stack`을 사용하여 통합 모니터링 체계(Prometheus, Grafana, Alertmanager)를 구축하는 절차입니다.

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
- 네임스페이스(`monitoring`) 생성
- Helm 배포 (Harbor 이미지 경로 반영)

## 3단계: HTTPRoute 적용 (Envoy Gateway 사용 시)

Envoy Gateway를 통해 모니터링 대시보드를 노출하려면 `manifests/httproute.yaml`을 적용합니다.

```bash
# hostname 확인 및 수정 (grafana.devops.internal 등)
kubectl apply -f manifests/httproute.yaml
```

## 4단계: 설치 확인 및 접속

```bash
# 파드 및 서비스 상태 확인
kubectl get pods,svc -n monitoring

# Grafana 초기 로그인 (values.yaml 설정 확인)
# ID: admin / Password: admin
```

| 서비스 | 내부 도메인 | 비고 |
| :--- | :--- | :--- |
| **Grafana** | `grafana.devops.internal` | 대시보드 |
| **Prometheus** | `prometheus.devops.internal` | 메트릭 조회 |
| **Alertmanager** | `alertmanager.devops.internal` | 알람 관리 |

## 디렉토리 구조 (Standard Structure)

| 경로 | 설명 |
| :--- | :--- |
| `charts/` | kube-prometheus-stack Helm 차트 |
| `images/` | 컨테이너 이미지 및 업로드 스크립트 |
| `manifests/` | HTTPRoute, ServiceMonitor 등 K8s 리소스 |
| `scripts/` | 설치/삭제 자동화 스크립트 |

## 삭제

```bash
./scripts/uninstall.sh
```
