---
hide:
  - navigation
  - toc
---

# Infra Cheatsheets { .md-display-1 }

**DevOps 실무를 위한 개인 지식 저장소**
잊어버리기 쉬운 명령어, 설치 절차, 트러블슈팅 가이드를 체계적으로 정리해 두었습니다.

[:fontawesome-brands-github: GitHub](https://github.com/kdelphinus/infra-cheatsheets){ .md-button .md-button--primary }
[:fontawesome-brands-google-drive: 설치 파일 드라이브](https://drive.google.com/drive/folders/1joMQRpZPWzKgU9BBsdxy3b0qzJMWpBC8?hl=ko/){ .md-button }
[:fontawesome-solid-box-archive: 설치 파일 GitHub](https://github.com/kdelphinus/air-gapped-install-file/){ .md-button }

---

<div class="grid cards" markdown>

-   :simple-kubernetes: **Kubernetes**

    ---

    컨테이너 오케스트레이션 및 폐쇄망 설치 운영 가이드

    *   [:octicons-arrow-right-24: Cheat Sheet](k8s/cheatsheet.md)
    *   [:octicons-arrow-right-24: 폐쇄망 설치 (v1.30)](k8s/offline-install/002-k8s-air-gapped-install.md)
    *   [:octicons-arrow-right-24: Envoy Gateway & HTTPRoute](k8s/gateway-api/001-envoy-install.md)
    *   [:octicons-arrow-right-24: 모니터링 & 백업](k8s/monitoring/001-kube-prometheus-stack.md)

-   :simple-openstack: **OpenStack**

    ---

    프라이빗 클라우드 구축 및 GPU 노드 연동 가이드

    *   [:octicons-arrow-right-24: Cheat Sheet](openstack/cheatsheet.md)
    *   [:octicons-arrow-right-24: 설치 가이드](openstack/base/install.md)
    *   [:octicons-arrow-right-24: GPU 노드 (PCI Passthrough)](openstack/gpu/init-gpu-node.md)
    *   [:octicons-arrow-right-24: Golden Image & 트러블슈팅](openstack/utils/golden-image.md)

-   :material-pipe: **CI/CD**

    ---

    폐쇄망 환경의 Harbor, GitLab, Jenkins, ArgoCD 구축

    *   [:octicons-arrow-right-24: Harbor & GitLab 설치](cicd/offline-install/000-harbor-install.md)
    *   [:octicons-arrow-right-24: ArgoCD 설치 및 연동](cicd/offline-install/002-argocd-install.md)
    *   [:octicons-arrow-right-24: Nexus Repository 설치](cicd/offline-install/004-nexus-install.md)
    *   [:octicons-arrow-right-24: 이미지 업데이트 재배포](cicd/operation/redeploy-with-new-image.md)

-   :simple-mariadb: **Database**

    ---

    고가용성 Galera Cluster 구성 및 장애 복구 가이드

    *   [:octicons-arrow-right-24: Galera Cluster 설치](db/ha/galera-cluster.md)
    *   [:octicons-arrow-right-24: Galera 장애 복구](db/ha/galera-recovery.md)
    *   [:octicons-arrow-right-24: MariaDB 폐쇄망 설치](db/install/mariadb-air-gapped-install.md)
    *   [:octicons-arrow-right-24: MariaDB 트러블슈팅](db/install/mariadb-troubleshooting.md)

-   :simple-googlecloud: **Cloud & Linux**

    ---

    GCP 인프라 자동화 및 Ubuntu 서버 초기화 가이드

    *   [:octicons-arrow-right-24: GCP Terraform 구성](cloud/use_terraform_with_gcp.md)
    *   [:octicons-arrow-right-24: GCP SDK Cheat Sheet](cloud/gcp-cheatsheet.md)
    *   [:octicons-arrow-right-24: Ubuntu 초기 설정](ubuntu/init-ubuntu-env.md)
    *   [:octicons-arrow-right-24: WSL 네트워크 설정](ubuntu/wsl/wsl-network-setting.md)

-   :material-bookshelf: **Reference**

    ---

    기타 유용한 도구 및 네트워크 설정 팁

    *   [:octicons-arrow-right-24: Git Cheat Sheet](git/cheatsheet.md)
    *   [:octicons-arrow-right-24: VSCode 단축키](ide/vscode_shortcut.md)
    *   [:octicons-arrow-right-24: 네트워크 IP & 서브넷 확인](network/tip/check-domain-ip.md)

</div>

