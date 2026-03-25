# 🚪 방화벽 및 포트 통신 확인 가이드

인프라 운영 중 가장 빈번하게 발생하는 "접속 불가능" 문제를 해결하기 위한 포트 통신 확인 방법들을 정리합니다.

## 1. 🔍 외부에서 특정 포트 확인 (Client -> Server)

로컬 PC나 다른 서버에서 대상 서버의 포트가 열려 있는지 확인하는 방법입니다.

### 1-1. `nc` (Netcat) 사용 (가장 추천)
빠르고 직관적으로 성공/실패 여부를 알 수 있습니다.

```bash
# 기본 사용법 (성공 시 즉시 종료)
nc -zv <TARGET_IP> <PORT>

# 2초 타임아웃 설정
nc -zv -w 2 192.168.10.100 443
```

### 1-2. `telnet` 사용
전통적인 방식으로, 접속 성공 시 화면이 지워지며 커서만 깜빡입니다.

```bash
telnet 192.168.10.100 8080
```
-   **종료 방법**: `Ctrl + ]` 입력 후 `quit` 타이핑.

---

## 2. 🏠 서버 내부에서 확인 (Server-side)

서버 본인에게 해당 프로세스가 떠 있는지, 포트가 리스닝 중인지 확인합니다.

### 2-1. `ss` 또는 `netstat` 사용
현재 리스닝 중인 포트 목록과 프로세스 ID를 확인합니다.

```bash
# -t (TCP), -l (Listening), -n (Numeric), -p (Process)
sudo ss -tlnp | grep 30002

# netstat 사용 시
sudo netstat -tlnp | grep 80
```

### 2-2. `lsof` 사용
특정 포트를 어떤 프로세스가 점유하고 있는지 정밀 확인합니다.

```bash
sudo lsof -i :443
```

---

## 3. 🌐 웹 서비스 접속 확인 (`curl`)

단순 포트 오픈을 넘어, 실제 HTTP 응답이 오는지 확인합니다.

### 3-1. 응답 헤더만 확인 (Response Code)
페이지 전체를 불러오지 않고 상태 코드만 빠르게 봅니다.

```bash
curl -I http://192.168.10.100:30002
```

### 3-2. SSL/TLS 인증서 무시 (Self-signed)
사설 인증서(Harbor 등)를 사용하는 환경에서 유용합니다.

```bash
curl -k https://harbor.local
```

---

## 4. 📝 트러블슈팅 체크리스트

포트가 열려있지 않다면(Connection Refused/Timeout) 아래 항목을 순서대로 점검하세요.

1.  **프로세스 구동 확인**: `ps aux | grep <process>`로 실행 중인지 확인.
2.  **포트 바인딩 확인**: `0.0.0.0` 또는 `::` (모든 IP)가 아닌 `127.0.0.1`로 묶여있지는 않은가?
3.  **OS 방화벽 (UFW / Firewalld)**:
    -   Ubuntu: `sudo ufw status`
    -   Rocky/RHEL: `sudo firewall-cmd --list-all`
4.  **클라우드 보안 그룹 (Security Group)**: GCP/AWS 등의 인바운드 규칙에 해당 포트가 허용되어 있는가?
