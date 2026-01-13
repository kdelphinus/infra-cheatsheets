# 🚀 Envoy 설치

2026년 3월부터 `Ingress Nginx` 에 대한 공식 지원이 종료됩니다.
이에 따라 Kubernetes의 `Gateway API` 와 `Envoy` 를 사용하여 합니다.

이 문서는 폐쇄망을 기준으로 합니다.
[설치 파일](https://drive.google.com/drive/folders/1joMQRpZPWzKgU9BBsdxy3b0qzJMWpBC8?hl=ko)
의 `envoy-1.36.3` 폴더를 받아주세요.

## 0. 아키텍처 개요 (Standard Architecture)

쿠버네티스 보안 및 네트워크 표준을 준수하는 구성입니다.

- **Network:** `hostNetwork: false` (Pod는 K8s 내부망 사용, 노드 네트워크와 격리)
- **Service:** `type: LoadBalancer` (외부 트래픽 진입점)
- **Traffic Flow:**
`Client` -> `External IP (LB)` -> `Service (80/443)` -> `Envoy Pod (10080/10443)`
-> `Backend Pod`

## 1. 설치

**[실행 위치: Master 1, Worker 1~3 전체]**

전체 노드에 `envoy` 이미지들을 로드합니다.

```bash
cd ./envoy-1.36.3
sudo bash ./images/upload_images.sh
```

**[실행 위치: Master 1]**

`install_envoy-gateway.sh` 스크립트에서 아래 변수를 환경에 맞게 변경합니다.
(기본값을 사용해도 괜찮습니다.)

- `NAMESPACE:` Gateway Namespace
- `CONTROLLER_CHART:` Controller Chart(기본값 고정)
- `INFRA_CHART:` Infra Chart(기본값 고정)
- `GW_NAME:` Gateway Name
- `IMG_GATEWAY:` Gateway 이미지(기본값 고정)
- `IMG_PROXY:` Proxy 이미지(기본값 고정)
- `GW_CLASS_NAME:` 클러스터 레벨 리소스 이름
- `GLOBAL_POLICY_FILE:` 전역 설정 파일 이름(기본값 고정)

이때 `NAMESPACE` 나 `GW_NAME` 를 변경했다면, `HTTPRoute` 파일에도 변경해야 합니다.

수정이 끝나면 스크립트를 실행합니다.

```bash
sudo bash install_envoy-gateway.sh
```

## 2. 배포 후 상태 확인 및 네트워크 구성

배포가 완료되면, 설치 시 선택한 모드에 따라 아래 Case 중 본인의 환경에 맞는 내용을 확인하세요.

### ✅ Case A: LoadBalancer 모드 (자동 할당 완료)

스크립트에서 [1] LoadBalancer를 선택했고, 클라우드(AWS/GKE) 환경이거나 MetalLB가 구성된 경우입니다.

- 확인: kubectl get svc -n envoy-gateway-system
- 상태: EXTERNAL-IP 필드에 IP 주소나 도메인이 표시됩니다.
- 조치: 별도 조치 불필요. 표시된 IP로 접속하면 됩니다.

### ⚠️ Case B: LoadBalancer 모드 (수동 할당 필요)

스크립트에서 [1] LoadBalancer를 선택했으나, IP를 할당해 줄 컨트롤러(MetalLB 등)가 없는 온프레미 환경입니다.

- 확인: kubectl get svc -n envoy-gateway-system
- 상태: EXTERNAL-IP가 `<pending>` 상태로 멈춰 있습니다.
- 조치: 특정 노드의 IP를 VIP처럼 사용하도록 수동으로 IP를 바인딩해야 합니다.
(아래 명령어의 1.1.1.213 부분을 실제 사용할 노드 IP로 변경하여 실행하세요.)

```bash
# 1. 대상 서비스 이름 추출
SVC_NAME=$(kubectl get svc -n envoy-gateway-system -o jsonpath='{.items[?(@.spec.type=="LoadBalancer")].metadata.name}')

# 2. External IP 수동 패치 (사용할 노드 IP로 수정 필수!)
kubectl patch svc -n envoy-gateway-system $SVC_NAME \
  --type merge \
  -p '{"spec":{"externalIPs":["1.1.1.213"]}}'

echo "✅ 서비스($SVC_NAME)에 외부 IP가 수동 할당되었습니다."
```

### ⚙️ Case C: NodePort 모드 (포트 고정)

스크립트에서 [2] NodePort를 선택한 경우입니다.
설치 스크립트에 의해 서비스 포트가 HTTP(30080), **HTTPS(30443)**으로 자동 고정되었습니다.

1. 포트 확인

    ```bash
    kubectl get svc -n envoy-gateway-system
    # 출력 확인: 80:30080/TCP, 443:30443/TCP
    ```

2. 환경별 접속 가이드

    - [C-1] 외부 L4 스위치(Hardware LB) 연동 시:
      - 네트워크 담당자에게 **"쿠버네티스 노드들의 IP와 고정 포트(30080, 30443)"**를
      L4 장비의 멤버(Real Server)로 등록 요청합니다.
      - 사용자는 L4 장비의 VIP(80/443)로 접속합니다.
    - [C-2] L4 장비가 없는 경우 (로컬/폐쇄망 직접 접속):
      - 별도의 장비 없이 PC에서 직접 접속합니다.
      - 접속 주소:
        - HTTP: http://<Node_IP>:30080
        - HTTPS: https://<Node_IP>:30443
      - 주의: 방화벽에서 해당 포트(30080, 30443)가 허용되어야 합니다.

## 3. 라우팅(HTTPRoute) 설정 및 검증

Gateway가 정상적으로 떴다면, 애플리케이션 연결 규칙(`HTTPRoute`)을 점검합니다.
이 검증은 서비스에 접근하지 못할 때 진행해도 됩니다.

### ✅ 체크리스트 1: 백엔드 포트 (Connection Refused)

Envoy는 서비스(ClusterIP) 포트가 아닌 **파드(Pod)의 실제 컨테이너 포트**로 접속을 시도합니다.

- **증상:** 503 Service Unavailable 또는 Connection Refused
- **확인 방법:** 실제 파드가 몇 번 포트를 열고 있는지 확인합니다.

```bash
# 1. 백엔드 앱의 파드 이름 확인
kubectl get pods -n <NAMESPACE>

# 2. 파드 설정에서 'containerPort' 확인 (예: my-app-pod-xyz)
kubectl get pod <POD_NAME> -n <NAMESPACE> -o yaml | grep containerPort
# 출력 예시: 
# - containerPort: 8080  <-- 이 번호가 정답입니다.
```

- **해결:** 위에서 확인한 **실제 포트(예: 8080)** 를 `HTTPRoute`의 `backendRefs` 포트로 설정해야 합니다.

```bash
# 포트를 80 -> 8080으로 변경하는 예시
kubectl patch httproute <ROUTE_NAME> -n <NAMESPACE> --type='json' \
  -p='[{"op": "replace", "path": "/spec/rules/0/backendRefs/0/port", "value": 8080}]'
```

### ✅ 체크리스트 2: 경로 재작성 (URL Rewrite)

애플리케이션이 하위 경로(Context Path)를 인식하지 못해 404가 발생할 경우 사용합니다.

- **상황:** `/oauth2/login` 호출 시 앱이 `/oauth2`를 경로로 인식하여 오류 발생.
- **해결:** `URLRewrite` 필터 적용.

```yaml

filters:
- type: URLRewrite
  urlRewrite:
    path:
      type: ReplacePrefixMatch
      replacePrefixMatch: /

```

## 4. 운영 및 로그 확인

Envoy Gateway는 동적으로 리소스를 관리하므로 파드 이름이 변경됩니다.
**Label Selector(`-l`)**를 사용하여 로그를 확인하는 것이 표준입니다.

### 📋 프록시(Data Plane) 로그

실제 트래픽 처리, 접속 오류 확인 시 사용합니다.

```bash
# Envoy Proxy 로그 실시간 확인
kubectl logs -n envoy-gateway-system -f -l gateway.envoyproxy.io/owning-gateway-name=cmp-gateway

```

### 🧠 컨트롤러(Control Plane) 로그

Gateway 설정 변환, 배포 실패 원인 분석 시 사용합니다.

```bash
# Gateway Controller 로그 확인
kubectl logs -n envoy-gateway-system -f -l app.kubernetes.io/name=envoy-gateway

```

## [별첨] Gateway 연결 상태 및 라우트 검증 가이드

Gateway 리소스와 HTTPRoute 리소스가 정상적으로 연결(Binding)되었는지 확인하는 방법입니다.

### 1. Gateway 관점: 연결된 라우트 수 확인

Gateway 리소스의 상태(Status)를 조회하여 몇 개의 라우트가 연결되었는지 확인합니다.

```bash
# Gateway 상태 상세 조회
kubectl get gateway cmp-gateway -n envoy-gateway-system -o yaml
```

확인 포인트 (status.listeners 섹션):

- `attachedRoutes:` 연결된 HTTPRoute의 개수입니다. 이 숫자가 0이면 연결된 라우트가 없는 것입니다.
- `conditions:` Programmed 상태가 True여야 정상 작동 중입니다.

```yaml
status:
  listeners:
  - name: http
    attachedRoutes: 1  # <-- 현재 연결된 라우트 개수
```

### 2. HTTPRoute 관점: 부모 Gateway 연결 확인

개별 `HTTPRoute` 가 Gateway를 찾았는지, 거절당하지는 않았는지 확인합니다.

```bash
# 네임스페이스 내의 모든 HTTPRoute 상태 요약 확인
kubectl get httproute -A
```

확인 포인트:

- PARENTS: 연결된 Gateway 이름이 표시되어야 합니다.
- STATUS: True 또는 Accepted 상태여야 합니다.

#### 상세 디버깅 (연결 실패 시)

만약 연결이 안 된다면 describe 명령어로 상세 원인을 파악합니다.

```bash
kubectl describe httproute <ROUTE_NAME> -n <NAMESPACE>
```

주요 실패 원인:

- Gateway 이름 불일치: parentRefs의 name이 실제 Gateway 이름(cmp-gateway)과 다름.
- Namespace 불일치: Gateway가 다른 네임스페이스의 라우트를 허용하지 않음
(Gateway Listener 설정의 allowedRoutes 확인 필요)
