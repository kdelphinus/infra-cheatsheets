# MariaDB v10.11.14 오프라인 설치 가이드 (Rocky Linux 9.6)

폐쇄망 환경에서 MariaDB v10.11.14를 Rocky Linux 9.6에 RPM으로 설치하는 절차를 안내합니다.

## 전제 조건

- Rocky Linux 9.6 서버 (폐쇄망)
- `common/rpms/` 및 `db/rpms/` 디렉토리 내 RPM 파일이 서버에 반입되어 있을 것

## 디렉토리 구조

| 경로 | 설명 |
| :--- | :--- |
| `common/rpms/` | 공통 의존성 RPM |
| `db/rpms/` | MariaDB 10.11.14 RPM 패키지 |
| `backup/` | mariabackup 기반 백업 구성 및 가이드 |

## Phase 1: RPM 설치

```bash
# 1. 공통 의존성 RPM 먼저 설치
sudo dnf localinstall -y --disablerepo='*' common/rpms/*.rpm

# 2. MariaDB RPM 설치
sudo dnf localinstall -y --disablerepo='*' db/rpms/*.rpm
```

## Phase 2: MariaDB 초기 설정

```bash
# MariaDB 서비스 활성화 및 시작
sudo systemctl enable --now mariadb

# 서비스 상태 확인
sudo systemctl status mariadb
```

보안 초기 설정을 실행합니다.

```bash
sudo mysql_secure_installation
```

실행 중 아래 항목을 설정합니다.

- root 비밀번호 설정
- 익명 사용자 삭제 (y)
- 원격 root 로그인 비활성화 (y)
- test 데이터베이스 삭제 (y)
- 권한 테이블 재로드 (y)

## Phase 3: 기본 설정 (my.cnf)

`/etc/my.cnf.d/` 아래 설정 파일을 생성하여 핵심 파라미터를 구성합니다.

!!! warning "lower_case_table_names 주의"
    `lower_case_table_names=1` 은 **DB 초기화(데이터 디렉토리가 비어 있는 상태) 전**에 적용되어야 합니다.
    이미 데이터가 있는 서버에서 이 값을 변경하면 기존 테이블에 접근할 수 없게 될 수 있습니다.

```bash
sudo tee /etc/my.cnf.d/custom.cnf <<'EOF'
[mysqld]
# ── 문자셋 ──────────────────────────────────────────────────────────────
character-set-server    = utf8mb4
collation-server        = utf8mb4_unicode_ci

# ── 네트워크 ────────────────────────────────────────────────────────────
# 모든 인터페이스에서 접속 허용 (특정 IP만 허용하려면 해당 IP 입력)
bind-address            = 0.0.0.0

# ── 스토리지 엔진 ────────────────────────────────────────────────────────
default_storage_engine  = InnoDB

# ── 호환성 ──────────────────────────────────────────────────────────────
# 테이블명 대소문자 구분 안 함 (1 = 소문자로 저장)
lower_case_table_names  = 1

# SQL Mode 완화: ONLY_FULL_GROUP_BY 제거하여 레거시 쿼리 호환성 확보
sql_mode                = "STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION"

# 바이너리 로그 포맷 (향후 복제 구성 또는 Galera 전환 시 필수)
binlog_format           = ROW

# ── 성능 ────────────────────────────────────────────────────────────────
max_connections         = 200
innodb_buffer_pool_size = 512M
EOF

sudo systemctl restart mariadb
```

## Phase 4: 초기 데이터베이스 및 사용자 생성

```bash
sudo mysql -u root -p <<'EOF'
CREATE DATABASE IF NOT EXISTS mydb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'appuser'@'%' IDENTIFIED BY 'StrongPassword!';
GRANT ALL PRIVILEGES ON mydb.* TO 'appuser'@'%';
FLUSH PRIVILEGES;
EOF
```

## Phase 5: 설치 확인

```bash
mysql -u root -p -e "SHOW DATABASES;"
mysql -u root -p -e "SELECT version();"
mysql -u root -p -e "SHOW VARIABLES LIKE 'character_set_server';"
```

## Phase 6: 방화벽 설정 (필요 시)

다른 서버에서 MariaDB에 접근해야 하는 경우 포트를 열어줍니다.

```bash
sudo firewall-cmd --permanent --add-port=3306/tcp
sudo firewall-cmd --reload
```

## 참고: 백업 구성

mariabackup 기반 백업 설정은 `backup/README.md` 를 참조하세요.

---

## 참고 문서

- [Galera Cluster 장애 복구 가이드](../ha/galera-recovery.md) — 전체 클러스터 다운 시 복구 절차
- [MariaDB 트러블슈팅 가이드](./mariadb-troubleshooting.md) — Systemd/SELinux/HA 구성 관련 주요 이슈 해결
