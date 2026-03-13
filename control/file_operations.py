"""
Zerith AI — File Operations
Read, write, find, and list files on the user's system.
Includes self-modification tools that allow Zerith to modify its own code.
"""

import os
import glob
from pathlib import Path
from utils.logger import log

# Get the Zerith project directory for safety checks
ZERITH_DIR = Path(__file__).resolve().parent.parent


def read_file(path: str) -> str:
    """Read and return the contents of a file."""
    try:
        target = os.path.expanduser(path)
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        log.info(f"Read file: {target} ({len(content)} chars)")
        return content[:5000] if len(content) > 5000 else content
    except Exception as e:
        log.warning(f"Could not read file: {e}")
        return f"Could not read file: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates parent directories if needed."""
    try:
        target = os.path.expanduser(path)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        log.info(f"Wrote file: {target} ({len(content)} chars)")
        return f"File written: {target}"
    except Exception as e:
        log.warning(f"Could not write file: {e}")
        return f"Could not write file: {e}"


def find_file(name: str, directory: str = "~") -> str:
    """
    Search for files matching a name pattern.
    Supports wildcards like *.py, report*, etc.
    """
    try:
        search_dir = os.path.expanduser(directory)
        pattern = os.path.join(search_dir, "**", name)
        matches = glob.glob(pattern, recursive=True)

        if not matches:
            return f"No files matching '{name}' found in {search_dir}"

        # Limit results to avoid flooding
        result_lines = [f"📄 {m}" for m in matches[:25]]
        summary = f"Found {len(matches)} file(s) matching '{name}':\n"
        summary += "\n".join(result_lines)
        if len(matches) > 25:
            summary += f"\n... and {len(matches) - 25} more"
        return summary
    except Exception as e:
        log.warning(f"File search failed: {e}")
        return f"File search failed: {e}"


def list_directory(path: str = ".") -> str:
    """List files and directories at the given path."""
    try:
        target = os.path.expanduser(path)
        entries = os.listdir(target)
        dirs = [f"📁 {e}" for e in entries if os.path.isdir(os.path.join(target, e))]
        files = [f"📄 {e}" for e in entries if os.path.isfile(os.path.join(target, e))]
        result = "\n".join(sorted(dirs) + sorted(files))
        return result or "(empty directory)"
    except Exception as e:
        log.warning(f"Could not list directory: {e}")
        return f"Could not list directory: {e}"


def edit_file(path: str, search: str = None, replace: str = None, content: str = None) -> str:
    """
    Edit a specific portion of a file or write entirely new content.
    Only allows editing within the Zerith project directory for safety.
    
    Parameters:
        path: File path to edit (must be within Zerith/ directory)
        search: Text to search for (for partial edits)
        replace: Text to replace the search text with
        content: Full file content (for complete overwrite)
    """
    try:
        target = os.path.expanduser(path)
        abs_target = os.path.abspath(target)
        abs_zerith = os.path.abspath(ZERITH_DIR)
        
        # Security check: only allow edits within Zerith directory
        if not abs_target.startswith(abs_zerith):
            log.warning(f"Blocked attempt to edit file outside Zerith: {target}")
            return f"Security: Can only edit files within the Zerith project directory.\nAllowed path: {ZERITH_DIR}"
        
        # Check if file exists
        file_exists = os.path.isfile(abs_target)
        
        # Create parent directories if needed
        os.makedirs(os.path.dirname(abs_target), exist_ok=True)
        
        if content is not None:
            # Full file overwrite
            with open(abs_target, "w", encoding="utf-8") as f:
                f.write(content)
            log.info(f"[SELF-MODIFY] Wrote file: {abs_target} ({len(content)} chars)")
            return f"File updated: {abs_target}"
        
        elif search is not None and replace is not None:
            # Partial edit - search and replace
            if not file_exists:
                return f"File does not exist: {path}"
            
            with open(abs_target, "r", encoding="utf-8", errors="replace") as f:
                file_content = f.read()
            
            if search not in file_content:
                return f"Search text not found in file. Make sure the exact text exists.\nFile: {path}"
            
            new_content = file_content.replace(search, replace, 1)  # Replace first occurrence
            
            with open(abs_target, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            log.info(f"[SELF-MODIFY] Edited file: {abs_target}")
            return f"File edited successfully: {path}"
        
        else:
            return "Please provide either 'content' for full overwrite, or 'search' and 'replace' for partial edit."
            
    except Exception as e:
        log.warning(f"Could not edit file: {e}")
        return f"Could not edit file: {e}"


def get_self_info() -> str:
    """Return information about Zerith's self-modification capabilities."""
    return """
Zerith Self-Coding Capabilities:
- read_file: Read any file in the project
- write_file: Write content to new or existing files
- edit_file: Modify specific parts of files using search/replace
- find_file: Search for files by name pattern
- list_directory: List contents of directories

Editable files include:
- templates/index.html (UI templates)
- static/app.js (Frontend JavaScript)
- static/style.css (Frontend styles)
- Any Python module in the Zerith/ directory

Safety: Cannot edit files outside the Zerith project directory.
"""


# Handler map for router registration
HANDLERS = {
    "read_file": read_file,
    "write_file": write_file,
    "find_file": find_file,
    "list_directory": list_directory,
    "edit_file": edit_file,           # Self-modification: edit file contents
    "get_self_info": get_self_info,   # Self-modification: capability info
}
