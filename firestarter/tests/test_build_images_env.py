import pytest
from ruamel.yaml import YAML

from firestarter.common.preprocessor import interpolate_config_values
from firestarter.common.validations import process_env_var
from firestarter.workflows.build_images.build_images import BuildImages, build_images_vars_resolver
from firestarter.workflows.build_images.config import Config


@pytest.mark.parametrize('value', ['abc123', '', 'true', '123', '"quoted"\\path\nnext', '${{ env.OTHER }}'])
def test_env_values_are_strings_not_yaml_or_expressions(monkeypatch, value):
    monkeypatch.setenv('BUILD_VALUE', value)
    data = YAML(typ='safe').load('''
quoted: "${{ env.BUILD_VALUE }}"
unquoted: ${{ env.BUILD_VALUE }}
single_quoted: '${{ env.BUILD_VALUE }}'
embedded: prefix-${{ env.BUILD_VALUE }}-${{env.BUILD_VALUE}}-suffix
list: ["${{ env.BUILD_VALUE }}"]
literal: true
''')
    result = interpolate_config_values(data, {'env': process_env_var})
    assert result['quoted'] == result['unquoted'] == result['single_quoted'] == value
    assert result['embedded'] == f'prefix-{value}-{value}-suffix'
    assert result['list'] == [value]
    assert result['literal'] is True


@pytest.mark.parametrize('allow_undefined', [False, True])
@pytest.mark.parametrize('symbol', ['github.ref_name', 'vars.X', 'secrets.X'])
def test_only_env_context_is_supported(allow_undefined, symbol):
    with pytest.raises(ValueError, match='Unknown context') as error:
        interpolate_config_values({'arg': '${{ ' + symbol + ' }}'}, {
            'env': lambda name: process_env_var(name, allow_undefined),
        })
    assert symbol in str(error.value)


def test_undefined_env_fails_by_default(monkeypatch):
    monkeypatch.delenv('MISSING_BUILD_VALUE', raising=False)
    with pytest.raises(ValueError, match='MISSING_BUILD_VALUE'):
        process_env_var('MISSING_BUILD_VALUE')


@pytest.mark.parametrize('value', ['org/app', '', False, 0, '${{ env.OTHER }}', '{{ secrets.TOKEN }}'])
def test_build_images_vars_values_are_strings_not_expressions(value):
    context = {'build_images_vars': build_images_vars_resolver({'repo_name': value})}
    expression = '${{ build_images_vars.repo_name }}'
    result = interpolate_config_values({'nested': {'values': [expression]}}, context)
    assert result == {'nested': {'values': [str(value)]}}


def test_undefined_env_empty_warns(monkeypatch, capsys):
    monkeypatch.delenv('MISSING_BUILD_VALUE', raising=False)
    assert process_env_var('MISSING_BUILD_VALUE', True) == ''
    assert '::warning::Environment variable \'MISSING_BUILD_VALUE\'' in capsys.readouterr().out


@pytest.fixture
def config_file(tmp_path):
    dockerfile = tmp_path / 'Dockerfile'
    dockerfile.write_text('FROM scratch\n')
    path = tmp_path / 'build_images.yaml'
    path.write_text(f'''
snapshots:
  default:
    dockerfile: {dockerfile}
    build_args:
      SHA: "${{{{ env.GITHUB_SHA }}}}"
    registry:
      repository: "service/${{{{ env.BUILD_REPO }}}}"
    extra_tags:
      - "snapshot-${{{{ env.BUILD_VERSION }}}}"
releases:
  default:
    dockerfile: {dockerfile}
    build_args:
      SHA: '${{{{ env.GITHUB_SHA }}}}'
    registry:
      repository: "service/${{{{ env.BUILD_REPO }}}}"
    extra_tags:
      - "release-${{{{ env.BUILD_VERSION }}}}"
''')
    return path


@pytest.mark.parametrize('image_type', ['snapshots', 'releases'])
def test_config_interpolates_before_validation(monkeypatch, config_file, image_type):
    monkeypatch.setenv('GITHUB_SHA', 'a' * 40)
    monkeypatch.setenv('BUILD_REPO', 'app')
    monkeypatch.setenv('BUILD_VERSION', 'v1.2.3')
    config = Config.from_yaml(str(config_file), image_type, {}, BuildImages.SCHEMA_FILE_PATH,
                             context={'env': process_env_var})
    image = config.images['default']
    assert image.build_args == {'SHA': 'a' * 40}
    assert image.registry['repository'] == 'service/app'
    prefix = 'snapshot' if image_type == 'snapshots' else 'release'
    assert image.extra_tags == [f'{prefix}-v1.2.3']


def test_missing_env_error_names_config_file(monkeypatch, config_file):
    monkeypatch.delenv('GITHUB_SHA', raising=False)
    with pytest.raises(ValueError, match='GITHUB_SHA') as error:
        Config.from_yaml(str(config_file), 'snapshots', {}, BuildImages.SCHEMA_FILE_PATH,
                         context={'env': process_env_var})
    assert str(config_file) in str(error.value)


@pytest.mark.parametrize('allow_undefined_env', [False, True])
@pytest.mark.parametrize('name', ['repo_name', 'MISSING_INPUT'])
def test_builder_interpolates_workflow_vars(monkeypatch, config_file, allow_undefined_env, name):
    monkeypatch.setenv('GITHUB_SHA', 'a' * 40)
    monkeypatch.setenv('BUILD_REPO', 'app')
    monkeypatch.setenv('BUILD_VERSION', 'v1.2.3')
    config_file.write_text(config_file.read_text().replace(
        '${{ env.GITHUB_SHA }}', '${{ env.GITHUB_SHA }} + ${{ build_images_vars.' + name + ' }}',
    ))
    kwargs = {
        'vars': {'from': 'aaaaaaa', 'repo_name': 'org/app',
                 'snapshots_registry': 'registry.test', 'releases_registry': 'registry.test',
                 'allow_undefined_env': allow_undefined_env, 'dereference_enabled': 'false'},
        'secrets': {}, 'additional_build_args': {}, 'config_file': str(config_file),
    }
    if name == 'MISSING_INPUT':
        with pytest.raises(ValueError, match="Undefined build_images variable 'MISSING_INPUT'") as error:
            BuildImages(**kwargs)
        assert str(config_file) in str(error.value)
    else:
        builder = BuildImages(**kwargs)
        assert builder.config.images['default'].build_args['SHA'] == 'a' * 40 + ' + org/app'


@pytest.mark.parametrize('env_value', [
    '{{ secrets.TOKEN }}', '{{ secrets.UNKNOWN }}', 'prefix-{{ secrets.TOKEN }}',
])
@pytest.mark.parametrize('expression', ['${{ env.BUILD_VERSION }}', 'prefix-${{ env.BUILD_VERSION }}'])
def test_env_produced_secret_placeholders_stay_literal(monkeypatch, tmp_path, env_value, expression):
    dockerfile = tmp_path / 'Dockerfile'
    dockerfile.write_text('FROM scratch\n')
    path = tmp_path / 'build_images.yaml'
    YAML().dump({'snapshots': {'default': {
        'dockerfile': str(dockerfile), 'build_args': {'VERSION': expression},
        'secrets': {'BUILD_SECRET': expression},
    }}}, path)
    monkeypatch.setenv('BUILD_VERSION', env_value)

    config = Config.from_yaml(str(path), 'snapshots', {'TOKEN': 'sensitive-value'},
                             BuildImages.SCHEMA_FILE_PATH, context={'env': process_env_var})
    expected = expression.replace('${{ env.BUILD_VERSION }}', env_value)
    assert config.images['default'].build_args['VERSION'] == expected
    assert config.images['default'].secrets['BUILD_SECRET'] == expected


@pytest.mark.parametrize('secret_value', ['token-value', '${{ env.OTHER }}', '{{ secrets.UNKNOWN }}'])
def test_original_secret_placeholders_resolve_without_reinterpreting_results(tmp_path, secret_value):
    dockerfile = tmp_path / 'Dockerfile'
    dockerfile.write_text('FROM scratch\n')
    path = tmp_path / 'build_images.yaml'
    YAML().dump({'snapshots': {'default': {
        'dockerfile': str(dockerfile),
        'build_args': {'TOKEN': '{{ secrets.TOKEN }}'},
        'secrets': {'TOKEN': '{{ secrets.TOKEN }}'},
        'registry': {'repository': '{{ secrets.TOKEN }}'},
    }}}, path)

    config = Config.from_yaml(str(path), 'snapshots', {'TOKEN': secret_value},
                             BuildImages.SCHEMA_FILE_PATH, context={'env': process_env_var})
    image = config.images['default']
    assert image.build_args['TOKEN'] == secret_value
    assert image.secrets['TOKEN'] == secret_value
    assert image.registry['repository'] == secret_value


@pytest.mark.parametrize('context', [None, {'env': process_env_var}])
def test_yaml_aliases_do_not_reinterpret_secret_results(tmp_path, context):
    dockerfile = tmp_path / 'Dockerfile'
    dockerfile.write_text('FROM scratch\n')
    path = tmp_path / 'build_images.yaml'
    shared_values = {'TOKEN': '{{ secrets.TOKEN }}'}
    YAML().dump({'snapshots': {'default': {
        'dockerfile': str(dockerfile), 'build_args': shared_values, 'secrets': shared_values,
    }}}, path)

    config = Config.from_yaml(str(path), 'snapshots', {'TOKEN': '{{ secrets.UNKNOWN }}'},
                             BuildImages.SCHEMA_FILE_PATH, context=context)
    assert config.images['default'].build_args == {'TOKEN': '{{ secrets.UNKNOWN }}'}
    assert config.images['default'].secrets == {'TOKEN': '{{ secrets.UNKNOWN }}'}


def test_legacy_secret_resolution_preserves_selected_type_and_dictionary_scope(tmp_path):
    dockerfile = tmp_path / 'Dockerfile'
    dockerfile.write_text('FROM scratch\n')
    path = tmp_path / 'build_images.yaml'
    YAML().dump({
        'snapshots': {'default': {
            'dockerfile': str(dockerfile),
            'build_args': {
                'NESTED': {'TOKEN': '{{ secrets.TOKEN }}'},
                'LIST': ['{{ secrets.UNKNOWN }}', {'TOKEN': '{{ secrets.UNKNOWN }}'}],
                'EMBEDDED': 'prefix-{{ secrets.UNKNOWN }}',
            },
            'extra_registries': [{
                'name': 'registry.test', 'repository': '{{ secrets.UNKNOWN }}',
                'auth_strategy': 'azure_oidc',
            }],
        }},
        'releases': {'default': {
            'dockerfile': str(dockerfile), 'build_args': {'TOKEN': '{{ secrets.UNKNOWN }}'},
        }},
    }, path)

    config = Config.from_yaml(str(path), 'snapshots', {'TOKEN': 'token-value'},
                             BuildImages.SCHEMA_FILE_PATH)
    image = config.images['default']
    assert image.build_args['NESTED'] == {'TOKEN': 'token-value'}
    assert image.build_args['LIST'] == ['{{ secrets.UNKNOWN }}', {'TOKEN': '{{ secrets.UNKNOWN }}'}]
    assert image.build_args['EMBEDDED'] == 'prefix-{{ secrets.UNKNOWN }}'
    assert image.extra_registries[0]['repository'] == '{{ secrets.UNKNOWN }}'


def test_original_missing_secret_still_fails(tmp_path):
    dockerfile = tmp_path / 'Dockerfile'
    dockerfile.write_text('FROM scratch\n')
    path = tmp_path / 'build_images.yaml'
    YAML().dump({'snapshots': {'default': {
        'dockerfile': str(dockerfile), 'build_args': {'TOKEN': '{{ secrets.UNKNOWN }}'},
    }}}, path)

    with pytest.raises(KeyError, match='UNKNOWN'):
        Config.from_yaml(str(path), 'snapshots', {}, BuildImages.SCHEMA_FILE_PATH,
                         context={'env': process_env_var})


def test_builder_allows_undefined_env(monkeypatch, config_file, capsys):
    monkeypatch.delenv('GITHUB_SHA', raising=False)
    monkeypatch.setenv('BUILD_REPO', 'app')
    monkeypatch.setenv('BUILD_VERSION', 'v1.2.3')
    builder = BuildImages(
        vars={'from': 'aaaaaaa', 'repo_name': 'org/app',
              'snapshots_registry': 'registry.test', 'releases_registry': 'registry.test',
              'allow_undefined_env': True},
        secrets={}, additional_build_args={}, config_file=str(config_file),
    )
    assert builder.config.images['default'].build_args == {'SHA': ''}
    output = capsys.readouterr().out
    assert '::warning::' in output
    assert 'GITHUB_SHA' in output


@pytest.mark.parametrize('extra_vars', [{}, {'allow_undefined_env': False}])
def test_builder_rejects_undefined_env_by_default(monkeypatch, config_file, extra_vars):
    monkeypatch.delenv('GITHUB_SHA', raising=False)
    with pytest.raises(ValueError, match='GITHUB_SHA'):
        BuildImages(
            vars={'from': 'aaaaaaa', 'repo_name': 'org/app',
                  'snapshots_registry': 'registry.test', 'releases_registry': 'registry.test',
                  **extra_vars},
            secrets={}, additional_build_args={}, config_file=str(config_file),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize('sha_value', ['b' * 40, '{{ secrets.TOKEN }}', '{{ secrets.UNKNOWN }}'])
@pytest.mark.parametrize('image_type,build_from', [
    ('snapshots', 'a' * 40), ('snapshots', 'v1.2.3-rc.1'), ('releases', 'v1.2.3'),
])
async def test_interpolated_args_reach_build_and_results(monkeypatch, mocker, config_file,
                                                       tmp_path, image_type, build_from, sha_value):
    monkeypatch.setenv('GITHUB_SHA', sha_value)
    monkeypatch.setenv('BUILD_REPO', 'app')
    monkeypatch.setenv('BUILD_VERSION', 'v1.2.3')
    results_file = tmp_path / 'results.yaml'
    builder = BuildImages(
        vars={'from': build_from, 'type': image_type, 'dereference_enabled': 'false',
              'repo_name': 'org/app', 'snapshots_registry': 'registry.test',
              'releases_registry': 'registry.test', 'snapshots_registry_creds': '',
              'releases_registry_creds': '', 'output_results': str(results_file)},
        secrets={'TOKEN': 'sensitive-value'}, additional_build_args={'SHA': 'global-value', 'GLOBAL': 'global'},
        config_file=str(config_file),
    )
    builder.filter_flavors()
    connection = mocker.patch('dagger.Connection')
    connection.return_value.__aenter__.return_value = mocker.MagicMock()
    compile_image = mocker.patch.object(builder, 'compile_image_and_publish')
    results = await builder.compile_images_for_all_flavors()
    args = compile_image.call_args.args[1]
    assert [(arg.name, arg.value) for arg in args] == [
        ('SHA', 'global-value'), ('GLOBAL', 'global'), ('SHA', sha_value),
    ]
    assert results[0]['build_args'] == {'SHA': sha_value}
    assert results[0]['image_tag'] == f'{build_from}_default'
    assert YAML(typ='safe').load(results_file)[0]['build_args'] == {'SHA': sha_value}
