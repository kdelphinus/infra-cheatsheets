# 🚀 GitLab & Jenkins 오프라인 설치 및 연동 가이드

폐쇄망 환경에서 GitLab EE v18.7과 Jenkins v2.528.3을 Kubernetes 위에 설치하고 상호 연동하는 절차를 안내합니다.

## 전제 조건

- Kubernetes 클러스터 구성 완료
- Helm v3.14.0 설치 완료
- `kubectl` CLI 사용 가능
- Harbor 레지스트리 접근 가능 (`<NODE_IP>:30002`)
- 스토리지 클래스(`local-path`) 구성 완료

---

## 1단계: 호스트 디렉토리 및 이미지 준비

모든 작업은 각 컴포넌트(`gitlab/`, `jenkins/`) 루트 디렉토리에서 실행합니다.

### 1.1 데이터 저장 경로 생성 (모든 워커 노드)

```bash
# GitLab 및 Jenkins 데이터 폴더 생성
sudo mkdir -p /data/jenkins_home
sudo mkdir -p /data/gitlab_data
sudo mkdir -p /data/gitlab_pg
sudo mkdir -p /data/gitlab_redis
sudo mkdir -p /data/gradle-cache

sudo chmod -R 777 /data
```

### 1.2 이미지 Harbor 업로드

각 디렉토리의 `images/upload_images_to_harbor_v3-lite.sh`를 실행합니다.

```bash
# GitLab 이미지 업로드
cd ~/gitlab-18.7
./images/upload_images_to_harbor_v3-lite.sh

# Jenkins 이미지 업로드
cd ~/jenkins-2.528.3
./images/upload_images_to_harbor_v3-lite.sh
```

---

## 2단계: GitLab 설치

### 2.1 운영 설정 (values.yaml 및 PV)

`values.yaml`에서 도메인 및 이미지 경로를 수정하고, `manifests/gitlab-pv.yaml`에서 노드 정보를 수정합니다.

### 2.2 설치 실행

```bash
cd ~/gitlab-18.7
chmod +x scripts/install.sh
./scripts/install.sh
```

- **초기 root 비밀번호 확인**:
  ```bash
  kubectl get secret gitlab-gitlab-initial-root-password -n gitlab -o jsonpath="{.data.password}" | base64 -d && echo
  ```

---

## 3단계: Jenkins 설치

### 3.1 운영 설정 (values.yaml 및 PV)

`values.yaml`에서 이미지 경로를 수정하고, `manifests/pv-volume.yaml` 및 `manifests/gradle-cache-pv-pvc.yaml`을 확인합니다.

### 3.2 설치 실행

```bash
cd ~/jenkins-2.528.3
chmod +x scripts/install.sh
./scripts/install.sh
```

- **초기 admin 비밀번호 확인**:
  ```bash
  kubectl get secret jenkins -n jenkins -o jsonpath="{.data.jenkins-admin-password}" | base64 -d && echo
  ```

---

## 4단계: GitLab <-> Jenkins 연동

### 4.1 GitLab: Personal Access Token 발급
- **Preferences > Personal Access Tokens**에서 `api` 스코프의 토큰을 생성합니다.

### 4.2 Jenkins: Credentials 등록
- **GitLab API Token**: 발급받은 토큰 등록
- **GitLab 계정**: 소스 체크아웃용 (ID/PW)
- **Harbor Registry**: 이미지 푸시용 (ID/PW)

### 4.3 Jenkins: 시스템 설정
- **Manage Jenkins > System > GitLab** 섹션에서 Connection 설정
- **GitLab host URL**: 클러스터 내부 주소 사용 (예: `http://gitlab-webservice-default.gitlab.svc.cluster.local:8181`)

### 4.4 Webhook 설정 (GitLab)
- 프로젝트 **Settings > Webhooks**에서 Jenkins Job URL 등록
- **URL**: `http://<JENKINS_INTERNAL_IP>:8080/project/<JOB_NAME>`

---

## 💡 운영 팁

- **리소스 관리**: GitLab은 메모리를 많이 소모하므로 최소 8GB 이상의 여유 공간이 있는 노드에 배치하십시오.
- **도메인 접속**: 사용자 PC의 `hosts` 파일에 게이트웨이 IP와 도메인을 등록해야 합니다.
  `<GATEWAY_IP>  gitlab.devops.internal`
- **에이전트 설정**: Jenkins 관리의 **Nodes and Clouds** 설정에서 K8s 클러스터 연결 정보를 정확히 입력해야 빌드 에이전트 Pod이 생성됩니다.

## 디렉토리 구조 (Standard Structure)

| 경로 | 설명 |
| :--- | :--- |
| `charts/` | Helm 차트 파일 |
| `images/` | 컨테이너 이미지 및 업로드 스크립트 |
| `manifests/` | PV, PVC, HTTPRoute 등 K8s 리소스 |
| `scripts/` | 설치, 삭제, 호스트 준비 스크립트 |

## 삭제

```bash
# 각 디렉토리에서 실행
./scripts/uninstall.sh
```
