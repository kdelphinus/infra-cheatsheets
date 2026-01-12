# 📝 [Troubleshooting] Envoy 환경에서 Service Endpoint가 있는데도 Connection Refused 발생하는 현상

## 1. 개요 (Summary)

- **현상:** 마이크로서비스 호출 시 `500 Server Error` 및 `Connection refused` 발생.
- **특이사항:** `kubectl get endpoints` 조회 시 **Pod IP와 Port가 정상적으로 잡혀있음에도 통신 불가.**
- **원인:** Deployment YAML에 **`containerPort` 선언이 누락**됨.
- **환경:** Kubernetes + **Envoy (Istio 등 Service Mesh)**

## 2. 증상 (Symptom)

Caller(호출하는 쪽) 서비스 로그에서 아래와 같은 오류가 발생하며 통신 실패.

```bash
io.netty.channel.AbstractChannel$AnnotatedConnectException: finishConnect(..) failed: Connection refused: <SERVICE_DOMAIN>/<POD_IP>:8080
```

하지만, K8s 리소스 상태를 확인해 보면 **네트워크 연결 정보(Endpoints)는 정상**으로 보임 (이것 때문에 혼란 발생).

```bash
# Service Endpoints 정상 (IP가 잡혀있음!)
$ kubectl get endpoints strato-imp-svc -n strato-product
NAME             ENDPOINTS            AGE
strato-imp-svc   192.168.104.23:8080  3d

```

## 3. 원인 분석 (Root Cause)

### 일반 K8s vs Envoy 환경의 차이

- **일반 K8s:** `containerPort`는 단순 정보 제공용(Informational)에 가깝습니다.
실제 프로세스가 포트를 열고 있으면, YAML에 안 적어도 통신이 되는 경우가 많습니다.
- **Envoy (Service Mesh) 환경:** `containerPort` 선언이 **필수(Mandatory)**입니다.

### 상세 메커니즘

1. **Envoy 사이드카(Sidecar)**는 Pod 내의 네트워크 트래픽을 가로채서(Interception) 처리합니다.
2. 이때 Envoy는 Deployment YAML에 명시된 
**`containerPort` 목록을 보고 "아, 이 포트로 들어오는 트래픽을 앱에게 넘겨줘야 하는구나"라고 Listener(수신 규칙)를 생성**합니다.
3. **설정이 누락되면:**
    - K8s Service는 Pod IP를 찾아서 Endpoints를 연결해 줍니다. (그래서 `get endpoints`에는 나옴)
    - 하지만 트래픽이 Pod 내부의 Envoy에 도착했을 때, **Envoy가 해당 포트를 처리할 규칙이 없어서 트래픽을 차단(Refuse)**합니다.

## 4. 해결 방법 (Solution)

Deployment Manifest(YAML)에 `containerPort`를 명시적으로 추가해야 합니다.

❌ 수정 전 (AS-IS): 포트 정보 없음

```yaml
spec:
  containers:
  - name: my-app
    image: my-image:v1
    # ports 섹션 누락됨

```

✅ 수정 후 (TO-BE): 포트 정보 추가

```yaml
spec:
  containers:
  - name: my-app
    image: my-image:v1
    ports:              # <--- 반드시 추가
    - containerPort: 8080
      protocol: TCP
      name: http        # (선택사항)

```

## 5. 결론 및 교훈 (Takeaway)

> **"Service Mesh(Envoy) 환경에서는 Endpoints가 보인다고 안심하지 말 것."**

- `kubectl get endpoints`는 K8s 컨트롤러가 "IP를 찾았다"는 뜻일 뿐, "통신이 된다"는 보장은 아닙니다.
- 사이드카 패턴을 사용할 때는 **반드시 애플리케이션이 사용하는 포트를 YAML에 명시**해야 Envoy가 길을 열어줍니다.
