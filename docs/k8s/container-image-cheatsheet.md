# 컨테이너 이미지 관리 치트시트 (nerdctl, Skopeo, ctr)

Kubernetes 환경(특히 containerd 사용 시)에서 컨테이너 이미지를 관리하고 트러블슈팅하는 데 유용한 도구들의 핵심 명령어 정리입니다.

---

## 1. nerdctl (containerd용 Docker 호환 CLI)

`nerdctl`은 `docker` 명령어와 거의 동일한 사용자 경험을 제공하면서 `containerd`를 직접 제어합니다.

### 기본 명령어 (Docker와 동일)

| 명령어 | 설명 |
| :--- | :--- |
| `nerdctl images` | 이미지 목록 |
| `nerdctl pull <image>` | 이미지 다운로드 |
| `nerdctl push <image>` | 이미지 업로드 |
| `nerdctl tag <src> <dest>` | 이미지 태그 지정 |
| `nerdctl run -d --name <name> <image>` | 컨테이너 백그라운드 실행 |
| `nerdctl ps -a` | 전체 컨테이너 목록 |
| `nerdctl build -t <tag> .` | 이미지 빌드 |
| `nerdctl logs -f <container>` | 컨테이너 로그 실시간 확인 |
| `nerdctl rm -f <container>` | 컨테이너 강제 삭제 |
| `nerdctl rmi <image>` | 이미지 삭제 |

### Kubernetes 네임스페이스 관리

Kubernetes에서 사용하는 이미지는 `k8s.io` 네임스페이스에 저장됩니다.
일반 `nerdctl images` 명령은 이 이미지를 보여주지 않으므로 `-n k8s.io` 옵션을 반드시 붙여야 합니다.

```bash
# K8s 이미지 목록 확인
sudo nerdctl -n k8s.io images

# K8s 실행 중인 컨테이너 확인
sudo nerdctl -n k8s.io ps
```

### Harbor(사설 레지스트리) 연동

```bash
# HTTP(insecure) Harbor 로그인
nerdctl login --insecure-registry <NODE_IP>:30002 -u admin -p password

# HTTPS Harbor 로그인
nerdctl login harbor.example.com -u admin -p password

# 이미지 pull (insecure)
sudo nerdctl -n k8s.io pull --insecure-registry <NODE_IP>:30002/library/myapp:1.0.0

# 이미지 태그 후 Harbor push (insecure)
nerdctl tag myapp:1.0.0 <NODE_IP>:30002/library/myapp:1.0.0
nerdctl push --insecure-registry <NODE_IP>:30002/library/myapp:1.0.0

# 로그아웃
nerdctl logout <NODE_IP>:30002
```

### 이미지 내보내기/가져오기 (Tar)

```bash
# 이미지 저장 (tar)
nerdctl save -o myapp_v1.tar myapp:1.0.0

# 이미지 로드
nerdctl load -i myapp_v1.tar

# K8s 네임스페이스(k8s.io)에 직접 로드
sudo nerdctl -n k8s.io load -i myapp_v1.tar
```

### Rootless 모드 지원 스크립트

`nerdctl` 전체 패키지(`nerdctl-full-*.tar.gz`)에 포함된 스크립트로 `root` 없이 컨테이너를 운영할 수 있습니다.

- **`containerd-rootless-setuptool.sh`**: Rootless 환경 설정 도구 (체크, 서비스 등록 등)
- **`containerd-rootless.sh`**: 루트리스 환경에서 `containerd`를 실행하는 래퍼 스크립트

---

## 2. Skopeo (이미지 및 레지스트리 조작 도구)

`Skopeo`는 컨테이너 엔진(Docker, containerd) 없이도 원격 레지스트리의 이미지를 검사하거나 복사할 수 있는 강력한 도구입니다.

### 이미지 정보 검사 (Inspect)

원격 레지스트리의 이미지를 다운로드하지 않고 메타데이터만 확인합니다.

```bash
# 기본 검사
skopeo inspect docker://docker.io/library/nginx:latest

# HTTPS Harbor (인증 필요)
skopeo inspect \
    --creds admin:password \
    docker://harbor.example.com/myproject/myapp:v1.0

# HTTP(insecure) Harbor (인증 필요)
skopeo inspect \
    --tls-verify=false \
    --creds admin:password \
    docker://192.168.1.10:30002/myproject/myapp:v1.0

# 특정 필드만 출력 (jq 활용)
skopeo inspect --tls-verify=false \
    docker://192.168.1.10:30002/myproject/myapp:v1.0 \
    | jq '.Layers | length'
```

### 이미지 태그 목록 조회 (list-tags)

Harbor에서 특정 이미지의 전체 태그 목록을 확인할 때 유용합니다.

```bash
# 공개 레지스트리
skopeo list-tags docker://docker.io/library/nginx

# Harbor (insecure)
skopeo list-tags \
    --tls-verify=false \
    docker://192.168.1.10:30002/library/myapp

# Harbor (인증 필요)
skopeo list-tags \
    --tls-verify=false \
    --creds admin:password \
    docker://192.168.1.10:30002/secret-project/myapp
```

### 이미지 복사 (Copy)

레지스트리 간 이미지를 복사하거나, 레지스트리 이미지를 로컬 tar로 저장합니다.

#### 레지스트리 → 레지스트리

```bash
# 공개 레지스트리 → Harbor (insecure)
skopeo copy \
    docker://docker.io/library/nginx:1.25 \
    --dest-tls-verify=false \
    --dest-creds admin:password \
    docker://192.168.1.10:30002/library/nginx:1.25

# Harbor → Harbor (둘 다 insecure)
skopeo copy \
    --src-tls-verify=false \
    --src-creds admin:srcpassword \
    --dest-tls-verify=false \
    --dest-creds admin:destpassword \
    docker://src-harbor.example.com/myproject/myapp:v1.0 \
    docker://dest-harbor.example.com/myproject/myapp:v1.0
```

#### 레지스트리 → 로컬 Tar

Harbor에서 인증이 필요한 이미지를 로컬 tar 파일로 추출하는 가장 일반적인 패턴입니다.

```bash
# Harbor: secret-project/my-app:v1.0 → 로컬 tar
# docker-archive 형식: <출력파일>:<저장할 이미지명>:<태그>
skopeo copy \
    --src-creds admin:password \
    docker://harbor.example.com/secret-project/my-app:v1.0 \
    docker-archive:my-app_v1.0.tar:my-app:v1.0

# insecure Harbor에서 추출
skopeo copy \
    --src-tls-verify=false \
    --src-creds admin:password \
    docker://192.168.1.10:30002/secret-project/my-app:v1.0 \
    docker-archive:my-app_v1.0.tar:my-app:v1.0
```

> `docker-archive` 포맷의 세 번째 필드(`my-app:v1.0`)는 tar 내부에 저장되는 이름과 태그입니다.
> 이 값을 지정하지 않으면 `docker load` 또는 `ctr import` 후 이미지 이름이 비어 있을 수 있습니다.

#### 로컬 Tar → 레지스트리

```bash
# 로컬 tar → Harbor (insecure)
skopeo copy \
    docker-archive:my-app_v1.0.tar \
    --dest-tls-verify=false \
    --dest-creds admin:password \
    docker://192.168.1.10:30002/library/my-app:v1.0
```

#### OCI 디렉토리 형식 (멀티 아키텍처)

```bash
# 레지스트리 → OCI 디렉토리 (멀티 아키텍처 포함)
skopeo copy --multi-arch all \
    docker://docker.io/library/nginx:latest \
    oci:./nginx-oci-dir:latest

# OCI 디렉토리 → 레지스트리
skopeo copy \
    oci:./nginx-oci-dir:latest \
    --dest-tls-verify=false \
    docker://192.168.1.10:30002/library/nginx:latest
```

### 이미지 삭제

```bash
# Harbor에서 이미지 삭제
skopeo delete \
    --tls-verify=false \
    --creds admin:password \
    docker://192.168.1.10:30002/library/myapp:v1.0
```

---

## 3. ctr (containerd 기본 CLI)

`ctr`은 `containerd` 패키지에 포함된 저수준 도구로, 별도의 설치 없이 바로 사용할 수 있지만 사용법이 다소 복잡합니다.

### 이미지 관리

```bash
# 이미지 목록 (전체 네임스페이스)
sudo ctr -n k8s.io images list

# 이미지명 필터링
sudo ctr -n k8s.io images list | grep kube-apiserver

# 이미지 pull (인증 필요 시)
sudo ctr -n k8s.io images pull \
    --user admin:password \
    192.168.1.10:30002/library/myapp:v1.0

# 이미지 pull (insecure)
sudo ctr -n k8s.io images pull \
    --plain-http \
    --user admin:password \
    192.168.1.10:30002/library/myapp:v1.0

# 이미지 태그
sudo ctr -n k8s.io images tag \
    docker.io/library/nginx:latest \
    192.168.1.10:30002/library/nginx:latest

# 이미지 삭제
sudo ctr -n k8s.io images rm docker.io/library/nginx:latest
```

### 이미지 가져오기/내보내기 (Import/Export)

```bash
# tar 파일 → k8s.io 네임스페이스로 로드 (가장 많이 사용)
sudo ctr -n k8s.io images import myapp_v1.tar

# 특정 플랫폼만 로드 (멀티아치 tar인 경우)
sudo ctr -n k8s.io images import --platform linux/amd64 myapp_v1.tar

# 이미지 내보내기 (export)
sudo ctr -n k8s.io images export myapp_v1.tar myapp:v1.0
```

### 이미지 push

```bash
# Harbor로 push (insecure)
sudo ctr -n k8s.io images push \
    --plain-http \
    --user admin:password \
    192.168.1.10:30002/library/myapp:v1.0

# 특정 플랫폼만 push
sudo ctr -n k8s.io images push \
    --plain-http \
    --platform linux/amd64 \
    --user admin:password \
    192.168.1.10:30002/library/myapp:v1.0
```

### 컨테이너/태스크 관리

```bash
# 컨테이너 목록
sudo ctr -n k8s.io containers list

# 실행 중인 태스크(프로세스) 목록
sudo ctr -n k8s.io tasks list

# 컨테이너 강제 종료
sudo ctr -n k8s.io tasks kill <container_id>
```

---

## 4. crictl (CRI 표준 디버깅 CLI)

`crictl`은 `cri-tools` 패키지에 포함된 CRI(Container Runtime Interface) 전용 CLI입니다.
kubeadm 설치 시 의존성으로 자동 설치되므로 **별도 설치가 필요 없습니다.**

`ctr`과 달리 **kubelet 관점**에서 Pod·컨테이너를 조회하므로, 실행 중인 파드를 직접 확인하거나
kubelet이 인식하는 상태를 점검할 때 적합합니다.

### 초기 설정 (containerd 소켓 지정)

설정 없이 실행하면 여러 소켓을 순서대로 탐색합니다. containerd 환경에서 명시적으로 고정하려면 아래와 같이 설정합니다.

```bash
# 설정 파일로 고정 (권장)
sudo tee /etc/crictl.yaml <<EOF
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 10
debug: false
EOF

# 또는 명령어마다 직접 지정
crictl --runtime-endpoint unix:///run/containerd/containerd.sock images
```

### 이미지 관리

```bash
# 이미지 목록
sudo crictl images

# 이미지명 필터링
sudo crictl images | grep kube-apiserver

# 이미지 pull
sudo crictl pull 192.168.1.10:30002/library/myapp:v1.0

# 이미지 삭제
sudo crictl rmi 192.168.1.10:30002/library/myapp:v1.0
```

### Pod 및 컨테이너 조회

`crictl`의 핵심 기능입니다. `kubectl`이 접근 불가한 상황에서도 노드의 Pod 상태를 직접 확인할 수 있습니다.

```bash
# 실행 중인 Pod 목록
sudo crictl pods

# 전체 Pod (종료 포함)
sudo crictl pods --state all

# 특정 네임스페이스 Pod 필터링
sudo crictl pods --namespace kube-system

# 특정 Pod 상세 정보
sudo crictl inspectp <pod_id>

# 실행 중인 컨테이너 목록
sudo crictl ps

# 전체 컨테이너 (종료 포함)
sudo crictl ps -a

# 특정 컨테이너 상세 정보
sudo crictl inspect <container_id>
```

### 로그 및 exec

```bash
# 컨테이너 로그 확인
sudo crictl logs <container_id>

# 실시간 로그 스트림
sudo crictl logs -f <container_id>

# 컨테이너 내부 명령 실행
sudo crictl exec -it <container_id> /bin/sh
```

### 리소스 사용량

```bash
# 컨테이너 CPU/메모리 사용량
sudo crictl stats

# 특정 컨테이너만 확인
sudo crictl stats <container_id>
```

### ctr vs crictl 차이점

| 구분 | ctr | crictl |
| :--- | :--- | :--- |
| **포함 패키지** | containerd | cri-tools (kubeadm 의존성) |
| **관점** | containerd 내부 (네임스페이스 직접 지정) | kubelet/CRI 표준 (Pod 단위) |
| **Pod 조회** | 불가 | `crictl pods` |
| **주 용도** | 이미지 import/export, 저수준 디버깅 | Pod·컨테이너 상태 점검, exec, 로그 |

---

## 요약 비교

| 기능 | nerdctl | Skopeo | ctr | crictl |
| :--- | :--- | :--- | :--- | :--- |
| **주요 목적** | Docker 대체, 친화적 UX | 레지스트리 간 복사·검사 | 저수준 디버깅, 기본 탑재 | Pod·컨테이너 상태 점검 |
| **별도 설치** | 필요 | 필요 | 불필요 (containerd 포함) | 불필요 (kubeadm 의존성) |
| **K8s 연동** | `-n k8s.io` | 관련 없음 (레지스트리 중심) | `-n k8s.io` | Pod 단위 조회 지원 |
| **이미지 빌드** | 지원 (Buildkit 연동) | 미지원 | 미지원 | 미지원 |
| **로컬 Tar 로드** | `load` | `copy docker-archive:` | `import` | 미지원 |
| **태그 목록 조회** | 미지원 | `list-tags` | 미지원 | 미지원 |
| **인증(creds) 옵션** | `login` 또는 `--insecure-registry` | `--creds user:pass` | `--user user:pass` | pull 시 인증 미지원 |
| **insecure 레지스트리** | `--insecure-registry` | `--tls-verify=false` | `--plain-http` | `/etc/crictl.yaml` 설정 |
| **멀티 아키텍처** | 제한적 | `--multi-arch all` | `--platform` | 미지원 |
| **Pod 조회** | 미지원 | 미지원 | 미지원 | `crictl pods` |
| **exec / 로그** | 지원 | 미지원 | 미지원 | `exec`, `logs` |

---

## 아키텍처 관점에서 본 도구 선택

### 왜 도구가 이렇게 많은가?

과거 Docker가 이미지 빌드·실행·배포·레지스트리 연동을 혼자 담당하던 구조는 단일 장애점이자 보안 리스크였습니다.
현대 컨테이너 생태계는 이 역할을 **OCI 표준** 위에서 전문 도구로 분리했습니다.

| 역할 | 담당 도구 | 비고 |
| :--- | :--- | :--- |
| 컨테이너 런타임 | containerd | kubelet이 CRI를 통해 직접 호출 |
| 런타임 진단 | ctr, crictl | containerd 내부 vs CRI(Pod) 관점 |
| 이미지 관리·이관 | nerdctl, Skopeo | UX 중심 vs 레지스트리 중심 |

이 분리 덕분에 각 레이어를 독립적으로 업그레이드하거나 교체할 수 있고, 보안 취약점의 영향 범위도 좁아집니다.

### 도구별 핵심 강점

**Skopeo — 이미지 이관의 핵심**

데몬 없이 동작하므로 containerd나 Docker가 없는 환경에서도 실행됩니다.
외부망에서 이미지를 tar로 추출하거나 레지스트리 간 직접 복사할 때 가장 가볍고 빠릅니다.
Harbor 프로젝트명 변환, 인증이 필요한 레지스트리 접근 등 CI/CD 파이프라인에서도 즐겨 쓰입니다.

```bash
# 외부 레지스트리 → 로컬 tar (Harbor 인증 포함)
skopeo copy \
    --src-creds admin:password \
    docker://harbor.example.com/secret-project/my-app:v1.0 \
    docker-archive:my-app_v1.0.tar:my-app:v1.0
```

**nerdctl — containerd 환경의 Docker 대체**

`docker` 명령어를 그대로 사용할 수 있어 진입 장벽이 낮습니다.
`buildkitd`와 결합하면 폐쇄망 노드 안에서도 이미지를 직접 빌드할 수 있습니다.
`-n k8s.io` 옵션으로 kubeadm 클러스터의 이미지 네임스페이스에도 접근합니다.

**crictl — K8s 노드 상태 점검의 기준**

kubelet이 CRI를 통해 보는 것과 동일한 관점으로 Pod·컨테이너 상태를 확인합니다.
`kubectl`이 동작하지 않는 장애 상황에서 노드의 실제 상태를 파악하는 1순위 도구입니다.
이미지 tag·push 기능은 없으므로 순수 진단 용도로만 사용합니다.

**ctr — 최후의 수단**

containerd에 기본 탑재되어 있어 어떤 환경에서도 사용 가능합니다.
다른 도구가 모두 실패했을 때 런타임 내부를 직접 조작하거나, tar 이미지를 강제로 import할 때 씁니다.
`-n k8s.io`를 명시하지 않으면 기본 네임스페이스(`default`)를 바라보므로 K8s 환경에서는 반드시 붙여야 합니다.

> **Podman**은 데몬 없는 보안 컨테이너 엔진으로, rootless 운영이나 K8s YAML 생성(`podman generate kube`)이 필요한 경우 도입을 검토합니다. 위 네 도구와 용도가 겹치지 않으므로 이 문서의 범위에서는 제외했습니다.

### 권장 워크플로우

```text
[외부망] 이미지 반출·정제
  └─ Skopeo copy → tar 파일 생성 (프로젝트명 정리, 인증 처리)

[내부망] 이미지 배포
  └─ ctr import  → containerd(k8s.io)에 로드
  └─ nerdctl push → Harbor로 업로드

[운영 중] 상태 점검
  └─ crictl pods / crictl ps  → kubelet 관점의 Pod·컨테이너 확인
  └─ nerdctl -n k8s.io images → 이미지 목록 확인
  └─ ctr (최후 수단)          → 런타임 직접 조작
```
