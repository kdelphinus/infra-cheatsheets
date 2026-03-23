# 🛠️ MariaDB 설치 트러블슈팅 및 운영 주의사항 (RHEL 9 / Rocky Linux 9)

RHEL 9 계열(Rocky Linux, AlmaLinux 포함)에서 MariaDB를 설치하거나 운영할 때 빈번하게 발생하는 이슈와 해결 방법을 정리합니다.

---

## 1. Systemd 보안 정책 (`ProtectSystem`) 이슈

**증상:** MariaDB 서비스 시작 실패 또는 특정 경로(커스텀 데이터 경로 등)에 대한 쓰기 권한 오류 발생.

**원인:** RHEL 9의 MariaDB 유닛 설정에는 `ProtectSystem=full` 정책이 기본 적용되어 있어, 시스템 바이너리 경로 및 일부 주요 디렉토리에 대한 쓰기를 차단합니다.

**해결 방법:** Systemd Override 설정을 통해 보안 정책을 완화하고 특정 경로에 대한 쓰기 권한을 부여합니다.

```bash
# 1. Override 디렉토리 생성
sudo mkdir -p /etc/systemd/system/mariadb.service.d

# 2. 보안 정책 완화 및 경로 허용 설정 작성
sudo tee /etc/systemd/system/mariadb.service.d/override.conf <<'EOF'
[Service]
ProtectSystem=off
ProtectHome=off
PrivateTmp=false
# 실제 사용하는 데이터 디렉토리 경로 명시 (예시)
ReadWritePaths=/app/mariadb_data
EOF

# 3. 설정 반영 및 재시작
sudo systemctl daemon-reload
sudo systemctl restart mariadb
```

---

## 2. SELinux 보안 컨텍스트 차단

**증상:** 파일 시스템 권한(750, mysql:mysql)이 올바름에도 불구하고 `Permission Denied`가 발생하거나 서비스 시작이 실패함.

**원인:** 커스텀 경로(예: `/app/mariadb_data`)를 사용할 경우, MariaDB 프로세스가 접근할 수 있는 SELinux 보안 컨텍스트(`mysqld_db_t`)가 해당 디렉토리에 부여되지 않았기 때문입니다.

**해결 방법:** 해당 경로에 영구적인 SELinux 정책을 적용합니다.

```bash
# 1. 특정 경로에 MariaDB 데이터 컨텍스트 유형 부여
sudo semanage fcontext -a -t mysqld_db_t "/app/mariadb_data(/.*)?"

# 2. 변경된 정책을 실제 파일 시스템에 적용 (재귀적 적용)
sudo restorecon -R -v /app/mariadb_data

# (참고) 적용된 정책 확인
ls -Zd /app/mariadb_data
```

---

## 3. HA(VIP) 구성 시 아키텍처 주의사항

Keepalived 등을 연동하여 VIP(Virtual IP)를 구성하거나 고가용성 환경을 설계할 때 주의해야 할 핵심 사항입니다.

### Shared-Nothing 원칙 준수

Galera Cluster는 각 노드가 **독립적인 로컬 스토리지**를 가져야 합니다.

- **위험 요인:** 기존 Active-Standby 방식처럼 동일한 SAN/iSCSI 디스크를 여러 노드에 동시 마운트하여 사용할 경우, 파일 시스템 메타데이터가 파손됩니다.
- **결과:** OS가 데이터 보호를 위해 디스크를 즉시 `Read-only`로 잠그며 DB 서비스가 중단됩니다.
- **해결책:** 반드시 노드별 로컬 디스크 또는 독립적인 전용 볼륨을 사용하십시오.

### Failover 및 펜싱(Fencing)

VIP 할당 직후 DB가 갑자기 멈춘다면, 사용 중인 HA 솔루션이 데이터 보호를 위해 노드를 격리(Fencing/STONITH)하고 있지는 않은지 로그를 확인하십시오. Galera 환경에서는 별도의 스토리지 공유 없이 네트워크 기반 동기화를 사용하므로 전통적인 클러스터 방식과 설계 방향이 다름을 인지해야 합니다.
