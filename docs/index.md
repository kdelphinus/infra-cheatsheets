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

  [:octicons-arrow-right-24: Cheat Sheet](k8s/cheatsheet.md)<br>
  [:octicons-arrow-right-24: 폐쇄망 설치 (v1.30)](k8s/offline-install/002-k8s-air-gapped-install.md)<br>
  [:octicons-arrow-right-24: Envoy Gateway 설치](k8s/gateway-api/001-envoy-install.md)<br>
  [:octicons-arrow-right-24: HTTPRoute 설정](k8s/gateway-api/002-convert_ingress_to_httproute.md)<br>
  [:octicons-arrow-right-24: Prometheus & Grafana](k8s/monitoring/001-kube-prometheus-stack.md)<br>
  [:octicons-arrow-right-24: Velero 백업](k8s/backup-restore/001-velero-install.md)

- :simple-openstack: **OpenStack**

  ---

  [:octicons-arrow-right-24: Cheat Sheet](openstack/cheatsheet.md)<br>
  [:octicons-arrow-right-24: 설치 가이드](openstack/base/install.md)<br>
  [:octicons-arrow-right-24: GPU 노드 초기화](openstack/gpu/init-gpu-node.md)<br>
  [:octicons-arrow-right-24: PCI Passthrough + Placement](openstack/gpu/pci-placement.md)<br>
  [:octicons-arrow-right-24: Golden Image 생성](openstack/utils/golden-image.md)<br>
  [:octicons-arrow-right-24: K8s 네트워크 장애 해결](openstack/troubleshooting/k8s-network-error.md)

- :material-pipe: **CI/CD**

  ---

  [:octicons-arrow-right-24: Harbor 설치](cicd/offline-install/000-harbor-install.md)<br>
  [:octicons-arrow-right-24: GitLab & Jenkins 설치](cicd/offline-install/001-gitlab_jenkins_install.md)<br>
  [:octicons-arrow-right-24: ArgoCD 설치](cicd/offline-install/002-argocd-install.md)<br>
  [:octicons-arrow-right-24: ArgoCD · Jenkins · Harbor 연동](cicd/offline-install/003-argocd-jenkins-harbor-integration.md)<br>
  [:octicons-arrow-right-24: Nexus 설치](cicd/offline-install/004-nexus-install.md)<br>
  [:octicons-arrow-right-24: 이미지 업데이트 재배포](cicd/operation/redeploy-with-new-image.md)

- :simple-mariadb: **Database**

  ---

  [:octicons-arrow-right-24: Galera Cluster 설치](db/ha/galera-cluster.md)<br>
  [:octicons-arrow-right-24: Galera 장애 복구](db/ha/galera-recovery.md)<br>
  [:octicons-arrow-right-24: MariaDB 폐쇄망 설치](db/install/mariadb-air-gapped-install.md)<br>
  [:octicons-arrow-right-24: MariaDB 트러블슈팅](db/install/mariadb-troubleshooting.md)

- :simple-googlecloud: **Cloud & Ubuntu**

  ---

  [:octicons-arrow-right-24: GCP 폐쇄망 환경 구성](cloud/use_terraform_with_gcp.md)<br>
  [:octicons-arrow-right-24: GCP SDK Cheat Sheet](cloud/gcp-cheatsheet.md)<br>
  [:octicons-arrow-right-24: Ubuntu 초기 설정](ubuntu/init-ubuntu-env.md)<br>
  [:octicons-arrow-right-24: WSL 네트워크 설정](ubuntu/wsl/wsl-network-setting.md)

- :material-bookshelf: **Reference**

  ---

  [:octicons-arrow-right-24: Git Cheat Sheet](git/cheatsheet.md)<br>
  [:octicons-arrow-right-24: VSCode 단축키](ide/vscode_shortcut.md)<br>
  [:octicons-arrow-right-24: 도메인 IP 확인](network/tip/check-domain-ip.md)<br>
  [:octicons-arrow-right-24: 서브넷 & 게이트웨이 확인](network/tip/check-network-subnet.md)

</div>
