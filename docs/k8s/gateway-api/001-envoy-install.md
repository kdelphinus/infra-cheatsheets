# 🚀 Envoy Gateway v1.36.3 오프라인 설치 가이드

본 문서는 **Envoy Gateway**를 폐쇄망 Kubernetes 환경에 설치하여 통합 L7 게이트웨이 체계를 구축하는 절차를 정의합니다.

## 📋 구성 명세

| 항목 | 사양 | 비고 |
| :--- | :--- | :--- |
| **Envoy Gateway** | **v1.36.3** | 오픈소스 L7 게이트웨이 |
| **Gateway API** | **v1.1.0+** | Kubernetes 표준 게이트웨이 API |
| **Storage** | ephemeral | 게이트웨이는 상태 비저장(Stateless) 기반 |

---

## 🛠️ 설치 전제 조건

- Kubernetes 클러스터 구성 완료
- Helm v3.x 설치 완료
- Harbor 레지스트리 접근 가능 (`<NODE_IP>:30002`)
- **MetalLB** 설치 완료 (LoadBalancer 모드 사용 시)

---

## 1단계: 이미지 Harbor 업로드

모든 작업은 컴포넌트 루트 디렉토리에서 실행합니다.

```bash
# upload_images_to_harbor_v3-lite.sh 상단 Config 수정
# HARBOR_REGISTRY: <NODE_IP>:30002

chmod +x images/upload_images_to_harbor_v3-lite.sh
./images/upload_images_to_harbor_v3-lite.sh
```

---

## 2단계: 설치 및 운영 설정 (values.yaml)

설치 전 컴포넌트 루트의 설정 파일들을 환경에 맞게 수정합니다.

| 파일명 | 용도 | 주요 수정 항목 |
| :--- | :--- | :--- |
| **`values-controller.yaml`** | Controller 설정 | 이미지 경로, 리소스 제한 등 |
| **`values-infra.yaml`** | Gateway 설정 | 서비스 타입(LB/NodePort), 노드 고정 여부 |
| **`manifests/policy-global.yaml`** | 전역 보안 정책 | EnvoyPatchPolicy (헤더 노출 방지 등) |

---

## 3단계: 설치 실행

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

**스크립트 실행 중 선택 사항:**
1. **설치 모드**: `1` (LoadBalancer) 또는 `2` (NodePort)
2. **노드 고정 (NodeSelector)**: Envoy Proxy를 배치할 특정 노드 이름 입력 (선택)
3. **전역 정책**: `manifests/policy-global.yaml` 적용 여부

---

## 4단계: 설치 확인

```bash
# 파드 상태 확인 (envoy-gateway-system 네임스페이스)
kubectl get pods -n envoy-gateway-system

# Gateway 및 서비스(LoadBalancer/NodePort) 확인
kubectl get gateway,svc -n envoy-gateway-system
```

---

## 5단계: 서비스 노출 (HTTPRoute 적용 예시)

신규 서비스를 Envoy를 통해 도메인 기반으로 노출하려면 `HTTPRoute` 리소스를 생성합니다.

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: my-app-route
  namespace: default
spec:
  parentRefs:
    - name: cmp-gateway
      namespace: envoy-gateway-system
  hostnames:
    - "my-app.internal"
  rules:
    - matches:
        - path: { type: PathPrefix, value: / }
      backendRefs:
        - name: my-app-service
          port: 80
```

---

## 💡 운영 팁

- **클라이언트 실IP 보존**: `values-infra.yaml`에서 `externalTrafficPolicy: Local` 설정을 반드시 확인하십시오.
- **NodePort 확인**: NodePort 모드 사용 시 호스트에서 `30080`(HTTP), `30443`(HTTPS) 포트가 정상 작동 중인지 확인하십시오.
- **트러블슈팅**: Gateway 상태가 `Ready: False`일 경우 `kubectl describe gateway cmp-gateway` 명령어로 이벤트 로그를 확인하십시오.

---

## 🗑️ 삭제 (Uninstall)

```bash
./scripts/uninstall.sh
```
