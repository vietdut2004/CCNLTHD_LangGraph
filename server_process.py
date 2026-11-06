"""Stop only a verified LangGraph CLI tree belonging to this checkout on Windows."""

from __future__ import annotations

import json
import ntpath
import os
import shlex
import subprocess
import time
from pathlib import Path


# Values are passed in a private environment, never interpolated into shell code.
_INSPECT_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$portNumber = [int]$env:LANGGRAPH_RESTART_PORT
$listeners = @(Get-NetTCPConnection -LocalPort $portNumber -State Listen -ErrorAction SilentlyContinue |
    Select-Object LocalAddress,LocalPort,OwningProcess)
$records = @{}
foreach ($listener in $listeners) {
    $nextId = [int]$listener.OwningProcess
    for ($depth = 0; $depth -lt 32 -and $nextId -gt 0; $depth++) {
        if ($records.ContainsKey([string]$nextId)) { break }
        $item = Get-CimInstance Win32_Process -Filter ('ProcessId = {0}' -f $nextId) -ErrorAction Stop
        if ($null -eq $item) { break }
        $records[[string]$nextId] = @{
            ProcessId = [int]$item.ProcessId
            ParentProcessId = [int]$item.ParentProcessId
            ExecutablePath = $item.ExecutablePath
            CommandLine = $item.CommandLine
            CreationDate = $item.CreationDate.ToUniversalTime().ToString('o')
        }
        $nextId = [int]$item.ParentProcessId
    }
}
@{ listeners = @($listeners); processes = @($records.Values) } |
    ConvertTo-Json -Depth 5 -Compress
"""


def _windows_path(path: str | Path) -> str:
    return ntpath.normcase(ntpath.normpath(str(path)))


def _is_project_cli(record: dict, project_dir: Path) -> bool:
    """Recognize this checkout's interpreter and the actual CLI module arguments."""
    expected = _windows_path(project_dir / '.venv' / 'Scripts' / 'python.exe')
    command = record.get('CommandLine') or ''
    try:
        args = [item.strip('"') for item in shlex.split(command, posix=False)]
    except ValueError:
        return False
    if len(args) < 4 or args[1:4] != ['-m', 'langgraph_cli', 'dev']:
        return False
    executable_matches = _windows_path(record.get('ExecutablePath') or '') == expected
    quoted_command_matches = command.lstrip().startswith('"') and _windows_path(args[0]) == expected
    return executable_matches or quoted_command_matches


def _verified_cli(snapshot: dict, project_dir: Path) -> dict | None:
    """Return a shared owned CLI ancestor, refusing unknown or unrelated listeners."""
    listeners = snapshot.get('listeners', [])
    if not listeners:
        return None
    records = {int(p['ProcessId']): p for p in snapshot.get('processes', [])}
    selected = {}
    for listener in listeners:
        current = int(listener['OwningProcess'])
        seen = set()
        owned = None
        child_created = None
        while current and current not in seen:
            seen.add(current)
            process = records.get(current)
            if process is None:
                break
            created = process.get('CreationDate')
            # A reused parent PID must not establish ownership of an older child.
            if not created or (child_created is not None and created > child_created):
                break
            if _is_project_cli(process, project_dir):
                owned = process
            child_created = created
            current = int(process.get('ParentProcessId') or 0)
        if owned is None:
            raise RuntimeError(
                'Cong 2024 dang duoc su dung boi tien trinh khong xac minh duoc thuoc do an. '
                'Khong dung tien trinh do; hay dong dung may chu trong terminal cua no.'
            )
        selected[int(owned['ProcessId'])] = owned
    if len(selected) != 1:
        raise RuntimeError('Co nhieu may chu tren cong nay; khong tu dong dung khi chua xac dinh ro.')
    return next(iter(selected.values()))


def _inspect_server(port: int) -> dict:
    env = os.environ.copy()
    env['LANGGRAPH_RESTART_PORT'] = str(int(port))
    result = subprocess.run(
        ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', _INSPECT_SCRIPT],
        env=env, capture_output=True, text=True, encoding='utf-8', errors='replace',
        timeout=20, check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    )
    return json.loads(result.stdout.lstrip('\ufeff'))


def _same_identity(first: dict, second: dict) -> bool:
    return all(first.get(key) == second.get(key) for key in (
        'ProcessId', 'CreationDate', 'ExecutablePath', 'CommandLine',
    ))


def restart_server(project_dir: Path, port: int = 2024) -> bool:
    """Stop the verified current CLI tree; the caller then starts the replacement.

    Returns False when nothing is listening. Does not delete thread persistence.
    This helper intentionally refuses to stop a server it cannot attribute to this
    project's virtual environment, even if the port answers the expected UI.
    """
    if os.name != 'nt':
        raise RuntimeError('Tuy chon --restart tu dong hien chi ho tro Windows.')
    project_dir = Path(project_dir).resolve()
    first = _verified_cli(_inspect_server(port), project_dir)
    if first is None:
        return False
    # Re-query both listener and process chain immediately before termination.
    second = _verified_cli(_inspect_server(port), project_dir)
    if second is None:
        return False
    if not _same_identity(first, second):
        raise RuntimeError('Tien trinh may chu da thay doi trong luc kiem tra. Hay chay lai lenh.')
    subprocess.run(
        ['taskkill.exe', '/PID', str(int(second['ProcessId'])), '/T', '/F'],
        capture_output=True, text=True, timeout=15, check=True,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    )
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if not _inspect_server(port).get('listeners'):
            return True
        time.sleep(.2)
    raise RuntimeError('Cong may chu chua duoc giai phong. Hay kiem tra terminal va chay lai.')
