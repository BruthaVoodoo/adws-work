# Jira Story Template — Reference

Use this template when creating Jira stories for the project. Copy the sections into the Story description and fill them out. Keeping stories consistent improves planning, estimation, and delivery.

##Summary
-----
Concise, clear, ≤ 15 words; reflects scope and outcome, summarizing the main objective of the story.
Example: “Add validation for image classification in RPS billing pipeline.”

##Description
-----------
  **Story Format**
  - Follows template: As a [role], I want [goal], so that [reason]
  - Example: “As a data analyst, I want automated detection of misclassified images in RPS, so that revenue leakage is reduced.”

  **Acceptance Criteria**
  - At least 1–2 testable conditions that define “done”
  - Example:
    - System flags misclassified images with ≥95% confidence.
    - Alerts appear in dashboard within 5 minutes.

  **Traceability To Epic**
  - Links to Epic ID and references Epic’s domain/outcome
  - Example: "Epic: [Jira Issue #] Revenue Leakage – Automated Detection"

  **Oprional (Recomended)**
  - One sentence on business value
    - Example: "Reduces revenue leakage by improving classification accuracy."

  - Critical dependency if needed
    - Example: "Requires image model API availability."
