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
- **Commit Messages**: 커밋 메시지는 가능한 한 **한글**로 작성하여 직관적으로 내용을 파악할 수 있게 하십시오. 또한, 모든 커밋 메시지 하단에는 반드시 `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`를 포함하여 협업 내역을 기록하십시오.
- **Documentation Consistency**: 새로운 문서가 추가되거나 기존 문서 구조가 변경될 경우, 반드시 `docs/index.md` 파일의 카테고리 목록도 함께 업데이트하여 동기화를 유지하십시오.
- **Push Policy**: 모든 커밋이 완료된 후 최종적으로 푸시를 진행하여 히스토리를 깔끔하게 유지하십시오.
