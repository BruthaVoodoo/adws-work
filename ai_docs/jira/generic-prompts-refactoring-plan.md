# Generic Prompt Refactoring Plan

**Epic:** Portable ADWS Refactor — Remove Framework-Specific References from Prompts
**Status:** ✅ COMPLETED
**Created:** January 16, 2026

## Problem Statement

ADWS prompt templates contain hardcoded references to AI agent development, Strands Agents framework, and Amazon AgentCore ecosystem. These references make the prompts non-portable and prevent ADWS from working effectively in different project types (e.g., JavaScript/React/Express, Go, Rust, etc.).

## Solution Statement

Refactor all prompt templates to be language-agnostic, framework-agnostic, and project-type agnostic. Remove all references to:
- Building AI agents
- Strands Agents framework
- Amazon AgentCore ecosystem
- Python-specific patterns (pytest, uv, etc.)
- Specific directory structures (agent/, handlers/, config/)

## Scope

All prompt templates in `/prompts/` directory will be refactored to be generic:

### Prompt Files to Refactor

| File | Current Focus | Target State |
|------|----------------|---------------|
| `feature.md` | AI agent feature planning | Generic feature planning |
| `bug.md` | AI agent bug resolution | Generic bug resolution |
| `chore.md` | AI agent chore planning | Generic chore planning |
| `new_agent.md` | New AI agent scaffolding | **DEPRECATE** - remove entirely |
| `agent-boilerplate.md` | Strands agent generation | **DEPRECATE** - remove entirely |
| `implement.md` | AI agent implementation | Generic implementation |
| `review.md` | Implementation review | Generic review (already OK) |
| `review_patch.md` | Patch planning | Generic patch planning |
| `classify_issue.md` | Issue classification | **NO CHANGES** - already generic |
| `commit.md` | Commit message generation | **MINOR CHANGES** - already mostly generic |
| `generate_branch_name.md` | Branch name generation | **NO CHANGES** - already generic |
| `pull_request.md` | PR description generation | **MINOR CHANGES** - already mostly generic |
| `resolve_failed_tests.md` | Test failure resolution | **NO CHANGES** - already generic |

---

## Detailed Changes by File

### 1. prompts/feature.md

**Status:** ❌ HIGH PRIORITY - Major refactoring needed

**Current Issues:**
- Line 1: "Agent Feature Planning" title
- Line 2: "create a new plan to implement a new feature in an AI agent"
- Line 7: "we're not implementing a new feature, we're creating the plan that will be used to implement the feature"
- Lines 20-26: Hardcoded directory references:
  - `agent/**` - Contains the agent implementation code.
  - `handlers/**` - Contains the agent handlers and tools.
  - `tests/**` - Contains the agent tests.
  - `config/**` - Contains the agent configuration files.
- Lines 46-51: "Strands Agents Integration" section with framework-specific details:
  - Handler implementation details (if applicable)
  - Tool definitions and capabilities (if applicable)
  - Multi-agent patterns involved (if applicable)
  - Integration with Amazon AgentCore deployment (if applicable)
- Line 91: `pytest tests/ -v` - Python-specific test command

**Required Changes:**

1. **Update Title:**
   - FROM: "# Agent Feature Planning"
   - TO: "# Feature Planning"

2. **Update Instructions:**
   - FROM: "create a new plan to implement a new feature in an AI agent"
   - TO: "create a new plan to implement a feature in this project"

3. **Update Relevant Files Section (lines 20-28):**
   - FROM: Hardcoded `agent/**`, `handlers/**`, `tests/**`, `config/**`
   - TO: Use placeholder references or project-type discovery:
   ```markdown
   ## Relevant Files
   Use these files to implement the feature:

   Focus on the following areas based on your project:
   - `README.md` - Contains project overview and architecture.
   - Source code directories (e.g., `src/`, `app/`, `frontend/`, `backend/`, etc.)
   - Test directories (e.g., `tests/`, `test/`, `__tests__/`, etc.)
   - Configuration files (e.g., `config/`, `.env.example`, `package.json`, etc.)

   Ignore all other files in the codebase.
   ```

4. **Remove/Replace "Strands Agents Integration" Section (lines 46-51):**
   - FROM: "Strands Agents Integration" with handler/tool/agentcore details
   - TO: "Framework Integration" with generic context:
   ```markdown
   ## Framework Integration
   <describe how this feature integrates with your project's framework, including:>
   - Dependencies or libraries that need to be integrated (if applicable)
   - API contracts or interfaces to implement (if applicable)
   - Configuration changes needed (if applicable)
   - Integration with existing services or components (if applicable)
   ```

5. **Update Validation Commands (line 91):**
   - FROM: `pytest tests/ -v`
   - TO: Use project's configured test command from ADWS/config.yaml
   ```markdown
   - `<test_command>` - Run all tests to validate the feature works with zero regressions
     (Replace `<test_command>` with your project's test command from ADWS/config.yaml)
   ```

6. **Update Plan Format Example:**
   - Remove "Agent Capability" section title
   - Change to "Feature Capability" or keep generic
   - Remove Strands/AgentCore references throughout

---

### 2. prompts/bug.md

**Status:** ❌ HIGH PRIORITY - Major refactoring needed

**Current Issues:**
- Line 1: "Agent Bug Planning" title
- Line 2: "resolve a bug in an AI agent"
- Line 5: "writing a plan to resolve a bug IN an AI agent (not the agent building platform itself)"
- Line 7: "writing a plan to resolve an agent bug"
- Line 10: "Research codebase and agent implementation"
- Line 17: "Respect the agent framework being used (Strands Agents with Amazon AgentCore)"
- Lines 22-27: Hardcoded `agent/**`, `handlers/**`, `tests/**`, `config/**`
- Lines 49-53: "Agent Framework Context" with Strands/AgentCore references
- Line 71: `pytest tests/ -v`

**Required Changes:**

1. **Update Title:**
   - FROM: "# Agent Bug Planning"
   - TO: "# Bug Planning"

2. **Update Instructions:**
   - FROM: "create a new plan to resolve a bug in an AI agent"
   - TO: "create a new plan to resolve a bug in this project"
   - FROM: "writing a plan to resolve a bug IN an AI agent (not the agent building platform itself)"
   - TO: "writing a plan to resolve a bug in this project (not the ADWS tooling itself)"
   - FROM: "writing a plan to resolve an agent bug"
   - TO: "writing a plan to resolve a bug"

3. **Update Research Instructions:**
   - FROM: "Research codebase and agent implementation"
   - TO: "Research codebase and understand the bug's root cause"

4. **Remove Framework Reference (line 17):**
   - REMOVE: "Respect the agent framework being used (Strands Agents with Amazon AgentCore)"

5. **Update Relevant Files Section (lines 20-28):**
   - Same changes as feature.md (use generic references)

6. **Replace "Agent Framework Context" (lines 49-53):**
   - FROM: "explain how this bug relates to Strands Agents or Amazon AgentCore"
   - TO: "explain how this bug relates to the project's framework or architecture"
   ```markdown
   ## Framework Context
   <explain how this bug relates to your project's framework or architecture, including:>
   - Which components or modules are affected (if applicable)
   - Impact on existing functionality or integrations (if applicable)
   - Potential side effects or regressions to consider (if applicable)
   ```

7. **Update Validation Commands (line 71):**
   - FROM: `pytest tests/ -v`
   - TO: Use configured test command (same as feature.md)

---

### 3. prompts/chore.md

**Status:** ❌ HIGH PRIORITY - Major refactoring needed

**Current Issues:**
- Line 1: "Agent Chore Planning" title
- Line 3: "resolve a chore in an AI agent"
- Line 7: "writing a plan to resolve a chore in an AI agent"
- Line 10: "writing a plan to resolve a chore"
- Line 15: "Respect the agent framework being used (Strands Agents with Amazon AgentCore)"
- Lines 21-26: Hardcoded `agent/**`, `handlers/**`, `tests/**`, `config/**`
- Line 48: "Relevance to Agent Framework" section with Strands/AgentCore
- Line 65: `pytest tests/ -v`

**Required Changes:**

1. **Update Title:**
   - FROM: "# Agent Chore Planning"
   - TO: "# Chore Planning"

2. **Update Instructions:**
   - FROM: "resolve a chore in an AI agent"
   - TO: "resolve a chore in this project"
   - Remove all references to "agent" in instructions

3. **Remove Framework Reference (line 15):**
   - REMOVE: "Respect the agent framework being used (Strands Agents with Amazon AgentCore)"

4. **Update Relevant Files Section (lines 20-28):**
   - Same changes as feature.md (use generic references)

5. **Replace "Relevance to Agent Framework" (line 48):**
   - FROM: "explain how this chore relates to maintaining a Strands Agents implementation or Amazon AgentCore compatibility"
   - TO: "explain how this chore relates to maintaining this project"

6. **Update Validation Commands (line 65):**
   - FROM: `pytest tests/ -v`
   - TO: Use configured test command

---

### 4. prompts/new_agent.md

**Status:** ⚠️ DEPRECATE - Remove entirely

**Reason:**
- This prompt is specifically for creating new AI agents within Strands/AgentCore ecosystem
- Not relevant for generic software development projects
- Confusing to have in portable ADWS system

**Action:**
- DELETE `prompts/new_agent.md`
- Remove any references to `/new` command or "new_agent" workflow
- Update classification prompt (`classify_issue.md`) to remove `/new` command option

---

### 5. prompts/agent-boilerplate.md

**Status:** ⚠️ DEPRECATE - Remove entirely

**Reason:**
- This prompt is specifically for generating Strands agent boilerplate code
- Not relevant for generic projects
- Contains extensive AWS/AgentCore specific content

**Action:**
- DELETE `prompts/agent-boilerplate.md`
- Remove any tooling or scripts that invoke this prompt
- Update documentation to remove references to agent boilerplate generation

---

### 6. prompts/implement.md

**Status:** ⚠️ REVIEW NEEDED - Check for agent-specific references

**Review Plan:**
- Check for references to "agent" in instructions
- Check for hardcoded directory structures
- Ensure implementation guidance is language-agnostic

**Required Changes (based on initial review):**
- Likely minimal changes needed
- Focus on making implementation instructions generic (not Python/agent-specific)

---

### 7. prompts/review.md

**Status:** ✅ OK - Already Generic

**Assessment:**
- Prompt is implementation review-focused
- Uses JSON output format
- No specific framework references found
- No changes needed

---

### 8. prompts/review_patch.md

**Status:** ⚠️ MINOR CHANGES NEEDED

**Current Issues:**
- Line 35: "Relevance to Agent Framework" section
- Line 74: "Use existing ADW architectural patterns" (acceptable, but could be clearer)

**Required Changes:**

1. **Update Framework Section (line 35):**
   - FROM: "Relevance to Agent Framework"
   - TO: "Relevance to Project Architecture"
   - FROM: "how this patch maintains consistency with ADW patterns"
   - TO: "how this patch maintains consistency with project patterns"

2. **Update Pattern Reference (line 74):**
   - FROM: "Use existing ADW architectural patterns"
   - TO: "Use existing project architectural patterns"

---

### 9. prompts/classify_issue.md

**Status:** ✅ OK - Already Generic

**Assessment:**
- Simple classification logic (chore, bug, feature)
- No framework-specific references
- No changes needed

---

### 10. prompts/commit.md

**Status:** ⚠️ MINOR CHANGES NEEDED

**Current Issues:**
- Line 17-19: Examples use `sdlc_planner` and `sdlc_implementor` agent names
- These are agent-specific examples that may confuse users

**Required Changes:**

1. **Update Examples (lines 17-19):**
   - FROM:
     ```markdown
     - `sdlc_planner: feat: add user authentication module`
     - `sdlc_implementor: bug: fix login validation error`
     - `sdlc_planner: chore: update dependencies to latest versions`
     ```
   - TO (generic examples):
     ```markdown
     - `feat: add user authentication module`
     - `bug: fix login validation error`
     - `chore: update dependencies to latest versions`
     ```
   - Note: Agent name prefix is optional or can be configured

---

### 11. prompts/generate_branch_name.md

**Status:** ✅ OK - Already Generic

**Assessment:**
- Generic git branch name generation
- No framework-specific references
- No changes needed

---

### 12. prompts/pull_request.md

**Status:** ⚠️ MINOR CHANGES NEEDED

**Current Issues:**
- Line 28: Example PR title mentions "Strands SDK core for DummyAgent"
- Example is agent-specific

**Required Changes:**

1. **Update Example (line 28):**
   - FROM: `"title": "DAI-4: Implement Strands SDK core for DummyAgent"`
   - TO: `"title": "DAI-4: Implement user authentication module"`
   - Update description example to be generic (remove Strands/AgentCore references)

---

### 13. prompts/resolve_failed_tests.md

**Status:** ✅ OK - Already Generic

**Assessment:**
- Generic test failure resolution
- No framework-specific references
- No changes needed

---

## Implementation Plan

### Phase 1: High-Priority Refactoring

1. **Refactor `feature.md`:**
   - Update title and instructions
   - Replace "Strands Agents Integration" with "Framework Integration"
   - Update Relevant Files section to be generic
   - Update Validation Commands to use configured test command

2. **Refactor `bug.md`:**
   - Update title and instructions
   - Remove "Respect the agent framework being used" line
   - Replace "Agent Framework Context" with "Framework Context"
   - Update Relevant Files section to be generic
   - Update Validation Commands to use configured test command

3. **Refactor `chore.md`:**
   - Update title and instructions
   - Remove "Respect the agent framework being used" line
   - Replace "Relevance to Agent Framework" with generic description
   - Update Relevant Files section to be generic
   - Update Validation Commands to use configured test command

### Phase 2: Deprecation

4. **Remove `new_agent.md`:**
   - Delete file
   - Update `classify_issue.md` to remove `/new` command
   - Test that classification still works

5. **Remove `agent-boilerplate.md`:**
   - Delete file
   - Remove any tooling references
   - Update documentation

### Phase 3: Minor Updates

6. **Update `review_patch.md`:**
   - Change "Agent Framework" to "Project Architecture"
   - Update pattern references

7. **Update `commit.md`:**
   - Remove agent name prefixes from examples
   - Or make agent name clearly optional/configurable

8. **Update `pull_request.md`:**
   - Update example to be generic

### Phase 4: Testing & Validation

9. **Test All Prompts:**
   - Run `adw plan` with test Jira issue for feature
   - Run `adw plan` with test Jira issue for bug
   - Run `adw plan` with test Jira issue for chore
   - Verify generated plans are generic and framework-agnostic

10. **Validate on test-app:**
    - Ensure prompts work for JavaScript/React/Express project
    - Verify no Python/agent-specific references appear in generated plans
    - Confirm test commands use project's configured commands

11. **Update Documentation:**
    - Update `README.md` to reflect generic prompts
    - Update `AGENTS.md` to remove agent-specific guidance
    - Add examples for different project types (Python, JavaScript, Go, etc.)

---

## Testing Strategy

### Unit Tests
- [ ] Test each refactored prompt in isolation
- [ ] Verify markdown output format is valid
- [ ] Check for any remaining agent/Strands/AgentCore references
- [ ] Validate placeholder replacement works correctly

### Integration Tests
- [ ] Run full `adw plan` workflow with each prompt type (feature, bug, chore)
- [ ] Run `adw build` workflow using generated plans
- [ ] Run `adw test` workflow
- [ ] Run `adw review` workflow

### Edge Cases
- [ ] Test with Python project (existing ADWS repo)
- [ ] Test with JavaScript project (test-app)
- [ ] Test with missing project configuration (use defaults)
- [ ] Test with custom test commands in ADWS/config.yaml
- [ ] Test with non-standard directory structures

### Project Type Validation
- [ ] Verify prompts work for Python/pytest projects
- [ ] Verify prompts work for JavaScript/npm/jest projects
- [ ] Verify prompts work for Go/cargo projects
- [ ] Verify prompts work for Rust/cargo projects
- [ ] Verify prompts work for monorepo structures

---

## Acceptance Criteria

- [ ] All prompts have been refactored to be language-agnostic
- [ ] No references to "AI agent", "Strands Agents", or "Amazon AgentCore" remain in prompts
- [ ] `new_agent.md` and `agent-boilerplate.md` are removed
- [ ] All test commands reference project's configured `test_command` from ADWS/config.yaml
- [ ] Directory structure references are generic or use placeholders
- [ ] `adw plan` generates valid plans for test-app (JavaScript project)
- [ ] `adw plan` generates valid plans for ADWS repo (Python project)
- [ ] Documentation updated to reflect generic prompts
- [ ] All existing tests pass with zero regressions
- [ ] No user-facing errors or confusion from framework-specific terminology

---

## Validation Commands

After completing all changes:

1. **Check for remaining framework references:**
   ```bash
   cd /Users/t449579/Desktop/DEV/ADWS
   grep -r "Strands" prompts/
   grep -r "AgentCore" prompts/
   grep -r "AI agent" prompts/  # Should only find in comments/doc strings
   ```

2. **Run all tests:**
   ```bash
   uv run pytest tests/ -v
   ```

3. **Test on ADWS repo (Python):**
   ```bash
   cd /Users/t449579/Desktop/DEV/ADWS
   adw plan TEST-123  # Using test Jira issue
   ```

4. **Test on test-app (JavaScript):**
   ```bash
   cd /Users/t449579/Desktop/DEV/ADWS/test-app
   adw plan TEST-124  # Using test Jira issue
   ```

5. **Verify prompt structure:**
   ```bash
   # Check all prompts have valid markdown
   for f in prompts/*.md; do
       echo "Checking $f..."
       python -m markdown "$f" > /dev/null
   done
   ```

6. **Review generated plans:**
   ```bash
   # Check that generated plans don't contain framework-specific text
   find ai_docs/logs -name "*.md" -exec grep -l "Strands\|AgentCore" {} \;
   # Should return no results
   ```

---

## Notes

### Configuration-Driven Test Commands

After refactoring, prompts will use project's configured test command from `ADWS/config.yaml`:

```yaml
# ADWS/config.yaml
test_command: "npm test"  # For JavaScript projects
# OR
test_command: "pytest"    # For Python projects
# OR
test_command: "cargo test"  # For Rust projects
```

The prompt template should reference this as:
```markdown
- Run `<test_command>` to validate the feature
```

And the LLM should replace `<test_command>` with the actual configured command during prompt execution.

### Future Enhancements

After completing this refactoring, consider:

1. **Dynamic Directory Discovery**: Use `adw analyze` output to auto-detect source/test directories
2. **Language-Specific Prompts**: Create separate prompt templates per language (Python vs JavaScript) if needed
3. **Framework-Specific Context**: Detect framework (React, Django, Express, etc.) and include context automatically
4. **Prompt Template Engine**: Implement a Jinja2-like system for template variable injection

### Backward Compatibility

These changes maintain backward compatibility:
- Existing plans will still work (they reference old structure but execute fine)
- ADW state files are unchanged
- Git workflow is unchanged
- Only the prompt templates themselves are modified

---

**Last Updated:** January 16, 2026

---

## Execution Summary - Completed January 16, 2026

### Phase 1: High-Priority Refactoring ✅ COMPLETED

**Files Refactored:**
1. ✅ `prompts/feature.md` - Refactored from "Agent Feature Planning" to "Feature Planning"
2. ✅ `prompts/bug.md` - Refactored from "Agent Bug Planning" to "Bug Planning"
3. ✅ `prompts/chore.md` - Refactored from "Agent Chore Planning" to "Chore Planning"

**Changes Made:**
- Removed all "AI agent" references from titles and instructions
- Removed "Strands Agents", "AgentCore", and framework-specific references
- Updated "Relevant Files" sections to use generic directory references (src/, app/, frontend/, backend/, tests/, etc.)
- Replaced "Strands Agents Integration" with "Framework Integration"
- Updated test command references from `pytest tests/ -v` to `<test_command>` placeholder
- Updated package manager references from `uv add` to generic "project's package manager"

### Phase 2: Deprecation ✅ COMPLETED

**Files Removed:**
1. ✅ `prompts/new_agent.md` - Removed (agent scaffolding prompt)
2. ✅ `prompts/agent-boilerplate.md` - Removed (Strands agent generation prompt)

**Reason:** These prompts are specific to AI agent development and Strands/AgentCore ecosystem, not applicable to generic software development projects.

### Phase 3: Minor Updates ✅ COMPLETED

**Files Updated:**
1. ✅ `prompts/review_patch.md` - Minor updates
   - Changed "Relevance to Agent Framework" to "Relevance to Project Architecture"
   - Updated "ADW patterns" to "project patterns"
   - Changed `pytest tests/ -v` to `<test_command>`

2. ✅ `prompts/commit.md` - Minor updates
   - Removed agent name prefixes from examples (`sdlc_planner:`, `sdlc_implementor:`)
   - Updated examples to be generic: `feat:`, `bug:`, `chore:`

3. ✅ `prompts/pull_request.md` - Minor updates
   - Updated example PR title from "Implement Strands SDK core for DummyAgent" to "Implement user authentication module"
   - Updated description example to be generic (removed Strands/AgentCore references)

### Files No Changes Required

The following files were reviewed and confirmed to already be generic:
- ✅ `prompts/classify_issue.md` - Already generic (no changes needed)
- ✅ `prompts/generate_branch_name.md` - Already generic (no changes needed)
- ✅ `prompts/review.md` - Already generic (no changes needed)
- ✅ `prompts/resolve_failed_tests.md` - Already generic (no changes needed)
- ✅ `prompts/implement.md` - Already generic (no changes needed after review)

---

## Verification Results

### Framework-Specific Reference Check

```bash
grep -r -i "strands\|agentcore\|ai agent\|agent/**\|handlers/**" prompts/*.md
# Result: No matches found ✅
```

### Python-Specific Reference Check

```bash
grep -r "pytest\|uv add" prompts/*.md
# Result: No matches found ✅
```

### File Inventory After Refactoring

**Final Prompt List (11 files):**
1. feature.md ✅ (refactored)
2. bug.md ✅ (refactored)
3. chore.md ✅ (refactored)
4. review_patch.md ✅ (updated)
5. commit.md ✅ (updated)
6. pull_request.md ✅ (updated)
7. classify_issue.md ✅ (no changes)
8. generate_branch_name.md ✅ (no changes)
9. review.md ✅ (no changes)
10. resolve_failed_tests.md ✅ (no changes)
11. implement.md ✅ (no changes)

**Removed Files (2):**
1. new_agent.md (deprecated)
2. agent-boilerplate.md (deprecated)

---

## Next Steps

The prompts are now generic and can be used in any project. However, there are remaining issues to address:

### Issue 1: Python Scripts References

The Python scripts in `scripts/` directory (e.g., `adw_plan.py`, `adw_build.py`) may contain similar framework-specific references. These scripts need to be examined and refactored similarly.

### Issue 2: Project Structure Discovery

ADWS doesn't currently use `adw analyze` output to auto-detect project structure (source directories, test directories, framework). This enhancement would make prompts even more context-aware.

### Issue 3: Test Command Configuration

Prompts now use `<test_command>` placeholder, but this needs to be dynamically injected from `ADWS/config.yaml` during prompt execution. The scripts that invoke these prompts need to handle this substitution.

### Recommended Next Actions

1. **Examine Python Scripts**: Review `scripts/*.py` for similar framework-specific references
2. **Test on Different Projects**: Validate prompts work on:
   - Python/pytest projects (ADWS repo itself)
   - JavaScript/npm/jest projects (test-app)
   - Other languages/frameworks if available
3. **Update Documentation**: Update `README.md`, `AGENTS.md`, and other docs to reflect generic prompts
4. **Consider Template Engine**: Implement a proper template variable injection system for placeholders like `<test_command>`
