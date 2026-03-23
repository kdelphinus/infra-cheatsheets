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

  `kubectl` 치트시트부터 폐쇄망 설치, Gateway API, 모니터링까지

  **폐쇄망 설치 (v1.30 / Rocky 9)**

  [준비](k8s/offline-install/001-ready-k8s-air-gapped-install.md) ·
  [K8s 설치 (HA)](k8s/offline-install/002-k8s-air-gapped-install.md) ·
  [기반 인프라](k8s/offline-install/003-necessary_infra_install.md) ·
  [MetalLB](k8s/offline-install/004-metallb-install.md)

  **Gateway API**

  [Ingress-Nginx](k8s/gateway-api/000-ingress-nginx-install.md) ·
  [Envoy Gateway](k8s/gateway-api/001-envoy-install.md) ·
  [운영 체크리스트](k8s/gateway-api/envoy-ops-checklist.md) ·
  [HTTPRoute](k8s/gateway-api/002-convert_ingress_to_httproute.md) ·
  [네트워크 구성](k8s/gateway-api/envoy-gateway-network-config.md)

  **기타**

  [Prometheus & Grafana](k8s/monitoring/001-kube-prometheus-stack.md) ·
  [Velero 백업](k8s/backup-restore/001-velero-install.md) ·
  [NFS Provisioner](k8s/use-pv-nas.md) ·
  [Cheat Sheet](k8s/cheatsheet.md)

- :simple-openstack: **OpenStack**

  ---

  Kolla-Ansible 기반 설치, GPU Passthrough, API 가이드

  **기본 가이드**

  [서비스 목록](openstack/base/reference.md) ·
  [설치 가이드](openstack/base/install.md) ·
  [API 명세](openstack/base/api.md) ·
  [Cheat Sheet](openstack/cheatsheet.md)

  **GPU 설정**

  [GPU 노드 초기화](openstack/gpu/init-gpu-node.md) ·
  [PCI Passthrough + Placement](openstack/gpu/pci-placement.md)

  **운영 & 트러블슈팅**

  [Cloud-init 설정](openstack/utils/cloud-init.md) ·
  [Golden Image 생성](openstack/utils/golden-image.md) ·
  [K8s 네트워크 장애 해결](openstack/troubleshooting/k8s-network-error.md) ·
  [Ironic 노드 추가](openstack/tools/add-ironic.md)

- :simple-cicd: **CI/CD**

  ---

  Harbor, GitLab, Jenkins, ArgoCD, Nexus 폐쇄망 구축 가이드

  **폐쇄망 설치**

  [Harbor](cicd/offline-install/000-harbor-install.md) ·
  [GitLab & Jenkins](cicd/offline-install/001-gitlab_jenkins_install.md) ·
  [ArgoCD](cicd/offline-install/002-argocd-install.md) ·
  [Nexus](cicd/offline-install/004-nexus-install.md)

  **연동 & 운영**

  [ArgoCD · Jenkins · Harbor 연동](cicd/offline-install/003-argocd-jenkins-harbor-integration.md) ·
  [이미지 업데이트 재배포](cicd/operation/redeploy-with-new-image.md)

- :simple-googlecloud: **Cloud (GCP)**

  ---

  Terraform으로 GCP 폐쇄망 환경 구성 및 SDK 치트시트

  [GCP 폐쇄망 환경 구성](cloud/use_terraform_with_gcp.md) ·
  [GCP SDK Cheat Sheet](cloud/gcp-cheatsheet.md)

- :simple-mariadb: **Database**

  ---

  MariaDB Galera Cluster HA 구성 및 폐쇄망 설치

  **HA 구성**

  [Galera Cluster 설치](db/ha/galera-cluster.md) ·
  [장애 복구 가이드](db/ha/galera-recovery.md)

  **폐쇄망 설치**

  [파일 준비](db/install/ready-mariadb-air-gapped-install.md) ·
  [MariaDB 설치](db/install/mariadb-air-gapped-install.md) ·
  [트러블슈팅](db/install/mariadb-troubleshooting.md)

- :simple-ubuntu: **Ubuntu & WSL**

  ---

  개발 환경 초기 설정 및 WSL 네트워크 구성

  [Ubuntu 초기 설정](ubuntu/init-ubuntu-env.md) ·
  [WSL 네트워크 설정](ubuntu/wsl/wsl-network-setting.md)

- :material-bookshelf: **Reference**

  ---

  자주 찾는 치트시트 & 팁

  [Git Cheat Sheet](git/cheatsheet.md) ·
  [VSCode 단축키](ide/vscode_shortcut.md) ·
  [도메인 IP 확인](network/tip/check-domain-ip.md) ·
  [서브넷 & 게이트웨이 확인](network/tip/check-network-subnet.md)

</div>
