"""Utility functions for ADW system."""

import json
import logging
import os
import re
import sys
import uuid
from typing import Any, TypeVar, Type, Union, Optional
from .config import config

# Import rich console functionality
try:
    from .rich_console import RichConsole, get_rich_console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    RichConsole = None

T = TypeVar('T')


def make_adw_id() -> str:
    """Generate a short 8-character UUID for ADW tracking."""
    return str(uuid.uuid4())[:8]


def setup_logger(
    adw_id: str, 
    trigger_type: str = "adw_plan_build", 
    use_rich: bool = True,
    enable_file_logging: bool = True
) -> logging.Logger:
    """Set up logger that writes to both console and file using adw_id.
    
    Args:
        adw_id: The ADW workflow ID
        trigger_type: Type of trigger (adw_plan_build, trigger_webhook, etc.)
        use_rich: Whether to use rich formatting for console output
        enable_file_logging: Whether to write logs to a file (default: True)
    
    Returns:
        Configured logger instance
    """
    # Create logger with unique name using adw_id
    logger = logging.getLogger(f"adw_{adw_id}")
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler - INFO and above
    if use_rich and RICH_AVAILABLE:
        try:
            from rich.logging import RichHandler
            console_handler = RichHandler(
                console=get_rich_console().console,
                show_time=False,
                show_path=False,
                markup=True
            )
        except ImportError:
            # Fallback to regular StreamHandler if RichHandler unavailable
            console_handler = logging.StreamHandler(sys.stdout)
    else:
        console_handler = logging.StreamHandler(sys.stdout)
    
    console_handler.setLevel(logging.INFO)
    # Simpler format for console (similar to current print statements)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    if enable_file_logging:
        # Get base logs path from config
        base_logs_path = config.logs_dir
        
        # Create log directory: {base_logs_path}/{adw_id}/{trigger_type}/
        log_dir = base_logs_path / adw_id / trigger_type
        os.makedirs(log_dir, exist_ok=True)
        
        # Log file path: ai_docs/logs/{adw_id}/adw_plan_build/execution.log
        log_file = log_dir / "execution.log"
        
        # File handler - captures everything (ALWAYS plain text for logs)
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        
        # Format with timestamp for file (ALWAYS plain text)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        logger.debug(f"Log file: {log_file}")
    
    # Log initial setup message
    logger.info(f"ADW Logger initialized - ID: {adw_id}")
    
    return logger


def get_rich_console_instance() -> Optional[RichConsole]:
    """Get rich console instance if available, otherwise None."""
    if RICH_AVAILABLE:
        return get_rich_console()
    return None


def get_logger(adw_id: str) -> logging.Logger:
    """Get existing logger by ADW ID.
    
    Args:
        adw_id: The ADW workflow ID
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"adw_{adw_id}")


def parse_json(text: str, target_type: Type[T] = None) -> Union[T, Any]:
    """Parse JSON that may be wrapped in markdown code blocks.
    
    Handles various formats:
    - Raw JSON
    - JSON wrapped in ```json ... ```
    - JSON wrapped in ``` ... ```
    - JSON with extra whitespace or newlines
    
    Args:
        text: String containing JSON, possibly wrapped in markdown
        target_type: Optional type to validate/parse the result into (e.g., List[TestResult])
        
    Returns:
        Parsed JSON object, optionally validated as target_type
        
    Raises:
        ValueError: If JSON cannot be parsed from the text
    """
    # Try to extract JSON from markdown code blocks
    # Pattern matches ```json\n...\n``` or ```\n...\n```
    code_block_pattern = r'```(?:json)?\s*\n(.*?)\n```'
    match = re.search(code_block_pattern, text, re.DOTALL)
    
    if match:
        json_str = match.group(1).strip()
    else:
        # No code block found, try to parse the entire text
        json_str = text.strip()
    
    # Try to find JSON array or object boundaries if not already clean
    if not (json_str.startswith('[') or json_str.startswith('{')):
        # Look for JSON array
        array_start = json_str.find('[')
        array_end = json_str.rfind(']')
        
        # Look for JSON object
        obj_start = json_str.find('{')
        obj_end = json_str.rfind('}')
        
        # Determine which comes first and extract accordingly
        if array_start != -1 and (obj_start == -1 or array_start < obj_start):
            if array_end != -1:
                json_str = json_str[array_start:array_end + 1]
        elif obj_start != -1:
            if obj_end != -1:
                json_str = json_str[obj_start:obj_end + 1]
    
    try:
        result = json.loads(json_str)
        
        # If target_type is provided, handle validation
        if target_type:
            # For the special case of dict, just ensure it's a dict
            if target_type is dict:
                if not isinstance(result, dict):
                    raise ValueError(f"Expected dict but got {type(result).__name__}")
            # For list types with __origin__
            elif hasattr(target_type, '__origin__'):
                if target_type.__origin__ == list:
                    if not isinstance(result, list):
                        raise ValueError(f"Expected list but got {type(result).__name__}")
                    item_type = target_type.__args__[0]
                    # Try Pydantic v2 first, then v1
                    if hasattr(item_type, 'model_validate'):
                        result = [item_type.model_validate(item) for item in result]
                    elif hasattr(item_type, 'parse_obj'):
                        result = [item_type.parse_obj(item) for item in result]
            # For Pydantic models
            else:
                if hasattr(target_type, 'model_validate'):
                    result = target_type.model_validate(result)
                elif hasattr(target_type, 'parse_obj'):
                    result = target_type.parse_obj(result)
            
        return result
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}. Text was: {json_str[:200]}...")
    except ValueError as e:
        # Re-raise ValueError for type mismatches
        raise e

def load_prompt(prompt_name: str) -> str:
    """Load a prompt template from the ADW/prompts directory."""
    # Go up 3 levels to get to the ADW root from adw_modules
    adw_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    prompt_file = os.path.join(adw_root, "prompts", f"{prompt_name}.md")

    try:
        with open(prompt_file, "r") as f:
            return f.read()
    except FileNotFoundError:
        raise ValueError(f"Prompt file not found: {prompt_file}")
    except Exception as e:
        raise IOError(f"Error reading prompt file {prompt_file}: {e}")


def get_test_command(target_dir: str = ".") -> str:
    """Detect the appropriate test command for the project.
    
    Args:
        target_dir: Directory to check for project files (ignored in config mode)
        
    Returns:
        Command string to run tests
    """
    return config.test_command
