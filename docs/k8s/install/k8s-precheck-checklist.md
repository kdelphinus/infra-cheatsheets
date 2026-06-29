# Kubernetes 설치 전 사전 확인 가이드 및 체크리스트 (K8s Pre-check Guide)

본 문서는 Kubernetes 클러스터를 설치(단일 구성 및 HA 고가용성 구성)하기 전, 대상 서버들의 OS 환경, 네트워크 대역, 시스템 리소스, 방화벽 포트 상태를 사전 검증하여 설치 실패 요인을 예방하기 위한 종합 가이드 및 체크리스트입니다.

---

## 1. 실장비 사전 확인 명령어 (Pre-check Commands)

설치 대상 노드에 접속하여 아래 명령어들을 실행해 시스템 상태가 Kubernetes 설치 조건을 만족하는지 확인하십시오.

### 1.1. 시스템 기본 정보 및 호스트네임 확인
각 노드는 고유한 호스트네임과 식별자(MAC 주소, UUID)를 가져야 합니다.
```bash
# OS 및 커널 버전 확인
cat /etc/os-release
uname -r

# 호스트네임 확인
hostnamectl

# MAC 주소 확인 (노드 간 중복 금지)
ip link

# Product UUID 확인 (노드 간 중복 금지)
sudo cat /sys/class/dmi/id/product_uuid
```

### 1.2. Swap 비활성화 상태 검증
Kubernetes는 swap 메모리가 활성화되어 있으면 kubelet이 오작동하거나 시동에 실패합니다.
```bash
# 활성화된 swap 디바이스가 없는지 확인 (아무 출력도 없어야 함)
swapon --show

# 메모리 상태에서 Swap 항목이 0B인지 확인
free -h
```

### 1.3. 시간 동기화 (NTP) 검증
노드 간 시간이 어긋나면 etcd 멤버 간 동기화 실패 및 etcd 시동 실패, 혹은 인증서 만료 에러가 발생합니다.
```bash
# 시스템 시간 및 동기화 활성화 상태 확인
timedatectl status

# Chrony 동기화 소스 및 상태 확인 (Chrony 사용 시)
chronyc tracking
chronyc sources
```

### 1.4. 디스크 여유 공간 및 Inode 확인
컨테이너 이미지 및 etcd 데이터가 쌓이는 경로의 여유 용량을 확인합니다.
```bash
# 디스크 용량 확인 (/var/lib/containerd 및 /var/lib/etcd 경로 확인)
df -h

# Inode 여유 공간 확인
df -i
```

### 1.5. 포트 충돌 및 방화벽 상태 확인
Kubernetes 핵심 컴포넌트가 사용할 포트(6443 등)가 이미 점유 중인지 체크합니다.
```bash
# K8s API 서버 포트 점유 여부 확인
ss -lntp | grep 6443

# 방화벽(firewalld / ufw) 활성화 여부 확인
systemctl status firewalld
sudo ufw status
```

---

## 2. Kubernetes 설치 전 필수 체크리스트 (Checklist)

아래 항목을 설치 전에 모두 확정 및 체크 완료한 뒤 설치를 진행하십시오.

### 2.1. 구성 및 작업 범위
* [ ] **구성 유형 확정:** WSL2 단일 노드, 단일 컨트롤 플레인, HA 3중화, 물리 서버, 가상 서버 여부 확정
* [ ] **노드 정보 확정:** 노드별 역할, hostname, 관리 IP, Kubernetes 통신 NIC, gateway, DNS, NTP 서버 정보 확정
* [ ] **작업 승인 확인:** reboot, 네트워크 서비스 재시작, 방화벽 reload, containerd/Docker 서비스 재시작, OS 패키지 전체 업데이트 가능 여부 및 작업 승인 범위 확보
* [ ] **기존 서비스 간섭 확인:** 대상 서버에 기존 구동 중인 컨테이너 서비스, 6443 포트 사용 서비스, NodePort 사용 서비스, HAProxy/keepalived 사용 여부 확인

### 2.2. 네트워크 대역 및 엔드포인트
* [ ] **Pod CIDR 확정:** `/20` 권장 (최소 `/22` 이상), CNI 선택에 맞게 대역 확정
* [ ] **Service CIDR 확정:** `/24` 가능 (여유가 필요하면 `/22` 권장)
* [ ] **네트워크 대역 중복 검증:** Pod CIDR과 Service CIDR이 서버 실제 IP, 사내망, VPN 대역, DB망, 관리망, 백업망, 스토리지망과 겹치지 않는지 확인
* [ ] **API Endpoint 확정:** 단일 노드 IP, VIP, FQDN 중 선택하고 인증서 SAN(Subject Alternative Names), DNS 레코드 또는 `/etc/hosts` 반영 방식 확정
* [ ] **VIP 검증 (HA 구성 시):** 로드밸런서용 VIP의 미사용 상태(Ping 응답 없음) 확인, keepalived VRRP protocol 112 허용 여부, HAProxy 6443 포트 바인딩 충돌 여부 확인

### 2.3. 방화벽 및 포트 허용
* [ ] **Control Plane 노드 포트 허용:** 6443/TCP (API Server), 2379-2380/TCP (etcd), 10250/TCP (Kubelet API), 10257/TCP (Kube-Controller), 10259/TCP (Kube-Scheduler)
* [ ] **Worker 노드 포트 허용:** 10250/TCP (Kubelet API), 10256/TCP (Kube-Proxy), NodePort 기본 범위 (30000-32767/TCP,UDP)
* [ ] **기타 부가 포트 확인:** CNI(Calico/Cilium 등), Ingress Controller, 스토리지 프로비저너, Harbor, 내부 DNS, NTP 등 연동에 필요한 포트 개방 여부 확인
* [ ] **방화벽 처리 방식 확정:** 운영 환경 특성상 방화벽 flush/reset이 금지된 경우, 설치 전 룰 기반 포트 오픈이 사전에 완료되었는지 확인

### 2.4. 런타임, OS, 폐쇄망 자산
* [ ] **컨테이너 런타임 상태:** Docker/containerd 설치 상태, 기존 구동 중인 컨테이너 영향 여부, containerd/Docker 재시작 가능 여부 확인
* [ ] **Cgroup Driver 정합성:** kubelet과 containerd의 cgroup driver가 모두 `systemd`로 일치하는지 확인
* [ ] **호환성 검증:** 대상 OS 버전, 커널 버전, Kubernetes 버전, containerd 버전, CNI 버전의 호환성 매트릭스 확인
* [ ] **시스템 초기화 상태:** Swap 영구 비활성화, 시간 동기화(NTP), 디스크 및 Inode 여유 공간, 호스트네임/MAC 주소/Product UUID 중복 없음 확인
* [ ] **폐쇄망 자산 완비:** 에어갭 설치에 필요한 DEB/RPM 패키지, 바이너리 tarball, 컨테이너 이미지 아카이브 (.tar), YAML 매니페스트, Helm 차트, Harbor CA 인증서 및 레지스트리 정보 완비 여부 확인

### 2.5. 설치 진행 및 비상 계획
* [ ] **미확정 조치 검토:** 미확정된 환경 변수나 설정 항목이 없는지 확인
* [ ] **장애 대응 계획:** 설치 실패 또는 장애 발생 시 롤백(Rollback) 범위, 백업 복구 절차, 긴급 연락망 확보
