# 📖 다중 마스터 환경의 etcd 전용 디스크 마이그레이션 절차서 (SOP 완성형 최종 승인판)

본 문서는 다중 마스터(Stacked etcd) 환경에서 각 마스터 노드의 etcd 데이터 디렉토리(`/var/lib/etcd`)를 신규 LVM 볼륨으로 안전하게 격리/이전하는 표준 운영 절차를 정의합니다.

---

## 🚫 [필독] 사전 인지 및 격리 원칙

### 1. 단일 장애점(SPOF) 해소 조건
본 작업은 디렉토리의 입출력 부하를 격리하는 절차입니다. 볼륨 자체의 디스크 장애 대비(예: AWS EBS GP3 볼륨 정책, 스토리지 RAID 구성 등)가 인프라 아키텍처 수준에서 별도로 확보되어야 합니다.

### 2. 로드밸런서(LB) 사전 점검 및 인증서 TLS SAN 확인
* 마스터 1대를 작업하는 동안, 외부 로드밸런서(LB)에서 해당 마스터의 6443 포트(API Server)가 정상적으로 **제외(Deregister/Out-of-service)**되는지 모니터링해야 합니다.
* etcdctl 통신 시 외부 IP를 사용하는 경우, **인증서의 주체 대체 이름(SAN)에 해당 마스터 IP가 포함**되어 있어야 TLS 오류가 나지 않습니다.
  ```bash
  # 인증서 SAN IP 포함 여부 사전 확인
  sudo openssl x509 -in /etc/kubernetes/pki/etcd/server.crt -text -noout | grep -A 1 "Subject Alternative Name"
  ```

### 3. 롤백(Rollback)과 스냅샷 복구(Snapshot Restore)의 관계 분리
* 본 문서에서 제공하는 **롤백 절차는 단순히 물리 디바이스와 원본 데이터 디렉토리를 원복하는 과정**입니다.
* etcd 데이터 자체의 훼손으로 인한 **스냅샷 복구(Snapshot Restore)는 API Server를 내리고 revision을 bump한 후 compaction 처리를 고려해야 하는 별도의 재해 복구 영역**입니다. 
* 본 절차 진행 도중 예상 외 데이터 유실이 확인되더라도, [etcd 재해복구 가이드](https://etcd.io/docs/v3.5/op-guide/recovery/)에 명시된 엄격한 가이드라인 없이 **스냅샷 복구를 즉흥적으로 수행해서는 절대 안 됩니다.**

### 4. ⚠️ [세션 끊김 시 수칙] 실행 쉘 세션 관리
* **모든 Step은 Step 0-A를 실행한 동일한 쉘 세션에서 연속 수행함을 전제로 합니다.**
* 만약 네트워크 끊김, SSH 재접속 등으로 **쉘 세션이 변경되거나 재시작된 경우**, 이어서 작업을 진행하기 전에 **반드시 아래 [Step 0-A]의 쉘 초기화 블록만 다시 실행**한 뒤 다음 단계 작업을 이어가십시오. (etcd 중단 상태에서 사전 검증을 돌리면 스크립트가 중단됩니다.)

---

## 🛠️ [단계 0-A] 공통 셸 초기화 (세션 재접속 시 필수 재실행)

```bash
# [중요] 스크립트 세션 중 에러 발생 시 즉시 중단 처리 및 파이프라인 에러 전파 활성화
set -euo pipefail

# =========================================================================
# [운영자 설정] 작업 대상 노드 정보에 맞추어 변수를 편집하십시오.
# =========================================================================
export TARGET_DISK="/dev/vdb"          # 대상 신규 디스크
export FS_TYPE="ext4"                  # ext4 또는 xfs
export BACKUP_DIR="/var/backups/etcd"  # 안전한 영구 로컬 백업 디렉토리
export CLUSTER_ENDPOINTS="https://10.0.0.11:2379,https://10.0.0.12:2379,https://10.0.0.13:2379" # 전체 마스터 IP 목록
# =========================================================================

# 1. 백업 디렉토리 생성 및 권한 제한 (로그 저장 전 반드시 먼저 수행)
sudo mkdir -p "${BACKUP_DIR}"
sudo chmod 700 "${BACKUP_DIR}"
sudo chown root:root "${BACKUP_DIR}"

# 2. 파일시스템 타입 검증
case "${FS_TYPE}" in
  ext4|xfs) echo "FS_TYPE 검증 통과: ${FS_TYPE}" ;;
  *) echo "[ERROR] FS_TYPE은 ext4 또는 xfs여야 합니다." >&2; exit 1 ;;
esac

# 3. 인증 통과용 etcdctl 쉘 함수 선언
etcdctl_auth() {
  sudo ETCDCTL_API=3 etcdctl \
    --cacert=/etc/kubernetes/pki/etcd/ca.crt \
    --cert=/etc/kubernetes/pki/etcd/server.crt \
    --key=/etc/kubernetes/pki/etcd/server.key \
    "$@"
}
```

---

## 🛠️ [단계 0-B] 작업 전 클러스터 사전 검증 (작업 개시 전 최초 1회만 실행)

```bash
set -euo pipefail

# 1. 작업 전 클러스터 멤버 상태 및 Raft 동기화(RAFT INDEX) 정보 확인 및 로그 저장 (sudo tee 사용으로 권한 분리 에러 방지)
etcdctl_auth --endpoints=${CLUSTER_ENDPOINTS} member list -w table | sudo tee "${BACKUP_DIR}/etcd_member_pre.log" >/dev/null
etcdctl_auth --endpoints=${CLUSTER_ENDPOINTS} endpoint status --cluster -w table | sudo tee -a "${BACKUP_DIR}/etcd_member_pre.log" >/dev/null

# 2. 기존 로그 확인 (백업 폴더가 700 root이므로 sudo cat 수행)
sudo cat "${BACKUP_DIR}/etcd_member_pre.log"
```

---

## 💻 [단계별 마이그레이션 작업] (마스터 노드별 순차 진행)

### Step 1. etcd 논리적 스냅샷 백업 및 외부 소산 (필수 관문)
이 단계는 단순 권장 사항이 아니라 **본 작업을 계속 진행하기 위해 도달해야 하는 게이트(Gate)**입니다.

```bash
set -euo pipefail

# 1. 스냅샷 파일명 정의 (호스트명 및 타임스탬프 부여로 덮어쓰기 방지)
export SNAPSHOT_FILE="${BACKUP_DIR}/etcd-pre-migration-$(hostname)-$(date +%Y%m%d%H%M%S).db"

# 2. Local etcd 스냅샷 백업 실행
etcdctl_auth --endpoints=https://127.0.0.1:2379 snapshot save "${SNAPSHOT_FILE}"

# 3. etcdutl을 통한 백업본 정상 진단
sudo etcdutl snapshot status "${SNAPSHOT_FILE}" -w table

# 4. [기밀성 보호 및 외부 소산] 백업 파일을 외부 안전한 원격 스토리지(Bastion 등)로 강제 전송
# (※ 아래 명령어는 예시이며, 실제 전송 시에는 소속 조직의 표준 원격 복사 도구 및 전송 방식을 사용하십시오.)
# 예: sudo scp -i /root/.ssh/id_rsa "${SNAPSHOT_FILE}" user@bastion-host:/secure/backups/

# 5. [필수 게이트 확인] 운영자 수동 승인 게이트
read -r -p "⚠️ [확인] 스냅샷 파일 외부 소산 및 복구 가능성 확인이 완료되었습니까? (type BACKUP_OK): " BACKUP_CONFIRM
if [ "${BACKUP_CONFIRM}" != "BACKUP_OK" ]; then
  echo "백업 외부 전송이 확인되지 않아 작업을 강제 중단합니다."
  exit 1
fi
```

### Step 2. 신규 디스크 파기 전 검증 및 LVM 구성 (Fail-Closed)
잘못된 대상 디스크 선정이나 LVM 중복 생성으로 인한 데이터 손실을 사전에 차단합니다.

```bash
set -euo pipefail

# 1. [LVM 중복 생성 방지 가드]
if sudo vgs vg-etcd &>/dev/null || sudo lvs vg-etcd/lv-etcd &>/dev/null; then
  echo "[ERROR] LVM 볼륨 그룹 vg-etcd 또는 논리 볼륨 lv-etcd가 이미 존재합니다. 작업을 중단합니다." >&2
  exit 1
fi

# 2. [대상 디스크 마운트 여부 검증]
if lsblk -nro MOUNTPOINT "${TARGET_DISK}" | grep -q '/'; then
  echo "[ERROR] ${TARGET_DISK} 또는 하위 디바이스가 이미 마운트되어 있습니다. 작업을 중단합니다." >&2
  exit 1
fi

# 3. [기존 메타데이터 검증] 파일시스템이나 파티션 정보가 감지되면 강제 중단
if sudo wipefs -n "${TARGET_DISK}" | grep -q 'offset'; then
  echo "[ERROR] ${TARGET_DISK}에 기존 파일시스템/파티션 서명이 남아있습니다. 작업을 중단합니다." >&2
  sudo wipefs -n "${TARGET_DISK}"
  exit 1
fi

# 4. [운영자 수동 최종 게이트]
read -r -p "⚠️ 경고: ${TARGET_DISK}의 모든 데이터가 유실됩니다. 계속하시겠습니까? (type YES): " CONFIRM
if [ "${CONFIRM}" != "YES" ]; then
  echo "작업이 취소되었습니다."
  exit 1
fi

# 5. LVM 구성 및 포맷
sudo pvcreate ${TARGET_DISK}
sudo vgcreate vg-etcd ${TARGET_DISK}
sudo lvcreate -l 100%FREE -n lv-etcd vg-etcd
sudo mkfs.${FS_TYPE} /dev/vg-etcd/lv-etcd

# 6. 임시 마운트 적용
sudo mkdir -p /mnt/etcd-temp
sudo mount /dev/vg-etcd/lv-etcd /mnt/etcd-temp
```

### Step 3. 컨트롤 플레인 서비스 및 etcd 컨테이너 완전 정지 검증
CRI 도구의 조회 실패 여부와 Kubelet 중지 후 실제 컨테이너의 정지 여부를 순차적으로 엄격히 검증합니다.

```bash
set -euo pipefail

# 1. [CRI 도구 동작성 사전 검증] crictl 자체 장애(소켓 오류 등)로 인한 정지 오인 방지
if ! sudo crictl ps >/tmp/crictl-ps-check.log 2>&1; then
  echo "[ERROR] crictl ps 조회 실패. CRI 런타임이 통신 불능 상태이므로 작업을 중단합니다." >&2
  sudo cat /tmp/crictl-ps-check.log >&2
  exit 1
fi

# 2. Kubelet 중지
sudo systemctl stop kubelet

# 3. etcd 컨테이너 다운 여부 3초 간격 반복 확인 (최대 10회)
echo "etcd 컨테이너 정지 대기 중..."
for i in {1..10}; do
  # crictl 명령의 결과값(ID 목록)을 변수로 직접 할당하여 판정
  ETCD_CONTAINERS=$(sudo crictl ps --name etcd -q)
  if [ -z "${ETCD_CONTAINERS}" ]; then
    echo "etcd 컨테이너가 완전히 정지되었습니다."
    break
  fi
  if [ $i -eq 10 ]; then
    echo "[WARNING] etcd 컨테이너가 꺼지지 않아 강제 종료를 시도합니다."
    echo "${ETCD_CONTAINERS}" | xargs -r sudo crictl stop
  fi
  sleep 3
done

# 4. [컨테이너 강제 확인 가드] etcd 컨테이너가 여전히 실행 중이면 즉시 중단
if sudo crictl ps | awk 'NR>1 && $0 ~ /etcd/ {found=1} END {exit found ? 0 : 1}'; then
  echo "[ERROR] etcd 컨테이너가 아직 실행 중입니다. 수동 확인 및 수동 프로세스 킬이 필요합니다." >&2
  sudo crictl ps --name etcd
  exit 1
fi

# 5. 컨테이너 런타임 중지 및 프로세스 점유 상태 검증 (lsof 없으면 fuser 사용)
sudo systemctl stop containerd

if command -v lsof &>/dev/null; then
  sudo lsof +D /var/lib/etcd || echo "etcd 디렉토리가 완전히 점유 해제되었습니다."
elif command -v fuser &>/dev/null; then
  sudo fuser -vm /var/lib/etcd || echo "etcd 디렉토리가 완전히 점유 해제되었습니다."
else
  echo "[WARNING] lsof/fuser가 모두 누락된 환경입니다. 5초 대기 후 수동 확인 권장."
  sleep 5
fi
```

### Step 4. 권한 보존 복제 및 오너십 백업
rsync 복사로 내부 파일 속성을 보존하고, dry-run/checksum/itemize-changes 대조를 통한 물리적 동질성 확보 및 파일 개수 불일치 진단을 최종 교차 검토합니다.

```bash
set -euo pipefail

# 1. 메타데이터, 확장속성(SELinux 포함)을 보존하여 복사 (로컬 간 복사이므로 -z 제외)
sudo rsync -aHAX --numeric-ids /var/lib/etcd/ /mnt/etcd-temp/

# 2. [데이터 동일성 상세 정밀 검증] dry-run + checksum + itemize-changes 3종 대조
echo "=== 데이터 정합성 상세 검증 ==="
# 복사본에 미세한 속성/데이터 오차가 있을 경우에만 결과물이 DIFF_CHECK에 기록됩니다.
DIFF_CHECK=$(sudo rsync -aHAX --numeric-ids --dry-run --checksum --itemize-changes /var/lib/etcd/ /mnt/etcd-temp/)
if [ -n "${DIFF_CHECK}" ]; then
  echo "[ERROR] 복제된 데이터에 원본과 불일치하는 물리적 오차가 감지되었습니다. 수동 점검이 필요합니다." >&2
  echo "${DIFF_CHECK}"
  exit 1
fi

# 3. [복제 메타데이터 검증] 원본과 대상의 용량 및 파일 개수 비교 확인
sudo du -sh /var/lib/etcd /mnt/etcd-temp
export SRC_COUNT=$(sudo find /var/lib/etcd -xdev | wc -l)
export DEST_COUNT=$(sudo find /mnt/etcd-temp -xdev | wc -l)
echo "원본 파일 개수: ${SRC_COUNT} | 신규 복사본 파일 개수: ${DEST_COUNT}"

if [ "${SRC_COUNT}" -ne "${DEST_COUNT}" ]; then
  echo "[ERROR] 원본 파일과 복사된 파일의 개수가 일치하지 않습니다. 복제를 수동 진단하십시오." >&2
  exit 1
fi

# 4. 기존 디렉토리 최상위의 numeric 소유권 및 권한 값 백업
export ETCD_UID=$(stat -c '%u' /var/lib/etcd)
export ETCD_GID=$(stat -c '%g' /var/lib/etcd)
export ETCD_PERM=$(stat -c '%a' /var/lib/etcd)

# 5. 임시 마운트 해제
sudo umount /mnt/etcd-temp
```

### Step 5. 신규 볼륨 마운트 및 최상위 디렉토리 오너십 복구
기존 디바이스를 백업명으로 돌린 후, 실제 새 장치가 정상 마운트되었음을 판정한 다음에 권한 및 SELinux를 설정합니다.

```bash
set -euo pipefail

# 1. 기존 etcd 디렉토리 백업명 변경
sudo mv /var/lib/etcd /var/lib/etcd.bak

# 2. 신규 디렉토리 생성 및 마운트
sudo mkdir -p /var/lib/etcd
sudo mount /dev/vg-etcd/lv-etcd /var/lib/etcd

# 3. [마운트 검증 가드] mountpoint 판정 통과 여부 확인
mountpoint -q /var/lib/etcd || {
  echo "[ERROR] 신규 볼륨 마운트가 실패했습니다. 이 상태에서 파일 수정을 진행하면 안 됩니다." >&2
  exit 1
}

# 4. 최상위 디렉토리 권한만 복원 (하위 파일은 rsync 보존값 유지, 재귀 chown -R 금지)
sudo chown ${ETCD_UID}:${ETCD_GID} /var/lib/etcd
sudo chmod ${ETCD_PERM} /var/lib/etcd

# 5. SELinux 보안 콘텍스트 복구 (Rocky Linux 등)
if command -v selinuxenabled &>/dev/null && selinuxenabled; then
    echo "SELinux 감지됨. 보안 콘텍스트 복구를 수행합니다."
    sudo restorecon -Rv /var/lib/etcd
    ls -Zd /var/lib/etcd
else
    echo "SELinux 미활성 또는 Ubuntu 환경입니다. 생략합니다."
fi
```

### Step 6. `/etc/fstab` 등록 및 상태 보존, Kubelet 방어막 구축 (핵심)
부팅 마운트 실패 방어막을 주입하고, **쉘 세션이 단절되더라도 다른 작업자가 안전하게 롤백할 수 있도록 마이그레이션 중간 상태(State) 파일**을 우선 작성한 뒤 fstab을 편집합니다.

```bash
set -euo pipefail

# 1. fstab 타임스탬프 백업
export FSTAB_BAK="/etc/fstab.bak.$(date +%Y%m%d%H%M%S)"
sudo cp -a /etc/fstab "${FSTAB_BAK}"
echo "fstab 백업 생성 완료: ${FSTAB_BAK}"

# 2. LVM 볼륨 UUID 획득
export NEW_UUID=$(sudo blkid -s UUID -o value /dev/vg-etcd/lv-etcd)
export MIGRATION_STATE="${BACKUP_DIR}/etcd-disk-migration.state"

# 3. [상태 영속화 우선 저장] fstab 수정 전에 상태 파일을 먼저 영속화하여 트랜잭션 도중 세션 유실 방지
sudo tee "${MIGRATION_STATE}" >/dev/null <<EOF
TARGET_DISK=${TARGET_DISK}
FS_TYPE=${FS_TYPE}
NEW_UUID=${NEW_UUID}
FSTAB_BAK=${FSTAB_BAK}
ETCD_UID=${ETCD_UID}
ETCD_GID=${ETCD_GID}
ETCD_PERM=${ETCD_PERM}
EOF
sudo chmod 600 "${MIGRATION_STATE}"

# 4. fstab append
if ! grep -q "${NEW_UUID}" /etc/fstab; then
  sudo tee -a /etc/fstab <<EOF
UUID=${NEW_UUID} /var/lib/etcd ${FS_TYPE} defaults,noatime 0 0
EOF
fi

# 5. [fstab 검증] 임시 해제 후 fstab 기반 정상 마운트 검증 (mountpoint로 마운트 확인 필수)
sudo umount /var/lib/etcd
sudo mount -a
mountpoint -q /var/lib/etcd || { echo "[ERROR] mount -a 실행 후 /var/lib/etcd 가 마운트되지 않았습니다. 즉시 점검하십시오." >&2; exit 1; }
sudo findmnt --verify

# 6. Kubelet 강제 마운트 의존성 및 사전 기동 검증(ExecStartPre) 주입
export MOUNTPOINT_PATH=$(which mountpoint)
sudo mkdir -p /etc/systemd/system/kubelet.service.d/
sudo tee /etc/systemd/system/kubelet.service.d/10-etcd-mount.conf <<EOF
[Unit]
RequiresMountsFor=/var/lib/etcd

[Service]
ExecStartPre=${MOUNTPOINT_PATH} -q /var/lib/etcd
EOF

# 7. systemd 재로드
sudo systemctl daemon-reload
```

### Step 7. 서비스 가동 및 전체 클러스터 검증 (Polling & Timeout)
서비스 복구 후 3분간 폴링하며 컨트롤 플레인의 모든 상태(Kubernetes Node, Pod 상태, 설정된 수의 마스터 노드의 etcd 헬스체크 통과)가 완전히 준비될 때까지 기다리고 검증합니다.

```bash
set -euo pipefail

# 1. 서비스 기동
sudo systemctl start containerd
sudo systemctl start kubelet

# 2. API Server 및 etcd 헬스 체크 루프 검증 (최대 3분 대기)
echo "컨트롤 플레인 컴포넌트 및 클러스터 헬스 체크 복구 검증 시작..."
export KUBECONFIG=/etc/kubernetes/admin.conf

# 동적으로 기대 마스터 노드 개수 계산
export EXPECTED_ENDPOINTS=$(printf '%s' "${CLUSTER_ENDPOINTS}" | awk -F',' '{print NF}')

for i in {1..18}; do
  echo "검증 시도 $i/18 (10초 간격)..."
  
  if kubectl get --raw='/readyz' &>/dev/null; then
    # [엄격한 헬스체크 및 덤프 확인] 실패 시 헬스체크 오류 원문을 직접 출력하도록 구조화
    HEALTH_OUTPUT=$(etcdctl_auth --endpoints=${CLUSTER_ENDPOINTS} endpoint health 2>&1 || true)
    echo "${HEALTH_OUTPUT}"
    # [중요] pipefail 환경에서 grep이 0건일 때(healthy가 없을 때) 1을 리턴하여 루프를 즉시 깨뜨리는 현상 방지
    HEALTHY_COUNT=$(printf '%s\n' "${HEALTH_OUTPUT}" | grep -c 'is healthy' || true)
    
    if [ "${HEALTHY_COUNT}" -eq "${EXPECTED_ENDPOINTS}" ]; then
      echo "✅ 전체 ${EXPECTED_ENDPOINTS}대의 etcd endpoint가 모두 정상 복구되었습니다."
      break
    fi
  fi
  
  if [ $i -eq 18 ]; then
    echo "❌ [ERROR] 3분 이내에 전체 마스터 etcd 헬스체크(${EXPECTED_ENDPOINTS}대)에 실패했습니다. 즉시 롤백을 진행하십시오."
    exit 1
  fi
  sleep 10
done

# 3. [최종 검증] 클러스터 관점의 다각도 상태 및 서비스 레벨 확인
kubectl get nodes -o wide
kubectl get pods -n kube-system -o wide -l component=etcd
etcdctl_auth --endpoints=${CLUSTER_ENDPOINTS} endpoint status --cluster -w table
```
* 해당 노드 확인이 완료되었다면, **다음 마스터 노드로 넘어가 Step 1부터 동일하게 순차 진행합니다.**

---

## 🚨 [장애 대응] 롤백(Rollback) 절차

마이그레이션 실패 시, **쉘 세션이 초기화되었거나 다른 작업자가 투입되더라도 안전하게 복제된 디렉토리를 원복**하기 위한 Fail-Safe 형태의 물리 원복 절차입니다. (쉘 소싱 방식을 차단하고 필수 검증 파싱 처리)

```bash
set -euo pipefail

# 1. 롤백 상태 복원 (세션이 끊겼을 때를 대비해 상태 파일 로드)
export BACKUP_DIR="${BACKUP_DIR:-/var/backups/etcd}"
export MIGRATION_STATE="${BACKUP_DIR}/etcd-disk-migration.state"

if [ -f "${MIGRATION_STATE}" ]; then
  echo "기존 마이그레이션 상태 파일 감지됨. 파싱을 시도합니다."
  
  # 상태 파일 로드 시 임의 쉘 스크립트 오염(Injection)을 원천 차단하기 위한 정적 파싱
  # 필수 키가 누락되었을 경우 친절하게 실패 사유를 출력하고 중단합니다.
  parse_state() {
    local key=$1 value
    value=$(grep -m1 "^${key}=" "${MIGRATION_STATE}" | cut -d'=' -f2- || true)
    [ -n "${value}" ] || { echo "[ERROR] 필수 식별자 ${key}가 상태 파일 내에서 누락되었습니다." >&2; exit 1; }
    printf '%s\n' "${value}"
  }
  
  export TARGET_DISK=$(parse_state "TARGET_DISK")
  export FS_TYPE=$(parse_state "FS_TYPE")
  export NEW_UUID=$(parse_state "NEW_UUID")
  export FSTAB_BAK=$(parse_state "FSTAB_BAK")
  export ETCD_UID=$(parse_state "ETCD_UID")
  export ETCD_GID=$(parse_state "ETCD_GID")
  export ETCD_PERM=$(parse_state "ETCD_PERM")
else
  echo "[WARNING] 마이그레이션 상태 파일이 감지되지 않았습니다. 현재 쉘 세션의 환경 변수를 따릅니다."
fi

# 2. [set -u 대비 가드] 변수가 정의되지 않았을 때 비정상 강제 종료를 방지하기 위해 기본값 처리
export NEW_UUID="${NEW_UUID:-}"

# 3. 원본 백업 디렉토리 존재 확인 가드 (백업이 유실되었는데 디렉토리를 비워버리는 참사 방지)
if [ ! -d /var/lib/etcd.bak ]; then
  echo "❌ [FATAL ERROR] /var/lib/etcd.bak 원본 백업 디렉토리가 부재합니다. 데이터 안전을 위해 자동 롤백을 즉각 중단합니다." >&2
  exit 1
fi

# 4. 서비스 정지
sudo systemctl stop kubelet
sudo systemctl stop containerd

# 5. 신규 볼륨 언마운트 시도
sudo umount /var/lib/etcd 2>/dev/null

# 6. [Fail-Closed 가드] 언마운트가 완벽히 되지 않았다면 삭제 작업을 차단
if mountpoint -q /var/lib/etcd; then
  echo "❌ [FATAL ERROR] /var/lib/etcd 가 여전히 마운트되어 있습니다." >&2
  echo "이 상태에서 rm -rf 를 실행하면 신규 디바이스 내부 데이터가 제거될 수 있으므로 롤백을 중단합니다." >&2
  exit 1
fi

# 7. Kubelet systemd override 방어막 삭제 및 데몬 재로드
sudo rm -f /etc/systemd/system/kubelet.service.d/10-etcd-mount.conf
sudo systemctl daemon-reload

# 8. fstab 에서 마운트 설정 라인만 정확히 색출하여 제거 (fstab.bak을 통째로 덮어씌워 유실되는 위험을 방지)
if [ -n "${NEW_UUID}" ]; then
  sudo sed -i.bak "/UUID=${NEW_UUID}[[:space:]]\+\/var\/lib\/etcd[[:space:]]/d" /etc/fstab
fi

# 9. 신규 빈 디렉토리 제거 및 원본 백업 디렉토리 원복
sudo rm -rf /var/lib/etcd
sudo mv /var/lib/etcd.bak /var/lib/etcd

# 10. 서비스 정상 복구 기동
sudo systemctl start containerd
sudo systemctl start kubelet

echo "🔄 롤백이 완료되었습니다. 클러스터 및 API Server 상태를 확인하십시오."
kubectl get nodes
```

---

## 🧹 [성공 후 정리 단계] 사후 클린업

마이그레이션 후 **3일(권장)** 이상 서비스 트래픽 처리에 지장이 없고 모니터링 메트릭에 I/O Latency 등의 특이 사항이 발견되지 않았을 경우, 임시 백업 및 상태 파일들을 안전하게 소거합니다.

```bash
set -euo pipefail

# 1. 환경 변수 유실 대비 기본값 적용
export BACKUP_DIR="${BACKUP_DIR:-/var/backups/etcd}"

# 2. 사후 정리 대상 디렉토리/파일 확인
ls -la /var/lib/etcd.bak
ls -l /etc/fstab.bak.*
ls -l "${BACKUP_DIR}/etcd-disk-migration.state"

# 3. [운영자 수동 최종 게이트]
read -r -p "⚠️ 경고: 마이그레이션 성공 후 임시 백업본을 정말 소거하시겠습니까? (type YES): " CLEAN_CONFIRM
if [ "${CLEAN_CONFIRM}" != "YES" ]; then
  echo "정리 작업이 취소되었습니다."
  exit 1
fi

# 4. 로컬 백업 파일 소거
sudo rm -rf /var/lib/etcd.bak
sudo rm -f "${BACKUP_DIR}/etcd-disk-migration.state"

# 5. [주의] 로컬에 남겨둔 etcd-pre-migration-*.db 파일은 외부 소산이 완료되었는지 확인한 후에 제거하는 것이 안전합니다.
```
