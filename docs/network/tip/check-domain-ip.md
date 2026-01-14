# 도메인(FQDN) 실제 IP 확인 방법

사내 서버 도메인(URL)이 현재 어떤 IP 주소로 연결(Resolve)되는지 확인하는 절차입니다.

## 방법 A: `nslookup` (DNS 서버 조회)

DNS 서버에 등록된 **공식적인 IP**를 확인할 때 가장 정확한 방법입니다.

```bash
# 사용법: nslookup [도메인주소]
nslookup harbor.internal.company.com

# 출력 예시
# Address: 10.20.30.40  <-- 이 부분이 실제 IP입니다.

```

## 방법 B: `ping` (간단 확인)

연결 상태를 확인함과 동시에, **현재 내 서버가 인식하는 IP**를 빠르게 볼 때 사용합니다.

```bash
# 사용법: ping [도메인주소]
ping harbor.internal.company.com

# 출력 예시
# PING harbor.internal.company.com (10.20.30.40) ... <-- 괄호 안 숫자가 IP

```

> **참고:** 방화벽으로 인해 Ping 응답이 없더라도(Request timeout), 첫 줄에 IP가 떴다면 도메인 해석은 성공한 것입니다.

---

## ✅ Check Point (주의사항)

### 1. 사내망 연결 필수

- `internal` 등이 포함된 사내 도메인은 **사내망(VPN 등)**에 연결된 상태에서만 조회가 가능합니다.

### 2. 로드 밸런서(L4/L7) IP 가능성

- 조회된 IP가 실제 서버의 물리 IP가 아니라, 앞단에 있는 **부하 분산 장비(VIP)**일 수 있습니다.
- **방화벽 신청 시:** 보통 이 조회된 IP(VIP)를 목적지로 적어내면 됩니다.

### 3. `/etc/hosts` 파일 우선순위 (중요 ⚠️)

- 리눅스는 DNS 서버보다 **내부 설정 파일(`/etc/hosts`)을 먼저 참조**합니다.
- 만약 `nslookup` 결과와 `ping` 결과의 IP가 다르다면,
`/etc/hosts` 파일에 예전 IP가 하드코딩(강제 고정)되어 있는지 확인해야 합니다.

```bash
# 로컬 강제 설정 확인
cat /etc/hosts | grep harbor.internal.company.com
```
