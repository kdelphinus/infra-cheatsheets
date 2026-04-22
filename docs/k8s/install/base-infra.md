# 기반 인프라 (Helm & 스토리지 프로비저너) 설치

Kubernetes 운영에 필수적인 **Helm**과 로컬 동적 스토리지 프로비저너(**Local Path Provisioner**)를 설치하는 절차입니다. 환경(온라인/오프라인)과 운영체제(OS)에 맞춰 설치를 진행하십시오.

---

## 🚀 Phase 1: Helm 설치 (Master-1 Only)

Helm은 마스터 노드에서 쿠버네티스 패키지를 관리하는 도구이므로, **마스터 노드 1대**에만 설치하면 됩니다.

### 🌐 온라인 환경

인터넷 연결이 가능한 환경에서는 공식 스크립트를 통해 최신 버전을 간편하게 설치할 수 있습니다.

=== "Ubuntu 24.04"

    ```bash
    # 필수 패키지(curl) 설치 확인 후 Helm 스크립트 실행
    sudo apt-get update && sudo apt-get install -y curl
    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    
    # 설치 확인
    helm version
    ```

=== "Rocky Linux 9.6"

    ```bash
    # 필수 패키지(curl) 설치 확인 후 Helm 스크립트 실행
    sudo dnf install -y curl
    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    
    # 설치 확인
    helm version
    ```

### 🔒 오프라인 (폐쇄망) 환경

인터넷이 차단된 환경에서는 사전에 다운로드한 바이너리 파일을 사용합니다.

=== "Ubuntu & Rocky 공통"

    ```bash
    # 1. 바이너리 폴더로 이동 (준비된 오프라인 패키지 경로)
    # 예: cd ~/k8s-offline/k8s/binaries
    
    # 2. 압축 해제
    tar -zxvf helm-v3.14.0-linux-amd64.tar.gz
    
    # 3. 실행 파일을 시스템 경로로 이동
    sudo mv linux-amd64/helm /usr/local/bin/helm
    
    # 4. 설치 확인
    helm version
    ```

---

## 🚀 Phase 2: Local Path Provisioner (영구 저장소) 설치

애플리케이션이 PVC(PersistentVolumeClaim)를 요청할 때, 파드가 실행 중인 노드의 로컬 디렉토리를 자동으로 할당해주는 동적 프로비저너를 설치합니다.

### 🌐 온라인 환경

=== "Ubuntu & Rocky 공통"

    ```bash
    # 1. 매니페스트 적용 (원격 저장소에서 직접 다운로드 및 적용)
    kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.28/deploy/local-path-storage.yaml
    
    # 2. 기본 스토리지 클래스로 지정 (자동 할당용)
    kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
    
    # 3. 상태 확인
    kubectl get pods -n local-path-storage
    ```

### 🔒 오프라인 (폐쇄망) 환경

오프라인 환경에서는 사전에 받아둔 매니페스트 파일과 로컬 레지스트리(Harbor 등)에 푸시된 이미지를 사용해야 합니다.

=== "Ubuntu & Rocky 공통"

    ```bash
    # 1. 매니페스트 적용 (오프라인 패키지에 포함된 yaml 사용)
    # cd ~/k8s-offline/k8s/utils
    kubectl apply -f local-path-storage.yaml
    
    # 2. 기본 스토리지 클래스로 지정 (자동 할당용)
    kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
    
    # 3. 상태 확인
    kubectl get pods -n local-path-storage
    ```

---

## 💡 참고 사항

- **Envoy Gateway**: L7 트래픽 제어를 위한 Envoy Gateway 설치는 [Gateway API 가이드](../gateway-api/envoy-v1.37.2-install.md)를 참고하십시오.
- **Harbor**: 사설 레지스트리 Harbor 설치는 [CI/CD 가이드](../../cicd/offline-install/000-harbor-install.md)를 참고하십시오.
