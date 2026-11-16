# Build images

Dagger workflow in a Python package, to be executed locally or from GitHub actions using the with [run-dagger-py](https://github.com/prefapp/run-dagger-py) action. It allows users to build and publish Docker images from a project, based on the definitions configured in the `.github/build_images.yaml` configuration file.

## Configuration file

Located by default at `.github/build_images.yaml`.

The configuration file needed by this package has the following structure.
```yaml
snapshots:
  example:
    registry:
      name: ttl.sh # Specify where to publish images
      repository: foo/bar # Used to generate the docker image name
    build_args: # List of build args used in the dockerfile
      REACT_APP_API_URL: prod.local
    dockerfile: './Dockerfile' # Path to the dockerfile used in the build process
    secrets:
      MY_AWS_SECRET: arn:aws:ssm:xxxx:123456767:parameter/my/secret
      MY_AZUREKV_SECRET: https://myvault.vault.azure.net/secrets/my-azure-secret/
```

## Variable interpolation
String values in `build_images.yaml` support interpolation in the form `{{ <context>.XXX }}`.

Only `env.*`, `build_images_vars.*`, and `build_images_secrets.*` contexts are supported.
`build_images_secrets.*` is restricted to direct values in a flavor's `secrets` mapping.

Take into account: 
- Action var input `allow_undefined` defaults to `false`: missing variables fail with their name and config path. Set it to the TOML boolean `true` (unquoted) to replace missing variables with an empty string and a warning annotation.
- Existing empty variables are valid.
- Config file schema validation applies after substitution.

> [!IMPORTANT]
> Those contexts refer to the **action's inputs**, and environment variables
> Contexts like `github.*`, `vars.*` `secrets.*` fail to be interpolated

### Available contexts
##### env
The variable interpolation supports environment variables defined in the environment of the process running this workflow, using the form: `{{ env.MY_VAR }}`

This works for quoted or unquoted values and embedded expressions such as `build-{{ env.GITHUB_RUN_ID }}`. 

> [!NOTE]
> - Substitution happens after YAML parsing and before schema validation, so values cannot inject
> - YAML syntax and are not recursively evaluated. 
> - Mapping keys are not interpolated.
> - Env-produced strings such as `{{ secrets.TOKEN }}` remain literal
> - Environment variable lookup is **case-sensitive**: names must match exactly.

> [!IMPORTANT]
> - Build arguments must have matching Dockerfile `ARG` declarations.
> - Never interpolate sensitive env values into build arguments: they may be stored in **image metadata** and results artifacts.
> - Use build secrets and Dockerfile secret mounts instead.

##### build_images_vars

Use `{{ build_images_vars.NAME }}` to reference parsed values passed through the
action's `with.vars` input. 

This is distinct from GitHub's `vars` context: GitHub
evaluates action inputs first, and this context reads the resulting workflow inputs.

```yaml
build_args:
  REPOSITORY: "{{ build_images_vars.repo_name }}"
```

Variable names are case-sensitive: `repo_name`, `REPO_NAME`, and `Repo_Name`
are **distinct inputs** and must be referenced with their exact spelling.

Missing variables fail with their name and config path, according to the `allow_undefined` input. 
Empty strings, boolean, and numbers are defined values.
Only explicitly supplied inputs are exposed, not workflow defaults or derived
properties; `build_images_vars.from` is the original input, not a de-referenced SHA.

> [!NOTE]
> - Variable lookup is **case-sensitive**
> - The same string-only substitution rules as `env` apply to nested values and list elements
> - Values are not recursively evaluated, secret-like placeholders remain literal, and mapping keys are not interpolated. 
> - Substitution does not turn a comma-separated platform string into a list or a boolean string into a YAML boolean.

Workflow inputs can contain credentials. This context does not add masking or
secret protection: use credential-bearing inputs only in credential fields, never
in build arguments, tags, or published results.

##### build_images_secrets

Use `{{ build_images_secrets.NAME }}` to reference the action's parsed `secrets`
input. Names are case-sensitive. This context is only permitted in direct values
at `snapshots.<flavor>.secrets.<name>` or `releases.<flavor>.secrets.<name>`:

```yaml
snapshots:
  example:
    dockerfile: Dockerfile
    build_args:
      CUSTOM_VAR: "{{ build_images_vars.CUSTOM_VAR }}"
    secrets:
      TOKEN: "{{ build_images_secrets.PAT }}"
      DB_PASSWORD: "{{ build_images_secrets.TEST_AWS }}"
```

Using this context in build args, tags, registry fields, or nested secret
structures fails before building, even when `allow_undefined=true`.
Missing names in allowed locations follow the usual `allow_undefined` behavior.
Values are not recursively interpolated, and mapping keys are not interpolated.

The context exposes the original input: GitHub expressions have already been
evaluated, but AWS SSM ARNs and Azure Key Vault URLs remain references until the
flavor is built. Only that flavor's secrets are resolved and mounted; unreferenced
input secrets are not fetched or mounted. Secret values are not included in the
results artifact. Dockerfiles must still avoid printing or copying mounted
secrets into the image. Secrets supplied through `env` or `build_images_vars`
are not protected by this context restriction.

## Input vars

Input vars are passed through the action's `vars` input (TOML `key=value` lines). Besides the configuration file, the following vars are supported.

### Required

The workflow fails with `Missing required variable: <name>` if any of these is missing or empty.

| Var | Description |
|-----|-------------|
| `from` | Commit SHA, tag or branch of the user's repository to build. It is checked out before building and is used as the image tag prefix (`<from>_<flavor>`). See `dereference_enabled`. |
| `repo_name` | Image repository name. Used as the image repository unless the flavor sets `registry.repository` (prefixed with `service_path` when set). |
| `snapshots_registry` | Default registry for `snapshots` builds (unless the flavor sets `registry.name`). |
| `releases_registry` | Default registry for `releases` builds (unless the flavor sets `registry.name`). |

### Optional

| Var | Default | Description |
|-----|---------|-------------|
| `type` | `snapshots` | Build type: `snapshots` or `releases`. Selects the top-level section of the config file, the default registry and its credentials. |
| `flavors` | `default` | Comma-separated list of flavors to build. Supports glob patterns (e.g. `dev-*`) and `*` for all flavors. If empty, only flavors with `auto: true` are built. |
| `platforms` | `*` | Comma-separated platform filter, intersected with each flavor's `platforms`. Valid values: `linux/amd64`, `linux/arm64`, `amd64`, `arm64`, or `*` (all platforms configured for the flavor). Flavors with no matching platform are skipped with a warning. |
| `dereference_enabled` | `true` | When `true` and `type` is `snapshots`, `from` is resolved to a 7-char short SHA (from a SHA, tag or `origin/<branch>`). For `releases` (or when `false`) `from` is used as-is. |
| `auth_strategy` | — | Default registry login strategy: `aws_oidc`, `azure_oidc`, `generic`, `ghcr` or `dockerhub`. Can be overridden per flavor with `registry.auth_strategy`. |
| `snapshots_registry_creds` | — | Credentials for `snapshots_registry`; also the default creds for flavor registries and `extra_registries` in `snapshots` builds. Must be present when `type` is `snapshots`. |
| `releases_registry_creds` | — | Same as above for `releases` builds. |
| `login_required` | `true` | Log in to `snapshots_registry` and `releases_registry` before building. Set to `false` (boolean or string, case-insensitive) to skip it. Flavor-specific registries and `extra_registries` are always logged in. |
| `service_path` | `""` | Prefix added to `repo_name` (`<service_path>/<repo_name>`) when the flavor does not set `registry.repository`. |
| `container_structure_filename` | — | Path to a [container-structure-test](https://github.com/GoogleContainerTools/container-structure-test) config. If not set, no tests are run. |
| `publish` | `true` | Publish images to the registries. ⚠️ Set to `false` (boolean or string, case-insensitive) to skip publishing. |
| `output_results` | `results.yaml` | File name (written under `/tmp`) where the list of built images is stored. |
| `workflow_run_id` | — | Included as-is in the results file. |
| `workflow_run_url` | — | Included as-is in the results file. |
| `allow_undefined` | `false` | Must be a TOML boolean (unquoted), otherwise the workflow fails. When `true`, undefined `{{ <context>.X }}` values become empty strings with a warning instead of failing. |

All input vars (as originally supplied, before defaults or de-referencing) are also available for interpolation via `{{ build_images_vars.NAME }}`.

## Secrets

Secrets can be used the same way that recommends [docker documentation](https://docs.docker.com/build/ci/github-actions/secrets/).

Secrets can be defined in multiples places:
- In the `secrets` input. Each flavor must explicitly reference the values it needs
  using `{{ build_images_secrets.NAME }}` in its `secrets` mapping.
- In the config file, in the `secrets` key of the flavor where is needed.

In both places the secrets can be:
- An string
- A AWS parameter store reference: arn:aws:ssm:xxxxx:yyyy:zzzz:parameter/my-secret"
- A Azure Keyvault reference: https://[a-zA-Z0-9\-]{3,24}.vault.azure.net/secrets/my-secret/

Additionally, in the `secrets` input, the GitHub `${{ secrets.xxx}}` context is available 

To do so add a secret variables similarly as you would do with any other firestarter-workflows packages. In your Dockerfile you must mount the secret following the `secrets` specification:

```Dockerfile
RUN --mount=type=secret,id=github_token,dst=/run/secrets/github_token \
    command-that-reads-token /run/secrets/github_token
```

> Remember to make sure the secret key name and secret id are the same


## Migration

- The `additional_build_args` input and CLI argument are removed, and
  `INPUT_ADDITIONAL_BUILD_ARGS` is no longer read. Move custom values into `vars`
  and explicitly reference them in each flavor's `build_args`.
- Input secrets are no longer mounted into every flavor. Add explicit
  `{{ build_images_secrets.NAME }}` references to each flavor's `secrets` mapping.

## Example

1. Create a repository that uses run-dagger-py (check [docs](https://github.com/prefapp/run-dagger-py/blob/main/docs/index.md) for more details).
2. Add a github workflow that uses this particular pacakge, see example below.
  ```yaml
  name: Build image
  on:
    workflow_dispatch:
      inputs:
        from:
          type: string
          description: 'Origin commit or tag'
          required: true
          default: ''
        flavors:
          type: string
          description: 'Flavor/s to build | one (alone), several (separated by commas) or all (*)'
          required: true
          default: '*' # all
  jobs:
    build-images:
      runs-on: ubuntu-22.04
      steps:
        - name: Checkout repository
          uses: actions/checkout@v3
          with:
            ref: ${{ github.event.inputs.from }}
            path: build

        - name: Checkout repository to get config file
          uses: actions/checkout@v3
          with:
            path: config

        - name: Call run-dagger-py action
          uses: prefapp/run-dagger-py@main
          with:
            working_directory: build
            pyproject_path: .dagger
            workflow: build_images
            config_file: ../config/.github/build_images.yaml
            vars: |
              repo_name="${{ github.repository }}"
              from="${{ github.event.inputs.from }}"
              flavors="${{ github.event.inputs.flavors }}"
              type="snapshots"
              snapshots_registry="ghcr.io"
              releases_registry="ghcr.io"
              auth_strategy="ghcr"
              snapshots_registry_creds=""
              releases_registry_creds=""
              container_structure_filename=".dagger/struct.yaml"
              dereference_enabled="true"
              login_required=false

            secrets: |
              github_token="${{ github.token }}"
  ```
  > Note that in the example the checkout action runs twice, one to clone the repo at `from`, and another to get the configuration file from the HEAD.
4. Create a configuration file (e.g. `.github/build_images.yaml`)
   Reference the example's input token explicitly:
   ```yaml
   snapshots:
     default:
       dockerfile: Dockerfile
       secrets:
         github_token: "{{ build_images_secrets.github_token }}"
   ```
5. Manually launch de workflow
