# 🚀 Envoy Gateway v1.36.3 오프라인 설치 가이드

폐쇄망 환경에서 Envoy Gateway를 Kubernetes 위에 설치하는 절차를 안내합니다.

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

## 2단계: 설치 및 운영 설정 (values.yaml)

루트 디렉토리의 설정 파일들을 환경에 맞게 수정합니다.

| 파일명 | 용도 | 비고 |
| :--- | :--- | :--- |
| **`values-controller.yaml`** | Envoy Gateway Controller 설정 | 이미지 경로 및 리소스 제한 등 |
| **`values-infra.yaml`** | Infrastructure (Gateway) 설정 | 서비스 타입(LB/NodePort), 포트 등 |
| **`manifests/policy-global.yaml`** | 전역 보안 및 트래픽 정책 | EnvoyPatchPolicy 등 |

## 3단계: 설치 실행

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

스크립트 실행 중 다음 항목을 선택합니다:

1. **설치 모드**: `1` (LoadBalancer) 또는 `2` (NodePort - 권장)
2. **노드 고정**: Envoy Proxy를 배치할 특정 노드 이름 입력 (선택)
3. **전역 정책**: `manifests/policy-global.yaml` 적용 여부

## 4단계: 설치 확인

```bash
# 파드 상태 확인
kubectl get pods -n envoy-gateway-system

# Gateway 및 서비스 확인
kubectl get gateway,svc -n envoy-gateway-system
```

## 5단계: 서비스 노출 (HTTPRoute)

신규 서비스를 Envoy를 통해 노출하려면 `HTTPRoute` 리소스를 생성하여 적용합니다.

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

## 💡 운영 및 트러블슈팅

### 네트워크 모드별 접속 가이드

- **LoadBalancer 모드**: MetalLB 등이 구성된 경우 `EXTERNAL-IP`로 접속합니다. 온프레미스에서 IP가 `<pending>`인 경우 특정 노드 IP를 수동으로 패치해야 할 수 있습니다.
- **NodePort 모드**: 기본적으로 HTTP(30080), HTTPS(30443) 포트로 고정됩니다. `externalTrafficPolicy: Local` 설정을 통해 클라이언트 실 IP를 보존할 수 있습니다.

### 체크리스트: 서비스 접근 불가 시

1. **백엔드 포트**: Envoy는 서비스 포트가 아닌 파드의 실제 `containerPort`로 접속을 시도합니다. 503 오류 발생 시 `HTTPRoute`의 포트가 실제 앱 포트와 일치하는지 확인하십시오.
2. **Gateway 상태**: `kubectl get gateway` 결과가 `false`일 경우 `kubectl describe gateway cmp-gateway` 명령어로 원인을 분석하십시오.
3. **로그 확인**: 
    - 프록시 로그: `kubectl logs -n envoy-gateway-system -f -l gateway.envoyproxy.io/owning-gateway-name=cmp-gateway`
    - 컨트롤러 로그: `kubectl logs -n envoy-gateway-system -f -l app.kubernetes.io/name=envoy-gateway`

## 디렉토리 구조 (Standard Structure)

| 경로 | 설명 |
| :--- | :--- |
| `charts/` | Envoy Gateway Helm 차트 |
| `images/` | 컨테이너 이미지 및 업로드 스크립트 |
| `manifests/` | Global Policy, HTTPRoute 예시 등 |
| `scripts/` | 설치/삭제 자동화 스크립트 |

## 삭제

```bash
./scripts/uninstall.sh
```
