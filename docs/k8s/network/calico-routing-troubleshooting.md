# 폐쇄망 환경 Calico CNI Default Gateway 및 서비스 라우팅 장애 해결 가이드

이 가이드는 베어메탈 또는 가상화 서버의 네트워크 카드 증설, IP 대역 변경 및 **기본 게이트웨이(Default Route)가 없는 폐쇄망 환경**으로 이전 시 발생하는 Calico CNI의 핵심 통신 장애에 대한 진단법과 영구 해결 방안을 다룹니다.

---

## [장애 유형 1] 신규 Pod의 Default Gateway ARP 해결 실패 (`FAILED`)

### 1. 증상 (Symptom)
* 신규 생성된 Pod 내부에서 외부/인터넷/클러스터 서비스 통신이 작동하지 않습니다.
* Pod 내부에서 `ip neigh` 실행 시 Calico 가상 게이트웨이 주소가 실패 상태(`FAILED`)로 출력됩니다.
  ```text
  169.254.1.1 dev eth0 FAILED
  ```
* **임시 조치**: Pod 내부에 static ARP를 강제로 밀어 넣으면 순간적으로 통신이 재개됩니다.
  ```bash
  ip neigh replace 169.254.1.1 lladdr ee:ee:ee:ee:ee:ee dev eth0
  ```

### 2. 원인 분석 (Root Cause)
* Calico CNI는 Pod 내부 게이트웨이로 가상 IP인 `169.254.1.1`을 세팅하고, 호스트 측의 가상 veth 카드인 `cali*` 인터페이스에 **Proxy ARP**(`proxy_arp=1`)를 활성화합니다.
* Pod가 게이트웨이의 MAC 주소를 묻는 ARP Request를 보낼 때, 호스트 커널은 **"요청된 IP(169.254.1.1)로 향하는 라우팅 경로가 존재하고, 그 경로의 출력 인터페이스가 ARP 요청을 받은 가상 카드(cali*)와 다를 때"**에만 응답을 보냅니다.
* 그러나 네트워크 환경을 이전하면서 호스트에 **Default Route(0.0.0.0/0)가 사라진 경우**, 호스트가 `169.254.1.1`로 가기 위한 경로를 라우팅 테이블에서 찾지 못하므로 Pod의 ARP 요청에 응답하지 않아 발생한 현상입니다.

---

## [장애 유형 2] Pod Sandbox 생성 실패 및 API Server 연결 차단

### 1. 증상 (Symptom)
* 신규 Pod를 생성하면 `ContainerCreating` 상태로 멈추며, `kubectl describe pod`에서 CNI 네트워킹 오류가 다량 발생합니다.
  ```text
  Failed to create pod sandbox: rpc error: code = Unknown desc = failed to setup network for sandbox ...:
  plugin type="calico" failed (add): error getting ClusterInformation:
  Get "https://10.96.0.1:443/apis/crd.projectcalico.org/v1/clusterinformations/default":
  dial tcp 10.96.0.1:443: connect: network is unreachable
  ```

### 2. 원인 분석 (Root Cause)
* Pod가 기동될 때 호스트 상에서 동작하는 Calico CNI 바이너리가 쿠버네티스 서비스 IP(기본값 `10.96.0.1:443`)를 통해 API 서버에 연결을 맺고 클러스터 정보를 갱신해야 합니다.
* 하지만 호스트의 기본 게이트웨이(Default Route)가 유실되었기 때문에, 호스트 커널은 Service CIDR 대역에 대한 경로를 찾지 못하고 `network is unreachable` 에러를 반환합니다.
* 특히 **`nmcli connection up`** 또는 **`netplan apply`** 등을 수행하여 네트워크 어댑터를 갱신하면, 이전에 임시로 추가해 둔 런타임 라우팅 규칙(`ip route add 10.96.0.0/12 ...`)들이 **전부 삭제(초기화)**되어 장애가 재발합니다.

---

## [사전 준비] 환경 변수 및 설정 값 확인

영구 설정을 추가하기 전에 사용 중인 호스트의 물리 인터페이스 이름과 Kubernetes Service CIDR를 확인해야 합니다.

### 1. 활성화된 물리 네트워크 인터페이스 확인
```bash
# Rocky Linux / NetworkManager 사용 환경
nmcli connection show --active

# Ubuntu / ip link 사용 환경
ip -o link show | awk -F': ' '{print $2}' | grep -E "^(eth|en|bond)"
```
> [!NOTE]
> 이 가이드에서는 물리 네트워크 인터페이스 이름을 **`eth0`** (NetworkManager 연결 프로필 이름은 **`"System eth0"`**) 기준으로 설명합니다. 실제 환경에 맞는 이름으로 변경하여 적용하십시오.

### 2. Kubernetes Service CIDR 확인
클러스터에 설정된 실제 Service IP 대역을 조회합니다.
```bash
kubectl cluster-info dump | grep -m 1 service-cluster-ip-range
# 또는 API Server Pod 설정 파일 확인
kubectl get pod -n kube-system -l component=kube-apiserver -o jsonpath='{.items[0].spec.containers[0].command}' | grep service-cluster-ip-range
```
> [!NOTE]
> 이 가이드에서는 Service CIDR를 기본값인 **`10.96.0.0/12`** 기준으로 설명합니다.

---

## 영구 해결 방안 (OS별 설정)

호스트가 `169.254.1.1` 및 `Service CIDR`에 대해 통신할 수 있도록 라우팅 테이블에 명시적인 링크-로컬(Link-local) 라우트를 영구적으로 등록합니다.

### 방법 A. Rocky Linux 9.x (NetworkManager 기준)

NetworkManager의 연결 설정에 ipv4.routes를 추가하여 프로필 활성화 시 자동으로 라우팅이 추가되도록 구성합니다.

```bash
# 1. 169.254.1.1/32 및 Service CIDR 대역(10.96.0.0/12) 라우트 영구 추가
# (연결 프로필 이름이 "System eth0"인 경우)
sudo nmcli connection modify "System eth0" +ipv4.routes "169.254.1.1/32, 10.96.0.0/12"

# 2. 네트워크 프로필 재활성화하여 설정 즉시 적용
sudo nmcli connection up "System eth0"
```

### 방법 B. Ubuntu 24.04 (Netplan 기준)

Ubuntu는 Netplan을 사용하여 네트워크를 구성하므로 설정 YAML 파일을 수정합니다.

```bash
# 1. Netplan 설정 파일 열기 (배포판마다 파일명이 다를 수 있음)
sudo vi /etc/netplan/01-netcfg.yaml
```

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0: # 실제 사용하는 물리 네트워크 인터페이스명 입력
      # 기존 IP 및 네임서버 설정 유지
      routes:
        - to: 169.254.1.1/32
          scope: link
        - to: 10.96.0.0/12
          scope: link
```

```bash
# 2. 변경된 설정 테스트 및 적용
sudo netplan try
sudo netplan apply
```

---

## 최종 상태 확인 및 검증 절차

모든 마스터 및 워커 노드에 설정을 반영한 후 아래 단계에 따라 최종 상태를 점검합니다.

### 1. 호스트 라우팅 테이블 조회
```bash
ip route | grep -E "169.254|10.96"
```
* **정상 출력 예시** (`proto static` 및 물리 인터페이스 매핑 확인):
  ```text
  10.96.0.0/12 dev eth0 proto static scope link metric 100
  169.254.1.1 dev eth0 proto static scope link metric 100
  ```

### 2. 신규 Pod 기동 및 연동 테스트
```bash
# 1. 테스트용 Pod 삭제 및 재생성
kubectl delete pod net-test --ignore-not-found
kubectl run net-test --image=busybox --restart=Never -- sleep 3600

# 2. Pod가 Running 상태가 될 때까지 대기 후 ARP 상태 검증
kubectl exec net-test -- ip neigh
```
* **정상 결과**: `169.254.1.1`에 대한 상태가 `FAILED`가 아니라, MAC 주소가 자동으로 매핑된 **`REACHABLE`** 또는 **`STALE`** 상태여야 합니다.

```bash
# 3. Pod 내부에서 API Server 서비스 포트(443) 통신 및 DNS 질의 테스트
kubectl exec net-test -- nc -vz -w 2 10.96.0.1 443
kubectl exec net-test -- nslookup kubernetes.default.svc.cluster.local
```
* **정상 결과**: 타임아웃 오류 없이 포트 오픈 성공 및 DNS 확인이 정상적으로 수행되어야 합니다.
