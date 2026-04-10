# 🛠️ 컨테이너 이미지 관리 치트시트 (nerdctl, Skopeo, ctr)

Kubernetes 환경(특히 containerd 사용 시)에서 컨테이너 이미지를 관리하고 트러블슈팅하는 데 유용한 도구들의 핵심 명령어 정리입니다.

---

## 1. nerdctl (containerd용 Docker 호환 CLI)

`nerdctl`은 `docker` 명령어와 거의 동일한 사용자 경험을 제공하면서 `containerd`를 직접 제어합니다.

### 기본 명령어 (Docker와 동일)
- **이미지 목록**: `nerdctl images`
- **이미지 풀**: `nerdctl pull <image>`
- **컨테이너 실행**: `nerdctl run -d --name <name> <image>`
- **컨테이너 목록**: `nerdctl ps -a`
- **이미지 빌드**: `nerdctl build -t <tag> .`
- **이미지 태그**: `nerdctl tag <src> <dest>`
- **로그 확인**: `nerdctl logs -f <container>`

### Kubernetes 네임스페이스 관리
Kubernetes에서 사용하는 이미지는 `k8s.io` 네임스페이스에 저장됩니다.
- **K8s 이미지 확인**: `nerdctl -n k8s.io images`
- **K8s 컨테이너 확인**: `nerdctl -n k8s.io ps`

### 이미지 내보내기/가져오기 (Tar)
- **저장**: `nerdctl save -o image.tar <image>`
- **로드**: `nerdctl load -i image.tar`
- **K8s로 로드**: `nerdctl -n k8s.io load -i image.tar`

---

## 2. Skopeo (이미지 및 레지스트리 조작 도구)

`Skopeo`는 컨테이너 엔진(Docker, containerd) 없이도 원격 레지스트리의 이미지를 검사하거나 복사할 수 있는 강력한 도구입니다.

### 이미지 정보 검사 (Inspect)
원격 레지스트리의 이미지를 다운로드하지 않고 메타데이터만 확인합니다.
- **기본**: `skopeo inspect docker://<registry>/<image>:<tag>`
- **인증 필요 시**: `skopeo inspect --creds <user>:<pass> docker://...`
- **TLS 무시**: `skopeo inspect --tls-verify=false docker://...`

### 이미지 복사 (Copy)
레지스트리 간 이미지를 복사하거나, 레지스트리 이미지를 로컬 디렉토리/tar로 저장합니다.
- **레지스트리 ↔ 레지스트리**:
  ```bash
  skopeo copy docker://source.com/img:v1 docker://dest.com/img:v1
  ```
- **레지스트리 → 로컬 Tar (docker-archive)**:
  ```bash
  skopeo copy docker://registry.com/img:v1 docker-archive:img-v1.tar:img:v1
  ```
- **로컬 Tar → 레지스트리**:
  ```bash
  skopeo copy docker-archive:img-v1.tar:img:v1 docker://registry.com/img:v1
  ```

### 이미지 삭제
- **원격 이미지 삭제**: `skopeo delete docker://<registry>/<image>:<tag>`

---

## 3. ctr (containerd 기본 CLI)

`ctr`은 `containerd` 패키지에 포함된 저수준 도구로, 별도의 설치 없이 바로 사용할 수 있지만 사용법이 다소 복잡합니다.

### 이미지 관리
- **이미지 목록**: `ctr images list`
- **K8s 이미지 목록**: `ctr -n k8s.io images list`
- **이미지 풀**: `ctr images pull <image>`
- **이미지 태그**: `ctr images tag <src> <dest>`
- **이미지 삭제**: `ctr images rm <image>`

### 이미지 가져오기/내보내기 (Import/Export)
`save/load` 대신 `export/import` 명령어를 사용합니다.
- **가져오기 (Import)**:
  ```bash
  # K8s 네임스페이스로 이미지 로드 (가장 많이 사용)
  sudo ctr -n k8s.io images import <image>.tar
  ```
- **내보내기 (Export)**:
  ```bash
  sudo ctr images export <image>.tar <image_name>
  ```

### 컨테이너/태스크 관리
- **컨테이너 목록**: `ctr containers list`
- **실행 중인 태스크**: `ctr tasks list`
- **컨테이너 강제 종료**: `ctr tasks kill <container_id>`

---

## 요약 비교

| 기능 | nerdctl | Skopeo | ctr |
| :--- | :--- | :--- | :--- |
| **주요 목적** | Docker 대체, 친화적 UX | 레지스트리 간 복사, 검사 | 저수준 디버깅, 기본 탑재 |
| **K8s 연동** | `-n k8s.io` 사용 | 관련 없음 (레지스트리 중심) | `-n k8s.io` 사용 |
| **이미지 빌드** | 지원 (Buildkit 연동) | 미지원 | 미지원 |
| **로컬 Tar 로드** | `load` | `copy` (docker-archive) | `import` |
