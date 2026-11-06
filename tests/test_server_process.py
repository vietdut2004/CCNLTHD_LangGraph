import unittest
from pathlib import Path
from unittest.mock import patch

from server_process import _is_project_cli, _verified_cli, restart_server


PROJECT = Path(r'C:\demo project')
EXE = str(PROJECT / '.venv' / 'Scripts' / 'python.exe')


def process(pid, parent, exe=EXE, command=None, created='2026-11-05T10:00:00Z'):
    return {
        'ProcessId': pid, 'ParentProcessId': parent,
        'ExecutablePath': exe,
        'CommandLine': command if command is not None else f'"{exe}" -m langgraph_cli dev --host 127.0.0.1',
        'CreationDate': created,
    }


def snapshot(owner=20, records=None):
    return {'listeners': [{'OwningProcess': owner}], 'processes': records or []}


class OwnershipTests(unittest.TestCase):
    def test_child_listener_is_attributed_to_project_cli_ancestor(self):
        cli = process(10, 1)
        worker = process(20, 10, exe=r'C:\Python\python.exe',
                         command='python.exe -c "multiprocessing worker"',
                         created='2026-11-05T10:00:01Z')
        self.assertEqual(_verified_cli(snapshot(records=[cli, worker]), PROJECT), cli)

    def test_other_checkout_cli_is_refused(self):
        other = process(20, 1, exe=r'C:\another project\.venv\Scripts\python.exe')
        with self.assertRaises(RuntimeError):
            _verified_cli(snapshot(records=[other]), PROJECT)

    def test_project_python_running_unrelated_module_is_refused(self):
        other = process(20, 1, command=f'"{EXE}" -m http.server 2024')
        with self.assertRaises(RuntimeError):
            _verified_cli(snapshot(records=[other]), PROJECT)

    def test_missing_owner_cannot_be_attributed_through_unknown_pid(self):
        with self.assertRaises(RuntimeError):
            _verified_cli(snapshot(records=[process(10, 1)]), PROJECT)

    def test_reused_parent_pid_cannot_claim_older_worker(self):
        cli = process(10, 1, created='2026-11-05T11:00:00Z')
        worker = process(20, 10, exe=r'C:\Python\python.exe', command='python.exe -c worker')
        with self.assertRaises(RuntimeError):
            _verified_cli(snapshot(records=[cli, worker]), PROJECT)

    def test_quoted_command_can_identify_venv_shim_when_executable_is_missing(self):
        self.assertTrue(_is_project_cli(process(
            10, 1, exe=None, command=f'"{EXE}" -m langgraph_cli dev --host 127.0.0.1'
        ), PROJECT))

    def test_module_name_only_inside_an_argument_is_not_a_cli(self):
        self.assertFalse(_is_project_cli(process(10, 1, command=f'"{EXE}" -c "-m langgraph_cli dev"'), PROJECT))


class RestartTests(unittest.TestCase):
    @patch('server_process.os.name', 'nt')
    @patch('server_process.subprocess.run')
    @patch('server_process._inspect_server')
    def test_no_listener_does_not_terminate_any_process(self, inspect, run):
        inspect.return_value = {'listeners': [], 'processes': []}
        self.assertFalse(restart_server(PROJECT))
        run.assert_not_called()

    @patch('server_process.os.name', 'nt')
    @patch('server_process.subprocess.run')
    @patch('server_process._inspect_server')
    def test_process_replaced_between_checks_is_not_terminated(self, inspect, run):
        # Use resolved project identity, just as the public helper does.
        project = PROJECT.resolve()
        exe = str(project / '.venv' / 'Scripts' / 'python.exe')
        before = process(20, 1, exe=exe)
        after = process(20, 1, exe=exe, created='2026-11-05T11:00:00Z')
        inspect.side_effect = [snapshot(records=[before]), snapshot(records=[after])]
        with self.assertRaises(RuntimeError):
            restart_server(PROJECT)
        run.assert_not_called()

    @patch('server_process.os.name', 'nt')
    @patch('server_process.subprocess.run')
    @patch('server_process._inspect_server')
    def test_owned_tree_is_stopped_and_port_release_confirmed(self, inspect, run):
        project = PROJECT.resolve()
        exe = str(project / '.venv' / 'Scripts' / 'python.exe')
        cli = process(10, 1, exe=exe)
        worker = process(20, 10, exe=r'C:\Python\python.exe', command='python.exe -c worker',
                         created='2026-11-05T10:00:01Z')
        running = snapshot(records=[cli, worker])
        inspect.side_effect = [running, running, {'listeners': [], 'processes': []}]
        self.assertTrue(restart_server(PROJECT))
        self.assertEqual(run.call_args.args[0], ['taskkill.exe', '/PID', '10', '/T', '/F'])
        self.assertEqual(inspect.call_count, 3)


if __name__ == '__main__':
    unittest.main()
