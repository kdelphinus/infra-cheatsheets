# Falco 런타임 탐지 트러블슈팅 가이드

Falco 구동 및 이벤트 수집 과정에서 발생할 수 있는 주요 장애 및 해결 방법을 기술합니다.

---

## 1. inotify 리소스 부족 (WSL2 필수)

Falco 구동 시 `could not initialize inotify handler` 에러가 발생하면 호스트(WSL2)의 리소스를 확장해야 합니다.
```bash
sudo sysctl -w fs.inotify.max_user_instances=512
sudo sysctl -w fs.inotify.max_user_watches=1048576
```

## 2. eBPF 드라이버 실패

커널이 BTF를 지원하지 않으면 Falco 파드가 구동되지 않습니다. `values.yaml`에서 `driver.kind`를 `ebpf`로 변경하여 재설치하세요.

## 3. K3s 소켓 미인식

K3s 환경에서 파드가 생성되었으나 이벤트를 수집하지 못한다면, 소켓 경로를 확인하세요. 본 패키지의 `install.sh`는 이를 자동 감지하지만, 수동 설정 시에는 다음 형식을 따릅니다.
```bash
# 설치 시 수동 주입 예시
helm upgrade --install falco ./charts/falco \
  --set collectors.containerEngine.engines.cri.sockets='{/run/k3s/containerd/containerd.sock}'
```
