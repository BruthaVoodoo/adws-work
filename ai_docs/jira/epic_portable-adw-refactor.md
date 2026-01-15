# Epic: Portable ADWS Refactor — Folder-based Zero-Pollution Deployment

#Summary
-----
Refactor ADWS to support a portable, folder-based installation model where configuration lives inside an ADWS folder and ADWS can be initialized into external projects via `adw init`.

##Description
-----------
This epic refactors ADWS core configuration and CLI workflows to enable zero project pollution and a straightforward install model. Key deliverables include moving config discovery to ADWS/config.yaml, implementing `adw init` to create the ADWS folder in a target project, combining `adw setup` and `adw healthcheck`, and ensuring `adw analyze` discovers target project structure without requiring project-root config files.

Business Value
  - Enables external developers to adopt ADWS without modifying their project roots, lowering adoption friction and improving uninstallability.
  - Demonstrates ADWS portability by allowing seamless initialization into arbitrary repositories and running end-to-end workflows.

Scope (in/out)
  - In-scope: Config discovery refactor, `adw init` script implementation, merging setup+healthcheck, update `adw analyze`, tests validating new behavior, documentation updates.
  - Out-of-scope: Full migration tooling for existing users (consider as follow-up), deep backwards-compatibility shims (only minimal compatibility handled).

Acceptance Criteria (Epic-level)
  - `adw init` creates ADWS/ folder in target repository with ADWS/config.yaml populated with defaults.
  - ADWS commands (`adw setup`, `adw analyze`, etc.) work when run from within a project containing ADWS/ folder and do not require `.adw.yaml` in project root.
  - Setup command validates external dependencies and reports clear, actionable errors.
  - Tests cover config discovery and `adw init` functionality.

User Stories
  - B1: Refactor config discovery to prefer ADWS/config.yaml and fallback to legacy locations with warning.
  - B2: Implement `adw init` CLI command to copy ADWS folder and initialize defaults.
  - B3: Combine `adw setup` + healthcheck into single validation flow and improve messages.
  - B4: Update `adw analyze` to discover project structure from within a repository containing ADWS/ folder.
  - B5: Docs, migration notes, and acceptance tests.

Dependencies
  - Current ADWS codebase and tests; owners for CLI and config modules.

Risk & Mitigations
  - Risk: Breaking existing workflows for current users. Mitigation: Implement a fallback to legacy `.adw.yaml` with clear deprecation warning and migration guide.
  - Risk: `adw init` incorrectly copies files or overwrites user files. Mitigation: Implement safe-create semantics that do not overwrite existing files unless user confirms.

Additional Notes
  - Owner: TBD.
  - Estimate: 3–5 days total across stories.

---

# Stories for Epic: Portable ADWS Refactor

## Story B1 — Refactor config discovery to prefer ADWS/config.yaml

**Status: ✅ Complete**

##Summary
Update ADWS config loader to search for ADWS/config.yaml in current working directory, falling back to legacy `.adw.yaml` with deprecation warning.

##Description
As a user, I want ADWS to load configuration from an ADWS folder so that projects are not polluted and ADWS can be uninstalled cleanly.

Acceptance Criteria
  - [x] Config loader checks for ./ADWS/config.yaml first.
  - [x] If not found, it falls back to legacy `.adw.yaml` and logs a deprecation warning indicating future removal.
  - [x] Unit tests validate both code paths.

Traceability To Epic
  - Epic: Portable ADWS Refactor — Folder-based Zero-Pollution Deployment

Estimate: 8–12 hours

**Completed:** January 15, 2026

**Implementation Details:**
- Modified `scripts/adw_modules/config.py` to implement priority-based discovery:
  - Priority 1: `./ADWS/config.yaml` in CWD
  - Priority 2: Walk up directory tree for `ADWS/config.yaml`
  - Priority 3: Fallback to legacy `.adw.yaml` with deprecation warning
- Created `tests/test_config_discovery.py` with 7 comprehensive unit tests
- Updated `project_root` property to correctly return parent of ADWS folder

**Files Changed:**
- `scripts/adw_modules/config.py`
- `tests/test_config_discovery.py` (new)

---

## Story B2 — Implement `adw init` CLI command

**Status: ✅ Complete**

##Summary
Create a CLI command `adw init` that copies ADWS folder contents into the current project and creates ADWS/config.yaml with sensible defaults.

##Description
As a developer, I want an easy way to install ADWS into a target repository so that I can test ADWS portability without manual copying.

Acceptance Criteria
  - [x] `adw init` can be run from an empty repository and creates ADWS/ with required files and ADWS/config.yaml containing default settings.
  - [x] `adw init` is idempotent and will not overwrite existing ADWS/ files unless a --force flag is provided with explicit confirmation.
  - [x] Basic integration test demonstrates init success and default config presence.

Traceability To Epic
  - Epic: Portable ADWS Refactor — Folder-based Zero-Pollution Deployment

Estimate: 4–8 hours

**Completed:** January 15, 2026

**Implementation Details:**
- Created `scripts/adw_templates/ADWS/` template directory with:
  - `config.yaml` - Default configuration with sensible settings
  - `README.md` - Documentation explaining folder structure
  - `logs/.gitkeep` - Empty logs directory
- Implemented `scripts/adw_init.py` with:
  - Safe-copy logic that checks for existing ADWS folder
  - `--force` flag with explicit confirmation prompt
  - Clear success messages and next steps
- Added `init` command to `scripts/adw_cli.py` CLI
- Created comprehensive integration test suite with 9 tests

**Files Changed:**
- `scripts/adw_templates/ADWS/config.yaml` (new)
- `scripts/adw_templates/ADWS/README.md` (new)
- `scripts/adw_templates/ADWS/logs/.gitkeep` (new)
- `scripts/adw_init.py` (new)
- `scripts/adw_cli.py` (updated - added init command)
- `tests/test_adw_init.py` (new)

---

## Story B3 — Combine `adw setup` + healthcheck into single flow

**Status: ✅ Complete**

##Summary
Merge setup and healthcheck commands into a single setup flow that configures required dependencies and validates environment with clear error messages.

##Description
As a user, I want a single command that both configures ADWS and verifies dependencies so that setup is straightforward and failure cases are obvious.

Acceptance Criteria
  - [x] `adw setup` runs configuration steps and then executes validations; returns non-zero exit code on failure with actionable messages.
  - [x] Command prints a single success message on completion and writes a setup log to ADWS/logs/.
  - [x] Integration tests verify behavior in success and failure modes.

Traceability To Epic
  - Epic: Portable ADWS Refactor — Folder-based Zero-Pollution Deployment

Estimate: 4–8 hours

**Completed:** January 15, 2026

**Implementation Details:**
- Created `scripts/adw_setup.py` with:
  - Configuration validation (ADWS folder and config.yaml existence)
  - Comprehensive health checks (environment, Jira, Bitbucket, GitHub CLI, OpenCode)
  - Setup log writing to ADWS/logs/ with timestamped files
  - Clear success/failure messages with actionable suggestions
- Added `setup` command to `scripts/adw_cli.py` CLI
- Kept `healthcheck` command for backward compatibility (deprecated)
- Updated `scripts/adw_init.py` to reference `adw setup` instead of `adw healthcheck`
- Created comprehensive integration test suite with 9 tests

**Files Changed:**
- `scripts/adw_setup.py` (new)
- `scripts/adw_cli.py` (updated - added setup command, deprecated healthcheck)
- `scripts/adw_init.py` (updated - changed healthcheck references to setup)
- `tests/test_adw_init.py` (updated - test expectations)
- `tests/test_adw_setup.py` (new)

---

## Story B4 — Update `adw analyze` to discover project structure

##Summary
Enhance `adw analyze` so it can operate within a repository containing ADWS/ folder and accurately discover the target project's structure.

##Description
As an ADWS operator, I want analyze to discover project files and suggest actions based on the test app structure so that ADWS can operate without project-root config.

Acceptance Criteria
  - `adw analyze` inspects the parent repository and returns a structured report indicating frontend/backend directories, package managers, and key files.
  - Tests confirm analyze works in test-app scaffold and in an example repo.

Traceability To Epic
  - Epic: Portable ADWS Refactor — Folder-based Zero-Pollution Deployment

Estimate: 4–8 hours

---

## Story B5 — Docs, migration notes, and acceptance tests

##Summary
Document the new ADWS init/setup flow, migration notes for existing users, and provide acceptance tests for the portable behavior.

##Description
As a maintainer, I want clear docs and migration guidance so that users can adopt the new model with minimal friction and the team has tests to prevent regressions.

Acceptance Criteria
  - README or docs updated with `adw init` and `adw setup` usage examples.
  - Migration guide for existing `.adw.yaml` users included with sample commands.
  - Automated acceptance tests added to `tests/` verifying init, setup, and analyze behaviors.

Traceability To Epic
  - Epic: Portable ADWS Refactor — Folder-based Zero-Pollution Deployment

Estimate: 4–6 hours
