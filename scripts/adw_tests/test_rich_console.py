"""Unit tests for rich console functionality."""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adw_modules.rich_console import RichConsole, get_rich_console, create_rich_console


class TestRichConsole:
    """Test the RichConsole class functionality."""
    
    def test_init_with_rich_available(self):
        """Test initialization when rich is available."""
        console = RichConsole()
        # Should be enabled if rich is available
        assert isinstance(console.enabled, bool)
    
    def test_init_force_terminal(self):
        """Test initialization with force_terminal parameter."""
        console = RichConsole(force_terminal=True)
        assert isinstance(console.enabled, bool)
    
    @patch('adw_modules.rich_console.RICH_AVAILABLE', False)
    def test_fallback_mode(self):
        """Test console works in fallback mode when rich is unavailable."""
        console = RichConsole()
        assert not console.enabled
        assert console.console is None
    
    def test_print_basic(self):
        """Test basic print functionality."""
        console = RichConsole()
        # Should not raise an error
        console.print("Test message")
    
    def test_rule_with_title(self):
        """Test rule printing with title."""
        console = RichConsole()
        console.rule("Test Title")
    
    def test_rule_without_title(self):
        """Test rule printing without title."""
        console = RichConsole()
        console.rule()
    
    def test_panel(self):
        """Test panel creation and printing."""
        console = RichConsole()
        console.panel("Test content", "Test Title")
    
    def test_status_messages(self):
        """Test all status message types."""
        console = RichConsole()
        console.success("Success message")
        console.error("Error message")
        console.warning("Warning message")
        console.info("Info message")
    
    def test_spinner_context_manager(self):
        """Test spinner context manager."""
        console = RichConsole()
        with console.spinner("Testing..."):
            pass  # Simulate some work
    
    def test_table_creation(self):
        """Test table creation with headers and rows."""
        console = RichConsole()
        headers = ["Name", "Status", "Details"]
        rows = [
            ["Test 1", "PASS", "All good"],
            ["Test 2", "FAIL", "Error occurred"]
        ]
        
        # Should not raise an error
        console.print_table("Test Results", headers, rows)
    
    def test_status_table_with_dict_results(self):
        """Test status table with dictionary test results."""
        console = RichConsole()
        tests = {
            "test_1": {"passed": True, "details": "All good"},
            "test_2": {"passed": False, "details": "Failed assertion"},
        }
        console.status_table(tests, "Unit Test Results")
    
    def test_status_table_with_bool_results(self):
        """Test status table with boolean test results."""
        console = RichConsole()
        tests = {
            "test_1": True,
            "test_2": False,
        }
        console.status_table(tests, "Simple Test Results")
    
    def test_status_table_empty(self):
        """Test status table with no results."""
        console = RichConsole()
        console.status_table({}, "Empty Results")
    
    @patch('adw_modules.rich_console.RICH_AVAILABLE', False)
    def test_fallback_print(self, capsys):
        """Test fallback printing when rich is not available."""
        console = RichConsole()
        console.print("Test fallback")
        captured = capsys.readouterr()
        assert "Test fallback" in captured.out
    
    @patch('adw_modules.rich_console.RICH_AVAILABLE', False)
    def test_fallback_status_messages(self, capsys):
        """Test fallback status messages when rich is not available."""
        console = RichConsole()
        console.success("Success")
        console.error("Error")
        console.warning("Warning")
        console.info("Info")
        
        captured = capsys.readouterr()
        assert "✓ Success" in captured.out
        assert "✗ Error" in captured.out
        assert "! Warning" in captured.out
        assert "i Info" in captured.out


class TestGlobalConsole:
    """Test global console functionality."""
    
    def test_get_rich_console(self):
        """Test getting the global console instance."""
        console = get_rich_console()
        assert isinstance(console, RichConsole)
    
    def test_create_rich_console(self):
        """Test creating a new console instance."""
        console = create_rich_console()
        assert isinstance(console, RichConsole)
    
    def test_create_rich_console_with_force_terminal(self):
        """Test creating a console with force_terminal parameter."""
        console = create_rich_console(force_terminal=True)
        assert isinstance(console, RichConsole)


if __name__ == "__main__":
    pytest.main([__file__])