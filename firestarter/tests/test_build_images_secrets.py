from copy import deepcopy
from types import SimpleNamespace

import pytest
from ruamel.yaml import YAML

from firestarter.cli.parser import main
from firestarter.workflows.build_images.build_images import BuildImages


EXPRESSION = '{{ build_images_secrets.TOKEN }}'
ARN = 'arn:aws:ssm:eu-west-1:041728615317:parameter/dev/my-postgres-pass'


def make_builder(tmp_path, image, secrets=None, **variables):
    dockerfile = tmp_path / 'Dockerfile'
    dockerfile.write_text('FROM scratch\n')
    config_file = tmp_path / 'build_images.yaml'
    image = {'dockerfile': str(dockerfile), **image}
    YAML().dump({kind: {'default': image} for kind in ('snapshots', 'releases')}, config_file)
    return BuildImages(
        vars={'from': 'aaaaaaa', 'repo_name': 'org/app',
              'snapshots_registry': 'registry.test', 'releases_registry': 'registry.test',
              'snapshots_registry_creds': '', 'dereference_enabled': False,
              'output_results': str(tmp_path / 'results.yaml'), **variables},
        secrets=secrets or {}, config_file=str(config_file),
    )


@pytest.mark.parametrize('kind', ['snapshots', 'releases'])
@pytest.mark.parametrize('value', ['literal', 'line one\nline two', ARN, ''])
def test_secret_context_preserves_raw_values(tmp_path, mocker, kind, value):
    resolve = mocker.patch.object(BuildImages, 'resolve_secrets')
    workflow = make_builder(tmp_path, {'secrets': {'ALIAS': EXPRESSION}},
                            {'TOKEN': value}, type=kind)
    assert workflow.config.images['default'].secrets == {'ALIAS': value}
    resolve.assert_not_called()


@pytest.mark.parametrize('image', [
    {'build_args': {'LEAK': EXPRESSION}},
    {'extra_tags': [EXPRESSION]},
    {'registry': {'name': EXPRESSION}},
    {'dockerfile': EXPRESSION},
    {'platforms': [EXPRESSION]},
    {'secrets': {'NESTED': {'TOKEN': EXPRESSION}}},
    {'secrets': {'NESTED': [EXPRESSION]}},
    {'build_args.LEAK': EXPRESSION},
])
@pytest.mark.parametrize('allow_undefined', [False, True])
def test_secret_context_rejected_outside_direct_secret_values(tmp_path, image, allow_undefined):
    with pytest.raises(ValueError) as error:
        make_builder(tmp_path, image, {'TOKEN': 'DO_NOT_PRINT'}, allow_undefined=allow_undefined)
    message = str(error.value)
    assert 'build_images_secrets' in message
    assert '$.snapshots.default.' in message
    assert "a flavor's 'secrets' mapping" in message
    assert 'DO_NOT_PRINT' not in message


@pytest.mark.parametrize('allow_undefined', [False, True])
def test_missing_secret_reports_path(tmp_path, capsys, allow_undefined):
    if allow_undefined:
        workflow = make_builder(tmp_path, {'secrets': {'ALIAS': EXPRESSION}},
                                allow_undefined=True)
        assert workflow.config.images['default'].secrets['ALIAS'] == ''
        message = capsys.readouterr().out
    else:
        with pytest.raises(ValueError) as error:
            make_builder(tmp_path, {'secrets': {'ALIAS': EXPRESSION}})
        message = str(error.value)
    assert 'TOKEN' in message
    assert '$.snapshots.default.secrets.ALIAS' in message


def test_secret_names_are_case_sensitive(tmp_path):
    with pytest.raises(ValueError, match="Undefined build_images_secrets variable 'TOKEN'"):
        make_builder(tmp_path, {'secrets': {'ALIAS': EXPRESSION}}, {'token': 'value'})


@pytest.mark.asyncio
async def test_only_explicit_flavor_inputs_reach_dagger(tmp_path, mocker):
    inputs = {'TOKEN': ARN, 'UNUSED': 'unused-secret'}
    original = deepcopy(inputs)
    workflow = make_builder(tmp_path, {
        'build_args': {'ARG': '{{ build_images_vars.CUSTOM }}'},
        'secrets': {'DB_PASSWORD': EXPRESSION},
    }, inputs, CUSTOM='custom-value', UNUSED_VAR='unused-var')
    workflow.config.images['plain'] = deepcopy(workflow.config.images['default'])
    workflow.config.images['plain'].build_args = {}
    workflow.config.images['plain'].secrets = {}
    workflow._flavors = ['default', 'plain']
    client = mocker.MagicMock()
    client.set_secret.side_effect = lambda name, value: (name, value)
    connection = mocker.patch('dagger.Connection')
    connection.return_value.__aenter__.return_value = client
    provider = mocker.patch(
        'firestarter.workflows.build_images.providers.secrets.factory.SecretProviderFactory.provider_from_str')
    provider.return_value.get_secret.return_value = 'resolved-password'
    compile_image = mocker.patch.object(workflow, 'compile_image_and_publish')
    results = await workflow.compile_images_for_all_flavors()
    provider.assert_called_once_with(ARN)
    client.set_secret.assert_called_once_with('DB_PASSWORD', 'resolved-password')
    first, second = compile_image.call_args_list
    assert {arg.name: arg.value for arg in first.args[1]} == {'ARG': 'custom-value'}
    assert first.args[2] == [('DB_PASSWORD', 'resolved-password')]
    assert second.args[1:3] == ([], [])
    assert workflow.config.images['default'].secrets['DB_PASSWORD'] == ARN
    assert inputs == original
    assert results[0]['build_args'] == {'ARG': 'custom-value'}
    assert 'resolved-password' not in (tmp_path / 'results.yaml').read_text()


def test_cli_rejects_removed_argument(monkeypatch, capsys):
    monkeypatch.setattr('sys.argv', ['firestarter', 'build_images', '--additional_build_args', '{}'])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert 'unrecognized arguments' in capsys.readouterr().err


def test_cli_ignores_removed_environment_input(monkeypatch, mocker):
    monkeypatch.setattr('sys.argv', ['firestarter', 'build_images'])
    for name in ('INPUT_VARS', 'INPUT_SECRETS', 'INPUT_CONFIG_FILE'):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv('INPUT_ADDITIONAL_BUILD_ARGS', 'invalid TOML deliberately')
    run = mocker.Mock(return_value=[])
    mocker.patch('firestarter.cli.parser.importlib.import_module',
                 return_value=SimpleNamespace(run=run))
    main()
    run.assert_called_once_with(vars={}, secrets={}, config_file=None)


def test_cli_logs_names_not_values(monkeypatch, mocker, caplog):
    monkeypatch.setattr('sys.argv', ['firestarter', 'build_images',
                                   '--vars', '{ CREDENTIAL = "variable-sensitive-value" }',
                                   '--secrets', '{ TOKEN = "secret-sensitive-value" }'])
    for name in ('INPUT_VARS', 'INPUT_SECRETS', 'INPUT_CONFIG_FILE'):
        monkeypatch.delenv(name, raising=False)
    mocker.patch('firestarter.cli.parser.importlib.import_module',
                 return_value=SimpleNamespace(run=mocker.Mock(return_value=[])))
    with caplog.at_level('DEBUG'):
        main()
    assert 'TOKEN' in caplog.text
    assert 'secret-sensitive-value' not in caplog.text
    assert 'variable-sensitive-value' not in caplog.text


def test_registry_login_does_not_log_credentials(tmp_path, mocker, caplog):
    workflow = make_builder(tmp_path, {})
    provider = mocker.patch(
        'firestarter.workflows.build_images.build_images.DockerRegistryAuthFactory.provider_from_str')
    with caplog.at_level('INFO'):
        workflow.login('generic', 'registry.test', 'registry-sensitive-value')
    assert provider.return_value.creds == 'registry-sensitive-value'
    assert 'registry-sensitive-value' not in caplog.text


def test_invalid_config_does_not_disclose_interpolated_secrets(tmp_path, capsys, caplog):
    import logging
    import traceback

    from firestarter.workflows.build_images import run

    secret = 'PLAINTEXT_SECRET_SENTINEL'
    config_file = tmp_path / 'build_images.yaml'
    YAML().dump({
        'snapshots': {
            'default': {
                'secrets': {'TOKEN': EXPRESSION},
            },
        },
        'releases': {
            'default': {
                'secrets': {'TOKEN': EXPRESSION},
            },
        },
    }, config_file)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(SystemExit) as error:
            run(
                vars={
                    'from': 'aaaaaaa',
                    'repo_name': 'org/app',
                    'snapshots_registry': 'registry.test',
                    'releases_registry': 'registry.test',
                    'snapshots_registry_creds': '',
                    'dereference_enabled': False,
                    'output_results': str(tmp_path / 'results.yaml'),
                },
                secrets={'TOKEN': secret},
                config_file=str(config_file),
            )

    assert error.value.code == 1
    out = capsys.readouterr().out
    rule = "'dockerfile' is a required property"
    expected = f"Invalid build images config '{config_file}': {rule}"

    assert expected in out
    assert '::error title=BuildImages Failure::' in out
    assert secret not in out
    assert 'On instance' not in out

    assert expected in caplog.text
    assert secret not in caplog.text
    assert 'On instance' not in caplog.text

    records = [r for r in caplog.records if r.exc_info]
    assert records
    formatted = ''.join(
        traceback.format_exception(*records[-1].exc_info)
    )
    assert secret not in formatted
    assert 'On instance' not in formatted
    assert records[-1].exc_info[1].__cause__ is None
    assert records[-1].exc_info[1].__context__ is None
    assert isinstance(records[-1].exc_info[1], ValueError)
