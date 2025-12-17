# Jira Story Template — Reference

##Summary
-----
Automate Review Screenshot Capture

##Description
-----------
  **Story Format**
  As a reviewer, I want automated screenshots of critical functionality during the review phase, so that I can visually verify the output without manual intervention.

  **Acceptance Criteria**
  - An optional, configurable screenshot capture step is implemented in the review workflow.
  - The system captures terminal output (e.g., using a CLI screenshot tool) or uses a headless renderer for UI/CLI output.
  - `review_result.screenshots` is populated with the generated files.
  - Generated screenshots are attached to the Jira issue via `jira_add_attachment`.

  **Traceability To Epic**
  - Epic: ADW Core - System Maturation and Feature Enhancement DAI-44

  **Optional (Recommended)**
  - Provides detailed visual evidence for audit and review purposes, replacing the removed R2 upload functionality.
