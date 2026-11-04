import pytest
from ruamel.yaml import YAML

from firestarter.common.preprocessor import PreProcessor
from firestarter.common.validations import process_env_var
from firestarter.workflows.build_images.build_images import BuildImages
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
    result = PreProcessor(data).preprocess({'env': process_env_var})
    assert result['quoted'] == result['unquoted'] == result['single_quoted'] == value
    assert result['embedded'] == f'prefix-{value}-{value}-suffix'
    assert result['list'] == [value]
    assert result['literal'] is True


@pytest.mark.parametrize('allow_undefined', [False, True])
@pytest.mark.parametrize('symbol', ['github.ref_name', 'vars.X', 'secrets.X'])
def test_only_env_context_is_supported(allow_undefined, symbol):
    with pytest.raises(ValueError, match='Unknown context') as error:
        PreProcessor({'arg': '${{ ' + symbol + ' }}'}).preprocess({
            'env': lambda name: process_env_var(name, allow_undefined),
        })
    assert symbol in str(error.value)


def test_undefined_env_fails_by_default(monkeypatch):
    monkeypatch.delenv('MISSING_BUILD_VALUE', raising=False)
    with pytest.raises(ValueError, match='MISSING_BUILD_VALUE'):
        process_env_var('MISSING_BUILD_VALUE')


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
@pytest.mark.parametrize('image_type,build_from', [
    ('snapshots', 'a' * 40), ('snapshots', 'v1.2.3-rc.1'), ('releases', 'v1.2.3'),
])
async def test_interpolated_args_reach_build_and_results(monkeypatch, mocker, config_file,
                                                       tmp_path, image_type, build_from):
    monkeypatch.setenv('GITHUB_SHA', 'b' * 40)
    monkeypatch.setenv('BUILD_REPO', 'app')
    monkeypatch.setenv('BUILD_VERSION', 'v1.2.3')
    results_file = tmp_path / 'results.yaml'
    builder = BuildImages(
        vars={'from': build_from, 'type': image_type, 'dereference_enabled': 'false',
              'repo_name': 'org/app', 'snapshots_registry': 'registry.test',
              'releases_registry': 'registry.test', 'snapshots_registry_creds': '',
              'releases_registry_creds': '', 'output_results': str(results_file)},
        secrets={}, additional_build_args={'SHA': 'global-value', 'GLOBAL': 'global'},
        config_file=str(config_file),
    )
    builder.filter_flavors()
    mocker.patch('dagger.Connection')
    compile_image = mocker.patch.object(builder, 'compile_image_and_publish')
    results = await builder.compile_images_for_all_flavors()
    args = compile_image.call_args.args[1]
    assert [(arg.name, arg.value) for arg in args] == [
        ('SHA', 'global-value'), ('GLOBAL', 'global'), ('SHA', 'b' * 40),
    ]
    assert results[0]['build_args'] == {'SHA': 'b' * 40}
    assert results[0]['image_tag'] == f'{build_from}_default'
    assert YAML(typ='safe').load(results_file)[0]['build_args'] == {'SHA': 'b' * 40}
