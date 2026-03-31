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

- :simple-kubernetes: **Kubernetes**

    ---

    컨테이너 오케스트레이션 및 폐쇄망 운영 가이드

  - [:octicons-arrow-right-24: Cheat Sheet](k8s/cheatsheet.md)
  - [:octicons-arrow-right-24: 폐쇄망 설치 (v1.30)](k8s/offline-install/002-k8s-air-gapped-install.md)
  - [:octicons-arrow-right-24: MetalLB 로드밸런서 설치](k8s/offline-install/004-metallb-install.md)
  - [:octicons-arrow-right-24: NFS 동적 스토리지 프로비저너](k8s/use-pv-nas.md)
  - [:octicons-arrow-right-24: Velero 백업 및 복구 구성](k8s/backup-restore/001-velero-install.md)
  - [:octicons-arrow-right-24: NGINX NIC 마이그레이션 가이드](k8s/gateway-api/nginx-nic-migration.md)
  - [:octicons-arrow-right-24: Envoy Gateway & HTTPRoute](k8s/gateway-api/001-envoy-install.md)
  - [:octicons-arrow-right-24: Prometheus & Grafana 모니터링](k8s/monitoring/001-kube-prometheus-stack.md)
  - [:octicons-arrow-right-24: Tetragon 런타임 보안 전략](k8s/security/003-tetragon-security-policy.md)

- :simple-openstack: **OpenStack**

    ---

    프라이빗 클라우드 구축 및 GPU 연동 가이드

  - [:octicons-arrow-right-24: OpenStack Cheat Sheet](openstack/cheatsheet.md)
  - [:octicons-arrow-right-24: 인프라 서비스 목록 (Reference)](openstack/base/reference.md)
  - [:octicons-arrow-right-24: 인프라 서비스 설치 가이드](openstack/base/install.md)
  - [:octicons-arrow-right-24: OpenStack API 명세](openstack/base/api.md)
  - [:octicons-arrow-right-24: GPU 노드 (PCI Passthrough)](openstack/gpu/init-gpu-node.md)

- :simple-googlecloud: **Public Cloud (GCP)**

    ---

    퍼블릭 클라우드 인프라 및 테라폼 자동화

  - [:octicons-arrow-right-24: Google Cloud SDK Cheat Sheet](cloud/gcp-cheatsheet.md)
  - [:octicons-arrow-right-24: Terraform 기반 GCP 환경 구성](cloud/use_terraform_with_gcp.md)

- :material-pipe: **CI/CD**

    ---

    자동화된 배포 파이프라인 및 아티팩트 관리

  - [:octicons-arrow-right-24: Harbor 레지스트리 설치](cicd/offline-install/000-harbor-install.md)
  - [:octicons-arrow-right-24: GitLab & Jenkins 설치](cicd/offline-install/001-gitlab_jenkins_install.md)
  - [:octicons-arrow-right-24: ArgoCD 설치 및 연동](cicd/offline-install/002-argocd-install.md)
  - [:octicons-arrow-right-24: ArgoCD — Jenkins · Harbor 연동](cicd/offline-install/003-argocd-jenkins-harbor-integration.md)
  - [:octicons-arrow-right-24: Nexus Repository 설치](cicd/offline-install/004-nexus-install.md)

- :simple-mariadb: **Database**

    ---

    고가용성 DB 클러스터 구성 및 관리 가이드

  - [:octicons-arrow-right-24: Galera Cluster 설치 및 운영](db/ha/galera-cluster.md)
  - [:octicons-arrow-right-24: MariaDB 폐쇄망 오프라인 설치](db/install/mariadb-air-gapped-install.md)
  - [:octicons-arrow-right-24: Redis Stream 개발자 가이드 및 설치](db/redis/001-redis-stream-overview.md)
  - [:octicons-arrow-right-24: DB 장애 복구 및 트러블슈팅](db/ha/galera-recovery.md)

- :octicons-terminal-24: **Linux & Server**

    ---

    서버 운영체제 초기화 및 환경 설정 가이드

  - [:octicons-arrow-right-24: Ubuntu 서버 초기 환경 설정](ubuntu/init-ubuntu-env.md)
  - [:octicons-arrow-right-24: WSL 네트워크 및 환경 설정](ubuntu/wsl/wsl-network-setting.md)

- :octicons-broadcast-24: **Network**

    ---

    인프라 통신 및 네트워크 트러블슈팅 팁

  - [:octicons-arrow-right-24: 도메인 실제 IP 및 레코드 체크](network/tip/check-domain-ip.md)
  - [:octicons-arrow-right-24: 서버 서브넷 및 게이트웨이 확인](network/tip/check-network-subnet.md)
  - [:octicons-arrow-right-24: 방화벽 및 포트 통신 확인 가이드](network/tip/port-check.md)

- :octicons-git-branch-24: **Git & Workflow**

    ---

    효율적인 협업을 위한 형상 관리 가이드

  - [:octicons-arrow-right-24: Git Cheat Sheet & 명령어 요약](git/cheatsheet.md)
  - [:octicons-arrow-right-24: Git 협업 컨벤션 및 브랜치 전략](git/convention.md)

- :octicons-code-24: **IDE & Productivity**

    ---

    개발 및 운영 생산성을 높여주는 도구 설정

  - [:octicons-arrow-right-24: VSCode 단축키 및 필수 설정](ide/vscode_shortcut.md)

</div>
