# 폐쇄망용 설치 파일 준비 (Ubuntu)

이 문서는 Ubuntu 24.04 등 Ubuntu 환경의 폐쇄망 쿠버네티스 구축을 위해 인터넷이 연결된 호스트에서 설치 파일(Debian 패키지, 컨테이너 이미지, 바이너리)을 준비하는 과정을 안내합니다.

## 📌 1단계: 작업 환경 준비 (인터넷 호스트)

인터넷이 가능한 Ubuntu 호스트에서 K8s 설치용 스크립트 디렉토리로 이동합니다.

```bash
# 작업 디렉토리 생성 및 이동
mkdir -p ~/k8s-offline-prep
cd ~/k8s-offline-prep

# (예시) 프로젝트에서 제공하는 설치 스크립트 디렉토리 구조 확보
# git clone https://github.com/kdelphinus/infra-cheatsheets.git (또는 관련 파일 복사)
```

## 📌 2단계: 설치 파일 다운로드 (download.sh)

제공된 `scripts/download.sh` 스크립트를 실행하여 오프라인 설치에 필요한 모든 에셋을 다운로드합니다. 이 스크립트는 `apt-get download`를 통해 DEB 패키지를 캐싱하고, `ctr` 또는 `docker`를 통해 K8s 컨트롤 플레인 및 CNI(Calico/Cilium) 이미지를 `tar`로 묶어 저장합니다.

```bash
# sudo 권한으로 다운로드 스크립트 실행
sudo ./scripts/download.sh
```

**스크립트 주요 동작:**
- **DEB 패키지**: `kubeadm`, `kubelet`, `kubectl`, `containerd.io`, `haproxy`, `keepalived` 및 필수 의존성 패키지 다운로드 (`k8s/debs/`)
- **컨테이너 이미지**: API Server, etcd, CoreDNS 등 K8s 핵심 이미지 및 CNI 관련 이미지 다운로드 후 tar 저장 (`k8s/images/`)
- **바이너리**: `helm`, `nerdctl` 등 필수 도구 다운로드 (`k8s/binaries/`)

## 📌 3단계: 폐쇄망용 압축 파일 생성

다운로드가 완료되면 해당 디렉토리 전체를 압축하여 폐쇄망 서버로 반입할 준비를 마칩니다.

```bash
cd ..
# 버전 정보를 포함하여 압축 (예: k8s-ubuntu-offline.tar.gz)
tar czf k8s-ubuntu-offline.tar.gz ./k8s-offline-prep
```

이제 생성된 압축 파일을 USB나 망연계 솔루션을 통해 폐쇄망의 대상 노드들로 이동시킨 후, [오프라인 설치 가이드](./offline-install.md)를 따라 설치를 진행합니다.
