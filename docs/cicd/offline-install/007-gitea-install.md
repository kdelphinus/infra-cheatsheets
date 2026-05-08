# Gitea v1.25.5 오프라인 설치 가이드

폐쇄망 Kubernetes 환경에서 Gitea Git 서버를 Helm으로 설치하는 절차를 정의합니다.

## 구성 명세

| 항목 | 버전 | 용도 |
| :--- | :--- | :--- |
| **Gitea** | **v1.25.5** | Git 서버 |
| **Gitea Chart** | **v12.5.3** | Helm 배포 |
| **데이터베이스** | SQLite / PostgreSQL | 저장소 |

---

## 사전 조건

- Kubernetes 클러스터 구성 완료
- Helm v3.x 설치 완료
- Harbor 레지스트리 접근 가능 (`<NODE_IP>:30002`)
- Envoy Gateway 설치 완료 (도메인 접속 사용 시)

---

## 아키텍처

```text
Client → NodePort :30003 → Gitea Pod (HTTP/Web UI)
Client → NodePort :30022 → Gitea Pod (SSH/Git)
Client → Envoy Gateway → gitea.devops.internal (도메인, 선택)
```

---

## 1단계: 에셋 준비 (인터넷 가능 환경)

```bash
# Helm 차트 다운로드
helm repo add gitea-charts https://dl.gitea.com/charts/
helm pull gitea-charts/gitea --version 12.5.3 --untar --untardir ./charts/
```

---

## 2단계: 이미지 업로드 (폐쇄망 환경)

```bash
chmod +x images/upload_images_to_harbor_v3-lite.sh
./images/upload_images_to_harbor_v3-lite.sh
```

---

## 3단계: 설치 실행

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

스크립트 실행 중 대화형으로 입력합니다.

### 이미지 소스 선택

```text
이미지 소스를 선택하세요:
  1) Harbor 레지스트리 사용  ← 권장
  2) 로컬 tar 직접 import
```

### 데이터베이스 선택

```text
데이터베이스를 선택하세요:
  1) SQLite  — 단일 노드, 소규모 팀 권장
  2) PostgreSQL — 고가용성, 대규모 팀 권장
```

| 타입 | 특징 |
| :--- | :--- |
| SQLite | 별도 DB Pod 불필요. 단일 노드 환경 권장 |
| PostgreSQL | 별도 PostgreSQL Pod 배포. 데이터 영속성 강화 |

### 노드 고정 (선택)

특정 워커 노드에 배치할 경우 노드 이름을 입력합니다. 엔터 입력 시 자동 배치됩니다.

---

## 4단계: 설치 확인

```bash
# Pod 상태 확인
kubectl get pods -n gitea

# 서비스 확인
kubectl get svc -n gitea
```

---

## 5단계: 초기 접속

### 접속 주소

| 접속 방식 | 주소 |
| :--- | :--- |
| NodePort (HTTP) | `http://<NODE_IP>:30003` |
| NodePort (SSH) | `ssh://git@<NODE_IP>:30022` |
| 도메인 | `http://gitea.devops.internal` |

### 관리자 계정

초기 관리자 계정은 `values.yaml`의 `adminUser` 항목을 참조합니다.

```bash
# Secret 방식 사용 시 비밀번호 확인
kubectl get secret gitea-admin-secret -n gitea \
  -o jsonpath='{.data.password}' | base64 -d
```

### Git 클라이언트 설정

```bash
# HTTP 방식
git clone http://<NODE_IP>:30003/<USER>/<REPO>.git

# SSH 방식
git clone ssh://git@<NODE_IP>:30022/<USER>/<REPO>.git
```

---

## 6단계: 삭제

```bash
./scripts/uninstall.sh
```

삭제 시 PV/PVC 삭제 여부를 선택합니다. PV는 `Retain` 정책이므로 PVC 삭제 후에도 호스트 데이터는 유지됩니다.

---

## 운영 참고

### 로그 확인

```bash
kubectl logs -n gitea -f -l app.kubernetes.io/name=gitea
```

### SQLite → PostgreSQL 전환

1. Gitea 관리자 페이지 → **사이트 관리** → **데이터베이스 마이그레이션** 실행
2. `install.sh` 재실행 시 DB 타입 `2` (PostgreSQL) 선택
3. 마이그레이션 완료 후 기존 SQLite 파일 삭제

### TLS 적용 (선택)

Envoy Gateway에서 TLS Termination을 처리합니다.

```bash
kubectl create secret tls gitea-tls \
  --cert=cert.pem \
  --key=key.pem \
  --namespace gitea
```

`manifests/httproute-gitea.yaml`에 HTTPS 리스너 참조를 추가하세요.
