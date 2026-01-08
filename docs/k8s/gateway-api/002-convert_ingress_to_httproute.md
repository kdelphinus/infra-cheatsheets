# 📘 HTTPRoute 기본 기능 및 Ingress to Gateway API (Envoy) 마이그레이션 가이드

본 문서는 `HTTPRoute` 기본 기능 및 기존 NGINX `Ingress` 리소스 변환 가이드입니다.

---

## 1. 변환 전 필수 점검 사항

1. **Gateway 이름:** 모든 Route는 `cmp-gateway` (Namespace: `envoy-gateway-system` )를
바라봐야 합니다.
   - 위 이름은 준비된 설치 파일의 기본값입니다.
   - Gateway 이름 및 Namespace는 설정한 값에 따라 다를 수 있습니다.
2. **Target Port 사용:** `backendRefs`의 포트는 Service Port(80) 대신
**Pod Container Port(예: 8080, 3000)**를 사용하는 것이 안전합니다.
3. **Namespace:** `HTTPRoute` 리소스는 반드시 연결하려는 **Service와 동일한 네임스페이스**에 생성해야 합니다.

---

## 2. Gateway API 기본 기능

Gateway API에서 제공하는 기능 중 기본 기능입니다.

### 1️⃣ 매칭 조건 (Matching Rules)

경로뿐만 아니라 **헤더, 쿼리 파라미터, HTTP 메서드**로도 분기할 수 있습니다.

```yaml
rules:
  - matches:
    # 1. 경로 매칭 (Prefix vs Exact)
    - path:
        type: PathPrefix # /api로 시작하는 모든 요청
        value: /api
      
    # 2. 헤더 매칭 (예: 디버그 모드)
    - headers:
      - name: x-debug-mode
        value: "true"
        
    # 3. 메서드 매칭 (GET 요청만 허용)
    - method: GET
    
    backendRefs:
    - name: my-service
      port: 8080

```

### 2️⃣ 트래픽 분할 (Canary Release)

별도의 서비스 메시(Istio 등) 없이도 **가중치(Weight)** 기반의 카나리 배포가 가능합니다.

```yaml
rules:
  - matches:
    - path:
        type: PathPrefix
        value: /v1
    backendRefs:
    # 기존 버전 (90% 트래픽)
    - name: app-v1-svc
      port: 8080
      weight: 90
    # 신규 버전 (10% 트래픽)
    - name: app-v2-svc
      port: 8080
      weight: 10

```

### 3️⃣ 리다이렉트 (Redirect)

구형 URL을 신규 URL로 넘기거나, HTTP를 HTTPS로 강제할 때 사용합니다.

```yaml
rules:
  - matches:
    - path:
        type: PathPrefix
        value: /old-path
    filters:
    - type: RequestRedirect
      requestRedirect:
        scheme: https        # 프로토콜 변경 (옵션)
        hostname: new.com    # 호스트 변경 (옵션)
        path:
          type: ReplaceFullPath
          replaceFullPath: /new-path # 경로 변경
        statusCode: 301      # 상태 코드 (301/302)

```

### 4️⃣ 헤더 조작 (Header Modification)

백엔드 서버로 요청을 보내기 전(Request)이나, 클라이언트로 응답을 주기 전(Response)에 헤더를 추가/삭제합니다.

```yaml
filters:
  # 요청 헤더 조작 (백엔드가 받을 헤더)
  - type: RequestHeaderModifier
    requestHeaderModifier:
      add:
      - name: "X-Envoy-Gateway"
        value: "true"
      remove: ["X-Internal-Secret"]

  # 응답 헤더 조작 (클라이언트가 받을 헤더)
  - type: ResponseHeaderModifier
    responseHeaderModifier:
      set:
      - name: "Cache-Control"
        value: "no-cache"

```

### 5️⃣ 미러링 (Traffic Mirroring)

운영 환경의 트래픽을 복제하여 **사용자에게 영향 없이** 테스트 서버로 똑같이 보내봅니다. (Shadowing)

```yaml
rules:
  - matches:
    - path:
        type: PathPrefix
        value: /payment
    
    # 실제 트래픽 처리
    backendRefs:
    - name: payment-prod-svc
      port: 8080
      
    # 트래픽 복제 (응답은 무시됨)
    filters:
    - type: RequestMirror
      requestMirror:
        backendRef:
          name: payment-test-svc
          port: 8080

```

---

## 3. 실전 변환 케이스 (Case Study)

### 📂 Case A: 모니터링 (Grafana) - Rewrite & Sub-path

Grafana와 같이 `/grafana` 경로로 들어오지만 앱은 `/`로 인식해야 하는 경우입니다.

🔴 Before (Ingress)

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2  # 경로 재작성
spec:
  rules:
  - http:
      paths:
      - path: /grafana(/|$)(.*)
        backend:
          service:
            name: grafana-svc
            port: { number: 3000 }

```

🟢 After (HTTPRoute)

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: strato-monitoring-route
  namespace: {{ .Values.monitoringOss.namespace }} # 서비스와 동일한 네임스페이스
  labels:
    app: grafana
spec:
  parentRefs:
  - name: cmp-gateway  # Gateway 이름
    namespace: envoy-gateway-system  # Gateway Namespace
  
  hostnames:
  - {{ .Values.productIngress.host | quote }}
  
  rules:
  # --------------------------------------------------------
  # Grafana 경로 (/grafana -> /)
  # --------------------------------------------------------
  - matches:
    - path:
        type: PathPrefix
        value: /grafana
    
    filters:
    # [핵심] URL Rewrite (/grafana/xxx -> /xxx)
    - type: URLRewrite
      urlRewrite:
        path:
          type: ReplacePrefixMatch
          replacePrefixMatch: /
    
    backendRefs:
    - name: grafana-svc
      port: 3000 # 실제 컨테이너 포트 권장

```

---

### 📂 Case B: API Gateway - CORS & Body Size

API 호출을 위한 Gateway로, **CORS 설정**과 **대용량 파일 업로드(20MB)** 설정이 필요합니다.

🔴 Before (Ingress)

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "20M"
    nginx.ingress.kubernetes.io/cors-allow-origin: "*"
    ...
```

🟢 After (HTTPRoute + EnvoyPatchPolicy)

1. 라우트 설정 (CORS & Rewrite)

    ```yaml
    apiVersion: gateway.networking.k8s.io/v1
    kind: HTTPRoute
    metadata:
    name: api-gateway-route
    namespace: {{ .Values.common.namespace }}
    spec:
    parentRefs:
    - name: cmp-gateway
        namespace: envoy-gateway-system
    hostnames:
    - {{ .Values.gatewayIngress.host | quote }}
    rules:
    - matches:
        - path:
            type: PathPrefix
            value: /gw
        filters:
        # 1. 경로 재작성 (/gw 제거)
        - type: URLRewrite
        urlRewrite:
            path:
            type: ReplacePrefixMatch
            replacePrefixMatch: /

        # 2. CORS 헤더 설정
        - type: ResponseHeaderModifier
        responseHeaderModifier:
            set:
            - name: "Access-Control-Allow-Origin"
            value: "*"
            - name: "Access-Control-Allow-Methods"
            value: "PUT, GET, POST, DELETE, OPTIONS, PATCH"
            - name: "Access-Control-Allow-Headers"
            value: "*"
            - name: "Access-Control-Allow-Credentials"
            value: "true"

        backendRefs:
        - name: api-gateway-svc
        port: {{ .Values.gateway.ports.internal }}
    ```

2. Body Size 설정 (전역 설정)

    Ingress의 `proxy-body-size`는 `HTTPRoute`에 없고 **`EnvoyPatchPolicy`** 로 Envoy
    설정을 직접 수정해야 합니다.

    ```yaml
    apiVersion: gateway.envoyproxy.io/v1alpha1
    kind: EnvoyPatchPolicy
    metadata:
    name: increase-body-limit-20m
    namespace: envoy-gateway-system  # [중요] Gateway와 같은 네임스페이스
    spec:
    targetRef:
        group: gateway.networking.k8s.io
        kind: Gateway
        name: cmp-gateway            # 대상 Gateway 이름
    type: JSONPatch
    jsonPatches:
    - type: "type.googleapis.com/envoy.config.listener.v3.Listener"
        # [중요] 리스너 이름 규칙: <namespace>/<gateway>/<listener_name>
        name: "envoy-gateway-system/cmp-gateway/http" 
        operation:
        op: add
        # HTTP Connection Manager(HCM) 설정에 max_request_bytes 주입
        path: "/filter_chains/0/filters/0/typed_config/max_request_bytes"
        value: 20971520 # 20MB (Byte 단위)
    ```

---

### 📂 Case C: 메인 포털 (Multi-path Routing)

하나의 호스트에서 `/oauth2`와 `/` (루트) 경로를 서로 다른 서비스로 분기합니다.

🔴 Before (Ingress)

```yaml
spec:
  rules:
    - path: /
      backend: strato-portal-frontend-svc
    - path: /oauth2
      backend: strato-auth-svc

```

🟢 After (HTTPRoute)

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: strato-product-route
  namespace: {{ .Values.common.namespace }}
spec:
  parentRefs:
  - name: cmp-gateway  # Gateway 이름
    namespace: envoy-gateway-system  # Gateway Namespace
  hostnames:
  - {{ .Values.productIngress.host | quote }}
  rules:
  # --------------------------------------------------------
  # 규칙 1: /oauth2 (인증 서비스) - 구체적인 경로가 우선 매칭됨
  # --------------------------------------------------------
  - matches:
    - path:
        type: PathPrefix
        value: /oauth2
    backendRefs:
    - name: strato-auth-svc
      port: 5555

  # --------------------------------------------------------
  # 규칙 2: / (메인 포털) - 나머지 모든 요청 처리
  # --------------------------------------------------------
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: strato-portal-frontend-svc
      port: 80

```

---

### 📂 Case D: Helm 템플릿 적용 (Portal Frontend)

Helm 차트(`values.yaml`)를 사용하는 동적 생성 예시입니다.

🟢 After (HTTPRoute with Helm)

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: strato-portal-frontend-route
  namespace: {{ default .Release.Namespace .Values.namespace }}
  labels:
    app.kubernetes.io/name: strato-portal-frontend
spec:
  parentRefs:
  - name: cmp-gateway
    namespace: envoy-gateway-system
  
  hostnames:
  - {{ .Values.ingress.domain | quote }}
  
  rules:
  # --------------------------------------------------------
  # 1. 인증 서비스 (/oauth2)
  # --------------------------------------------------------
  - matches:
    - path:
        type: PathPrefix
        value: /oauth2
    backendRefs:
    - name: {{ .Values.ingress.oauth2.serviceName }} # strato-auth-svc
      port: {{ .Values.ingress.oauth2.servicePort }} # 5555

  # --------------------------------------------------------
  # 2. 메인 포털 (/)
  # --------------------------------------------------------
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: strato-portal-frontend-svc
      port: {{ .Values.service.port }}   # 80

```

---

## 4. 요약 및 주의사항

1. **Rewrite Target:** `annotation` 대신 `filters.urlRewrite`를 사용합니다.
2. **CORS:** `annotation` 대신 `filters.responseHeaderModifier`를 사용합니다.
3. **Body Size:** `HTTPRoute`가 아닌 `EnvoyPatchPolicy`로 전역 설정해야 합니다. (Byte 단위 주의)
4. **우선순위:** `rules` 리스트의 순서는 상관없으나,
**가장 긴 경로(More Specific Path)**가 자동으로 우선순위를 갖습니다. (예: `/oauth2`가 `/`보다 우선)
