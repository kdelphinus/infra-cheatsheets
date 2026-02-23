# 💽 NAS PV 연결 가이드

이 가이드는 쿠버네티스(K8s) 환경에서 NAS(NFS)를 영구 볼륨(PV)으로 연결하는 방법을 설명합니다. 신규 서비스 배포와 기존 데이터 이관 상황에 맞춰 선택하여 적용하실 수 있습니다.

---

## 0단계: 공통 사전 준비 (A안, B안 공통)

K8s PV를 생성하기 전, NAS 서버 내부에 각 서비스가 사용할 하위 디렉토리를 미리 생성해야 합니다.

### Step 1: 오프라인 패키지 설치 및 서비스 기동

모든 워커 노드에서 NFS 클라이언트 패키지를 설치하고 서비스를 활성화합니다.

```bash
cd /경로/nfs_package_bundle
sudo dnf localinstall *.rpm -y
sudo systemctl enable --now rpcbind
```

### Step 2: NAS 출입구(Export Path) 확인

임의의 워커 노드에서 아래 명령어를 실행하여 NAS 서버가 허용한 경로를 확인합니다.

```bash
showmount -e <NAS_IP>
```

!!! info "결과 예시"
    `/applog *` (이 가이드에서는 `/applog`가 NAS의 기본 출입구라고 가정합니다.)

### Step 3: 워커 노드 마운트 및 하위 폴더 생성

NAS 내부 공간에 서비스별 전용 폴더를 생성합니다. 이 작업은 **하나의 노드에서 한 번만** 수행하면 됩니다.

```bash
# 1. 임시 마운트 포인트 생성
mkdir -p /mnt/nas_root

# 2. NAS 출입구를 임시 폴더에 연결
sudo mount -t nfs <NAS_IP>:/applog /mnt/nas_root

# 3. NAS 내부로 이동하여 서비스별 폴더 생성
cd /mnt/nas_root
mkdir grafana mariadb prometheus

# 4. 권한 부여 (Pod가 접근할 수 있도록 권한을 개방합니다)
chmod -R 777 /mnt/nas_root/*

# 5. 작업 완료 후 마운트 해제
cd ~
sudo umount /mnt/nas_root
```

!!! tip "PV 작성 시 경로 매핑 공식"
    쿠버네티스 PV YAML의 `path`는 다음과 같이 조합됩니다.
    
    *   **공식:** `NAS 출입구 경로` + `/` + `생성한 하위 디렉토리 이름`
    *   **예시:** `path: /applog/grafana`

---

## [A안] 신규 서비스 생성 시

기존 데이터가 없는 상태에서 처음부터 NAS를 연결하여 배포하는 방식입니다.

### Step A-1: PV 및 PVC 생성

0단계에서 생성한 하위 경로를 지정하여 K8s 객체를 생성합니다.

```yaml
# a-storage.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-grafana
spec:
  capacity:
    storage: 10Gi
  accessModes: ["ReadWriteMany"]
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual-nas
  nfs:
    server: <NAS_IP>
    path: /applog/grafana
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-grafana
  namespace: monitoring
spec:
  accessModes: ["ReadWriteMany"]
  storageClassName: manual-nas
  resources:
    requests:
      storage: 10Gi
  volumeName: pv-grafana
```

### Step A-2: Deployment 배포 (InitContainer 포함)

권한 문제를 방지하기 위해 `initContainers`를 포함하여 배포합니다.

```yaml
# a-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  replicas: 1
  template:
    spec:
      securityContext:
        fsGroup: 472
      initContainers:
        - name: fix-permissions
          image: busybox
          command: ["sh", "-c", "chown -R 472:472 /var/lib/grafana"]
          securityContext:
            runAsUser: 0
          volumeMounts:
            - name: grafana-storage
              mountPath: /var/lib/grafana
      containers:
        - name: grafana
          volumeMounts:
            - name: grafana-storage
              mountPath: /var/lib/grafana
      volumes:
        - name: grafana-storage
          persistentVolumeClaim:
            claimName: pvc-grafana
```

---

## [B안] 기존 데이터 이관 시

운영 중인 `hostPath` 데이터를 보존하면서 스토리지를 NAS로 교체하는 방식입니다.

### Step B-1: PV 및 PVC 사전 생성

[A안]의 `Step A-1`과 동일하게 PV와 PVC를 미리 생성해 둡니다.

### Step B-2: 1차 데이터 동기화 (무중단)

서비스 중단 없이 기존 데이터를 NAS로 복사합니다.

```bash
mkdir -p /mnt/nas_temp
sudo mount -t nfs <NAS_IP>:/applog /mnt/nas_temp

# 기존 hostPath에서 NAS로 데이터 복사 (원본 경로 뒤에 /를 붙여주세요)
sudo rsync -avh /monitoring/grafana/ /mnt/nas_temp/grafana/
```

### Step B-3: 컷오버 및 최종 동기화 (최소 중단)

쓰기 작업을 방지하기 위해 Pod를 정지시킨 후 잔여 데이터를 복사합니다.

```bash
# 1. Pod 일시 중지
kubectl scale deployment grafana -n monitoring --replicas=0

# 2. 최종 데이터 동기화 (삭제된 파일까지 일치시킵니다)
sudo rsync -avh --delete /monitoring/grafana/ /mnt/nas_temp/grafana/
```

### Step B-4: Deployment 업데이트 및 재개

`hostPath` 설정을 제거하고 생성한 PVC로 교체합니다.

```yaml
# b-deployment-update.yaml (Volumes 부분 수정)
volumes:
  - name: grafana-storage
    persistentVolumeClaim:
      claimName: pvc-grafana
```

!!! note "마무리"
    정상 기동이 확인되면 임시 마운트를 해제합니다: `sudo umount /mnt/nas_temp`

---

## 설계 트레이드오프 분석

| 비교 항목 | [A안] 신규 생성 | [B안] 기존 데이터 이관 |
| :--- | :--- | :--- |
| **작업 복잡도** | **매우 낮음.** YAML 배포로 완료. | **높음.** 수동 복사 작업 필요. |
| **데이터 보존** | 초기화 상태로 시작. | 기존 설정과 데이터가 완벽히 유지됨. |
| **서비스 중단** | 영향 없음. | 동기화 시점에 수 분 이내의 중단 발생. |
| **권장 상황** | 신규 구축 또는 테스트 환경. | 운영 중인 프로덕션 시스템. |
