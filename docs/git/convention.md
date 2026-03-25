# 🤝 Git 협업 컨벤션 및 브랜치 전략

이 문서는 프로젝트의 일관성을 유지하고 효율적인 협업을 위해 준수해야 할 Git 커밋 컨벤션과 브랜치 전략을 정의합니다.

## 1. 🌿 브랜치 전략 (Git Flow Lite)

규모가 작은 프로젝트 특성에 맞춰 단순화된 **Git Flow Lite** 방식을 사용합니다.

| 브랜치 | 설명 | 배포 대상 |
| :--- | :--- | :--- |
| **`main`** | 제품으로 출시될 수 있는 상태의 브랜치 (안정화 버전) | GitHub Pages (Prod) |
| **`feature/`** | 새로운 문서 추가나 기능 개선을 위한 작업 브랜치 | - |
| **`fix/`** | 버그 수정이나 오타 교정 등을 위한 작업 브랜치 | - |

- 모든 작업은 `feature/` 또는 `fix/` 브랜치에서 진행하며, 완료 후 `main` 브랜치로 Pull Request를 보냅니다.
- `main` 브랜치에 병합될 때 GitHub Actions를 통해 문서가 자동으로 배포됩니다.

---

## 2. 📝 커밋 메시지 컨벤션

커밋 메시지는 한글 작성을 원칙으로 하며, 변경 사항을 직관적으로 파악할 수 있도록 작성합니다.

### 메시지 구조
```text
<type>(<scope>): <subject>

<body> (선택 사항)

Co-Authored-By: Gemini CLI <noreply@google.com>
```

### Type 목록
- **`feat`**: 새로운 문서 추가 또는 신규 기능
- **`fix`**: 문서 오타 수정 또는 버그 해결
- **`docs`**: 문서 구조 변경 또는 `mkdocs.yml` 설정 수정
- **`style`**: 디자인 수정 (CSS 등 시각적 요소)
- **`refactor`**: 코드/문서 구조 개선 (기능 변화 없음)
- **`chore`**: 빌드 업무 수정, 패키지 매니저 설정 등

### 주의 사항
- **의미 단위 커밋 (Atomic Commit)**: 여러 작업을 하나의 커밋으로 뭉뚱그리지 말고, 작업 단위로 나누어 커밋합니다.
- **협업 기록**: 모든 커밋 하단에는 `Co-Authored-By: Gemini CLI <noreply@google.com>`를 포함합니다.

---

## 3. 🚀 작업 흐름 (Workflow)

1.  **브랜치 생성**: `git switch -c feature/add-new-guide`
2.  **작업 및 커밋**: `git add .` -> `git commit -m "feat: 신규 가이드 문서 추가"`
3.  **최신화**: `git pull --rebase origin main` (Merge 커밋 방지)
4.  **푸시 및 PR**: `git push origin feature/add-new-guide` 이후 GitHub에서 PR 생성
