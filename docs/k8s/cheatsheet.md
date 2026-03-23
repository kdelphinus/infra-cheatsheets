# ☸️ Kubernetes Cheat Sheet

## 🚀 1. 쉘 자동완성 설정 (Shell Autocomplete)

가장 먼저 설정해야 할 필수 기능입니다.

### bash

```bash
source <(kubectl completion bash) # 현재 세션에 적용
echo "source <(kubectl completion bash)" >> ~/.bashrc # 영구 적용
alias k=kubectl # 'k' 단축키 설정
complete -o default -F __start_kubectl k # 'k' 단축키에도 자동완성 적용
```

### zsh

```zsh
source <(kubectl completion zsh)  # set up autocomplete in zsh into the current shell
echo '[[ $commands[kubectl] ]] && source <(kubectl completion zsh)' >> ~/.zshrc # add autocomplete permanently to your zsh shell
alias k=kubectl
complete -o default -F __start_kubectl k
```

-----

## 📂 2. 클러스터 및 컨텍스트 관리 (Config & Context)

여러 클러스터와 네임스페이스를 관리할 때 사용합니다.

```bash
kubectl config view                        # 전체 kubeconfig 설정 확인
kubectl config get-contexts                # 컨텍스트 목록 확인
kubectl config current-context             # 현재 컨텍스트 확인
kubectl config use-context <name>          # 컨텍스트 변경
kubectl config set-context --current --namespace=<ns>  # 기본 네임스페이스 변경 (매번 -n 입력 생략)
kubectl api-resources                      # 사용 가능한 리소스 종류 및 단축어(Shortnames) 확인
kubectl api-versions                       # 사용 가능한 API 그룹 버전 확인
```

-----

## 🛠 3. 리소스 생성 (Create & Dry Run)

**Best Practice:** YAML 파일을 직접 짜지 말고, 명령어로 뼈대를 만든 후 수정하세요. (`--dry-run=client -o yaml`)

| 리소스 | 명령어 템플릿 |
| :--- | :--- |
| **Pod** | `k run nginx --image=nginx --restart=Never --dry-run=client -o yaml > pod.yaml` |
| **Deployment** | `k create deploy web --image=nginx --replicas=3 --dry-run=client -o yaml > deploy.yaml` |
| **Service** | `k expose deploy web --port=80 --target-port=8080 --type=NodePort --dry-run=client -o yaml > svc.yaml` |
| **CronJob** | `k create cronjob my-job --image=busybox --schedule="*/1 * * * *" --dry-run=client -o yaml > cron.yaml` |
| **Job** | `k create job my-job --image=busybox --dry-run=client -o yaml > job.yaml` |
| **Secret** | `k create secret generic my-pass --from-literal=pwd=123 --dry-run=client -o yaml > sec.yaml` |
| **ConfigMap** | `k create cm my-config --from-file=config.txt --dry-run=client -o yaml > cm.yaml` |

-----

## 🔍 4. 조회 및 필터링 (Get & Inspect)

### 기본 조회

```bash
kubectl get all -n <namespace>   # 특정 네임스페이스 전체 리소스 조회
kubectl get po,svc,deploy        # 주요 리소스만 골라서 조회
kubectl get po -A                # 모든 네임스페이스의 Pod 조회
kubectl get nodes -o wide        # 노드 OS, 커널 버전, 내부 IP 확인
kubectl get events --sort-by=.metadata.creationTimestamp # 시간순 이벤트 조회 (디버깅용)
```

### 출력 형식 (Formatting) & 정렬

```bash
kubectl get po -o wide                       # IP, Node 정보 포함
kubectl get po --show-labels                 # 라벨 정보 포함
kubectl get po -l app=nginx                  # 특정 라벨 필터링
kubectl get po --sort-by=.status.startTime   # 실행 시간순 정렬
kubectl get po -o yaml > backup.yaml         # YAML로 전체 스펙 추출
```

### JSONPath (데이터 추출)

```bash
# 모든 노드의 이름만 추출
kubectl get nodes -o jsonpath='{.items[*].metadata.name}'
# 특정 Pod의 환경변수 확인
kubectl get po <pod> -o jsonpath='{.spec.containers[0].env}'
```

-----

## 🩺 5. 디버깅 및 로그 (Troubleshoot & Logs)

### 로그 분석

```bash
kubectl logs <pod>                           # 로그 확인
kubectl logs -f <pod>                        # 실시간 로그 (tail -f)
kubectl logs <pod> -c <container>            # 특정 컨테이너 로그 (Multi-container)
kubectl logs <pod> --previous                # 이전 컨테이너(Crash난 직후) 로그 확인
kubectl logs -l app=backend --all-containers=true # 해당 라벨을 가진 모든 Pod 로그
```

### 상태 진단

```bash
kubectl describe pod <pod>                   # Pod 상세 상태 및 이벤트(Events) 확인 (★필수)
kubectl describe node <node>                 # 노드 리소스 부족/상태 확인
kubectl top pods                             # Pod별 CPU/Memory 사용량 (Metrics Server 필요)
kubectl top nodes                            # 노드별 리소스 사용량
```

### 접속 및 실행

```bash
kubectl exec -it <pod> -- /bin/bash          # 컨테이너 쉘 접속
kubectl exec -it <pod> -- ls -F /app         # 접속 없이 명령어만 실행
kubectl cp <pod>:/path/file ./local_file     # 파일 복사 (Pod -> Local)
kubectl cp ./local_file <pod>:/path/file     # 파일 복사 (Local -> Pod)
```

### 임시 디버깅 Pod 실행

```bash
# 네트워크 테스트용(curl, nslookup 등) 임시 Pod 실행 후 삭제
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
```

-----

## 🔄 6. 앱 관리 및 스케일링 (Deploy & Scale)

### 업데이트 및 롤백

```bash
kubectl set image deploy/<name> nginx=nginx:1.19 # 이미지 버전 업데이트 (롤링 업데이트)
kubectl rollout status deploy/<name>         # 배포 진행 상태 확인
kubectl rollout history deploy/<name>        # 배포 이력(Revision) 확인
kubectl rollout undo deploy/<name>           # 바로 이전 버전으로 롤백
kubectl rollout undo deploy/<name> --to-revision=2 # 특정 버전으로 롤백
kubectl rollout pause deploy/<name>          # 배포 일시 정지
kubectl rollout resume deploy/<name>         # 배포 재개
```

### 스케일링 (Scaling)

```bash
kubectl scale deploy/<name> --replicas=5     # 수동 스케일링
kubectl autoscale deploy/<name> --min=2 --max=10 --cpu-percent=80 # HPA(Auto Scaling) 설정
```

-----

## 🌐 7. 네트워크 (Networking)

```bash
kubectl get svc -o wide                      # 서비스 ClusterIP, Selector 확인
kubectl get ing                              # 인그레스(Ingress) 주소 확인
kubectl get endpoints <svc-name>             # 서비스와 연결된 실제 Pod IP(Endpoint) 확인
kubectl port-forward <pod> 8080:80           # 로컬 포트 포워딩 (Pod)
kubectl port-forward svc/<name> 8080:80      # 로컬 포트 포워딩 (Service)
```

-----

## 🗑 8. 삭제 및 정리 (Delete & Clean up)

```bash
kubectl delete -f filename.yaml              # 파일 기준 삭제
kubectl delete po <pod>                      # Pod 삭제
kubectl delete po -l app=nginx               # 라벨 기준 일괄 삭제
kubectl delete ns <name>                     # 네임스페이스 삭제 (내부 리소스 전체 삭제됨)
# [강제 삭제] 종료(Terminating) 상태에서 멈춘 Pod 삭제
kubectl delete pod <pod> --grace-period=0 --force
```

-----

## 🏗 9. 노드 유지보수 (Node Maintenance) - 관리자용

```bash
kubectl cordon <node>                        # 스케줄링 중단 (신규 Pod 배치 금지)
kubectl uncordon <node>                      # 스케줄링 재개
kubectl drain <node> --ignore-daemonsets     # 노드 비우기 (기존 Pod를 다른 노드로 이동)
kubectl taint nodes <node> key=value:NoSchedule # 테인트 설정 (특정 Pod만 오게 함)
```

-----

## 🔐 10. 보안, 권한 및 토큰 관리 (Security, Auth & Tokens)

내부 권한 확인(RBAC)과 만료된 클라우드(CSP) 인증 토큰을 갱신하는 필수 명령어입니다.

### 👨‍👩‍👧‍👦 역할 확인

```bash
kubectl get serviceaccounts                  # 서비스 어카운트 목록
kubectl get clusterroles                     # 클러스터 권한 목록
```

### ☁️ 클라우드(CSP) 인증 토큰 갱신 (Token Expired 해결)

*"You must be logged in to the server"* 에러가 뜰 때, 각 클라우드 CLI로 `kubeconfig`를 갱신합니다.

```bash
# AWS EKS (Amazon)
aws eks update-kubeconfig --name <cluster-name> --region <region>

# GCP GKE (Google)
gcloud container clusters get-credentials <cluster-name> --region <region>

# Azure AKS (Microsoft)
az aks get-credentials --resource-group <rg-name> --name <cluster-name>
```

### 🔑 서비스 어카운트 토큰 관리 (Service Account)

CI/CD 연동이나 대시보드 로그인용 토큰을 발급합니다. (K8s v1.24+ 필수)

```bash
# [Modern] 토큰 즉시 발급 (유효기간 설정 가능)
kubectl create token <service-account-name> --duration=24h

# [Legacy] 기존 Secret 기반 토큰 추출 (Base64 디코딩)
kubectl get secret <secret-name> -o jsonpath='{.data.token}' | base64 --decode
```

### 🛡️ 권한 확인 (RBAC Check)

현재 사용자나 특정 계정이 작업을 수행할 권한이 있는지 확인합니다.

```bash
# "내가 배포(Deployment)를 만들 수 있나?" (Yes/No 반환)
kubectl auth can-i create deployments

# 특정 네임스페이스에서 권한 확인
kubectl auth can-i delete pods -n <namespace>

# [관리자용] 특정 서비스 어카운트(sa)가 권한이 있는지 확인 (impersonate)
kubectl auth can-i get nodes --as=system:serviceaccount:<ns>:<sa-name>
```

### 🎫 클러스터 조인 토큰 (Kubeadm 전용)

온프레미스(On-premise) 환경에서 노드를 추가할 때 사용합니다.

```bash
# 유효한 조인 토큰 목록 확인
kubeadm token list

# 토큰이 만료되었을 때 재생성 (조인 명령어 전체 출력)
kubeadm token create --print-join-command
```

-----

### 💡 팁 (Tips)

- **리소스가 안 지워질 때:** `finalizers` 설정 때문일 수 있습니다. `kubectl edit`으로 `finalizers` 항목을 지우면 삭제됩니다.
- **YAML 추출 습관:** 운영 중인 리소스를 수정하기 전에 반드시 `kubectl get <resource> -o yaml > backup.yaml`로 백업하세요.
- **Watch 모드:** 배포 후 `kubectl get pods -w`를 켜두면 상태 변화를 실시간으로 볼 수 있어 답답함이 줄어듭니다.

-----

## ⚓ Helm Essential Cheat Sheet (Bonus)

Kubernetes의 `apt`나 `yum` 같은 패키지 매니저, Helm의 필수 명령어입니다.

### 1. 저장소(Repo) 관리

차트(패키지)를 다운로드할 저장소를 관리합니다.

```bash
helm repo add <name> <url>       # 저장소 추가 (예: bitnami https://charts.bitnami.com/bitnami)
helm repo update                 # 저장소 최신 정보 갱신 (apt update와 동일)
helm repo list                   # 등록된 저장소 목록 확인
helm search repo <keyword>       # 차트 검색 (예: helm search repo nginx)
```

### 2. 설치 및 관리 (Install & Manage)

애플리케이션(Release)을 설치하고 업그레이드합니다.

```bash
# 차트 설치 (기본)
helm install <release-name> <repo/chart>
# 예: helm install my-nginx bitnami/nginx

# 특정 네임스페이스에 설치하며 네임스페이스 자동 생성
helm install <release-name> <repo/chart> -n <ns> --create-namespace

# 설정 값(values.yaml)을 변경하며 설치
helm install <release-name> <repo/chart> --set replicaCount=3

# 사용자 정의 values 파일로 설치
helm install <release-name> <repo/chart> -f values.yaml

# 배포된 앱 목록 확인
helm list -A  # 모든 네임스페이스 조회
```

### 3. 업그레이드 및 삭제 (Upgrade & Uninstall)

```bash
# 차트 버전 업그레이드 또는 설정 변경
helm upgrade <release-name> <repo/chart> -f new-values.yaml

# 배포된 앱 삭제
helm uninstall <release-name>
```

### 4. 디버깅 및 검증 (Debug & Verify)

**Pro Tip:** `helm template`은 실제로 클러스터에 설치하지 않고, 생성될 YAML 파일만 미리 보여줍니다. (`--dry-run`과 유사)

```bash
# 렌더링될 YAML 미리보기 (설치 전 검증 필수 단계)
helm template <release-name> <repo/chart> -f values.yaml > result.yaml

# 현재 실행 중인 릴리즈의 적용된 values 값 확인
helm get values <release-name>

# 현재 실행 중인 릴리즈의 전체 Manifest 확인
helm get manifest <release-name>

# 릴리즈의 배포 이력 및 상태 확인
helm status <release-name>
```
