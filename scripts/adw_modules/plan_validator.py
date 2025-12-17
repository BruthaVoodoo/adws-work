"""Plan validation module for cross-referencing output with implementation plans.

This module validates that actual execution matches the original implementation plan,
identifying discrepancies and missing steps.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class PlanStep:
    """Represents a single step in an implementation plan."""
    
    step_number: int
    title: str
    description: str
    optional: bool = False


@dataclass
class PlanValidationResult:
    """Result of validating plan execution."""
    
    plan_valid: bool
    total_steps: int
    executed_steps: int
    missing_steps: List[str] = field(default_factory=list)
    optional_steps_skipped: List[str] = field(default_factory=list)
    unexpected_steps: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)


def parse_plan_steps(plan_content: str) -> List[PlanStep]:
    """Parse implementation plan to extract steps.
    
    Looks for sections like:
    - "## Step 1: Title"
    - "### 1. Title"
    - "1. Title"
    
    Returns list of PlanStep objects.
    """
    steps = []
    
    # Try to find step sections with various formats
    patterns = [
        # Markdown headers: ## Step 1: Description or ### 1. Description
        r'#{2,3}\s+(?:Step\s+)?(\d+)[.:]\s+(.+?)(?:\n|$)',
        # Numbered lists: 1. Description
        r'^\d+\.\s+(.+?)(?:\n|$)',
    ]
    
    step_number = 0
    for pattern in patterns:
        matches = re.finditer(pattern, plan_content, re.MULTILINE | re.IGNORECASE)
        
        for match in matches:
            step_number += 1
            
            if len(match.groups()) == 2:
                title = match.group(2).strip()
            else:
                title = match.group(1).strip()
            
            # Check if step is marked as optional
            optional = 'optional' in title.lower()
            
            # Clean up title (remove formatting)
            title = re.sub(r'\*\*(.+?)\*\*', r'\1', title)  # Remove **bold**
            title = re.sub(r'\*(.+?)\*', r'\1', title)      # Remove *italic*
            
            steps.append(PlanStep(
                step_number=step_number,
                title=title,
                description=plan_content[match.start():min(match.end() + 200, len(plan_content))],
                optional=optional
            ))
    
    return steps


def extract_executed_steps_from_output(output: str) -> List[str]:
    """Extract list of steps executed according to output log.
    
    Looks for patterns like:
    - "✓ Step X: description"
    - "✔ Completed: description"
    - "Step X completed"
    - Numbers with checkmarks or success indicators
    """
    executed = []
    
    # Look for completed step indicators
    patterns = [
        r'(?:✓|✔|→|\*)\s*(?:Step\s+)?(\d+)[.:]\s*(.+?)(?:\n|$)',
        r'(?:✓|✔)\s+(.+?)(?:\n|$)',
        r'Completed[:\s]+(?:Step\s+)?(\d+)?:?\s*(.+?)(?:\n|$)',
        r'Successfully\s+(?:executed|ran|completed)[:\s]+(.+?)(?:\n|$)',
        r'(?:Step|step)\s+(\d+).*?:?\s*(.+?)(?:\n|$)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, output, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) >= 1:
                step_text = match.group(0)
                executed.append(step_text.strip())
    
    return list(set(executed))  # Remove duplicates


def cross_reference_plan_output(
    plan_content: str,
    output: str
) -> PlanValidationResult:
    """Cross-reference execution output with original plan.
    
    Args:
        plan_content: Original implementation plan
        output: Copilot CLI execution output
        
    Returns:
        PlanValidationResult with validation details
    """
    try:
        # Parse plan steps
        plan_steps = parse_plan_steps(plan_content)
        
        if not plan_steps:
            logger.warning("No steps found in plan")
            return PlanValidationResult(
                plan_valid=False,
                total_steps=0,
                executed_steps=0,
                validation_errors=["No executable steps found in plan"]
            )
        
        # Extract executed steps from output
        executed_steps = extract_executed_steps_from_output(output)
        
        # Match executed steps to plan steps
        matched_steps = []
        missing_steps = []
        optional_skipped = []
        
        for plan_step in plan_steps:
            step_matched = False
            
            # Look for this step in executed steps
            for executed in executed_steps:
                if str(plan_step.step_number) in executed or plan_step.title.lower() in executed.lower():
                    step_matched = True
                    matched_steps.append(plan_step.title)
                    break
            
            if not step_matched:
                if plan_step.optional:
                    optional_skipped.append(plan_step.title)
                else:
                    missing_steps.append(plan_step.title)
        
        # Validation passes if all required steps are executed
        plan_valid = len(missing_steps) == 0
        
        result = PlanValidationResult(
            plan_valid=plan_valid,
            total_steps=len(plan_steps),
            executed_steps=len(matched_steps),
            missing_steps=missing_steps,
            optional_steps_skipped=optional_skipped,
        )
        
        logger.info(
            f"Plan validation: {result.executed_steps}/{result.total_steps} steps executed, "
            f"{len(result.missing_steps)} missing"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error validating plan: {e}")
        return PlanValidationResult(
            plan_valid=False,
            total_steps=0,
            executed_steps=0,
            validation_errors=[str(e)]
        )


def identify_missing_steps(
    plan_content: str,
    output: str
) -> List[str]:
    """Identify which steps from the plan were not executed.
    
    Returns list of missing step descriptions.
    """
    result = cross_reference_plan_output(plan_content, output)
    return result.missing_steps


def validate_step_execution(
    plan_content: str,
    output: str,
    required_steps: Optional[List[str]] = None
) -> Tuple[bool, Dict[str, any]]:
    """Validate that required steps were executed.
    
    Args:
        plan_content: Original plan
        output: Execution output
        required_steps: Optional list of specific steps that must be executed
        
    Returns:
        (validation_passed, validation_details)
    """
    result = cross_reference_plan_output(plan_content, output)
    
    validation_details = {
        'plan_valid': result.plan_valid,
        'total_steps': result.total_steps,
        'executed_steps': result.executed_steps,
        'execution_rate': f"{result.executed_steps}/{result.total_steps}",
        'missing_steps': result.missing_steps,
        'optional_skipped': result.optional_steps_skipped,
    }
    
    # Check required steps if provided
    if required_steps:
        missing_required = [s for s in required_steps if s in result.missing_steps]
        if missing_required:
            validation_details['required_steps_missing'] = missing_required
            result.plan_valid = False
    
    logger.debug(f"Step validation details: {validation_details}")
    
    return result.plan_valid, validation_details


def get_plan_summary(plan_content: str) -> Dict[str, any]:
    """Get summary information about a plan.
    
    Returns dict with plan metadata and structure.
    """
    steps = parse_plan_steps(plan_content)
    
    return {
        'total_steps': len(steps),
        'required_steps': len([s for s in steps if not s.optional]),
        'optional_steps': len([s for s in steps if s.optional]),
        'step_titles': [s.title for s in steps],
        'steps': steps
    }
