# 인프라 치트시트 신규 가이드 반영 및 템플릿 v3.1 보완 완료 보고서

`tmp/` 디렉토리에 유입된 변경 자산과 첨부해주신 PDF(Rocky 9.6 템플릿 생성 가이드 v3.1)를 기반으로, 전체 문서 보완 및 신규 추가, 네비게이션 연동, 그리고 빌드/배포 및 정리를 최종 완료했습니다.

---

## 1. 반영 및 보완 완료된 문서 목록

### 🛡️ OPA Gatekeeper v3.17.0 오프라인 설치 가이드 신설
*   OPA 기반 정책 통제 엔진인 Gatekeeper v3.17.0을 에어갭 환경에서 헬름 차트 및 이미지 아카이브를 통해 배포하는 절차를 한글 격식체로 새로 구성했습니다.
    *   [Gatekeeper 오프라인 설치 가이드](docs/k8s/security/004-gatekeeper-install.md)

### 🏗️ Kubernetes 설치 가이드 5종 최신 패치 반영
*   Harbor TLS CA 인증서 설정 후 `containerd` 서비스를 재기동하는 명령(`sudo systemctl restart containerd`)을 수록했습니다.
*   nerdctl pull 및 skopeo 복사/목록 조회 예제 시, insecure registry 대신 TLS 검증 및 FQDN 주소를 사용하는 구성 지침으로 통일했습니다.
*   Rocky v1.30 offline-install 내 grub2-mkconfig 실행 시 BIOS(Legacy) 부팅 환경에 대한 분기 명령어를 추가했습니다.
*   Ubuntu v1.33.11 offline-install 내 Calico CNI 멀티 홈 IP 대응 경고 문구 위치를 Tigera Operator 방식 가이드 하단으로 재배치하여 설명 무결성을 강화했습니다.
    *   [Rocky v1.30 오프라인 설치 가이드](docs/k8s/install/rocky-9/v1.30/offline-install.md)
    *   [Rocky v1.30 온라인 설치 가이드](docs/k8s/install/rocky-9/v1.30/online-install.md)
    *   [Rocky v1.33.7 온라인 설치 가이드](docs/k8s/install/rocky-9/v1.33.7/online-install.md)
    *   [Ubuntu v1.33.11 오프라인 설치 가이드](docs/k8s/install/ubuntu-24.04/v1.33.11/offline-install.md)
    *   [Ubuntu v1.33.11 온라인 설치 가이드](docs/k8s/install/ubuntu-24.04/v1.33.11/online-install.md)

### 🐧 VMware Rocky 9.6 Vagrant 기반 템플릿 생성 가이드 v3.1 업데이트
*   기존 v3.0 가이드를 첨부된 PDF 내용을 바탕으로 LVM 디스크 자동 확장 및 NetworkManager 청소 지침을 전면 보완하여 업그레이드했습니다.
*   **루트 디스크 LVM PV 파티션 자동 팽창 대응**: `/dev/sda3` LVM PV 파티션 팽창을 위한 cloud-init growpart 타겟 구성 및 첫 부팅용 LVM 루트 확장 스크립트(`/usr/local/sbin/resize-lvm-root.sh`)와 systemd 원샷 서비스(`resize-lvm-root.service`)를 작성하도록 가이드를 개정했습니다.
*   **루트 파티션 확인 및 가변 대응 경고 추가**: 환경별로 루트 PV 파티션 명칭(sda3, sda4 등)이 다를 수 있으므로 이를 확인 및 수정해야 한다는 주의 사항(`!!! warning`)을 강력하게 주입했습니다.
*   **NetworkManager 커넥션 초기화 보강**: 프로비저닝 시 IP 꼬임/충돌 방지를 위해 nmcli connection 및 nmconnection 실제 파일을 완전 소거하는 지침을 수록했습니다.
    *   [VMware Rocky 9.6 템플릿 생성 가이드](docs/vm-template/rocky-vagrant-guide.md)

---

## 2. 네비게이션 연동 및 대시보드 반영
*   [mkdocs.yml](mkdocs.yml)에 `Gatekeeper 정책 통제` 메뉴를 새롭게 추가하고 가이드 1종을 연동했으며, VM Template 가이드 명칭을 v3.1로 갱신했습니다.
*   [docs/index.md](docs/index.md) 대시보드 화면에 Gatekeeper 정책 통제 및 VM 템플릿 v3.1 가이드 링크를 연동했습니다.

---

## 3. 검증 및 빌드/배포 수행 내용
1.  **로컬 빌드 검증**: `mkdocs build` 명령을 가동하여 100% 정상 빌드됨을 검증했습니다.
2.  **의미 단위 Atomic Commits**: 4개의 기능 단위 한글 커밋으로 분할하여 로컬 커밋을 생성했습니다. 각 커밋에는 협업 규칙인 `Co-Authored-By: Antigravity <noreply@google.com>`를 포함했습니다.
