"""
Zerith AI — System Commands
Execute shell commands and open applications. All operations go through the safety layer.
"""

import os
import subprocess
import platform
from utils.logger import log
from utils.permissions import check_and_confirm


def run_command(command: str, timeout: int = 30) -> str:
    """
    Execute a shell command and return stdout.
    Requires user permission via the safety layer.
    """
    if not check_and_confirm("run_command", command):
        return "Command execution denied by user."

    log.info(f"Running command: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.expanduser("~"),
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\n[stderr] {result.stderr.strip()}"
        log.info(f"Command completed (exit code {result.returncode})")
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        log.warning(f"Command timed out after {timeout}s: {command}")
        return f"Command timed out after {timeout} seconds"
    except Exception as e:
        log.warning(f"Command failed: {e}")
        return f"Command failed: {e}"


def open_application(name: str) -> str:
    """Open an application by name (Windows-focused)."""
    log.info(f"Opening application: {name}")
    system = platform.system()

    try:
        if system == "Windows":
            os.startfile(name)
        elif system == "Darwin":  # macOS
            subprocess.Popen(["open", "-a", name])
        else:  # Linux
            subprocess.Popen([name])
        return f"Opened {name}"
    except FileNotFoundError:
        # Try via start command on Windows
        if system == "Windows":
            try:
                subprocess.Popen(f"start {name}", shell=True)
                return f"Opened {name} via start command"
            except Exception as e:
                log.warning(f"Could not open application: {e}")
                return f"Could not open application '{name}': {e}"
        log.warning(f"Application not found: {name}")
        return f"Application not found: {name}"
    except Exception as e:
        log.warning(f"Could not open application: {e}")
        return f"Could not open application '{name}': {e}"


def get_system_info() -> str:
    """Return basic system information."""
    info = {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
    }
    return "\n".join(f"{k}: {v}" for k, v in info.items())


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
    "run_command": run_command,
    "open_application": open_application,
    "get_system_info": get_system_info,
    "list_directory": list_directory,
}
