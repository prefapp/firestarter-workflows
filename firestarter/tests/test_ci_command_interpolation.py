import subprocess
from types import SimpleNamespace

import pytest

from firestarter.workflows.ci.bash_runner import create_script_from_commands
from firestarter.workflows.ci.task_manager import TaskManager


@pytest.mark.parametrize('context_name', ['vars', 'secrets', 'env'])
@pytest.mark.parametrize('value', ['safe', 'two words', 'safe; printf INJECTED'])
def test_ci_interpolation_preserves_literal_shell_argument(
    tmp_path, monkeypatch, mocker, context_name, value,
):
    monkeypatch.setenv('VALUE', value)
    path = tmp_path / 'ci.yaml'
    path.write_text(
        'image: alpine\nversion: "1"\ntasks:\n'
        '  - name: print-value\n'
        '    run: |\n'
        "      printf '%s|' ${{ " + context_name + '.VALUE }}\n'
    )
    manager = TaskManager()
    manager.context = SimpleNamespace(vars={'VALUE': value}, secrets={'VALUE': value})
    scheduler = mocker.patch('firestarter.workflows.ci.task_manager.task_scheduler')
    manager.load(str(path), '../workflows/ci/schema.json')
    config = scheduler.call_args.args[0]

    # Execute the same script creation path used by bash_runner, without Dagger.
    commands = config['tasks'][0]['run']
    script = create_script_from_commands(commands.split('\n'), str(tmp_path))
    result = subprocess.run(['bash', '-e', script], capture_output=True, text=True, check=True)

    assert result.stdout == value + '|'
