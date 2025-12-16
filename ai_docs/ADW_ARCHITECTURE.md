# ADW (AI Developer Workflow) Deep Dive

Comprehensive documentation for the ADW framework, architecture, and implementation details.

## What is ADW?

**ADW** is an **AI-driven software development orchestration engine** that automates the entire software development workflow:

1. **Takes** a Jira issue description
2. **Understands** it via AI classification
3. **Plans** solutions using specialized Bedrock agents
4. **Executes** plans via GitHub Copilot CLI
5. **Commits** changes with semantic messages
6. **Creates** pull requests for review
7. **Tracks** progress via Jira and state files
8. **Recovers** from failures via persistent state

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  EXTERNAL INTEGRATIONS                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Jira Issue   │  │ Git (Branch, │  │ Bedrock      │  │
│  │              │  │  Commits, PR)│  │ Agents       │  │
│  │ - Title      │  │              │  │              │  │
│  │ - Labels     │  │ + Bitbucket  │  │ + GitHub     │  │
│  │ - Comments   │  │              │  │   Copilot    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         ▲                  ▲                  ▲          │
└─────────┼──────────────────┼──────────────────┼──────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    ┌────────▼────────┐
                    │   ADW ENGINE     │
                    └──────────────────┘
                         Phase 1
                    ┌────────────────┐
                    │ - Fetch issue  │
                    │ - Classify     │
                    │ - Plan         │
                    │ - Branch       │
                    │ - Save state   │
                    └────────┬───────┘
                             │
                        ┌────▼────────┐
                        │   PLAN FILE  │
                        │  (Markdown)  │
                        └────┬────────┘
                             │
                         Phase 2
                    ┌────────────────┐
                    │ - Load state   │
                    │ - Checkout     │
                    │ - Copilot exec │
                    │ - Commit       │
                    │ - Update PR    │
                    └────────┬───────┘
                             │
                         Phase 3
                    ┌────────────────┐
                    │ - Run tests    │
                    │ - Report       │
                    └──────────────┘
```

---

## Three-Phase Execution Model

### Phase 1: Planning (`adw_plan.py`)

**Purpose:** Analyze the issue and generate a detailed implementation plan

**Process:**
1. Load environment and setup logging
2. Generate/validate ADW ID (unique workflow identifier)
3. Fetch issue from Jira
4. Detect domain from labels (ADW_Core or ADW_Agent)
5. Classify issue type (/bug, /feature, /chore, /new)
6. Generate branch name
7. Create git branch
8. Generate detailed implementation plan using Bedrock agent
9. Save plan file to disk
10. Commit plan to git
11. Create pull request in Bitbucket
12. Save state for Phase 2
13. Post progress to Jira

**Output:**
- Implementation plan (markdown file)
- Git branch created and pushed
- Pull request created
- State file saved

**Key Decisions Made:**
- Issue type/classification
- Domain (ADW_Core or ADW_Agent)
- Agent name (if ADW_Agent)
- Implementation approach (in plan)

---

### Phase 2: Building (`adw_build.py`)

**Purpose:** Execute the plan and make actual code changes

**Process:**
1. Load existing state from Phase 1
2. Validate state (branch_name, plan_file, issue_class)
3. Checkout the feature branch
4. Read the plan file
5. Invoke GitHub Copilot CLI with the plan
6. Copilot executes each step:
   - Modifies files
   - Runs tests/validation
   - Makes commits
7. Generate implementation commit message
8. Commit implementation changes
9. Push changes to remote
10. Update pull request in Bitbucket
11. Save updated state
12. Post progress to Jira

**Output:**
- Modified code files
- Git commits with implementation
- Updated PR in Bitbucket
- Updated state file
- Jira comments with progress

**Critical Note:** Copilot CLI output is NOT currently parsed or validated. Only exit code is checked.

---

### Phase 3: Testing (`adw_test.py`)

**Purpose:** Validate that the implementation works correctly

**Process:**
1. Load state from previous phases
2. Run test suite
3. Collect test results
4. Report results to Jira
5. Update pull request with test status

**Output:**
- Test results
- Updated PR with test status
- Final state for merge readiness

---

## State Management

### State File Format

**Location:** `{domain}/ai_docs/logs/{adw_id}/adw_state.json`

```json
{
  "adw_id": "abc123def456",
  "issue_number": "123",
  "branch_name": "feature-issue-123-adw-abc123-description",
  "plan_file": "/path/to/123-abc123-plan.md",
  "issue_class": "/feature",
  "domain": "ADW_Core",
  "agent_name": null
}
```

**Core Fields:**
- `adw_id` - Unique workflow identifier (UUID)
- `issue_number` - Jira issue number
- `branch_name` - Git branch being worked on
- `plan_file` - Path to generated plan
- `issue_class` - Classified issue type
- `domain` - ADW_Core or ADW_Agent
- `agent_name` - Agent name (if ADW_Agent)

### State Lifecycle

```
Phase 1               Phase 2               Phase 3
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Create       │     │ Load & Update │     │ Load & Final │
│ Initial      │────▶│              │────▶│ Updates      │
│ State        │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘

Save Point 1    →    Save Point 2    →    Save Point 3
(After plan)         (After impl)         (After tests)
```

### State Recovery

If workflow is interrupted:
1. State file persists on disk
2. Run Phase 2 with same ADW ID to resume
3. ADW loads state from Phase 1
4. Continues from where it left off

---

## Domain Routing

### ADW_Core Domain

**Use For:** ADW Framework Development

**Detection:** Jira label = `ADW_Core`

**Paths:**
- State: `/ADW/ai_docs/logs/{adw_id}/`
- Plans: `/ADW/ai_docs/specs/{type}/`
- Logs: `/ADW/ai_docs/logs/{adw_id}/`

**Files Modified:**
- `/ADW/scripts/adw_*.py`
- `/ADW/scripts/adw_modules/`
- `/ADW/prompts/`

---

### ADW_Agent Domain

**Use For:** Strands Agent Development

**Detection:**
- Jira label = `ADW_Agent`
- Title format = `AgentName-Description`

**Paths:**
- State: `/{AgentName}/ai_docs/logs/{adw_id}/`
- Plans: `/{AgentName}/ai_docs/specs/{type}/`
- Logs: `/{AgentName}/ai_docs/logs/{adw_id}/`

**Files Modified:**
- `/{AgentName}/src/agent.py`
- `/{AgentName}/src/handlers.py`
- `/{AgentName}/src/tools.py`
- `/{AgentName}/src/config.py`
- `/{AgentName}/tests/`

**Validation:**
- Must have exactly ONE label (ADW_Core XOR ADW_Agent)
- If ADW_Agent: title must follow `AgentName-Description` format
- Extracts agent name from title automatically

---

## Issue Classification

### Slash Commands

ADW uses slash commands to classify and route issues:

| Command | Purpose | Domains | Prompt |
|---------|---------|---------|--------|
| `/new` | Create new agent from scratch | ADW_Agent only | `new_agent.md` |
| `/feature` | Add new feature/capability | Both | `feature.md` |
| `/bug` | Fix issue | Both | `bug.md` |
| `/chore` | Refactor/maintenance | Both | `chore.md` |

### Classification Process

1. Phase 1 extracts minimal issue info
2. Calls `issue_classifier` Bedrock agent
3. Agent analyzes and returns slash command
4. Command determines which prompt template to use
5. Prompt template provides domain-specific guidance to planner

---

## LLM Prompt System

### Prompt Templates

Located in `/ADW/prompts/`:

**Core Prompts:**
- `classify_issue.md` - Issue type classification
- `bug.md` - Bug fix planning
- `feature.md` - Feature implementation planning
- `chore.md` - Maintenance task planning
- `new_agent.md` - New agent scaffolding (Strands-specific!)

**Support Prompts:**
- `commit.md` - Commit message generation
- `pull_request.md` - PR description generation
- `branch_name.md` - Branch naming logic

### Prompt Customization

Each prompt is a markdown template with:
- Clear instructions for the LLM
- Placeholders for dynamic content
- Format specifications for expected output
- Domain-specific guidance

**Example: `new_agent.md`**
```markdown
# New Agent Creation Plan

Create a plan to scaffold and implement a new AI agent...

## Strands Agents Integration
<describe how this agent integrates with:>
- Handler implementation details
- Tool definitions and capabilities
- Multi-agent patterns involved
- Integration with Amazon AgentCore deployment
```

The `new_agent.md` includes Strands-specific guidance that `feature.md` doesn't have.

---

## The GitHub Copilot Integration

### What Copilot Does

Copilot CLI is invoked in Phase 2 to execute the plan:

```python
command = [
    "copilot",
    "-p", prompt,
    "--allow-all-tools",      # Full tool access
    "--allow-all-paths",      # Full filesystem access
    "--log-level", "debug",
]

result = subprocess.run(command, cwd=target_dir)
```

### Copilot Capabilities

With `--allow-all-tools` and `--allow-all-paths` flags:
- Create/modify/delete files
- Run shell commands
- Execute tests
- Make git commits
- Access entire working directory

### Current Output Handling

**Issue:** Copilot outputs unstructured natural language text, not JSON

**Current Approach:**
```python
output = result.stdout
logger.debug(f"Copilot output:\n{output}")
return AgentPromptResponse(output=output, success=(exit_code == 0))
```

**Problems:**
- ❌ No parsing of Copilot output
- ❌ Only checks exit code (0 = success)
- ❌ Can't detect errors in logs
- ❌ No metrics extraction
- ❌ No step validation

**Needed Improvements:**
- Parse natural language output for keywords (ERROR, WARNING, ✓, ✗)
- Extract metrics (files changed, tests run, etc.)
- Validate steps completed against plan
- Check git status to confirm changes
- Add structured result format

---

## Bedrock Agent System

### Specialized Agents

Each Bedrock agent specializes in one task:

**Agent: `issue_classifier`**
- Input: Issue title, description, labels
- Task: Determine issue type
- Output: `/bug`, `/feature`, `/chore`, or `/new`

**Agent: `sdlc_planner`**
- Input: Issue context + appropriate prompt template
- Task: Generate implementation plan
- Output: Detailed markdown plan with steps

**Agent: `branch_generator`**
- Input: Issue, classification, ADW ID
- Task: Generate branch name
- Output: Branch name (format: `{type}-issue-{num}-adw-{id}-{desc}`)

**Agent: `sdlc_planner_committer`**
- Input: Issue context, implementation description
- Task: Generate commit message
- Output: Commit message

**Agent: `pr_creator`**
- Input: Issue, plan, branch, ADW ID
- Task: Generate PR title and description
- Output: JSON with `title` and `description`

### Agent Specialization Pattern

Narrow focus reduces hallucination:
- Classification agent only classifies (doesn't plan)
- Planning agent only plans (doesn't classify)
- Each agent has domain-specific prompt
- Output format is constrained

---

## Integration Points

### Jira Integration

**Reads:**
- Issue title, description, labels
- Issue comments
- Issue status

**Writes:**
- Comments with ADW progress
- Comments with ADW ID for correlation
- Status updates

**Format:**
```
{adw_id}_{agent_name}: ✅ Message
```

### Git/Bitbucket Integration

**Operations:**
- Create feature branches
- Make commits
- Push to remote
- Create pull requests
- Update pull request descriptions

**Branch Format:**
```
{type}-issue-{number}-adw-{id}-{descriptor}
```

**Example:**
```
feature-issue-123-adw-abc123def456-add-logging
```

### Bedrock Integration

**Available Agents:**
- issue_classifier
- sdlc_planner
- branch_generator
- sdlc_planner_committer
- pr_creator

**Invocation:**
```python
request = AgentTemplateRequest(
    agent_name="sdlc_planner",
    prompt=prompt,
    adw_id=adw_id,
    model="sonnet",  # or "opus"
    domain=domain,
    workflow_agent_name=agent_name
)
response = execute_template(request)
```

---

## Data Models

### Key Data Types

**ADWStateData**
```python
class ADWStateData(BaseModel):
    adw_id: str
    issue_number: Optional[str]
    branch_name: Optional[str]
    plan_file: Optional[str]
    issue_class: Optional[IssueClassSlashCommand]
    domain: Literal["ADW_Core", "ADW_Agent"]
    agent_name: Optional[str]
```

**AgentPromptResponse**
```python
class AgentPromptResponse(BaseModel):
    output: str
    success: bool
    session_id: Optional[str] = None
```

**IssueClassSlashCommand**
```python
IssueClassSlashCommand = Literal["/chore", "/bug", "/feature", "/new"]
```

---

## Execution Flow Diagrams

### Full Pipeline: ADW_Core

```
┌─────────────────────────────────┐
│ Jira Issue: ADW_Core            │
│ "/improve_copilot_parsing"      │
└──────────────┬──────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│ Phase 1: Planning                │
│ ├─ Classify: /feature            │
│ ├─ Generate plan                 │
│ ├─ Create: feature-issue-X branch│
│ └─ Save state                    │
└──────────────┬──────────────────┘
               │
         Plan File: /ADW/ai_docs/specs/feature/X-Y-plan.md
               │
               ▼
┌──────────────────────────────────┐
│ Phase 2: Building                │
│ ├─ Load state                    │
│ ├─ Copilot modifies:             │
│ │  └─ /ADW/scripts/adw_build.py  │
│ │  └─ /ADW/scripts/adw_modules/  │
│ ├─ Makes commits                 │
│ └─ Push & update PR              │
└──────────────┬──────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│ Phase 3: Testing (optional)      │
│ ├─ Run ADW tests                 │
│ ├─ Report results                │
│ └─ Update PR                     │
└──────────────┬──────────────────┘
               │
               ▼
        PR Ready for Review
```

### Full Pipeline: ADW_Agent

```
┌─────────────────────────────────┐
│ Jira Issue: ADW_Agent           │
│ "DummyAgent-Add auth handler"   │
└──────────────┬──────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│ Phase 1: Planning                │
│ ├─ Extract agent: DummyAgent     │
│ ├─ Classify: /feature            │
│ ├─ Generate Strands-aware plan   │
│ ├─ Create: feature-issue-X       │
│ └─ Save state                    │
└──────────────┬──────────────────┘
               │
    Plan File: /DummyAgent/ai_docs/specs/feature/X-Y-plan.md
               │
               ▼
┌──────────────────────────────────┐
│ Phase 2: Building                │
│ ├─ Load state from DummyAgent    │
│ ├─ Copilot modifies:             │
│ │  └─ /DummyAgent/src/handlers.py│
│ │  └─ /DummyAgent/src/agent.py   │
│ ├─ Makes commits                 │
│ └─ Push & update PR              │
└──────────────┬──────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│ Phase 3: Testing (optional)      │
│ ├─ Run agent tests               │
│ ├─ Report results                │
│ └─ Update PR                     │
└──────────────┬──────────────────┘
               │
               ▼
        PR Ready for Review
```

---

## Error Handling & Recovery

### Environment Validation

Checked at startup:
- `JIRA_SERVER` - Jira URL
- `JIRA_USERNAME` - Jira user
- `JIRA_API_TOKEN` - Jira API token
- (Optional: AWS credentials)
- (Optional: Bitbucket credentials)

### Domain Validation

**ADW_Core:**
- Must have exactly ONE label: `ADW_Core`
- No title format requirement

**ADW_Agent:**
- Must have exactly ONE label: `ADW_Agent`
- Must have title format: `AgentName-Description`
- Validates agent name extraction

### Git Operations

Handled scenarios:
- Branch already exists → checkout instead of create
- No changes to commit → skip commit silently
- Merge conflicts → reported to Jira
- Push failures → reported to Jira

### Plan Parsing

Multiple fallback patterns:
1. Try to extract from `<content>` tags
2. Try to find markdown headers
3. Return error if neither works

### State Recovery

If interrupted:
1. State file persists on disk
2. Resume with same ADW ID
3. Can retry from any phase
4. Logs show where last phase ended

---

## Performance & Scalability

### Sequential Execution

Phases run sequentially to maintain state:
```
Phase 1 → saves → Phase 2 → saves → Phase 3
```

Could be parallelized for:
- Multiple independent issues
- Different domains simultaneously
- Separate test execution

### Concurrency Considerations

**Safe:** Multiple ADW IDs running in parallel
**Unsafe:** Same issue/branch in multiple processes
**Recommendation:** Queue-based dispatch (not implemented)

---

## Monitoring & Observability

### Jira Comments

All progress posted with ADW ID:
```
abc123_ops: ✅ Starting planning phase
abc123_ops: ✅ Domain detected: ADW_Core
abc123_issue_classifier: ✅ Issue classified as: /feature
abc123_sdlc_planner: ✅ Implementation plan created
abc123_sdlc_implementor: ✅ Solution implemented
abc123_ops: ✅ Planning phase completed
```

### Log Files

Per ADW ID:
- Phase logs with detailed execution steps
- State snapshots at each save point
- Error messages and exceptions
- Jira comment history

### State Files

Persistent JSON files enabling:
- Workflow resumption
- Audit trail
- Debugging
- Testing

---

## Extensibility

### Adding New Issue Type

1. Create new prompt: `/ADW/prompts/new_type.md`
2. Update `IssueClassSlashCommand` in `data_types.py`
3. Add case to classification logic
4. Add appropriate LLM guidance to prompt

### Adding New Domain

1. Update `detect_domain_from_labels()` in `domain_router.py`
2. Implement path routing in `domain_router.py`
3. Add domain-specific validation
4. Update state management if needed

### Adding New Bedrock Agent

1. Register agent name in `workflow_ops.py`
2. Create agent execution function
3. Define input/output format
4. Add to `execute_template()` routing

---

## Future Improvements

### High Priority

1. **Copilot Output Parsing**
   - Parse natural language logs for keywords
   - Extract metrics and validation results
   - Detect errors even when exit code = 0

2. **Structured Results**
   - Enhanced `AgentPromptResponse` with metrics
   - Validation results per step
   - File change tracking

3. **Git Validation**
   - Check `git status` after Copilot execution
   - Verify expected files were modified
   - Track file diffs

### Medium Priority

1. **Concurrency**
   - Queue-based dispatch system
   - Parallel phase execution for independent issues
   - Lock mechanism for branch safety

2. **Rollback**
   - Ability to revert PR and branch
   - Rollback to previous state
   - Commit reversal

3. **Advanced Logging**
   - Database logging
   - Structured logs (JSON)
   - Analytics/metrics dashboard

### Low Priority

1. **UI Dashboard**
   - Visual workflow status
   - Plan approval UI
   - Metrics visualization

2. **Multi-Agent Coordination**
   - Agent-to-agent communication
   - Dependency tracking
   - Complex workflows

---

## Reference Implementation

See `/DummyAgent/` for a complete Strands agent example that's managed by ADW:
- Shows Strands framework patterns
- Demonstrates AgentCore integration
- Includes test structure
- Shows deployment options

---

**Version:** 1.0
**Last Updated:** November 24, 2024
