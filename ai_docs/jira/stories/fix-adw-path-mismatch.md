# Jira Story Template — Reference

##Summary
-----
Align Implementation Paths with Specification

##Description
-----------
  **Story Format**
  As a developer, I want the file paths in the specification and implementation to match, so that I don't get confused during development and testing and CI pipelines run correctly.

  **Acceptance Criteria**
  - The specification is updated to reference actual implementation locations (e.g., `scripts/adw_review.py` instead of `ADW/adw_review.py`) OR compatibility wrappers are added at `ADW/` paths.
  - `adw_modules.utils` is correctly referenced instead of non-existent `ADW/utils/console.py`.
  - CI/test paths and documentation are updated to use the unified paths.

  **Traceability To Epic**
  - Epic: ADW Core - System Maturation and Feature Enhancement DAI-44

  **Optional (Recommended)**
  - Reduces developer confusion and ensures tests run against correct files.
