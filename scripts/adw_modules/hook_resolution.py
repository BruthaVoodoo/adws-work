import sys
import logging
from typing import Optional
from .data_types import CommitResult
from .agent import execute_opencode_prompt
from .git_ops import commit_changes
from .utils import get_rich_console_instance


def handle_commit_failure(
    commit_result: CommitResult,
    commit_msg: str,
    adw_id: str,
    logger: logging.Logger,
    max_attempts: int = 3,
) -> CommitResult:
    """
    Handle commit failure with interactive resolution loop.
    Returns the final CommitResult (success or failure).
    """
    if commit_result.success:
        return commit_result

    # If not interactive or not hook failure, just return failure
    # Note: We check isatty to avoid hanging in CI/automated environments
    if not sys.stdin.isatty() or not commit_result.hook_failure_detected:
        return commit_result

    rich_console = get_rich_console_instance()

    attempts = 0
    current_result = commit_result

    while attempts < max_attempts and not current_result.success:
        if rich_console:
            rich_console.rule("Pre-commit Hook Failure", style="red")
            # Truncate output if too long for display
            display_output = current_result.output
            if len(display_output) > 2000:
                display_output = display_output[:2000] + "\n... (truncated)"

            rich_console.print(f"[red]{display_output}[/red]")
            rich_console.print("\n[bold]Options:[/bold]")
            rich_console.print("  [green](A)[/green] Attempt AI Fix")
            rich_console.print("  [yellow](T)[/yellow] Try Commit Again")
            rich_console.print("  [red](R)[/red] Report & Abort")
        else:
            print(f"\nPre-commit Hook Failure:\n{current_result.output}")
            print("\nOptions: (A)ttempt AI Fix, (T)ry Commit Again, (R)eport & Abort")

        try:
            choice = input("\nChoose an option [A/T/R]: ").strip().upper()
        except EOFError:
            # Handle case where input fails (e.g. detached head)
            return current_result

        if choice == "A":
            attempts += 1
            logger.info(
                f"Attempting AI fix for hook failure (Attempt {attempts}/{max_attempts})"
            )

            if rich_console:
                rich_console.info(
                    f"Attempting AI fix (Attempt {attempts}/{max_attempts})"
                )

            # Call Agent to fix
            if rich_console:
                with rich_console.spinner("Running AI fix..."):
                    success = _run_ai_fix(current_result.output, adw_id, logger)
            else:
                print("Running AI fix...")
                success = _run_ai_fix(current_result.output, adw_id, logger)

            if success:
                # Retry commit
                logger.info("AI fix reported success, retrying commit")
                if rich_console:
                    with rich_console.spinner("Retrying commit..."):
                        current_result = commit_changes(commit_msg)
                else:
                    print("Retrying commit...")
                    current_result = commit_changes(commit_msg)

                if current_result.success:
                    if rich_console:
                        rich_console.success("Commit successful after AI fix!")
                    else:
                        print("Commit successful!")
            else:
                if rich_console:
                    rich_console.error("AI Fix failed to execute.")

        elif choice == "T":
            # Just retry commit
            logger.info("Retrying commit manually")
            if rich_console:
                with rich_console.spinner("Retrying commit..."):
                    current_result = commit_changes(commit_msg)
            else:
                print("Retrying commit...")
                current_result = commit_changes(commit_msg)

        elif choice == "R":
            logger.info("User chose to abort")
            break

        else:
            if rich_console:
                rich_console.warning("Invalid option")
            else:
                print("Invalid option")

    return current_result


def _run_ai_fix(error_output: str, adw_id: str, logger: logging.Logger) -> bool:
    """Run OpenCode agent to fix hook errors."""
    prompt = f"""
    The pre-commit hooks failed with the following output:
    
    {error_output}
    
    Please analyze the errors and fix the code to satisfy the hooks.
    Common issues: formatting (black, prettier), linting (flake8, eslint), types (mypy, tsc).
    Run the necessary commands or edit files to fix these issues.
    
    If the tool output suggests a command to fix (e.g. 'black .'), run it.
    """

    try:
        response = execute_opencode_prompt(
            prompt=prompt,
            task_type="test_fix",  # Using test_fix model (Sonnet) for fixing hooks
            adw_id=adw_id,
            agent_name="hook_fixer",
        )
        return response.success
    except Exception as e:
        logger.error(f"Error running AI fix: {e}")
        return False
