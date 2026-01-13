# 🚀 Infra Cheatsheets

> **DevOps 실무를 위한 개인 지식 저장소 (Knowledge Base)**
> 잊어버리기 쉬운 인프라 설치 절차, 명령어, 트러블슈팅 가이드를 체계적으로 정리하는 공간입니다.

## 🌐 Documentation Site

이 레포지토리의 내용은 **GitHub Pages**를 통해 웹사이트 형태로 배포되고 있습니다.  
가독성 좋은 문서를 보시려면 아래 링크를 방문해 주세요.

### 👉 [Infra cheatsheets의 Github IO 주소](https://kdelphinus.github.io/infra-cheatsheets/)

### 👉 [설치 파일 GitHub](https://github.com/kdelphinus/air-gapped-install-file/)

### 👉 [설치 파일 드라이브](https://drive.google.com/drive/folders/1joMQRpZPWzKgU9BBsdxy3b0qzJMWpBC8?hl=ko/)

## 🛠️ Built With

이 프로젝트는 문서를 코드로 관리(Docs as Code)하기 위해 아래 도구들을 사용합니다.

| Category | Technology | Description |
| :--- | :--- | :--- |
| **Framework** | **MkDocs** | 정적 사이트 생성기 (Static Site Generator) |
| **Theme** | **Material for MkDocs** | 구글 머티리얼 디자인 테마 적용 |
| **Deploy** | **GitHub Actions** | 문서 수정 시 GitHub Pages 자동 배포 |

## 💻 Local Development

로컬 환경에서 문서를 수정하거나 미리보기를 실행하는 방법입니다.

### 1. Prerequisites

Python 3.x 버전이 필요합니다.

### 2. Install Dependencies

```bash
# 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate

# MkDocs 및 Material 테마 설치
pip install mkdocs-material

# 로컬 서버 실행
mkdocs serve
```

명령어 실행 후 브라우저에서 [http://127.0.0.1:8000](http://127.0.0.1:8000)으로 접속하여 실시간 미리보기를 확인할 수 있습니다.
