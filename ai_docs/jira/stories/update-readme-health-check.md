# Jira Story: Update README with Health Check in Usage Section

## Summary
Add `scripts/adw_test/health_check.py` to README Usage section as first step.

## Description

**Story Format**
- As a new ADW user, I want to run a health check script before using the system, so that I can verify my environment setup and ensure readiness.

**Acceptance Criteria**
- The `README.md` file is updated.
- A new sub-section is added under the "Usage" section, titled "0. Health Check" or similar.
- This new section instructs the user to run `uv run scripts/adw_test/health_check.py`.
- The instructions should explain that the health check verifies system readiness and dependencies.

**Traceability To Epic**
- Epic: ADW System Maturation

**Optional (Recommended)**
- **Business Value**: Improves user onboarding experience and reduces setup-related support issues by providing an early validation step.
