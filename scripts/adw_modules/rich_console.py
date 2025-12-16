"""
Rich console wrapper for ADW CLI tools.
Provides centralized styling and console management.
"""
from typing import Optional, ContextManager
import sys

try:
    from rich.console import Console
    from rich.theme import Theme
    from rich.panel import Panel
    from rich.text import Text
    from rich.status import Status
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Define a custom theme for ADW
ADW_THEME = {
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "highlight": "magenta",
    "step": "bold blue",
}

class RichConsole:
    """Wrapper around rich.console.Console with ADW-specific styling."""
    
    def __init__(self, force_terminal: Optional[bool] = None):
        self.enabled = RICH_AVAILABLE
        if RICH_AVAILABLE:
            console_args = {"theme": Theme(ADW_THEME)}
            if force_terminal is not None:
                console_args["force_terminal"] = force_terminal
            self.console = Console(**console_args)
        else:
            self.console = None

    def print(self, *args, **kwargs):
        """Pass through to console.print if available, else print."""
        if self.console:
            self.console.print(*args, **kwargs)
        else:
            print(*args, **kwargs)

    def rule(self, title: str = "", style: str = "rule.line"):
        """Draw a horizontal rule with an optional title."""
        if self.console:
            self.console.rule(title, style=style)
        else:
            print(f"--- {title} ---" if title else "-" * 40)

    def panel(self, renderable, title: str = "", style: str = "none"):
        """Render a panel."""
        if self.console:
            self.console.print(Panel(renderable, title=title, border_style=style))
        else:
            print(f"[{title}]\n{renderable}\n")

    def info(self, message: str):
        """Print an info message."""
        if self.console:
            self.console.print(f"[info]ℹ[/info] {message}")
        else:
            print(f"i {message}")

    def success(self, message: str):
        """Print a success message."""
        if self.console:
            self.console.print(f"[success]✔[/success] {message}")
        else:
            print(f"✓ {message}")

    def warning(self, message: str):
        """Print a warning message."""
        if self.console:
            self.console.print(f"[warning]⚠[/warning] {message}")
        else:
            print(f"! {message}")

    def error(self, message: str):
        """Print an error message."""
        if self.console:
            self.console.print(f"[error]✖[/error] {message}")
        else:
            print(f"✗ {message}")

    def step(self, message: str):
        """Print a step header."""
        if self.console:
            self.console.print(f"\n[step]➤ {message}[/step]")
        else:
            print(f"\n➤ {message}")

    def spinner(self, message: str) -> ContextManager:
        """Return a status spinner context manager."""
        if self.console:
            return self.console.status(message, spinner="dots")
        else:
            # Fallback context manager that just prints the message
            class SimpleSpinner:
                def __enter__(self):
                    print(f"{message}...", end="", flush=True)
                def __exit__(self, exc_type, exc_val, exc_tb):
                    if exc_type:
                        print(" Failed!")
                    else:
                        print(" Done.")
            return SimpleSpinner()

    def print_table(self, title: str, headers: list, rows: list):
        """Print a table with headers and rows."""
        if self.console and RICH_AVAILABLE:
            table = Table(title=title)
            for header in headers:
                table.add_column(header)
            for row in rows:
                table.add_row(*[str(cell) for cell in row])
            self.console.print(table)
        else:
            print(f"\n--- {title} ---")
            print(" | ".join(headers))
            print("-" * (sum(len(h) for h in headers) + len(headers) * 3 - 1))
            for row in rows:
                print(" | ".join(str(cell) for cell in row))

    def status_table(self, data: dict, title: str = "Status"):
        """Render a table from a dictionary."""
        if not data:
            if self.console and RICH_AVAILABLE:
                self.console.print(f"[dim]{title}: No results[/dim]")
            else:
                print(f"{title}: No results")
            return
            
        if self.console and RICH_AVAILABLE:
            table = Table(title=title, box=None)
            table.add_column("Test", style="cyan", no_wrap=True)
            table.add_column("Status", style="magenta")
            
            for key, value in data.items():
                if isinstance(value, bool):
                    status = "PASS" if value else "FAIL"
                elif isinstance(value, dict) and 'passed' in value:
                    status = "PASS" if value['passed'] else "FAIL"
                    if 'details' in value:
                        status += f" - {value['details']}"
                elif hasattr(value, 'passed'):
                    status = "PASS" if value.passed else "FAIL"
                    if hasattr(value, 'test_name'):
                        status += f" - {value.test_name}"
                else:
                    status = str(value)
                    
                table.add_row(str(key), status)
            
            self.console.print(table)
        else:
            print(f"\n--- {title} ---")
            for key, value in data.items():
                if isinstance(value, bool):
                    status = "PASS" if value else "FAIL"
                elif isinstance(value, dict) and 'passed' in value:
                    status = "PASS" if value['passed'] else "FAIL"
                    if 'details' in value:
                        status += f" - {value['details']}"
                else:
                    status = str(value)
                print(f"{key}: {status}")


# Singleton instance
_rich_console = None

def get_rich_console() -> RichConsole:
    """Get the singleton RichConsole instance."""
    global _rich_console
    if _rich_console is None:
        _rich_console = RichConsole()
    return _rich_console

def create_rich_console(force_terminal: Optional[bool] = None) -> RichConsole:
    """Create a new RichConsole instance."""
    return RichConsole(force_terminal=force_terminal)
