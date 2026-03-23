# 🚀 Monitoring 오프라인 설치 가이드 (ctr 기반)

본 문서는 폐쇄망 Kubernetes 환경에서 **kube-prometheus-stack**을 기반으로 통합 모니터링 체계(Prometheus/Grafana)를 구축하는 절차를 정의합니다.

## 📋 구성 명세

| 항목 | 버전 | 용도 |
| :--- | :--- | :--- |
| **Kube-Prometheus-Stack** | **v62.7.0** | 모니터링 통합 스택 (Helm) |
| **Prometheus** | **v2.54.1** | 시계열 데이터 수집 및 쿼리 |
| **Grafana** | **v11.2.0** | 데이터 시각화 및 대시보드 |
| **Alertmanager** | **v0.27.0** | 경고 및 알림 관리 |

---

## 🛠️ 설치 전제 조건

- Kubernetes 클러스터 구성 완료
- Helm v3.x 설치 완료
- Harbor 레지스트리 접근 가능 (`<NODE_IP>:30002`)
- (도메인 접속 시) Envoy Gateway 설치 완료

---

## 1단계: 이미지 Harbor 업로드

컴포넌트 루트 디렉토리에서 실행합니다.

```bash
# 1. 이미지 로드 (ctr 사용)
for f in images/*.tar; do sudo ctr -n k8s.io images import "$f"; done

# 2. upload_images_to_harbor_v3-lite.sh 상단 Config 수정
# HARBOR_REGISTRY: <NODE_IP>:30002

chmod +x images/upload_images_to_harbor_v3-lite.sh
./images/upload_images_to_harbor_v3-lite.sh
```

---

## 2단계: 설치 실행

모든 작업은 컴포넌트 루트 디렉토리에서 실행합니다.

```bash
# 헬름 설치 (루트의 values.yaml 자동 반영)
chmod +x scripts/install.sh
./scripts/install.sh
```

**스크립트 자동 처리 항목:**

- 네임스페이스 (`monitoring`) 생성 및 스토리지 설정 적용
- Helm 배포 (Harbor 이미지 경로 자동 생성)
- Grafana 초기 비밀번호 설정

---

## 3단계: HTTPRoute 적용 (Envoy Gateway 사용 시)

Envoy Gateway를 통해 모니터링 대시보드를 노출하려면 `HTTPRoute`를 적용합니다.
`manifests/httproute.yaml` 상단의 `hostname`을 실제 도메인으로 수정한 뒤 실행합니다.

```bash
# 도메인 예시: grafana.devops.internal / prometheus.devops.internal
kubectl apply -f manifests/httproute.yaml
```

---

## 4단계: 설치 확인 및 접속

### 4.1 설치 상태 확인

```bash
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

### 4.2 Grafana 접속

포트 포워딩을 통해 로컬에서 즉시 접속 테스트를 진행할 수 있습니다.

```bash
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
```

**초기 로그인 정보 (values.yaml 참고):**

| 항목 | 기본값 |
| :--- | :--- |
| **ID** | `admin` |
| **Password** | `admin` |

---

## 💡 운영 및 재설치 팁

- **PVC 유지**: Helm `uninstall` 시 PVC는 삭제되지 않습니다. 데이터를 완전히 초기화하려면 `kubectl delete pvc --all -n monitoring` 명령어를 수동으로 실행하십시오.
- **리소스 제한**: Grafana와 Prometheus의 리소스 사용량을 관찰하고, 필요 시 `values.yaml`에서 `resources`를 조정하십시오.

---

## 🗑️ 삭제 (Uninstall)

```bash
./scripts/uninstall.sh
```
