# 인프라 치트시트 신규 컴포넌트 및 가이드 보완 완료 보고서

`tmp/` 디렉토리에 유입된 변경 자산들을 기반으로, 전체 문서 보완 및 신규 추가, 네비게이션 연동, 그리고 빌드/배포 및 정리를 최종 완료했습니다.

---

## 1. 반영 및 보완 완료된 문서 목록

### 🏗️ Kubernetes 설치 및 containerd / Calico 설정 보완
*   **containerd Registry config path 보장 스크립트 및 수동 지침 추가**:
    *   Harbor TLS 인증서 설정을 위해 containerd의 registry config path를 보장하는 스크립트(`ensure-containerd-registry-config-path.sh`)와 FQDN 및 포트별 디렉토리에 전체 체인 인증서를 수동으로 배치하는 지침을 모두 추가하였습니다.
    *   Calico CNI 멀티 홈 IP 오작동을 방지하기 위한 경고(`!!! warning`) 문구를 추가하였습니다.
    *   [Rocky v1.30 오프라인 설치 가이드](docs/k8s/install/rocky-9/v1.30/offline-install.md)
    *   [Rocky v1.30 온라인 설치 가이드](docs/k8s/install/rocky-9/v1.30/online-install.md)
    *   [Rocky v1.33.7 온라인 설치 가이드](docs/k8s/install/rocky-9/v1.33.7/online-install.md)
    *   [Ubuntu v1.33.11 오프라인 설치 가이드](docs/k8s/install/ubuntu-24.04/v1.33.11/offline-install.md)
    *   [Ubuntu v1.33.11 온라인 설치 가이드](docs/k8s/install/ubuntu-24.04/v1.33.11/online-install.md)

### 🦊 CI/CD 설치 가이드 최신화
*   **ArgoCD v3.4.3**: 차트 버전 갱신, HostPath 볼륨 사용 시 특정 노드에 파드를 고정하기 위한 노드 셀렉터(`TARGET_NODE`) 설정 가이드와 NodePort 매개변수화 보완, 대화형 설정 적용(`values-override.yaml`) 절차를 통합했습니다.
    *   [ArgoCD 오프라인 설치 가이드](docs/cicd/offline-install/004-argocd-install.md)
*   **Jenkins v2.555.3**: OpenTofu IaC 툴체인을 내장하기 위해 사용자가 커스텀 이미지(`cmp-jenkins-full`)를 빌드 및 로드하는 절차를 보강했습니다.
    *   [Jenkins 오프라인 설치 가이드](docs/cicd/offline-install/002-jenkins-install.md)

### 🗄️ Apache Kafka (v3.9.0 & v4.0.0) KRaft 모드 가이드 신설
*   ZooKeeper 없이 3개의 카프카 브로커 노드로 클러스터를 배포하는 **KRaft co-located** 모드 배포 가이드를 신규 작성했습니다. StatefulSet 1:1 PV 바인딩을 위한 정적 PV 매니페스트 구성 및 오버라이드 템플릿 사용법을 포함합니다.
    *   [Kafka v3.9.0 오프라인 설치 가이드](docs/db/kafka/kafka-3.9.0-install.md)
    *   [Kafka v4.0.0 오프라인 설치 가이드](docs/db/kafka/kafka-4.0.0-install.md)

### 🏷️ 기존 컴포넌트 버전명 매칭을 위한 디렉토리 정리 (Rename)
*   서비스 및 헬름 차트 버전에 맞춰 가이드 내의 경로 갱신과 트러블슈팅 지침을 보강하였습니다.
    *   [Falco 설치 가이드](docs/k8s/security/001-falco-install.md) (v8.0.1 ➡️ v0.43.0, inotify 및 K3s 소켓 트러블슈팅 추가)
    *   [NFS Provisioner 설치 가이드](docs/k8s/use-pv-nas.md) (v4.0.18 ➡️ v4.0.2)
    *   [OpenTelemetry Collector 설치 가이드](docs/k8s/monitoring/opentelemetry-collector-install.md) (v0.158.0 ➡️ v0.153.0)
    *   [OpenTelemetry Operator 설치 가이드](docs/k8s/monitoring/opentelemetry-operator-install.md) (v0.114.1 ➡️ v0.152.0)

---

## 2. 네비게이션 연동 및 대시보드 반영
*   [mkdocs.yml](mkdocs.yml)에 `Database -> Kafka` 메뉴를 새롭게 추가하고 가이드 2종을 연동했습니다.
*   [docs/index.md](docs/index.md) 대시보드 화면에 Kafka 카드 및 가이드 링크를 추가하였습니다.
*   [docs/guide/infra-standard.md](docs/guide/infra-standard.md) 표준화 현황에 모니터링(0.89.0), Falco(0.43.0)의 버전 매핑 정보를 현행화했습니다.

---

## 3. 검증 및 빌드/배포 수행 내용
1.  **로컬 빌드 검증**: `wsl -d Ubuntu --cd /home/mjko/infra-cheatsheets ./venv/bin/mkdocs build` 명령을 가동하여 100% 정상 빌드됨을 검증했습니다.
2.  **의미 단위 Atomic Commits**: 5개의 기능 단위 한글 커밋으로 분할하여 로컬 커밋을 생성했습니다. 각 커밋에는 협업 규칙인 `Co-Authored-By: Antigravity <noreply@google.com>`를 포함했습니다.
