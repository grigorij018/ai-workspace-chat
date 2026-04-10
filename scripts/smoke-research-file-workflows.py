#!/usr/bin/env python3
"""Dependency-light wiring smoke for research/file workflows."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


CHECKS = [
    (
        "router enables deep research",
        "backend/open_webui/orchestrator/router.py",
        ["DEEP_RESEARCH_PATTERN", "'deep_research': 'deep_research'", "features['deep_research'] = True"],
    ),
    (
        "router enables pptx generation",
        "backend/open_webui/orchestrator/router.py",
        ["PPTX_PROMPT_PATTERN", "'pptx_generation': 'pptx_generation'", "features['pptx_generation'] = True"],
    ),
    (
        "file loader covers required demo formats",
        "backend/open_webui/retrieval/loaders/main.py",
        ["PyPDFLoader", "Docx2txtLoader", "ExcelLoader", "CSVLoader", "'txt'", "'md'"],
    ),
    (
        "chat web research is multi-query and cited through files",
        "backend/open_webui/utils/middleware.py",
        ["deep_research", "SearchForm(queries=queries)", "'type': 'deep_research'", "apply_deep_research_answer_contract"],
    ),
    (
        "pptx artifact is generated as chat file event",
        "backend/open_webui/utils/middleware.py",
        ["chat_pptx_generation_handler", "create_chat_pptx_file", "'type': 'files'", "PPTX_CONTENT_TYPE"],
    ),
    (
        "pptx builder exists",
        "backend/open_webui/orchestrator/research.py",
        ["Presentation()", "Problem", "Solution", "Architecture", "Demo Flow", "Roadmap"],
    ),
    (
        "contracts document the unified flow",
        "docs/CONTRACTS.md",
        ["parse -> chunk -> embed -> retrieve -> cite", "features.deep_research=true", "features.pptx_generation=true"],
    ),
]


def main() -> int:
    failures: list[str] = []
    for label, rel_path, needles in CHECKS:
        text = (ROOT / rel_path).read_text()
        missing = [needle for needle in needles if needle not in text]
        if missing:
            failures.append(f"{label}: {rel_path} missing {missing}")

    if failures:
        print("Research/file workflow smoke check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Research/file workflow smoke check passed ({len(CHECKS)} checks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
