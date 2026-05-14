# src/yini_test/utils/executables.py
from __future__ import annotations

import os
import shutil

# For example, the cross-platform command "npx" should resolve:
# - on Windows to: C:\Program Files\nodejs\npx.cmd
# - on Linux to:   /usr/bin/npx
def resolve_executable(command: str) -> str:
    """Resolve an executable command in a cross-platform way.

    On Windows, command-line tools installed by Node.js are often available
    as .cmd shims, for example npx.cmd. Python's subprocess module does not
    always resolve these when shell=False and the command is passed as a list.

    If the command can be resolved directly, the resolved path is returned.
    On Windows, if direct resolution fails, a .cmd variant is also tried.
    If nothing is found, the original command is returned so subprocess can
    raise the normal FileNotFoundError.
    """
    resolved = shutil.which(command)

    if resolved is not None:
        return resolved

    if os.name == "nt" and not command.lower().endswith((".exe", ".cmd", ".bat")):
        resolved_cmd = shutil.which(f"{command}.cmd")

        if resolved_cmd is not None:
            return resolved_cmd

    return command
