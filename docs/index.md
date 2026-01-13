---
hide:
  - navigation
---

# 🚀 Infra Cheatsheets

**DevOps 실무를 위한 개인 지식 저장소 (Knowledge Base)**  
잊어버리기 쉬운 명령어, 설치 절차, 트러블슈팅 가이드를 체계적으로 정리해 두었습니다.

---

## 🌐 Documentation Site

### 👉 [Infra cheatsheets의 Github 주소](https://github.com/kdelphinus/infra-cheatsheets)

### 👉 [설치 파일 GitHub](https://github.com/kdelphinus/air-gapped-install-file/)

### 👉 [설치 파일 드라이브](https://drive.google.com/drive/folders/1joMQRpZPWzKgU9BBsdxy3b0qzJMWpBC8?hl=ko/)

---

## 📂 Categories

### ☸️ Kubernetes

- [**Cheat Sheets**](k8s/cheatsheet.md) : 자주 사용하는 `kubectl` 명령어 모음
- **폐쇄망 설치**: [준비](k8s/offline-install/001-ready-k8s-air-gapped-install.md) · [K8s 설치](k8s/offline-install/002-k8s-air-gapped-install.md) · [기반 인프라(Helm/Harbor) 구성](k8s/offline-install/003-necessary_infra_install.md)
- **Gateway API**: [Envoy 설치](k8s/gateway-api/001-envoy-install.md) · [HTTPRoute 설정](k8s/gateway-api/002-convert_ingress_to_httproute.md)

### ☁️ OpenStack

- [**Cheat Sheets**](openstack/cheatsheet.md) : OpenStack CLI 핵심 명령어
- **기본 가이드**: [서비스 목록](openstack/base/reference.md) · [설치 가이드](openstack/base/install.md) · [API 명세](openstack/base/api.md)
- **고급 설정**: [GPU 노드 초기화](openstack/gpu/init-gpu-node.md) · [PCI Placement](openstack/gpu/pci-placement.md)
- **Troubleshooting**: [K8s 네트워크 통신 장애 해결](openstack/troubleshooting/k8s-network-error.md)

### 🛠️ DevOps Utilities

- **CI/CD**: [폐쇄망 GitLab & Jenkins 설치](cicd/offline-install/001-gitlab_jenkins_install.md)
- **Database**: [MariaDB Galera Cluster](db/ha/galera-cluster.md) · [폐쇄망 설치 파일 준비](db/install/ready-mariadb-air-gapped-install.md)
- **Ubuntu/WSL**: [초기 환경 설정](ubuntu/init-ubuntu-env.md) · [WSL 네트워크 설정](ubuntu/wsl/wsl-network-setting.md)

### 📝 Reference

- **Git**: [Cheat Sheets](git/cheatsheet.md)
- **IDE**: [VSCode 단축키 모음](ide/vscode_shortcut.md)
- **Network**: [도메인 실제 IP 체크](network/tip/check-domain-ip.md)
