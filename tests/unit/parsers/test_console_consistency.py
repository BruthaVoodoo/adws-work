import re
import pytest


def test_adw_build_contains_phase_rules():
    with open('scripts/adw_build.py', 'r') as f:
        src = f.read()

    # Check for Preparing Workspace, Committing Changes, Finalizing Git Operations, Build Complete
    assert 'rich_console.rule("Preparing Workspace", style="cyan")' in src
    assert 'rich_console.rule("Committing Changes", style="cyan")' in src
    assert 'rich_console.rule("Finalizing Git Operations", style="cyan")' in src
    assert 'rich_console.rule("✅ Build Complete", style="green")' in src


def test_adw_review_contains_phase_rules_and_spinners():
    with open('scripts/adw_review.py', 'r') as f:
        src = f.read()

    # Phase rules
    assert 'rich_console.rule("Preparing Workspace", style="cyan")' in src
    assert 'rich_console.rule("Committing Changes", style="cyan")' in src
    assert 'rich_console.rule("Finalizing Git Operations", style="cyan")' in src

    # Completion rules
    assert 'rich_console.rule("✅ Review Complete", style="green")' in src
    assert 'rich_console.rule("❌ Review Failed", style="red")' in src

    # Spinner usage for checkout, commit, and push/finalize
    assert 'with rich_console.spinner(' in src
    # Ensure commit spinner and finalize spinner specifically are present
    assert 'with rich_console.spinner("Committing review to git...' in src or 'with rich_console.spinner("Committing implementation to git...' in src
    assert 'with rich_console.spinner("Pushing changes and updating PR...")' in src


if __name__ == '__main__':
    pytest.main(['-q'])
