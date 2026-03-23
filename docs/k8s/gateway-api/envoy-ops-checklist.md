# 🚀 Envoy Gateway 운영 전환 체크리스트

본 문서는 Envoy Gateway를 설치한 후, 실제 운영 환경의 **SLB(Server Load Balancer/L4)**와 연동하여 서비스를 오픈하기 전 반드시 확인해야 할 사항들을 정의합니다.

---

## 🏗️ 배경 개념 정리

### SLB (Server Load Balancer)

클라이언트 요청을 여러 워커 노드에 분산시켜주는 장비입니다. VIP로 들어온 트래픽을 워커 노드의 NodePort로 전달합니다.

- **흐름**: `Client → VIP(SLB) → Worker Node:30080 → Envoy → Service`

### SNAT vs DSR

SLB가 트래픽을 전달하는 방식에 따라 클라이언트 실IP 보존 여부가 결정됩니다.

| 방식 | 설명 | 클라이언트 실IP 보존 |
| :--- | :--- | :--- |
| **SNAT** | SLB가 출발지 IP를 자신의 IP로 변조 | ❌ (SLB IP만 보임) |
| **DSR** | 패킷 소스 IP를 유지하며 전달 | ✅ (실IP 보존) |

> !!! tip "네트워크 팀 문의 사항"
> "운영 중인 SLB가 SNAT 방식인가요, DSR 방식인가요?"라고 사전에 확인하십시오.

### PROXY Protocol (PP)

SNAT 방식에서 실IP를 보존하기 위해 패킷 헤더에 원본 정보를 포함하는 기술입니다.

- **주의**: 현재 표준 설정에는 PP가 활성화되어 있습니다. **SLB가 PP를 지원하지 않는데 Envoy에서 켜져 있으면 통신이 즉시 차단됩니다.**

---

## 🛠️ 운영 환경 전환 절차

### 1단계: 워커 노드 포트 개방 확인

NodePort(30080, 30443)는 커널 규칙으로 동작하여 일반적인 포트 확인 명령으로 안 보일 수 있습니다. TCP 연결을 직접 테스트하십시오.

```bash
# 워커 노드 IP에서 NodePort 통신 확인
nc -zv <WORKER_NODE_IP> 30080
nc -zv <WORKER_NODE_IP> 30443
```

### 2단계: 네트워크 팀 최종 확인 항목

- [ ] **L4 라우팅**: VIP → Worker NodePort(30080/30443) 등록 완료 여부
- [ ] **SLB 방식**: SNAT 인지 DSR 인지 확인
- [ ] **PP 지원**: SLB에서 PROXY Protocol 송신 설정을 했는지 확인
- [ ] **Health Check**: L4 장비에서 워커 노드 포트 상태 체크(TCP/HTTP) 설정 여부

### 3단계: PROXY Protocol (PP) 설정 조정

2단계 확인 결과에 따라 정책 유지 여부를 결정합니다.

**A. SLB가 PP를 보내지 않는 경우 (일반 하드웨어 L4)**:
정책을 삭제해야 통신이 가능합니다.

```bash
kubectl delete clienttrafficpolicy enable-proxy-protocol -n envoy-gateway-system
```

**B. SLB가 PP를 보내는 경우**:
기본 정책을 유지합니다.

### 4단계: Gateway 주소를 VIP로 변경

외부에서 인식하는 게이트웨이 주소를 실제 VIP로 패치합니다.

```bash
kubectl patch gateway cmp-gateway -n envoy-gateway-system \
  --type='merge' \
  -p '{"spec":{"addresses":[{"type":"IPAddress","value":"<VIP_IP>"}]}}'
```

### 5단계: 상태 및 접속 확인

```bash
# Gateway 주소가 VIP로 반영되었는지 확인
kubectl get gateway cmp-gateway -n envoy-gateway-system

# 실제 접속 테스트 (응답 코드 확인)
curl -s -o /dev/null -w "%{http_code}\n" https://<DOMAIN>/
```

---

## 📋 클라이언트 실IP 보존 현황 요약

| SLB 방식 | PP 지원 여부 | Envoy에서 보이는 소스 IP |
| :--- | :--- | :--- |
| **DSR** | 불필요 | 실제 클라이언트 IP |
| **SNAT + PP** | 지원 | 실제 클라이언트 IP |
| **SNAT (No PP)** | 미지원 | SLB 장비 IP (실IP 손실) |

---

## 🔄 롤백 방법 (Rollback)

문제가 발생하여 이전 상태(`externalIPs` 방식)로 되돌리는 방법입니다.

```bash
# 1. Gateway 주소를 다시 워커 노드 IP로 변경
kubectl patch gateway cmp-gateway -n envoy-gateway-system --type='merge' \
  -p '{"spec":{"addresses":[{"type":"IPAddress","value":"<WORKER_NODE_IP>"}]}}'

# 2. PP 정책을 삭제했다면 재생성 (히어독 방식)
kubectl apply -f - <<'EOF'
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: ClientTrafficPolicy
metadata:
  name: enable-proxy-protocol
  namespace: envoy-gateway-system
spec:
  targetRef:
    group: gateway.networking.k8s.io
    kind: Gateway
    name: cmp-gateway
  enableProxyProtocol: true
EOF
```
