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

## :simple-kubernetes: Kubernetes Platform

컨테이너 오케스트레이션 및 폐쇄망 기반 플랫폼 운영 가이드입니다.

<div class="grid cards" markdown>

- :simple-kubernetes: **Kubernetes Core**

    ---

    K8s 클러스터 구축 및 관리의 핵심 가이드

    - [:octicons-arrow-right-24: Kubernetes Cheat Sheet](k8s/cheatsheet.md)
    - [:octicons-arrow-right-24: 폐쇄망 설치 준비 (Air-gapped)](k8s/offline-install/001-ready-k8s-air-gapped-install.md)
    - [:octicons-arrow-right-24: v1.30 폐쇄망 설치 가이드](k8s/offline-install/002-k8s-air-gapped-install.md)
    - [:octicons-arrow-right-24: 기반 인프라 및 MetalLB 설치](k8s/offline-install/004-metallb-install.md)

- :material-router-wireless: **Network & Storage**

    ---

    트래픽 제어 및 영구 데이터 관리를 위한 구성

    - [:octicons-arrow-right-24: Ingress NGINX 설치 및 운영](k8s/gateway-api/000-ingress-nginx-install.md)
    - [:octicons-arrow-right-24: Envoy Gateway & HTTPRoute](k8s/gateway-api/001-envoy-install.md)
    - [:octicons-arrow-right-24: NFS 동적 스토리지 프로비저너](k8s/use-pv-nas.md)
    - [:octicons-arrow-right-24: NGINX NIC 마이그레이션 가이드](k8s/gateway-api/nginx-nic-migration.md)

- :material-shield-check: **Ops & Security**

    ---

    안정적인 클러스터 운영을 위한 모니터링 및 보안

    - [:octicons-arrow-right-24: Prometheus & Grafana 모니터링](k8s/monitoring/001-kube-prometheus-stack.md)
    - [:octicons-arrow-right-24: Velero 백업 및 복구 구성](k8s/backup-restore/001-velero-install.md)
    - [:octicons-arrow-right-24: Tetragon 런타임 보안 전략](k8s/security/003-tetragon-security-policy.md)
    - [:octicons-arrow-right-24: Falco 런타임 위협 탐지](k8s/security/001-falco-install.md)

- :material-pipe: **CI/CD 파이프라인**

    ---

    자동화된 배포 파이프라인 및 아티팩트 관리

    - [:octicons-arrow-right-24: Harbor 레지스트리 설치](cicd/offline-install/000-harbor-install.md)
    - [:octicons-arrow-right-24: GitLab & Jenkins 통합 설치](cicd/offline-install/001-gitlab_jenkins_install.md)
    - [:octicons-arrow-right-24: ArgoCD 설치 및 연동 가이드](cicd/offline-install/002-argocd-install.md)
    - [:octicons-arrow-right-24: Nexus Repository 설치](cicd/offline-install/004-nexus-install.md)

- :simple-mariadb: **Database (HA)**

    ---

    고가용성 DB 클러스터 구성 및 관리 가이드

    - [:octicons-arrow-right-24: MariaDB Galera Cluster 설치](db/ha/galera-cluster.md)
    - [:octicons-arrow-right-24: MariaDB 폐쇄망 오프라인 설치](db/install/mariadb-air-gapped-install.md)
    - [:octicons-arrow-right-24: Redis Stream 개발자 가이드](db/redis/001-redis-stream-overview.md)
    - [:octicons-arrow-right-24: DB 장애 복구 및 트러블슈팅](db/ha/galera-recovery.md)

</div>

---

## :simple-openstack: Infrastructure & Cloud

프라이빗 및 퍼블릭 클라우드 인프라 구축 및 자동화 가이드입니다.

<div class="grid cards" markdown>

- :simple-openstack: **OpenStack**

    ---

    프라이빗 클라우드 구축 및 GPU 연동 가이드

    - [:octicons-arrow-right-24: OpenStack Cheat Sheet](openstack/cheatsheet.md)
    - [:octicons-arrow-right-24: 인프라 서비스 설치 가이드](openstack/base/install.md)
    - [:octicons-arrow-right-24: GPU 노드 (PCI Passthrough)](openstack/gpu/init-gpu-node.md)
    - [:octicons-arrow-right-24: K8s 네트워크 통신 장애 해결](openstack/troubleshooting/k8s-network-error.md)

- :simple-googlecloud: **Public Cloud (GCP)**

    ---

    퍼블릭 클라우드 인프라 및 테라폼 자동화

    - [:octicons-arrow-right-24: Google Cloud SDK Cheat Sheet](cloud/gcp-cheatsheet.md)
    - [:octicons-arrow-right-24: Terraform 기반 GCP 환경 구성](cloud/use_terraform_with_gcp.md)

</div>

---

## :octicons-tools-24: Operations & Skills

효율적인 서버 운영 및 협업을 위한 기초 기술 가이드입니다.

<div class="grid cards" markdown>

- :octicons-terminal-24: **Linux & Server**

    ---

    서버 운영체제 초기화 및 환경 설정 가이드

    - [:octicons-arrow-right-24: Ubuntu 서버 초기 환경 설정](ubuntu/init-ubuntu-env.md)
    - [:octicons-arrow-right-24: WSL 네트워크 및 환경 설정](ubuntu/wsl/wsl-network-setting.md)

- :octicons-broadcast-24: **Network Tips**

    ---

    인프라 통신 및 네트워크 트러블슈팅 팁

    - [:octicons-arrow-right-24: 도메인 IP 및 레코드 체크](network/tip/check-domain-ip.md)
    - [:octicons-arrow-right-24: 서버 서브넷 및 게이트웨이 확인](network/tip/check-network-subnet.md)
    - [:octicons-arrow-right-24: 방화벽 및 포트 통신 확인 가이드](network/tip/port-check.md)

- :octicons-git-branch-24: **Git & Tools**

    ---

    효율적인 협업을 위한 형상 관리 및 IDE 설정

    - [:octicons-arrow-right-24: Git 협업 컨벤션 및 브랜치 전략](git/convention.md)
    - [:octicons-arrow-right-24: Git Cheat Sheet & 명령어 요약](git/cheatsheet.md)
    - [:octicons-arrow-right-24: VSCode 단축키 및 필수 설정](ide/vscode_shortcut.md)

</div>
