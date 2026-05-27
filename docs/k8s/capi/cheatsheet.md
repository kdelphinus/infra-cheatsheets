# ☸️ Cluster API (CAPI) & 리소스 관리 Cheat Sheet

이 문서는 **Cluster API (CAPI)** 환경에서 배포된 쿠버네티스 워크로드 클러스터(dev, stg, prd)의 상태 검증, 리소스 모니터링, NetApp Trident 연동 API 호출 및 삭제 장애 발생 시 **finalizers** 수동 소거를 통한 강제 클린업 가이드라인을 집약한 치트시트예요.

---

## 1. 생성된 워크로드 클러스터 상태 진단

CAPI가 생성한 워크로드 클러스터의 관리용 `kubeconfig` 보안 비밀 값(Secret)을 디코딩하여 노드 및 파드의 런타임 가동 현황을 교차 검증해요.

### 💻 개발(dev) 환경
```bash
# 1.1 Secret 리소스에서 kubeconfig 추출 및 Base64 디코딩
kubectl get secret dev-cluster-kubeconfig -n default -o jsonpath='{.data.value}' | base64 -d > dev.kubeconfig

# 1.2 노드 상태 점검
kubectl --kubeconfig=dev.kubeconfig get nodes

# 1.3 전체 네임스페이스 파드 구동 상태 진단
kubectl --kubeconfig=dev.kubeconfig get pods -A
```

### 🖥️ 스테이징(stg) 환경
```bash
# 2.1 Secret 리소스에서 kubeconfig 추출 및 Base64 디코딩
kubectl get secret stg-cluster-kubeconfig -n default -o jsonpath='{.data.value}' | base64 -d > stg.kubeconfig

# 2.2 노드 상태 점검
kubectl --kubeconfig=stg.kubeconfig get nodes

# 2.3 전체 네임스페이스 파드 구동 상태 진단
kubectl --kubeconfig=stg.kubeconfig get pods -A
```

### 🚀 운영(prd) 환경
```bash
# 3.1 Secret 리소스에서 kubeconfig 추출 및 Base64 디코딩
kubectl get secret prd-cluster-kubeconfig -n default -o jsonpath='{.data.value}' | base64 -d > prd.kubeconfig

# 3.2 노드 상태 점검
kubectl --kubeconfig=prd.kubeconfig get nodes

# 3.3 전체 네임스페이스 파드 구동 상태 진단
kubectl --kubeconfig=prd.kubeconfig get pods -A
```

---

## 2. CAPI 플랫폼 및 vSphere 리소스 일괄 모니터링

CAPI 아키텍처를 이루는 주요 CRD 자원의 라이프사이클을 전체 네임스페이스 단위로 빠르게 조회하는 명령어 모음이에요.

### 2.1 CAPI 코어 컴포넌트 자원 스캔
클러스터 토폴로지, 머신 배포 그룹 및 제어 평면(KubeadmControlPlane) 명세를 조회해요.
```bash
kubectl get \
  cluster,machinedeployments,machinesets,machines,kubeadmcontrolplanes,kubeadmconfigtemplates \
  -A
```

### 2.2 인프라 프로바이더(vSphere) 특화 자원 스캔
VMware vSphere 하이퍼바이저 맵 상에 할당된 머신 템플릿과 노드 매핑 관계를 조회해요.
```bash
kubectl get \
  vsphereclusters,vspheremachines,vspheremachinetemplates \
  -A
```

---

## 3. NetApp NAS 스토리지 클래스 구성 API 연동 (stg 기준)

스테이징(stg) 환경 등의 플랫폼 API Gateway를 통하여 NetApp Trident 스토리지 클래스를 바인딩하고 NAS 스토리지 연동 규격을 동적 전송하는 API 포스팅 규격 예시예요.

*   **API 엔드포인트 URL**: `http://10.185.40.44:31012/api/v2/storage-class/nas-config`
*   **헤더 요건**: 
    *   `Authorization: Bearer 4f051dcf-1a6e-4889-b39d-bc59f8364545`
    *   `Content-Type: application/json`

```bash
curl -X 'POST' \
  'http://10.185.40.44:31012/api/v2/storage-class/nas-config' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer 4f051dcf-1a6e-4889-b39d-bc59f8364545' \
  -H 'Content-Type: application/json' \
  -d '{
  "serviceGroupUuid": "687fa180-d4f0-4bad-8533-321bf9b272aa",
  "cloudType": "VMWARE",
  "netapp": {
    "credential": {
      "userId": "vsadmin",
      "password": "#anfmv44"
    },
    "managementLif": "172.16.126.146",
    "svm": "LGEHQ_K8S1_QA",
    "dataLifs": [
      "172.16.126.145"
    ],
    "exportPolicy": "default"
  }
}'
```

---

## 4. CAPI 자원 안전 삭제 프로토콜

배포된 워크로드 클러스터를 명시적으로 폐기할 때 리소스 꼬임이나 교착 상태(Deadlock)를 방지하기 위한 표준 순차 삭제 절차예요.

```bash
# 4.1 클러스터 이름 변수 설정
CLUSTER="dev-cluster"

# 4.2 컨트롤플레인 및 머신 배포 그룹 정상 삭제 명령 전송 (비동기 트리거)
kubectl delete \
  machinedeployments,machinesets,machines,kubeadmcontrolplanes,kubeadmconfigtemplates \
  -l cluster.x-k8s.io/cluster-name="$CLUSTER" \
  --wait=false

# 4.3 vSphere 하위 자원 명시적 차단 삭제 명령
kubectl delete vsphereclusters,vspheremachines,vspheremachinetemplates \
  -l cluster.x-k8s.io/cluster-name="$CLUSTER" \
  --wait=false
```

---

## 🚨 5. 리소스 삭제 장애 시 Finalizer 강제 해제 패치 (강력 권장)

> [!WARNING]
> CAPI 머신이나 클러스터 리소스를 삭제할 때 하이퍼바이저 통신 차단, 제어 루프 에러 등으로 인해 `Terminating` 상태에 영구 고착되는 장애가 빈번히 발생해요. 
> 
> 이 경우, 객체의 무덤 마크 역할을 하는 **`finalizers` 지문을 null 패치**하여 자원을 완벽하게 강제 소거시킬 수 있어요.

```bash
# 대상 클러스터 명칭 지정
CLUSTER="dev-cluster"

# 5.1 CAPI 핵심 클러스터 객체의 finalizer 강제 리셋
kubectl patch cluster "$CLUSTER" \
  -p '{"metadata":{"finalizers":null}}' \
  --type=merge

# 5.2 vSphere 인프라용 클러스터 객체의 finalizer 강제 리셋
kubectl patch vspherecluster "$CLUSTER" \
  -p '{"metadata":{"finalizers":null}}' \
  --type=merge

# 5.3 해당 클러스터의 vSphere 크레덴셜 보안 비밀(Secret) finalizer 제거
kubectl patch secret "$CLUSTER-vsphere-credentials" \
  -p '{"metadata":{"finalizers":null}}' \
  --type=merge
```
> [!TIP]
> 위 패치 명령이 들어간 직후 `kubectl get cluster -A` 조회를 진행하면 오랫동안 Terminating 상태로 얽혀있던 클러스터 정보가 원천 클리어된 것을 체감할 수 있어요.
