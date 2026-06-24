---
hide:
  - navigation
  - toc
---

# Infra Cheatsheets { .md-display-1 }

**DevOps 및 인프라 엔지니어를 위한 지식 저장소**
잊어버리기 쉬운 명령어, 표준화된 설치 절차, 트러블슈팅 가이드를 체계적으로 관리합니다.

[:fontawesome-brands-github: GitHub](https://github.com/kdelphinus/infra-cheatsheets){ .md-button .md-button--primary }
[:fontawesome-solid-book: 인프라 표준 가이드](guide/infra-standard.md){ .md-button }

!!! info "인프라 설치 및 구성 표준 가이드"
    본 프로젝트의 모든 컴포넌트는 수립된 표준(`install.conf` 기반 상태 보존 등)을 준수합니다. 신규 구축 및 수정 시 [인프라 설치 및 구성 표준 가이드](guide/infra-standard.md)를 반드시 확인하십시오.

---

## :simple-kubernetes: 쿠버네티스 플랫폼

폐쇄망 환경의 멀티 OS 지원 및 보안 강화 플랫폼 가이드입니다.

<div class="grid cards" markdown>

- :simple-kubernetes: **K8s 핵심 및 설치**

    ---

    클러스터 구축 및 OS별 최적 설정

    - [:octicons-arrow-right-24: Ubuntu 24.04 설치 파일 준비 (v1.33.11)](k8s/install/ubuntu-24.04/v1.33.11/ready-offline.md)
    - [:octicons-arrow-right-24: Ubuntu 24.04 오프라인 설치 (v1.33.11)](k8s/install/ubuntu-24.04/v1.33.11/offline-install.md)
    - [:octicons-arrow-right-24: Ubuntu 24.04 온라인 설치 (v1.36.1)](k8s/install/ubuntu-24.04/v1.36.1/online-install.md)
    - [:octicons-arrow-right-24: Rocky Linux 설치 파일 준비 (v1.30)](k8s/install/rocky-9/v1.30/ready-offline.md)
    - [:octicons-arrow-right-24: Rocky Linux 오프라인 설치 (v1.30)](k8s/install/rocky-9/v1.30/offline-install.md)
    - [:octicons-arrow-right-24: 오프라인 빌더 사용 가이드](k8s/install/k8s-offline-builder-guide.md)
    - [:octicons-arrow-right-24: 오프라인 빌더 재현성 검증 (v1.33.11)](k8s/install/reproducibility-check-ubuntu.md)
    - [:octicons-arrow-right-24: Helm 및 스토리지 프로비저너 설치](k8s/install/base-infra.md)
    - [:octicons-arrow-right-24: Kubernetes Cheat Sheet](k8s/cheatsheet.md)
    - [:octicons-arrow-right-24: Cluster API & 리소스 치트시트](k8s/capi/cheatsheet.md)

- :material-wan: **네트워크 및 인그레스**

    ---

    트래픽 제어 및 차세대 Gateway API

    - [:octicons-arrow-right-24: Envoy Gateway 및 HTTPRoute 설치](k8s/gateway-api/envoy-v1.37.2-install.md)
    - [:octicons-arrow-right-24: Cilium (CNI) 오프라인 설치](k8s/network/cilium-install.md)
    - [:octicons-arrow-right-24: NGINX NIC 마이그레이션 가이드](k8s/gateway-api/nginx-nic-migration.md)

- :material-shield-check: **보안 및 백업**

    ---

    런타임 보안 탐지 및 데이터 보호

    - [:octicons-arrow-right-24: Tetragon 런타임 보안 전략](k8s/security/003-tetragon-security-policy.md)
    - [:octicons-arrow-right-24: Falco 이상행위 탐지 가이드](k8s/security/001-falco-install.md)
    - [:octicons-arrow-right-24: Gatekeeper 정책 통제 가이드](k8s/security/004-gatekeeper-install.md)
    - [:octicons-arrow-right-24: Velero 백업 및 복구 구성](k8s/backup-restore/001-velero-install.md)

- :material-cog: **운영 및 스토리지**

    ---

    모니터링 및 영구 저장소 관리

    - [:octicons-arrow-right-24: Prometheus 및 Grafana 통합 모니터링](k8s/monitoring/001-kube-prometheus-stack.md)
    - [:octicons-arrow-right-24: OpenTelemetry Collector 오프라인 설치](k8s/monitoring/opentelemetry-collector-install.md)
    - [:octicons-arrow-right-24: OpenTelemetry Operator 오프라인 설치](k8s/monitoring/opentelemetry-operator-install.md)
    - [:octicons-arrow-right-24: NFS 동적 스토리지 프로비저너](k8s/use-pv-nas.md)
    - [:octicons-arrow-right-24: NetApp Trident 스토리지 프로비저너](k8s/storage/trident-install.md)
    - [:octicons-arrow-right-24: MetalLB 로드밸런서 설치](k8s/install/metallb-install.md)
    - [:octicons-arrow-right-24: etcd 전용 디스크 마이그레이션 SOP](k8s/operations/etcd-disk-migration-sop.md)

- :material-alert-circle-outline: **장애 해결 및 트러블슈팅**

    ---

    클러스터 운영 중 발생하는 장애 대응 가이드

    - [:octicons-arrow-right-24: Calico CNI 라우팅 장애 해결](k8s/troubleshooting/calico-routing-troubleshooting.md)
    - [:octicons-arrow-right-24: ContainerPort 누락 장애 해결](k8s/troubleshooting/missed-containerport.md)
    - [:octicons-arrow-right-24: Cilium CNI 설치 트러블슈팅](k8s/troubleshooting/cilium-troubleshooting.md)
    - [:octicons-arrow-right-24: Falco 런타임 탐지 트러블슈팅](k8s/troubleshooting/falco-troubleshooting.md)
    - [:octicons-arrow-right-24: Tetragon 런타임 차단 트러블슈팅](k8s/troubleshooting/tetragon-troubleshooting.md)
    - [:octicons-arrow-right-24: HTTPRoute 라우팅 트러블슈팅](k8s/troubleshooting/httproute-troubleshooting.md)

</div>

---

## :material-pipe: 플랫폼 생태계 (CI/CD)

자동화된 배포 및 아티팩트 관리 가이드입니다.

<div class="grid cards" markdown>

- :material-layers: **레지스트리 및 저장소**

    ---

    사설 저장소 서비스 구축

    - [:octicons-arrow-right-24: Harbor 레지스트리 설치](cicd/offline-install/000-harbor-install.md)
    - [:octicons-arrow-right-24: Nexus Repository 설치](cicd/offline-install/006-nexus-install.md)

- :material-sync: **CI/CD 파이프라인**

    ---

    지속적 통합 및 배포 플랫폼

    - [:octicons-arrow-right-24: GitLab 설치](cicd/offline-install/001-gitlab-install.md)
    - [:octicons-arrow-right-24: Jenkins 설치](cicd/offline-install/002-jenkins-install.md)
    - [:octicons-arrow-right-24: GitLab Omnibus 설치](cicd/offline-install/003-gitlab-omnibus-install.md)
    - [:octicons-arrow-right-24: ArgoCD 설치 및 연동 가이드](cicd/offline-install/004-argocd-install.md)
    - [:octicons-arrow-right-24: Gitea 경량 Git 서비스 설치](cicd/offline-install/007-gitea-install.md)
    - [:octicons-arrow-right-24: Tekton Pipelines 설치](cicd/offline-install/008-tekton-install.md)

</div>

---

## :simple-mariadb: 데이터베이스 클러스터 (HA)

고가용성 DB 클러스터 및 캐시 서비스 운영 가이드입니다.

<div class="grid cards" markdown>

- :simple-mariadb: **관계형 데이터베이스**

    ---

    MariaDB 고가용성 클러스터

    - [:octicons-arrow-right-24: MariaDB Galera Cluster 설치](db/ha/galera-cluster.md)
    - [:octicons-arrow-right-24: MariaDB Galera Cluster 온라인 설치](db/ha/galera-cluster-online.md)
    - [:octicons-arrow-right-24: MariaDB 폐쇄망 오프라인 설치](db/install/mariadb-air-gapped-install.md)
    - [:octicons-arrow-right-24: DB 장애 복구 및 트러블슈팅](db/ha/galera-recovery.md)
    - [:octicons-arrow-right-24: Galera Cluster 복구 가이드](db/backup-restore/mariadb-galera-restore-guide.md)
    - [:octicons-arrow-right-24: Galera Cluster 백업 동작 확인](db/backup-restore/mariadb-galera-backup-verify-guide.md)

- :simple-redis: **NoSQL 및 캐시**

    ---

    Redis 고성능 데이터 스트림

    - [:octicons-arrow-right-24: Redis Stream 개발 가이드](db/redis/001-redis-stream-overview.md)
    - [:octicons-arrow-right-24: Redis Stream 설치 및 운영](db/redis/002-redis-stream-install.md)

- :simple-apachekafka: **분산 메시징 플랫폼**

    ---

    Apache Kafka 고가용성 클러스터 (KRaft)

    - [:octicons-arrow-right-24: Apache Kafka v3.9.0 설치](db/kafka/kafka-3.9.0-install.md)
    - [:octicons-arrow-right-24: Apache Kafka v4.0.0 설치](db/kafka/kafka-4.0.0-install.md)

</div>

---

## :material-cloud: 인프라 및 클라우드

프라이빗 및 퍼블릭 클라우드 인프라 구축 가이드입니다.

<div class="grid cards" markdown>

- :simple-openstack: **OpenStack 사설 클라우드**

    ---

    클라우드 구축 및 GPU 연동 가이드

    - [:octicons-arrow-right-24: OpenStack Cheat Sheet](openstack/cheatsheet.md)
    - [:octicons-arrow-right-24: 인프라 서비스 설치 가이드](openstack/base/install.md)
    - [:octicons-arrow-right-24: 신규 노드 추가 가이드 (Kolla)](openstack/base/add-node.md)
    - [:octicons-arrow-right-24: GPU 노드 (PCI Passthrough)](openstack/gpu/init-gpu-node.md)
    - [:octicons-arrow-right-24: K8s 네트워크 통신 장애 해결](openstack/troubleshooting/k8s-network-error.md)

- :simple-googlecloud: **공용 클라우드 (GCP)**

    ---

    퍼블릭 클라우드 인프라 및 테라폼 자동화

    - [:octicons-arrow-right-24: Google Cloud SDK Cheat Sheet](cloud/gcp-cheatsheet.md)
    - [:octicons-arrow-right-24: Terraform 기반 GCP 환경 구성](cloud/use_terraform_with_gcp.md)

- :material-server: **VMware VM 템플릿**

    ---

    VMware 최적화 템플릿 빌드 및 리소스 관리

    - [:octicons-arrow-right-24: VM 템플릿 일반 제작 표준 가이드](vm-template/general-guide.md)
    - [:octicons-arrow-right-24: Rocky 9.6 Vagrant 기반 템플릿 빌드 (v3.1)](vm-template/rocky-vagrant-guide.md)
    - [:octicons-arrow-right-24: Rocky 9 K8s 노드 템플릿 제작 실무](vm-template/k8s-rocky-template.md)
    - [:octicons-arrow-right-24: Rocky 9 K8s 노드 템플릿 업그레이드](vm-template/k8s-rocky-template-upgrade.md)

</div>

---

## :octicons-tools-24: 운영 및 기술 역량

서버 운영 및 협업을 위한 기초 기술 가이드입니다.

<div class="grid cards" markdown>

- :octicons-terminal-24: **리눅스 및 서버 OS**

    ---

    OS 초기화 및 가상화 환경 설정

    - [:octicons-arrow-right-24: Ubuntu 서버 초기 환경 설정](ubuntu/init-ubuntu-env.md)
    - [:octicons-arrow-right-24: WSL 네트워크 및 환경 설정](ubuntu/wsl/wsl-network-setting.md)

- :octicons-broadcast-24: **네트워크 팁**

    ---

    네트워크 진단 및 통신 확인 가이드

    - [:octicons-arrow-right-24: 도메인 IP 및 레코드 체크](network/tip/check-domain-ip.md)
    - [:octicons-arrow-right-24: 서버 서브넷 및 게이트웨이 확인](network/tip/check-network-subnet.md)
    - [:octicons-arrow-right-24: 방화벽 및 포트 통신 확인 가이드](network/tip/port-check.md)

- :octicons-git-branch-24: **Git 및 워크플로우**

    ---

    협업 컨벤션 및 개발 생산성 도구

    - [:octicons-arrow-right-24: Git 협업 컨벤션 및 브랜치 전략](git/convention.md)
    - [:octicons-arrow-right-24: Git Cheat Sheet 및 명령어 요약](git/cheatsheet.md)
    - [:octicons-arrow-right-24: VSCode 단축키 및 필수 설정](ide/vscode_shortcut.md)

</div>
