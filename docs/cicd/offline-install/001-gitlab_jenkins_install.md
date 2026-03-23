# 🚀 GitLab & Jenkins 오프라인 설치 및 연동 가이드

본 문서는 폐쇄망 Kubernetes 환경에서 **GitLab v18.7**과 **Jenkins v2.528.3**을 설치하고 CI/CD 파이프라인 구축을 위해 상호 연동하는 절차를 정의합니다.

## 📋 구성 명세

| 항목 | 버전 | 용도 |
| :--- | :--- | :--- |
| **GitLab EE** | **v18.7** | 소스 코드 관리 및 형상 관리 |
| **Jenkins** | **v2.528.3** | 빌드 및 배포 자동화 (CI/CD) |
| **Helm Charts** | 최신 stable | 각 컴포넌트 배포용 차트 |

---

## 🛠️ 설치 전제 조건

- Kubernetes 클러스터 구성 완료
- Helm v3.x 설치 완료
- Harbor 레지스트리 접근 가능 (`<NODE_IP>:30002`)
- (도메인 접속 시) Envoy Gateway 또는 Ingress-Nginx 설치 완료

---

## 1단계: 호스트 디렉토리 준비

모든 작업은 각 컴포넌트 루트 디렉토리에서 실행합니다. PV 데이터 저장 경로를 대상 노드에 미리 생성합니다.

```bash
# GitLab 및 Jenkins 컴포넌트 루트에서 실행
chmod +x scripts/setup-host-dirs.sh
./scripts/setup-host-dirs.sh
```

**주요 생성 경로:**
- GitLab: `/data/gitlab` (Config, Data, Redis 등)
- Jenkins: `/data/jenkins_home`, `/data/gradle-cache`

---

## 2단계: 이미지 Harbor 업로드

```bash
# images/upload_images_to_harbor_v3-lite.sh 상단 Config 수정
# HARBOR_REGISTRY: <NODE_IP>:30002

./images/upload_images_to_harbor_v3-lite.sh
```

---

## 3단계: 운영 설정 (values.yaml 및 PV)

설치 전 컴포넌트 루트의 설정 파일들을 환경에 맞게 수정합니다.

| 컴포넌트 | 파일명 | 주요 수정 항목 |
| :--- | :--- | :--- |
| **GitLab** | `values.yaml` | 도메인, 이미지 경로, 리소스 제한 |
| | `manifests/gitlab-pv.yaml` | 노드 이름(`nodeAffinity`), 저장 경로 |
| **Jenkins** | `values.yaml` | 이미지 경로, 리소스 제한, 서비스 타입 |
| | `manifests/pv-volume.yaml` | 노드 이름(`nodeAffinity`), 저장 경로 |

---

## 4단계: 설치 실행 (GitLab & Jenkins)

각 컴포넌트 디렉토리에서 설치 스크립트를 실행합니다.

```bash
# 1. GitLab 설치
cd ~/gitlab-18.7
chmod +x scripts/install.sh
./scripts/install.sh

# 2. Jenkins 설치
cd ~/jenkins-2.528.3
chmod +x scripts/install.sh
./scripts/install.sh
```

**스크립트 주요 기능:**
- 네임스페이스 (`gitlab`, `jenkins`) 생성 및 PV/PVC 적용
- 노드 고정 (NodeSelector) 처리
- Helm 배포 (Harbor 이미지 경로 자동 반영)
- 초기 관리자 비밀번호 자동 출력

---

## 5단계: 초기 접속 및 비밀번호 확인

### 5.1 GitLab 초기 접속

- **URL**: `http://<NODE_IP>` 또는 설정 도메인
- **계정**: `root`
- **비밀번호 확인**:
  ```bash
  kubectl get secret gitlab-gitlab-initial-root-password \
    -n gitlab -o jsonpath="{.data.password}" | base64 -d && echo
  ```

### 5.2 Jenkins 초기 접속

- **URL**: `http://<NODE_IP>:30000` (NodePort)
- **계정**: `admin`
- **비밀번호 확인**:
  ```bash
  kubectl get secret jenkins -n jenkins \
    -o jsonpath="{.data.jenkins-admin-password}" | base64 -d && echo
  ```

---

## 🔗 GitLab-Jenkins 연동 가이드

1. **GitLab Access Token 생성**: Jenkins가 GitLab API에 접근할 수 있도록 Personal Access Token을 발급합니다.
2. **Jenkins GitLab Plugin 설정**: Jenkins 관리 > 시스템 설정에서 GitLab 서버 정보를 등록합니다.
3. **WebHook 설정**: GitLab 프로젝트 설정 > Webhooks에서 Jenkins 빌드 트리거 URL을 등록합니다.

---

## 🗑️ 삭제 (Uninstall)

```bash
./scripts/uninstall.sh
```
