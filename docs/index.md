---
hide:
  - navigation
  - toc
---

# Infra Cheatsheets { .md-display-1 }

**DevOps 및 인프라 엔지니어를 위한 지식 저장소**
잊어버리기 쉬운 명령어, 표준화된 설치 절차, 트러블슈팅 가이드를 체계적으로 관리합니다.

[:fontawesome-brands-github: GitHub](https://github.com/kdelphinus/infra-cheatsheets){ .md-button .md-button--primary }
[:fontawesome-brands-google-drive: 설치 파일 드라이브](https://drive.google.com/drive/folders/1joMQRpZPWzKgU9BBsdxy3b0qzJMWpBC8?hl=ko/){ .md-button }
[:fontawesome-solid-book: 인프라 표준 가이드](guide/infra-standard.md){ .md-button }

!!! note
    설치 문서는 [설치 파일 GitHub](https://github.com/kdelphinus/air-gapped-install-file/)에 가장 먼저 업데이트됩니다.

!!! info "인프라 설치 및 구성 표준 가이드"
    본 프로젝트의 모든 컴포넌트는 수립된 표준(`install.conf` 기반 상태 보존 등)을 준수합니다. 신규 구축 및 수정 시 [인프라 설치 및 구성 표준 가이드](guide/infra-standard.md)를 반드시 확인하십시오.

---

## :simple-kubernetes: Kubernetes Platform

폐쇄망 환경의 멀티 OS 지원 및 보안 강화 플랫폼 가이드입니다.

<div class="grid cards" markdown>

- :simple-kubernetes: **K8s Core & Install**

    ---

    클러스터 구축 및 OS별 최적 설정

    - [:octicons-arrow-right-24: Ubuntu 24.04 **설치 파일 준비**](k8s/install/ubuntu/ready-offline.md)
    - [:octicons-arrow-right-24: Ubuntu 24.04 **오프라인 설치**](k8s/install/ubuntu/offline-install.md)
    - [:octicons-arrow-right-24: Rocky Linux 9.6 **설치 파일 준비**](k8s/install/rocky/ready-offline.md)
    - [:octicons-arrow-right-24: Rocky Linux 9.6 **오프라인 설치**](k8s/install/rocky/offline-install.md)
    - [:octicons-arrow-right-24: **Helm & 스토리지 프로비저너** 설치](k8s/offline-install/003-necessary_infra_install.md)
    - [:octicons-arrow-right-24: Kubernetes Cheat Sheet](k8s/cheatsheet.md)

- :material-wan: **Network & Ingress**

    ---

    트래픽 제어 및 차세대 Gateway API

    - [:octicons-arrow-right-24: Envoy Gateway & HTTPRoute](k8s/gateway-api/envoy-v1.37.2-install.md)
    - [:octicons-arrow-right-24: Cilium (CNI) 오프라인 설치](k8s/network/cilium-install.md)
    - [:octicons-arrow-right-24: NGINX NIC 마이그레이션 가이드](k8s/gateway-api/nginx-nic-migration.md)

- :material-shield-check: **Security & Backup**

    ---

    런타임 보안 탐지 및 데이터 보호

    - [:octicons-arrow-right-24: Tetragon 런타임 보안 전략](k8s/security/003-tetragon-security-policy.md)
    - [:octicons-arrow-right-24: Falco 이상행위 탐지 가이드](k8s/security/001-falco-install.md)
    - [:octicons-arrow-right-24: Velero 백업 및 복구 구성](k8s/backup-restore/001-velero-install.md)

- :material-cog: **Operations & Storage**

    ---

    모니터링 및 영구 저장소 관리

    - [:octicons-arrow-right-24: Prometheus & Grafana 통합 모니터링](k8s/monitoring/001-kube-prometheus-stack.md)
    - [:octicons-arrow-right-24: NFS 동적 스토리지 프로비저너](k8s/use-pv-nas.md)
    - [:octicons-arrow-right-24: MetalLB 로드밸런서 설치](k8s/offline-install/004-metallb-install.md)

</div>

---

## :material-pipe: Platform Ecosystem (CI/CD)

자동화된 배포 및 아티팩트 관리 가이드입니다.

<div class="grid cards" markdown>

- :material-layers: **Registry & Repository**

    ---

    사설 저장소 서비스 구축

    - [:octicons-arrow-right-24: Harbor 레지스트리 설치](cicd/offline-install/000-harbor-install.md)
    - [:octicons-arrow-right-24: Nexus Repository 설치](cicd/offline-install/004-nexus-install.md)

- :material-sync: **CI/CD Pipelines**

    ---

    지속적 통합 및 배포 플랫폼

    - [:octicons-arrow-right-24: GitLab & Jenkins 통합 설치](cicd/offline-install/001-gitlab_jenkins_install.md)
    - [:octicons-arrow-right-24: ArgoCD 설치 및 연동 가이드](cicd/offline-install/002-argocd-install.md)
    - [:octicons-arrow-right-24: Gitea 경량 Git 서비스 설치](cicd/offline-install/005-gitea-install.md)

</div>

---

## :simple-mariadb: Database Cluster (HA)

고가용성 DB 클러스터 및 캐시 서비스 운영 가이드입니다.

<div class="grid cards" markdown>

- :simple-mariadb: **Relational Database**

    ---

    MariaDB 고가용성 클러스터

    - [:octicons-arrow-right-24: MariaDB Galera Cluster 설치](db/ha/galera-cluster.md)
    - [:octicons-arrow-right-24: MariaDB 폐쇄망 오프라인 설치](db/install/mariadb-air-gapped-install.md)
    - [:octicons-arrow-right-24: DB 장애 복구 및 트러블슈팅](db/ha/galera-recovery.md)

- :simple-redis: **NoSQL & Cache**

    ---

    Redis 고성능 데이터 스트림

    - [:octicons-arrow-right-24: Redis Stream 개발 가이드](db/redis/001-redis-stream-overview.md)
    - [:octicons-arrow-right-24: Redis Stream 설치 및 운영](db/redis/002-redis-stream-install.md)

</div>

---

## :material-cloud: Infrastructure & Cloud

프라이빗 및 퍼블릭 클라우드 인프라 구축 가이드입니다.

<div class="grid cards" markdown>

- :simple-openstack: **OpenStack Private Cloud**

    ---

    클라우드 구축 및 GPU 연동 가이드

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

서버 운영 및 협업을 위한 기초 기술 가이드입니다.

<div class="grid cards" markdown>

- :octicons-terminal-24: **Linux & Server OS**

    ---

    OS 초기화 및 가상화 환경 설정

    - [:octicons-arrow-right-24: Ubuntu 서버 초기 환경 설정](ubuntu/init-ubuntu-env.md)
    - [:octicons-arrow-right-24: WSL 네트워크 및 환경 설정](ubuntu/wsl/wsl-network-setting.md)

- :octicons-broadcast-24: **Network Tips**

    ---

    네트워크 진단 및 통신 확인 가이드

    - [:octicons-arrow-right-24: 도메인 IP 및 레코드 체크](network/tip/check-domain-ip.md)
    - [:octicons-arrow-right-24: 서버 서브넷 및 게이트웨이 확인](network/tip/check-network-subnet.md)
    - [:octicons-arrow-right-24: 방화벽 및 포트 통신 확인 가이드](network/tip/port-check.md)

- :octicons-git-branch-24: **Git & Workflow**

    ---

    협업 컨벤션 및 개발 생산성 도구

    - [:octicons-arrow-right-24: Git 협업 컨벤션 및 브랜치 전략](git/convention.md)
    - [:octicons-arrow-right-24: Git Cheat Sheet & 명령어 요약](git/cheatsheet.md)
    - [:octicons-arrow-right-24: VSCode 단축키 및 필수 설정](ide/vscode_shortcut.md)

</div>
