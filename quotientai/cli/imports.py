import importlib
import inspect
import sys
from pathlib import Path

from quotientai.exceptions import QuotientAIError
from quotientai.resources.runs import Run


def import_evaluate(path: Path) -> callable:
    """
    Searches for and imports the quotient.evaluate call from the specified path.

    Args:
        path: Path to either the specific evaluation file or directory to search in

    Returns:
        A callable that returns a Run object when executed

    Raises:
        QuotientAIError: If no valid evaluation file or function is found
    """
    if path.is_file():
        # If it's a file, use it directly
        if "evaluate" not in path.name:
            raise QuotientAIError(
                f"File '{path}' does not contain 'evaluate' in its name. "
                "Please provide a valid evaluation file."
            )
        files_to_check = [path]
    else:
        # If it's a directory, find all evaluate files
        files_to_check = list(path.rglob("*evaluate*.py"))
        if not files_to_check:
            raise QuotientAIError(
                f"no evaluation files found in '{path}'. "
                "expected to find Python files with 'evaluate' in their name"
            )

    for file_path in files_to_check:
        try:
            # Import the module
            module_name = inspect.getmodulename(str(file_path))
            spec = importlib.util.spec_from_file_location(module_name, str(file_path))
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Look through module's contents
            for name, obj in inspect.getmembers(module):
                # First check if it's a callable
                if callable(obj):
                    try:
                        # Try calling the function
                        result = obj()
                        # Check if it returns a Run object
                        if isinstance(result, Run):
                            return obj
                    except:
                        # Skip if calling the function fails
                        continue

        except Exception as e:
            raise QuotientAIError(
                f"error running evaluation with {file_path}: {str(e)}"
            )

    raise QuotientAIError(
        f"no valid `quotient.evaluate` calls found in {path}. "
        "make sure your file contains a function that returns a Run object from quotient.evaluate"
    )
