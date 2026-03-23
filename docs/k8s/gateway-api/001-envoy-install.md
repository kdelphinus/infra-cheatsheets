# 🚀 Envoy Gateway v1.36.3 오프라인 설치 가이드

본 문서는 **Envoy Gateway**를 폐쇄망 Kubernetes 환경에 설치하여 통합 L7 게이트웨이 체계를 구축하고, 온프레미스 네트워크(VIP/L4)와 연동하는 절차를 정의합니다.

## 📋 구성 명세

| 항목 | 사양 | 비고 |
| :--- | :--- | :--- |
| **Envoy Gateway** | **v1.36.3** | 오픈소스 L7 게이트웨이 |
| **Gateway API** | **v1.1.0+** | Kubernetes 표준 게이트웨이 API |
| **Network Mode** | `hostNetwork: false` | K8s 내부망 사용 (표준) |

---

## 🏗️ 아키텍처 및 트래픽 흐름

### 1. LoadBalancer 모드 (MetalLB 등 사용 시)
```text
Client → External IP (LB) → Service (80/443) → Envoy Pod → Backend Pod
```

### 2. NodePort + VIP 모드 (온프레미스 표준)
```text
Client → VIP (L4/HAProxy) → Worker Node IP:30080/30443 → Envoy Pod → Backend Pod
```

---

## 🛠️ 설치 전제 조건

- Kubernetes 클러스터 구성 완료
- Helm v3.x 설치 완료
- Harbor 레지스트리 접근 가능 (`<NODE_IP>:30002`)

---

## 1단계: 이미지 Harbor 업로드

컴포넌트 루트 디렉토리에서 실행합니다.

```bash
# upload_images_to_harbor_v3-lite.sh 상단 Config 수정
# HARBOR_REGISTRY: <NODE_IP>:30002

chmod +x images/upload_images_to_harbor_v3-lite.sh
./images/upload_images_to_harbor_v3-lite.sh
```

---

## 2단계: 설치 및 운영 설정 (values.yaml)

| 파일명 | 용도 | 주요 수정 항목 |
| :--- | :--- | :--- |
| **`values-controller.yaml`** | Controller 설정 | 이미지 경로, 리소스 제한 등 |
| **`values-infra.yaml`** | Gateway 설정 | 서비스 타입(LB/NodePort), 노드 고정 여부 |
| **`manifests/policy-global.yaml`** | 전역 보안 정책 | EnvoyPatchPolicy (헤더 노출 방지 등) |

---

## 3단계: TLS 사전 구성 (HTTPS 사용 시)

HTTPS를 사용할 경우 Helm 배포 전 Gateway 네임스페이스에 TLS Secret을 생성합니다.

```bash
# 1. 네임스페이스 생성
kubectl create ns envoy-gateway-system --dry-run=client -o yaml | kubectl apply -f -

# 2. TLS Secret 생성 (인증서 파일 필요)
kubectl create secret tls strato-tls \
  --cert=cert.pem \
  --key=key.pem \
  --namespace envoy-gateway-system
```

---

## 4단계: 설치 실행

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

**스크립트 실행 중 인터랙티브 옵션:**
1. **설치 모드**: `1` (LoadBalancer) 또는 `2` (NodePort)
2. **노드 고정 (NodeSelector)**: Envoy Proxy를 배치할 특정 워커 노드 고정 여부 (성능/보안 목적)
3. **전역 정책 적용**: `manifests/policy-global.yaml` 적용 여부 (보안 및 트래픽 제어 정책)

---

## 5단계: 배포 후 네트워크 구성 (환경별 대응)

### Case A: LoadBalancer — 자동 할당 (MetalLB 환경)
`EXTERNAL-IP`가 자동으로 할당되면 해당 IP로 즉시 접속 가능합니다.

### Case B: LoadBalancer — 수동 할당 (온프레미스)
`EXTERNAL-IP`가 `<pending>`인 경우 워커 노드 IP를 수동으로 바인딩합니다. 
- **참고**: DaemonSet + `externalTrafficPolicy: Local` 구성이라면 모든 워커 노드 IP를 등록해야 트래픽이 분산됩니다. 앞단에 별도 VIP가 있다면 해당 VIP 하나만 등록해도 무방합니다.

```bash
# 서비스에 외부 IP 패치 (단일 또는 다중 IP)
kubectl patch svc -n envoy-gateway-system envoy-cmp-gateway \
  -p '{"spec":{"externalIPs":["10.10.10.73","10.10.10.74","10.10.10.75"]}}'

# Gateway 리소스에 주소 패치 (상태가 False인 경우)
kubectl patch gateway cmp-gateway -n envoy-gateway-system --type='merge' \
  -p '{"spec":{"addresses":[{"type":"IPAddress","value":"10.10.10.73"},{"type":"IPAddress","value":"10.10.10.74"}]}}'
```

### Case C: NodePort — VIP 연동
NodePort 모드 설치 시 HTTP **30080**, HTTPS **30443** 포트로 고정됩니다. 환경에 따라 아래 방식 중 하나를 선택하여 연동합니다.

#### 1) L4 스위치(Hardware LB) 연동 시
네트워크 담당자에게 워커 노드 IP와 고정 포트(**30080, 30443**)를 L4 장비의 **Real Server**로 등록 요청합니다. 사용자는 L4 장비의 VIP(80/443)를 통해 접속합니다.
- **트래픽 흐름**: `Client → VIP(L4) → Worker IP:30080/30443 → Envoy Pod`

#### 2) L4 장비가 없는 경우 (Keepalived + HAProxy)
워커 노드에 소프트웨어 로드밸런서를 구성하여 80/443 포트를 30080/30443으로 중계합니다.

#### 3) 별도 LB 장비 없이 단일 노드 직접 접속
임시 테스트 환경이거나 LB 구성이 어려운 경우 워커 노드의 IP와 고정 포트로 직접 접속합니다.
- **HTTP**: `http://<NODE_IP>:30080`
- **HTTPS**: `https://<NODE_IP>:30443`
- **주의**: 해당 노드의 방화벽에서 30080, 30443 포트가 허용되어야 합니다.

---

## 💡 운영 팁

- **클라이언트 실IP 보존**: `values-infra.yaml`에서 `externalTrafficPolicy: Local` 설정을 확인하십시오. 이 설정이 되어 있어야 백엔드 앱에서 클라이언트의 실제 IP를 식별할 수 있습니다.
- **NodePort 포트 확인**: NodePort 모드 사용 시 호스트 노드에서 **30080**(HTTP), **30443**(HTTPS) 포트가 정상적으로 Listen 상태인지 확인하십시오.
- **트러블슈팅**: 
    - Gateway 상태가 `Ready: False`인 경우: `kubectl describe gateway cmp-gateway` 명령어로 이벤트 로그를 확인하십시오.
    - 정책 미적용 시: `kubectl get envoypatchpolicy -n envoy-gateway-system` 명령어로 정책 리소스를 확인하십시오.

---

## 🔗 다음 단계
설치가 완료되었다면, 실제 운영 환경의 L4 장비와 연동하기 위해 **[운영 전환 체크리스트](envoy-ops-checklist.md)**를 확인하십시오.

---

## 🗑️ 삭제 (Uninstall)

```bash
./scripts/uninstall.sh
```
