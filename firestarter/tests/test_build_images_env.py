import pytest
from ruamel.yaml import YAML

from firestarter.common.preprocessor import interpolate_config_values
from firestarter.common.validations import process_env_var
from firestarter.workflows.build_images.build_images import BuildImages, vars_input_resolver
from firestarter.workflows.build_images.config import load_config_values


@pytest.mark.parametrize('value', ['', 'true', '123', False, 0, '"quoted"\\path\nnext',
                                 '{{ secrets.TOKEN }}', '{{ env.OTHER }}'])
def test_values_are_strings_not_yaml_or_expressions(monkeypatch, value):
    monkeypatch.setenv('BUILD_VALUE', str(value))
    data = load_config_values('''
quoted: "{{ env.BUILD_VALUE }}"
unquoted: {{ env.BUILD_VALUE }}
single_quoted: '{{ vars_input.VALUE }}'
embedded: prefix-{{ env.BUILD_VALUE }}-{{vars_input.value}}-suffix
list: [{{ env.BUILD_VALUE }}]
literal: true
"{{ env.KEY }}": unchanged
''')
    result = interpolate_config_values(data, {
        'env': process_env_var, 'vars_input': vars_input_resolver({'Value': value}),
    })
    assert result['quoted'] == result['unquoted'] == result['single_quoted'] == str(value)
    assert result['embedded'] == f'prefix-{value}-{value}-suffix'
    assert result['list'] == [str(value)]
    assert result['literal'] is True
    assert result['{{ env.KEY }}'] == 'unchanged'


@pytest.fixture
def config_file(tmp_path):
    dockerfile = tmp_path / 'Dockerfile'
    dockerfile.write_text('FROM scratch\n')
    path = tmp_path / 'build_images.yaml'
    YAML().dump({'snapshots': {'default': {
        'dockerfile': str(dockerfile),
        'build_args': {'VALUE': '{{ env.BUILD_VALUE }}', 'INPUT': '{{ vars_input.RePo_NaMe }}'},
    }}}, path)
    return path


def builder(config_file, **variables):
    return BuildImages(
        vars={'from': 'aaaaaaa', 'repo_name': 'org/app',
              'snapshots_registry': 'registry.test', 'releases_registry': 'registry.test',
              'dereference_enabled': False, **variables},
        secrets={}, additional_build_args={}, config_file=str(config_file),
    )


@pytest.mark.parametrize('context', ['env', 'vars_input'])
@pytest.mark.parametrize('allow_undefined', [False, True])
def test_missing_variables_report_location(monkeypatch, config_file, capsys, context, allow_undefined):
    monkeypatch.delenv('MISSING_VALUE', raising=False)
    source = config_file.read_text().replace('{{ env.BUILD_VALUE }}', '{{ ' + context + '.MISSING_VALUE }}')
    config_file.write_text(source)
    if allow_undefined:
        result = builder(config_file, allow_undefined=True)
        assert result.config.images['default'].build_args['VALUE'] == ''
        message = capsys.readouterr().out
        assert '::warning::' in message
    else:
        with pytest.raises(ValueError) as error:
            builder(config_file)
        message = str(error.value)
    assert 'MISSING_VALUE' in message
    assert '$.snapshots.default.build_args.VALUE' in message
    assert str(config_file) in message


@pytest.mark.parametrize('symbol', ['github.ref_name', 'vars.X', 'secrets.X', 'build_images_args.X'])
@pytest.mark.parametrize('allow_undefined', [False, True])
def test_unsupported_contexts_fail(config_file, symbol, allow_undefined):
    config_file.write_text(config_file.read_text().replace('{{ env.BUILD_VALUE }}', '{{ ' + symbol + ' }}'))
    with pytest.raises(ValueError, match='Unknown context'):
        builder(config_file, allow_undefined=allow_undefined)


def test_env_lookup_is_case_sensitive(monkeypatch):
    monkeypatch.setenv('BUILD_VALUE', '')
    monkeypatch.delenv('build_value', raising=False)
    assert process_env_var('BUILD_VALUE') == ''
    with pytest.raises(ValueError):
        process_env_var('build_value')


@pytest.mark.parametrize('value', ['true', 'false', 0, 1, None])
def test_allow_undefined_requires_boolean(config_file, value):
    with pytest.raises(ValueError, match='TOML boolean'):
        builder(config_file, allow_undefined=value)


def test_only_explicit_original_inputs_are_exposed(monkeypatch, config_file):
    monkeypatch.setenv('BUILD_VALUE', 'ok')
    config_file.write_text(config_file.read_text().replace('{{ vars_input.RePo_NaMe }}', '{{ vars_input.from }}'))
    monkeypatch.setattr(BuildImages, 'dereference_from_input', lambda self, value: 'bbbbbbb')
    result = builder(config_file, dereference_enabled=True)
    assert result.from_version == 'bbbbbbb'
    assert result.config.images['default'].build_args['INPUT'] == 'aaaaaaa'
    config_file.write_text(config_file.read_text().replace('{{ vars_input.from }}', '{{ vars_input.type }}'))
    with pytest.raises(ValueError, match='type'):
        builder(config_file)


def test_credential_resolution_does_not_mutate_input_context(monkeypatch, config_file):
    monkeypatch.setenv('BUILD_VALUE', 'ok')
    config_file.write_text(config_file.read_text().replace(
        '{{ vars_input.RePo_NaMe }}', '{{ vars_input.snapshots_registry_creds }}'))

    def resolve(self, secrets):
        self.vars['snapshots_registry_creds']['TOKEN'] = 'resolved'
        return secrets

    monkeypatch.setattr(BuildImages, 'resolve_secrets', resolve)
    workflow = builder(config_file, snapshots_registry_creds={'TOKEN': 'original'})
    assert workflow.config.images['default'].build_args['INPUT'] == "{'TOKEN': 'original'}"


def test_schema_validation_follows_string_substitution(monkeypatch, config_file):
    from jsonschema import ValidationError

    monkeypatch.setenv('BUILD_VALUE', 'ok')
    data = YAML(typ='safe').load(config_file)
    data['snapshots']['default']['platforms'] = '{{ vars_input.platforms }}'
    YAML().dump(data, config_file)
    with pytest.raises(ValidationError):
        builder(config_file, platforms='amd64,arm64')


@pytest.mark.asyncio
@pytest.mark.parametrize('value', ['value', '{{ secrets.TOKEN }}'])
async def test_interpolated_values_reach_build_and_results(monkeypatch, mocker, config_file, tmp_path, value):
    monkeypatch.setenv('BUILD_VALUE', value)
    result_file = tmp_path / 'results.yaml'
    workflow = builder(config_file, snapshots_registry_creds='', output_results=str(result_file))
    workflow.filter_flavors()
    connection = mocker.patch('dagger.Connection')
    connection.return_value.__aenter__.return_value = mocker.MagicMock()
    compile_image = mocker.patch.object(workflow, 'compile_image_and_publish')
    results = await workflow.compile_images_for_all_flavors()
    assert {arg.name: arg.value for arg in compile_image.call_args.args[1]} == {
        'INPUT': 'org/app', 'VALUE': value,
    }
    assert results[0]['build_args']['VALUE'] == value
    assert YAML(typ='safe').load(result_file)[0]['build_args']['VALUE'] == value
