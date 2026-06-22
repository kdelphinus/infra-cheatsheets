# OPA Gatekeeper v3.17.0 오프라인 설치 가이드

본 문서는 폐쇄망 Kubernetes 클러스터에 OPA(Open Policy Agent) 기반의 정책 통제 엔진인 Gatekeeper v3.17.0을 설치하는 절차를 안내합니다.

모든 명령은 `gatekeeper-3.17.0/` 디렉터리에서 실행합니다.

---

## 0. 오프라인 설치 자산 준비 (인터넷 환경)

폐쇄망에 반입할 Helm 차트와 컨테이너 이미지(.tar)가 `charts/` 및 `images/` 디렉토리에 없는 경우, **인터넷이 연결된 외부 PC(리눅스)**에서 아래 스크립트를 실행하여 자산을 다운로드해야 합니다.

> ⚠️ **주의**: 이 작업은 폐쇄망 내부가 아닌, 외부망에서 사전에 수행되어야 합니다. (Docker 또는 containerd(`ctr`), `helm` CLI 설치 필수)

```bash
cd gatekeeper-3.17.0
chmod +x ./scripts/download_assets_offline.sh
sudo ./scripts/download_assets_offline.sh
```

완료 후 다음 파일들이 로컬에 저장됩니다.

| 경로 | 설명 |
| :--- | :--- |
| `charts/gatekeeper/` | Gatekeeper Helm 차트 |
| `images/openpolicyagent-gatekeeper-v3.17.0.tar` | Gatekeeper controller, webhook, audit 이미지 패키지 |
| `images/openpolicyagent-gatekeeper-crds-v3.17.0.tar` | Gatekeeper CRD 설치용 이미지 |

준비된 `gatekeeper-3.17.0/` 디렉터리 전체를 이동식 매체 또는 로컬 네트워크망을 통해 폐쇄망 내부로 반입합니다.

---

## 1. 전제 조건

- Kubernetes 클러스터가 정상 동작해야 합니다.
- `kubectl`, `helm`, `ctr` 명령을 사용할 수 있어야 합니다.
- `charts/gatekeeper/` 또는 Gatekeeper 차트 tgz 파일이 준비되어 있어야 합니다.
- Harbor 방식을 사용할 경우, Gatekeeper 이미지가 Harbor에 업로드되어 있어야 합니다.

---

## 2. 이미지 준비 (폐쇄망 환경)

### 방법 A. Harbor 레지스트리 사용

폐쇄망 환경에 Harbor가 구축되어 있는 경우, 이미지를 Harbor에 일괄 업로드합니다.

```bash
chmod +x ./images/upload_images_to_harbor_v3-lite.sh
sudo ./images/upload_images_to_harbor_v3-lite.sh
```

업로드 후 Harbor 프로젝트에 다음 이미지가 정상적으로 등록되었는지 확인합니다.
- `gatekeeper:v3.17.0`
- `gatekeeper-crds:v3.17.0`

### 방법 B. 로컬 containerd 이미지 직접 사용

단일 노드 환경이거나 모든 노드에 tar 파일을 직접 임포트할 수 있는 경우, 설치 스크립트에서 로컬 방식을 선택합니다. 수동으로 임포트하는 명령어는 다음과 같습니다.

```bash
sudo ctr -n k8s.io images import ./images/openpolicyagent-gatekeeper-v3.17.0.tar
sudo ctr -n k8s.io images import ./images/openpolicyagent-gatekeeper-crds-v3.17.0.tar
```

> ⚠️ **주의**: 멀티 노드 클러스터에서는 Gatekeeper Pod가 스케줄링되어 실행될 수 있는 모든 대상 노드에 이미지를 사전 로드해야 합니다.

---

## 3. 자동 설치 및 업그레이드

```bash
sudo ./scripts/install.sh
```

설치 스크립트는 다음 값을 입력받아 `install.conf`에 저장합니다.

| 항목 | 설명 |
| :--- | :--- |
| **이미지 소스** | Harbor 또는 로컬 tar 직접 사용 |
| **Harbor 주소** | 예: `172.30.235.20:30002` |
| **Harbor 프로젝트** | 예: `library` |
| **Namespace** | 기본값: `gatekeeper-system` |
| **replicas** | controller-manager 복제 수 (기본값: `3`) |
| **audit interval** | audit 실행 주기 (기본값: `60`) |

기존 설치 또는 `install.conf` 설정 파일이 감지되면 다음 메뉴가 표시되어 분기 처리할 수 있습니다.

| 메뉴 | 동작 |
| :--- | :--- |
| **업그레이드** | 기존 설정을 보존하면서 Helm upgrade 수행 |
| **재설치** | 기존 Helm 릴리스를 완벽히 제거한 뒤 설정을 재설정하여 설치 |
| **초기화** | Helm 릴리스, 네임스페이스 및 `install.conf` 파일 제거 |
| **취소** | 아무런 작업도 수행하지 않고 종료 |

---

## 4. 수동 설치 및 업그레이드 (Manual Fallback)

자동화 스크립트를 사용하지 않고 명시적으로 직접 설치를 전개하려는 경우, 아래 절차를 따릅니다.

### Harbor 이미지 경로 사용 시

`values.yaml`에서 `<NODE_IP>`와 `<PROJECT>` 부분을 실제 환경에 부합하는 Harbor 주소와 프로젝트 이름으로 치환하여 배포합니다.

```bash
sed -i \
  -e 's|<NODE_IP>|172.30.235.20:30002|g' \
  -e 's|<PROJECT>|library|g' \
  ./values.yaml

helm upgrade --install gatekeeper ./charts/gatekeeper \
  -n gatekeeper-system \
  --create-namespace \
  -f ./values.yaml \
  --wait
```

### 로컬 이미지 직접 사용 시

```bash
helm upgrade --install gatekeeper ./charts/gatekeeper \
  -n gatekeeper-system \
  --create-namespace \
  -f ./values-local.yaml \
  --wait
```

---

## 5. 설치 검증

설치가 완료되면 Gatekeeper Pod 및 웹훅 구성이 정상 기동 중인지 검증합니다.

```bash
kubectl get pods -n gatekeeper-system
kubectl get validatingwebhookconfiguration | grep gatekeeper
kubectl get mutatingwebhookconfiguration | grep gatekeeper
kubectl get crd | grep gatekeeper.sh
```

정상 상태일 때의 예시는 다음과 같습니다.

```text
gatekeeper-audit-xxxxxxxxxx-xxxxx                 1/1   Running
gatekeeper-controller-manager-xxxxxxxxxx-xxxxx    1/1   Running
```

---

## 6. 정책 적용 테스트 (Dry-Run 검증)

아래 예시는 `gatekeeper-system` 정책이 동작하는지 확인하기 위해 dry-run 형식으로 간단한 제약을 임시 등록해보는 시나리오입니다.

```bash
kubectl apply --dry-run=server -f - <<'EOF'
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
      validation:
        openAPIV3Schema:
          type: object
          properties:
            labels:
              type: array
              items:
                type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels
        violation[{"msg": msg}] {
          provided := {label | input.review.object.metadata.labels[label]}
          required := {label | label := input.parameters.labels[_]}
          missing := required - provided
          count(missing) > 0
          msg := sprintf("missing required labels: %v", [missing])
        }
EOF
```

---

## 7. 제거 및 초기화

### 자동화 제거 스크립트 실행
```bash
sudo ./scripts/uninstall.sh
```

### 수동 삭제 절차
```bash
helm uninstall gatekeeper -n gatekeeper-system
kubectl delete ns gatekeeper-system --ignore-not-found=true
rm -f ./install.conf
```

> [!WARNING]
> CRD와 기존 생성된 Constraint 리소스까지 완전히 제거하려면, 운영 중인 서비스들에 미치는 정책 영향도를 반드시 확인한 뒤 신중하게 삭제를 수행하십시오.

```bash
kubectl get crd | grep gatekeeper.sh
kubectl get crd | grep gatekeeper.sh | awk '{print $1}' | xargs -r kubectl delete crd
```
