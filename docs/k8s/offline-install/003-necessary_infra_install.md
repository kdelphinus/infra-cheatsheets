# 기반 인프라 (Helm & 스토리지 프로비저너) 설치

폐쇄망 환경에서 Kubernetes 운영에 필수적인 Helm과 로컬 동적 스토리지 프로비저너를 설치하는 절차를 안내합니다.

- **가이드 환경**
  - **OS**: Rocky Linux 9.6 / Ubuntu 24.04 (공통)
- 폐쇄망용 K8s 설치 파일이 준비되어 있어야 합니다.

---

## 🚀 Phase 1: Helm 설치 (Master-1 Only)

Helm은 마스터 노드에서 명령어를 내리는 도구이므로, **마스터 노드 1대**에만 설치하면 됩니다.

**[실행 위치: K8s-Master-Node-1]**

```bash
# 1. 바이너리 폴더로 이동 (환경에 맞는 경로 지정)
# cd ~/k8s-offline/k8s/binaries

# 2. 압축 해제
tar -zxvf helm-v3.14.0-linux-amd64.tar.gz

# 3. 실행 파일을 시스템 경로로 이동
sudo mv linux-amd64/helm /usr/local/bin/helm

# 4. 설치 확인
helm version
```

---

## 🚀 Phase 2: Local Path Provisioner (영구 저장소) 설치

애플리케이션이 PVC를 요청할 때 노드의 로컬 디렉토리를 자동으로 할당해주는 동적 프로비저너를 설치합니다.

**[Master-1 노드]**

```bash
# 1. 매니페스트 적용
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
