"""
Zerith AI — File Operations
Read, write, find, and list files on the user's system.
"""

import os
import glob
from utils.logger import log


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


# Handler map for router registration
HANDLERS = {
    "read_file": read_file,
    "write_file": write_file,
    "find_file": find_file,
    "list_directory": list_directory,
}
