---
hide:
  - navigation
  - toc
---

# Infra Cheatsheets

**DevOps 실무를 위한 개인 지식 저장소**
잊어버리기 쉬운 명령어, 설치 절차, 트러블슈팅 가이드를 체계적으로 정리해 두었습니다.

---

[:fontawesome-brands-github: GitHub](https://github.com/kdelphinus/infra-cheatsheets){ .md-button }
[:fontawesome-brands-google-drive: 설치 파일 드라이브](https://drive.google.com/drive/folders/1joMQRpZPWzKgU9BBsdxy3b0qzJMWpBC8?hl=ko/){ .md-button }
[:fontawesome-solid-box-archive: 설치 파일 GitHub](https://github.com/kdelphinus/air-gapped-install-file/){ .md-button }

---

<div class="grid cards" markdown>

- :simple-kubernetes: **Kubernetes**

  ---

  폐쇄망 설치 · Gateway API · 모니터링 · 스토리지

  [Cheat Sheet](k8s/cheatsheet.md) ·
  [폐쇄망 설치](k8s/offline-install/002-k8s-air-gapped-install.md) ·
  [Envoy Gateway](k8s/gateway-api/001-envoy-install.md) ·
  [Prometheus & Grafana](k8s/monitoring/001-kube-prometheus-stack.md)

- :simple-openstack: **OpenStack**

  ---

  Kolla-Ansible 기반 설치 · GPU Passthrough · 운영 가이드

  [Cheat Sheet](openstack/cheatsheet.md) ·
  [설치 가이드](openstack/base/install.md) ·
  [GPU 노드 초기화](openstack/gpu/init-gpu-node.md) ·
  [PCI Passthrough](openstack/gpu/pci-placement.md)

- :material-pipe: **CI/CD**

  ---

  Harbor · GitLab · Jenkins · ArgoCD · Nexus 폐쇄망 구축

  [Harbor 설치](cicd/offline-install/000-harbor-install.md) ·
  [GitLab & Jenkins](cicd/offline-install/001-gitlab_jenkins_install.md) ·
  [ArgoCD](cicd/offline-install/002-argocd-install.md) ·
  [연동 가이드](cicd/offline-install/003-argocd-jenkins-harbor-integration.md)

- :simple-googlecloud: **Cloud (GCP)**

  ---

  Terraform으로 GCP 폐쇄망 환경 구성 및 SDK 치트시트

  [GCP 폐쇄망 환경 구성](cloud/use_terraform_with_gcp.md) ·
  [GCP SDK Cheat Sheet](cloud/gcp-cheatsheet.md)

- :simple-mariadb: **Database**

  ---

  MariaDB Galera Cluster HA 구성 및 폐쇄망 설치

  [Galera Cluster 설치](db/ha/galera-cluster.md) ·
  [장애 복구](db/ha/galera-recovery.md) ·
  [MariaDB 설치](db/install/mariadb-air-gapped-install.md) ·
  [트러블슈팅](db/install/mariadb-troubleshooting.md)

- :simple-ubuntu: **Ubuntu & WSL**

  ---

  개발 환경 초기 설정 및 WSL 네트워크 구성

  [Ubuntu 초기 설정](ubuntu/init-ubuntu-env.md) ·
  [WSL 네트워크 설정](ubuntu/wsl/wsl-network-setting.md)

- :material-bookshelf: **Reference**

  ---

  Git · VSCode · 네트워크 팁 모음

  [Git Cheat Sheet](git/cheatsheet.md) ·
  [VSCode 단축키](ide/vscode_shortcut.md) ·
  [도메인 IP 확인](network/tip/check-domain-ip.md) ·
  [서브넷 & 게이트웨이 확인](network/tip/check-network-subnet.md)

</div>
