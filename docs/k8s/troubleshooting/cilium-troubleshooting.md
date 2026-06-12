# Cilium CNI 설치 트러블슈팅 가이드

Cilium 설치 및 재설치 과정에서 발생할 수 있는 주요 장애 및 해결 방법을 기술합니다.

---

## 1. 포드 상태 확인

모든 Cilium 관련 포드가 `Running` 상태여야 합니다.
```bash
kubectl get pods -n kube-system -l "app.kubernetes.io/part-of=cilium"
```

## 2. 포트 충돌 이슈 (FailedScheduling)

재설치 시 `0/1 nodes are available: 1 node(s) didn't have free ports...` 에러와 함께 포드가 `Pending` 상태로 머물 수 있습니다.
- **원인**: 이전 Cilium 설치 시 생성된 바이너리 프로세스가 호스트 포트(9234, 9963 등)를 여전히 점유하고 있는 경우입니다.
- **해결**: `install.sh`의 `2) 재설치` 또는 `3) 초기화` 옵션을 사용하면 자동으로 해당 프로세스를 찾아 종료합니다. 

### ⚠️ 주의: 포트를 변경한 경우
만약 `values.yaml`에서 Cilium의 기본 포트를 변경하여 운영 중이라면, **스크립트의 자동 클린업이 작동하지 않습니다.** 이 경우 아래 명령어를 사용하여 직접 포트 점유 여부를 확인하고 종료해야 합니다.

| 컴포넌트 | 기본 포트 | 용도 |
| :--- | :--- | :--- |
| Operator | 9234, 9963 | Health Check, Metrics |
| Agent | 4240, 4244 | Health, Hubble Server |
| Agent API | 9876, 9890 | Local API, Metrics |

**수동 해결 명령어:**
```bash
# 특정 포트(예: 9234)를 사용하는 프로세스 강제 종료
sudo fuser -k -9 9234/tcp
```

## 3. Cilium 에이전트 상태 상세 확인

```bash
kubectl exec -it -n kube-system ds/cilium -- cilium status
```
