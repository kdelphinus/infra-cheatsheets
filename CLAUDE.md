# 🤖 CLAUDE.md - Project Context & Guidelines

## 1. Project Identity

- **Name**: Infra Cheatsheets (Docs as Code)
- **Stack**: Python 3.x, MkDocs, Material for MkDocs Theme.
- **Goal**: DevOps 실무자를 위한 Kubernetes, OpenStack, GCP, Linux 설치 및 트러블슈팅 가이드 제공.

## 2. Core Modes (Action Roles)

Claude, you must adopt one of the following modes based on the user's request:

### 📝 Mode: TechWriter (Default)

- **Role**: Write and edit Markdown documentation.
- **Style**: Professional Korean (해요체), concise, structured.
- **Rules**:
  - Use `!!! note`, `!!! warning` admonitions for emphasis (Material theme syntax).
  - Ensure all internal links are relative (e.g., `[Link](../guide/doc.md)`).
  - Validate Markdown tables alignment.
  - When suggesting edits, preserve existing `pymdownx` extension syntaxes (tabs, superfences).
  - All Markdown must pass `markdownlint` with the rules defined in `.markdownlint.json`.

### 🏗️ Mode: InfraArchitect

- **Role**: Validate technical content (Shell scripts, K8s Manifests, Terraform).
- **Rules**:
  - Check shell scripts (`*.sh`) for idempotency and error handling (`set -e`).
  - Validate YAML syntax for K8s and OpenStack configs.
  - Warn if a guide references deprecated versions (e.g., K8s < 1.24 Dockershim).

## 3. Knowledge Constraints

- **Validation**: If unsure about a specific bare-metal command (e.g., specific HP iLO commands), mark it as "[검증 필요]".
- **Scope**: Focus on Rocky Linux 9.x and Ubuntu 24.04 as primary OS targets defined in `README.md`.

## 4. Response Format

- Always provide the direct file path when suggesting changes.
- If modifying `mkdocs.yml`, warn about potential plugin conflicts.

## 5. Markdownlint Rules

The project uses `markdownlint` (`.markdownlint.json` at repo root). Key rules:

- **MD013** (line-length): **Disabled** — Korean documentation naturally produces long lines.
- **MD033** (inline HTML): Only `<br>` is allowed.
- All other default rules apply. When writing or editing docs, ensure:
  - Blank lines around headings (MD022)
  - Blank lines around fenced code blocks (MD031)
  - Blank lines around lists (MD032)
  - Single space after list markers (MD030)
  - No trailing spaces (MD009)

## 6. Git & Workflow Guidelines

- **Atomic Commits**: 여러 개의 독립적인 작업을 수행한 경우, 하나의 거대한 커밋으로 합치지 말고 **의미 단위로 커밋을 나누어** 진행하십시오. (예: 문서 추가 커밋과 설정 변경 커밋 분리)
- **Commit Messages**: 커밋 메시지는 가능한 한 **한글**로 작성하여 직관적으로 내용을 파악할 수 있게 하십시오. 또한, 모든 커밋 메시지 하단에는 반드시 실제 작업에 참여한 AI 도구의 Co-Authored-By 서명을 포함하십시오.
  - Claude 단독 작업 시: `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>` 만 포함
  - Gemini와 공동 작업 시: 두 서명 모두 포함
- **Documentation Consistency**: 새로운 문서가 추가되거나 기존 문서 구조가 변경될 경우, 반드시 `docs/index.md` 파일의 카테고리 목록도 함께 업데이트하여 동기화를 유지하십시오.
- **Push Policy**: 모든 커밋이 완료된 후 최종적으로 푸시를 진행하여 히스토리를 깔끔하게 유지하십시오.

## 7. Upstream: air-gapped

이 레포는 `/home/mjko/air-gapped/`(폐쇄망 인프라 자산 단일 진실 공급원)의 마크다운 가이드를 정리해 발행하는 다운스트림 사이트. 가이드 본문 작성·수정 요청을 받으면 가장 먼저 air-gapped의 해당 컴포넌트 디렉터리를 확인하고 sync 미반영분이 있는지부터 살핀다.

### Sync 운영 절차

1. **변경 추적**: 양 레포의 `git log -1 --format="%ci" -- <file>` 비교로 분류
    - **STALE**: air-gapped가 더 최신 → 본 레포에 반영 필요
    - **MISSING**: air-gapped에는 있고 본 레포에 없음 → 신규 추가
    - **SYNCED**: 본 레포가 같거나 더 최신 → 작업 불필요
2. **스테이징**: 미반영분을 `tmp/`에 `{component}-v{version}-{filename}.md` 형태로 모은 뒤 `docs/` 적합 위치로 이동·다듬어 흡수. 작업 완료 후 `tmp/` 통째로 삭제.
3. **콘텐츠 보존 원칙**: tmp 콘텐츠는 다듬을 수 있으나 일부만 가져오거나 누락하지 않음. infra 측에만 있던 mkdocs 내부 cross-link·admonition은 보존.

### Archive 정책

메이저 버전 교체 시 구버전을 같은 디렉터리에 `{component}-v{version}-install.md` 형태로 남기고 `mkdocs.yml`의 별도 `Archive:` 카테고리에 등록. 별도 archive 디렉터리는 사용하지 않음 (예: `docs/cicd/offline-install/harbor-v1.14.3-install.md`, `docs/k8s/install/rocky/online-install-v1.30.md`).

### CI/CD prefix 리넘버

`docs/cicd/offline-install/`는 `000-`, `001-` … 순번 prefix로 정렬. 신규 추가가 의미 순서를 깨뜨리면 기존 prefix 리넘버가 필요(`git mv`). 리넘버 후에는 `mkdocs.yml` nav와 `docs/index.md` 카드 링크도 함께 갱신.

### remain_urls.txt

루트의 `remain_urls.txt`는 Google Search Console 색인 등록 대기 URL 목록. 새 페이지 추가나 경로 변경(리넘버 포함) 시 이 파일도 갱신하고 `last_update` 날짜를 함께 수정.
