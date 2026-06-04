# Rocky Linux 9 기반 K8s VM 템플릿 복사 및 업그레이드 가이드

이 가이드는 이미 제작된 쿠버네티스(Kubernetes) 노드용 VM 템플릿을 복사(복제)하여, 새로운 버전의 쿠버네티스 버전이 적용된 신규 VM 템플릿을 제작하는 절차를 다룹니다.

**K8s 업그레이드는 반드시 `1.33.x` -> `1.34.x` 와 같이 1단계씩 진행해야 합니다.**

---

## 전체 작업 흐름

1. 기존 K8s VM 템플릿 복제 및 부팅
2. Kubernetes RPM 저장소 버전 정보 업데이트
3. Kubernetes 구성 컴포넌트(kubeadm, kubelet, kubectl) 업그레이드 설치
4. 컨테이너 런타임(containerd) 및 샌드박스(Pause) 이미지 조율
5. 가상 머신 식별자 및 캐시 정보 초기화
6. 시스템 종료 및 템플릿 변환

---

## 상세 가이드

### 1단계. 기존 템플릿 복제 및 임시 VM 기동

기존에 정상 작동 중이던 템플릿( `K8M_1.33.7_C_VM_Rocky9.7` )을 복사하여 임시 가상 머신을 배포합니다.

1. vSphere에서 기존 템플릿을 복제합니다.
2. 복제한 템플릿을 가상 시스템으로 변환한 후 VM을 생성합니다.
3. 생성된 VM의 네트워크 연결을 복구한 후 전원을 켭니다.

---

### 2단계. K8s 리포지토리 정보 업데이트
쿠버네티스 마이너 버전(예: `v1.33` -> `v1.34`) 업그레이드를 진행하는 경우, 공식 패키지 저장소(RPM Repository) 설정 내의 주소를 대상 버전에 맞추어 수정해야 합니다.

> **패치 버전 업그레이드 시**  
> `v1.33.7`에서 `v1.33.8`처럼 마이너 버전이 바뀌지 않는 단순 패치 버전을 변경할 때에는 이 리포지토리 수정 단계를 건너뛰고 3단계로 진행하면 됩니다.

1. `/etc/yum.repos.d/kubernetes.repo` 파일을 편집기로 엽니다.
   ```bash
   sudo vi /etc/yum.repos.d/kubernetes.repo
   ```
2. `baseurl` 및 `gpgkey`에 명시되어 있는 버전 트랙 주소(예: `/v1.33/`)를 목표 버전에 부합하는 주소(예: `/v1.34/`)로 변경합니다.
   ```ini
   [kubernetes]
   name=Kubernetes
   baseurl=https://pkgs.k8s.io/core:/stable:/v1.34/rpm/
   enabled=1
   gpgcheck=1
   gpgkey=https://pkgs.k8s.io/core:/stable:/v1.34/rpm/repodata/repomd.xml.key
   exclude=kubelet kubeadm kubectl cri-tools kubernetes-cni
   ```

---

### 3단계. 신규 버전 K8s 패키지 업그레이드 설치
기존에 의도치 않은 자동 업데이트를 막기 위해 설정된 `exclude` 항목을 무시하고, 지정한 타겟 버전의 패키지를 DNF를 통해 명시적으로 설치합니다.

```bash
# 3.1 DNF 캐시 갱신
sudo dnf clean all
sudo dnf makecache

# 3.2 목표 버전을 명시하여 kubeadm, kubelet, kubectl 설치
# (아래 예시 버전 '1.34.0'은 실제 필요로 하는 버전으로 대체하여 입력해 주세요.)
sudo dnf install -y --disableexcludes=kubernetes \
    kubelet-1.34.0-* kubeadm-1.34.0-* kubectl-1.34.0-*
```

---

### 4단계. Containerd 및 샌드박스(Pause) 이미지 조율
쿠버네티스 버전이 바뀌면 컨테이너 런타임인 `containerd`의 샌드박스(Pause) 이미지 표준 버전 요구사항도 함께 변동될 수 있습니다. 이를 동기화합니다.

1. 설치된 Kubernetes가 지원하는 Pause 이미지 버전을 확인합니다.

```sh
# 1.34.0 버전을 확인할 때
kubeadm config images list --kubernetes-version=v1.34.0
```

```sh
# 출력 예시
registry.k8s.io/kube-apiserver:v1.34.0
registry.k8s.io/kube-controller-manager:v1.34.0
registry.k8s.io/kube-scheduler:v1.34.0
registry.k8s.io/kube-proxy:v1.34.0
registry.k8s.io/pause:3.11 # pause 버전을 확인합니다.
registry.k8s.io/etcd:3.5.15-0
registry.k8s.io/coredns/coredns:v1.11.3
```

2. `/etc/containerd/config.toml` 내의 `sandbox_image` 버전 매핑 정보를 확인하고 수정합니다.

   ```bash
   sudo vi /etc/containerd/config.toml
   ```

   `sandbox_image` 값을 `3.10`에서 `3.11`로 변경한다.

   ```toml
   [plugins.'io.containerd.cri.v1.images'.pinned_images]
     sandbox_image = 'registry.k8s.io/pause:3.11'
   ```

3. 설정을 반영하기 위해 `containerd` 서비스를 재시작합니다.
   ```bash
   sudo systemctl restart containerd
   ```

> **폐쇄망(Private Registry) 환경 주의**  
> 외부 네트워크 접속이 차단된 폐쇄망 환경의 사설 레지스트리(Harbor 등)를 사용 중이라면, 템플릿 배포 및 노드 가동 시 새로운 샌드박스 이미지를 정상적으로 가져올 수 있도록 **사설 레지스트리 내에 신규 pause 이미지를 업로드하고 `{HARBOR_URL}/{HARBOR_PROJECT}/pause:3.11` 와 같이 경로를 수정해야합니다.**

---

### 5단계. VM 템플릿 배포용 시스템 청소 (필수)
새로운 템플릿에서 추후 복제될 VM들이 IP 중복, UUID 및 호스트명 충돌, cloud-init 캐시 오류를 겪지 않도록 임시 데이터와 식별자를 모두 제거합니다.

```bash
# 5.1 NetworkManager 유동 IP 연결 설정 삭제
sudo rm -f /etc/NetworkManager/system-connections/*.nmconnection

# 5.2 netplan 경로 디렉토리 내 임시 설정 삭제
sudo rm -f /etc/netplan/*
sudo systemctl restart NetworkManager

# 5.3 cloud-init 히스토리 로그 및 캐시 제거
sudo cloud-init clean --logs
sudo rm -rf /var/lib/cloud/*

# 5.4 machine-id 초기화 (이후 부팅 시 새 UUID가 정상 할당되도록 설정)
sudo truncate -s 0 /etc/machine-id
sudo rm -f /var/lib/dbus/machine-id

# 5.5 저널로그 캐시 공간 초기화
sudo journalctl --vacuum-time=0

# 5.6 임시 디렉토리 정리
sudo rm -rf /tmp/*

# 5.7 쉘 히스토리 비우기
history -c && history -w

# 5.8 가상 머신 종료
sudo poweroff
```

---

### 6단계. 신규 템플릿 변환

1. VM 전원이 완전히 꺼진 후, 가상화 솔루션 콘솔에서 해당 VM을 다시 **템플릿으로 변환** 합니다.
2. 이때 이름은 아래와 같이 네이밍 규칙에 맞게 변경합니다.
   - 마스터노드: `K8M_{K8S 버전}_C_VM_{OS}` (예시: `K8M_1.34.0_C_VM_Rocky9.7`)
   - 워커노드: `K8W_{K8S 버전}_C_VM_{OS}` (예시: `K8W_1.34.0_C_VM_Rocky9.7`)

