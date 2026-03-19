# 🛠️ MariaDB Galera Cluster 장애 복구 가이드 (Full Crash Recovery)

모든 노드가 비정상 종료되어 서비스가 전면 중단된 경우(Full Crash)의 복구 절차를 안내합니다.

> 💡 **[중요] 데이터 디렉토리 경로 확인**
>
> 본 가이드는 `/app/mariadb_data` 경로를 기준으로 작성되었습니다. **실제 서버의 설치 구성에 따라 데이터 경로가 다를 수 있으므로**, 명령어 실행 전 실제 데이터 저장 경로를 반드시 확인하고 해당 경로로 치환하여 사용하시기 바랍니다.

---

## 1. 복구 논리 (Logic)

*   **최신 트랜잭션 판별:** 모든 노드가 다운된 경우, 가장 최신 트랜잭션(`seqno`)을 보유한 노드를 찾아 Primary(Bootstrap 대상)로 승격시켜야 데이터 유실 및 무거운 전체 동기화(SST)를 방지할 수 있습니다.
*   **커스텀 경로 스캔:** 데이터가 커스텀 경로에 저장된 경우, 엔진 내부 상태를 강제 스캔할 때 반드시 `--datadir` 옵션을 명시해야 합니다.

---

## 2. 복구 절차

### 1단계: DB 클러스터 상태 확인 및 Primary 노드 판별

1.  **프로세스 확인:** 3대 서버 모두에서 MariaDB 프로세스가 없는지 확인합니다.
    ```bash
    ps -ef | grep mysql
    ```
2.  **복구 위치(seqno) 추출:** 3대 서버 모두에서 아래 명령어를 실행하여 트랜잭션 번호를 찾습니다.
    ```bash
    sudo /usr/sbin/mariadbd --wsrep-recover --datadir=/app/mariadb_data
    ```
3.  **Primary 노드 선정:** 로그 마지막의 `Recovered position: UUID:seqno` 값 중 **숫자(seqno)가 가장 큰 노드**를 Primary로 선정합니다.
    *   숫자가 같다면 `grastate.dat`의 `safe_to_bootstrap: 1`인 노드를 선택합니다.

### 2단계: Primary 노드 부트스트랩 (Bootstrap)

1.  **상태 파일 수정:** Primary 노드의 `/app/mariadb_data/grastate.dat` 파일에서 `safe_to_bootstrap: 1`로 수정합니다.
2.  **클러스터 초기화 실행:** Primary 노드에서만 실행합니다.
    ```bash
    sudo galera_new_cluster
    ```
3.  **검증:** 아래 명령어로 결과가 `1`인지 확인합니다.
    ```bash
    sudo mariadb -u root -e "SHOW STATUS LIKE 'wsrep_cluster_size';"
    ```

### 3단계: 나머지 노드 합류 (Join)

1.  **서비스 순차 시작:** 나머지 노드에서 **하나씩** 서비스를 시작합니다.
    ```bash
    sudo systemctl start mariadb
    ```
2.  **최종 검증:** 아무 노드에서나 클러스터 사이즈가 `3`으로 복구되었는지 확인합니다.
    ```bash
    sudo mariadb -u root -e "SHOW STATUS LIKE 'wsrep_cluster_size';"
    ```

### 4단계: K8s 애플리케이션 파드 정상화

DB 접속 실패로 `CrashLoopBackOff` 상태인 파드들을 재시작하여 연결을 복구합니다.

```bash
kubectl rollout restart deployment --all -n [네임스페이스]
```

---

## 3. 최종 복구 체크리스트

| 완료 | 분류 | 점검 대상 및 명령어 | 기준 / 비고 |
| :---: | :--- | :--- | :--- |
| [ ] | **사전 조사** | `ps -ef \| grep mysql` | 3대 모두 잔여 DB 프로세스 없음 |
| [ ] | **상태 추출** | `--wsrep-recover --datadir=[경로]` | 3대 중 `seqno` 최고값 판별 완료 |
| [ ] | **부트스트랩** | Primary 노드: `sudo galera_new_cluster` | `wsrep_cluster_size` = 1 확인 |
| [ ] | **노드 합류** | 나머지 노드: `sudo systemctl start mariadb` | `wsrep_cluster_size` = 3 확인 |
| [ ] | **파드 복구** | K8s: `kubectl rollout restart deployment` | 앱 파드 `Running` 상태 확인 |
