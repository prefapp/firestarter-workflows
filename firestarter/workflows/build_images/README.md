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

Only `env.*` and `vars_input.*` contexts are supported. 

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

##### vars_input

Use `{{ vars_input.NAME }}` to reference parsed values passed through the
action's `with.vars` input. 

This is distinct from GitHub's `vars` context: GitHub
evaluates action inputs first, and this context reads the resulting workflow inputs.

```yaml
build_args:
  REPOSITORY: "{{ vars_input.repo_name }}"
```

Variable names are case-sensitive: `repo_name`, `REPO_NAME`, and `Repo_Name`
are **distinct inputs** and must be referenced with their exact spelling.

Missing variables fail with their name and config path, according to the `allow_undefined` input. 
Empty strings, boolean, and numbers are defined values.
Only explicitly supplied inputs are exposed, not workflow defaults or derived
properties; `vars_input.from` is the original input, not a de-referenced SHA.

> [!NOTE]
> - Variable lookup is **case-sensitive**
> - The same string-only substitution rules as `env` apply to nested values and list elements
> - Values are not recursively evaluated, secret-like placeholders remain literal, and mapping keys are not interpolated. 
> - Substitution does not turn a comma-separated platform string into a list or a boolean string into a YAML boolean.

Workflow inputs can contain credentials. This context does not add masking or
secret protection: use credential-bearing inputs only in credential fields, never
in build arguments, tags, or published results.

### Required and optional input vars

Beyond the configuration file which is mandatory, there are some other extra arguments that must be set.
* `repo_name`: The image_name to be used.
* `flavors`: 
* `platforms`:
* `auth_strategy`:
* snapshots_registry
* releases_registry
* output_results
* type: 
* `from` : The commit SHA, tag or branch used to create the image, from the user's repository. This point will define the image tag.
* `on_premises`: List of flavors to build (separated by commas). An `*` is accepted to build and publish all of them.
* workflow_run_id
* workflow_run_url
* login_required
* service_path=
* snapshots_registry_creds
* releases_registry_creds
Additionally there are some optional inputs:

* `allow_undefined`: boolean, default `false`. When `true`, undefined `{{ <context>.X }}` values become empty strings with a warning instead of failing.
* `dereference_enabled`: whether the `from` value is de-referenced into a short SHA before building (defaults to `true`). It is only applied for `snapshots` builds; for other types the raw `from` value is always used as-is.
* `container_structure_filename`: path of the [container-structure-test](https://github.com/GoogleContainerTools/container-structure-test) filename (if not set, no tests are checked)
* `publish`: publish the docker image to the registry, by default `true`.  ⚠️ If set to `false` image will be not published to the registry.

## Secrets

Secrets can be used the same way that recommends [docker documentation](https://docs.docker.com/build/ci/github-actions/secrets/).

Secrets can be defined in multiples places:
- In the `secrets` input. Available to all flavors.
- In the config file, in the `secrets` key of the flavor where is needed.

In both places the secrets can be:
- An string
- A AWS parameter store reference: arn:aws:ssm:xxxxx:yyyy:zzzz:parameter/my-secret"
- A Azure Keyvault reference: https://[a-zA-Z0-9\-]{3,24}.vault.azure.net/secrets/my-secret/

Additionally, in the `secrets` input, the GitHub `${{ secrets.xxx}}` context is available 

To do so add a secret variables similarly as you would do with any other firestarter-workflows packages. In your Dockerfile you must mount the secret following the `secrets` specification:

```Dockerfile
RUN --mount=type=secret,id=github_token,dst=/run/secrets/github_token \
    echo "The secret token is: $(cat /run/secrets/github_token)"
```

> Remember to make sure the secret key name and secret id are the same


## Additional build args

In addition to those found in the configuration file, additional build args may be set using the command line argument `--additional-build-args` or via the `INPUT_ADDITIONAL_BUILD_ARGS` environment variable. These values can then be used in the Dockerfile, for example:

```Dockerfile
ARG YOUR_BUILD_ARG
ENV YOUR_BUILD_ARG=$YOUR_BUILD_ARG

RUN echo "The additional build arg is: $YOUR_BUILD_ARG"
```

> [!WARNING]
> Secrets and build args set in the configuration file will overwrite those set via `additional-build-args`.

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
        on_premises:
          type: string
          description: 'On-premises name/s | one (alone), several(separated by commas) or all (*)'
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
              from_point="${{ github.event.inputs.from }}"
              on_premises="${{ github.event.inputs.on_premises }}"
              container_structure_filename=".dagger/struct.yaml"
              dereference_enabled="true"
              login_required=false

            secrets: |
              github_token="${{ github.token }}"
  ```
  > Note that in the example the checkout action runs twice, one to clone the repo in the `from_point`, and another to geht the configuration file from the HEAD.
4. Create a configuration file (e.g. `.github/build_images.yaml`)
5. Manually launch de workflow
