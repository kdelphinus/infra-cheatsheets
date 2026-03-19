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
- **Gateway API**: [Envoy 설치](k8s/gateway-api/001-envoy-install.md) · [HTTPRoute 설정](k8s/gateway-api/002-convert_ingress_to_httproute.md) · [네트워크 설정](k8s/gateway-api/envoy-gateway-network-config.md) · [ContainerPort 누락 해결](k8s/gateway-api/missed-containerport.md)
- **Storage**: [NAS PV 연결 가이드](k8s/use-pv-nas.md)

### ☁️ Cloud

- [**GCP Cheat Sheet**](cloud/gcp-cheatsheet.md) : Google Cloud SDK 핵심 명령어
- **Terraform**: [GCP 폐쇄망 환경 구성](cloud/use_terraform_with_gcp.md)

### 🚀 CI/CD

- **폐쇄망 설치**: [GitLab & Jenkins](cicd/offline-install/001-gitlab_jenkins_install.md) · [ArgoCD 설치](cicd/offline-install/002-argocd-install.md) · [ArgoCD-Jenkins-Harbor 연동](cicd/offline-install/003-argocd-jenkins-harbor-integration.md)
- **운영**: [Harbor 기반 이미지 재배포](cicd/operation/redeploy-with-new-image.md)

### 🐧 Ubuntu & WSL

- [**Ubuntu 초기 설정**](ubuntu/init-ubuntu-env.md)
- [**WSL 네트워크 설정**](ubuntu/wsl/wsl-network-setting.md)

### 💾 Database

- **HA**: [MariaDB Galera Cluster](db/ha/galera-cluster.md) · [장애 복구](db/ha/galera-recovery.md)
- **폐쇄망 설치**: [MariaDB 설치 파일 준비](db/install/ready-mariadb-air-gapped-install.md) · [트러블슈팅 및 주의사항](db/install/mariadb-troubleshooting.md)

### ☁️ OpenStack

- [**Cheat Sheets**](openstack/cheatsheet.md) : OpenStack CLI 핵심 명령어
- **기본 가이드**: [서비스 목록](openstack/base/reference.md) · [설치 가이드](openstack/base/install.md) · [API 명세](openstack/base/api.md)
- **GPU 설정**: [GPU 노드 초기화](openstack/gpu/init-gpu-node.md) · [PCI Placement](openstack/gpu/pci-placement.md)
- **Troubleshooting**: [K8s 네트워크 통신 장애 해결](openstack/troubleshooting/k8s-network-error.md)
- **Tools**: [Ironic 노드 추가](openstack/tools/add-ironic.md)
- **Utils**: [Cloud-init 설정](openstack/utils/cloud-init.md) · [Golden Image 생성](openstack/utils/golden-image.md)

### 📝 Reference

- **Git**: [Cheat Sheets](git/cheatsheet.md)
- **IDE**: [VSCode 단축키 모음](ide/vscode_shortcut.md)
- **Network**: [도메인 IP 체크](network/tip/check-domain-ip.md) · [네트워크 서브넷 확인](network/tip/check-network-subnet.md)
