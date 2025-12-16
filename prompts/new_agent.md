# New Agent Creation Plan

Create a plan to scaffold and implement a new AI agent using the exact specified markdown `Plan Format`. Follow the `Instructions` to create the plan and use the `Relevant Files` to focus on the right areas.

## Instructions

- IMPORTANT: You're creating a plan to scaffold a new AI agent from scratch.
- IMPORTANT: The `Agent` describes the new agent that will be created. This is a plan for creating the agent structure and initial implementation based on the `Plan Format` below.
- Create the plan in the agent's `ai_docs/specs/new/` directory with filename: `{issue_number}-{adw_id}-plan.md`
- Use the `Plan Format` below to create the plan.
- Research existing agents in the ADW system to understand patterns, architecture, and conventions before planning.
- IMPORTANT: Replace every <placeholder> in the `Plan Format` with the requested value. Add as much detail as needed to scaffold the agent successfully.
- Use your reasoning model: THINK HARD about the agent requirements, design, and implementation approach.
- Follow existing patterns and conventions in existing agents. Don't reinvent the wheel.
- Design for extensibility and maintainability within the Strands Agents framework.
- If you need a new library, use `uv add` and be sure to report it in the `Notes` section of the `Plan Format`.
- Don't use decorators. Keep it simple.
- Respect the agent framework being used (Strands Agents with Amazon AgentCore).
- Start your research by examining other agent directories in /ADW/../

## Relevant Files

Focus on the following files to understand the pattern:
- Reference agents' `README.md` - Contains agent overview and architecture
- Reference agents' `agent/**` - Contains agent implementation code
- Reference agents' `handlers/**` - Contains agent handlers and tools
- Reference agents' `tests/**` - Contains agent tests
- Reference agents' `config/**` - Contains agent configuration files

Ignore all other files in the reference codebase.

## Plan Format

```md
# New Agent: <agent name>

## Agent Description
<describe the agent's purpose, responsibilities, and value proposition>

## Agent Capabilities
<describe what capabilities and skills this agent will have>

## Problem Statement
<clearly define the specific problem or opportunity this agent addresses>

## Solution Statement
<describe the proposed agent architecture and how it integrates with Strands Agents/AgentCore>

## Strands Agents Integration
<describe how this agent integrates with the Strands framework, including:>
- Handler implementation details (if applicable)
- Tool definitions and capabilities (if applicable)
- Multi-agent patterns involved (if applicable)
- Integration with Amazon AgentCore deployment (if applicable)

## Agent Structure
Describe the scaffolding for the new agent:
- Directory structure to create
- Core modules needed
- Configuration requirements
- Dependencies needed

## Relevant Reference Files
Use these reference agents/files to model the structure:

<find and list the reference agents/files that are relevant and describe why they are relevant in bullet points. If there are new files that need to be created to implement the agent, list them in an h3 'New Files to Create' section.>

## Implementation Plan
### Phase 1: Scaffolding
<describe the foundational directory structure and basic setup>

### Phase 2: Core Agent Implementation
<describe the main agent handler and tool implementations>

### Phase 3: Configuration & Integration
<describe configuration setup and integration with Strands framework>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<list step by step tasks as h3 headers plus bullet points. use as many h3 headers as needed to scaffold and implement the agent. Order matters, start with directory structure then move on to the specific implementation. Include creating tests throughout the implementation process.>

## Testing Strategy
### Unit Tests
<describe unit tests needed for the agent components>

### Integration Tests
<describe integration tests needed to ensure the agent works with the Strands framework>

### Edge Cases
<list edge cases that need to be tested>

## Acceptance Criteria
<list specific, measurable criteria that must be met for the agent scaffolding to be considered complete>

## Validation Commands
Execute every command to validate the agent is properly scaffolded with zero regressions.

<list commands you'll use to validate with 100% confidence the agent is properly scaffolded and works correctly. every command must execute without errors so be specific about what you want to run to validate the agent works as expected. Include commands to test the agent end-to-end.>

- `pytest tests/ -v` - Run all agent tests to validate the agent works with zero regressions
- Any agent-specific validation or initialization checks

## Notes
<optionally list any additional notes, future considerations, or context that are relevant to the new agent that will be helpful to the developer>
```

## Placeholder Reference

The following placeholders will be replaced with actual Jira issue context:
- `{issue_key}` - The Jira issue key (e.g., "DAI-5")
- `{issue_title}` - The issue title/summary
- `{issue_description}` - The full issue description with requirements
- `{issue_labels}` - Comma-separated labels associated with the issue
- `{issue_state}` - Current state of the issue (e.g., "In Progress")

## New Agent

**Issue:** {issue_key}
**Status:** {issue_state}
**Labels:** {issue_labels}

### Agent Name
{issue_title}

### Agent Description
{issue_description}

---

Describe the new agent that needs to be created based on the issue context above. Include:
- What is the agent's purpose?
- What problems does it solve?
- What capabilities and skills will it have?
- What domain or system will it work with?
