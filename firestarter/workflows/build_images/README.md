# Build images

Dagger workflow in a Python package, to be executed locally or from Github actions, with [run-dagger-py](https://github.com/prefapp/run-dagger-py). Allows users to build and publish multiple docker images, based on a configuration file.

## Configuration file

The configuration file needed by this package has the following structure.
```
images:
  example:
    registry: ttl.sh # Specify where to publish images
    repository: foo/bar # Used to generate the docker image name
    build_args: # List of build args used in the dockerfile
      REACT_APP_API_URL: prod.local
    dockerfile: './Dockerfile'# Path to the dockerfile used in the build process
```

## Variables

### Environment interpolation

String values in `build_images.yaml` support `${{ env.X }}` using the environment
of the process running this workflow. This works for quoted or unquoted values
and embedded expressions such as `build-${{ env.GITHUB_RUN_ID }}`. Substitution
happens after YAML parsing and before schema validation, so values cannot inject
YAML syntax and are not recursively evaluated. Mapping keys are not interpolated.
Env-produced strings such as `{{ secrets.TOKEN }}` remain literal; legacy secret
placeholders are resolved only when authored in the original YAML. Resolved
secret values are not evaluated as env expressions or other secret placeholders.
Expressions in all flavors and types are processed, even if not selected to build.

Only `env.*` is supported: `github.*`, `vars.*`, and `secrets.*` fail with a clear
error. This changes configurations which previously passed expressions literally;
migrate `${{ github.ref_name }}` to `${{ env.GITHUB_REF_NAME }}`. GitHub's default
environment variables describe the triggering event, not necessarily the `from`
ref checked out for the build (for example, a PR's `GITHUB_SHA` is its merge SHA).

Workflow var `allow_undefined_env` defaults to `false`: missing variables fail
with their name and config path. Set it to the TOML boolean `true` (unquoted) to
replace missing variables with an empty string and a GitHub warning annotation.
Existing empty variables are valid.
Schema validation still applies after substitution.

Build arguments must have matching Dockerfile `ARG` declarations. Flavor arguments
override `additional_build_args`. Never interpolate sensitive env values into
build arguments: they may be stored in image metadata and results artifacts.
Use build secrets and Dockerfile secret mounts instead.

### Required and optional variables

Beyond the configuration file which is mandatory, there are some other extra variables that must be set.

* `repo_name`: The image_name to be used.
* `from_point` : The commit SHA, tag or branch used to create the image, from the user's repository. This point will define the image tag.
* `on_premises`: List of flavours to build (separated by commas). An `*` is accepted to build and publish all of them.

Additionally there are some optional variables:

* `allow_undefined_env`: boolean, default `false`. When `true`, undefined `${{ env.X }}` values become empty strings with a warning instead of failing.

* `dereference_enabled`: whether the `from` value is dereferenced into a short sha before building (defaults to `true`). It is only applied for `snapshots` builds; for other types the raw `from` value is always used as-is.
* `container_structure_filename`: path of the [container-structure-test](https://github.com/GoogleContainerTools/container-structure-test) filename (if not set, no tests are checked)

    > Highly recommended! ⚠️
* `publish`: publish the docker image to the registry


## Secrets

Secrets can be used the same way that recommends [docker documentation](https://docs.docker.com/build/ci/github-actions/secrets/).

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
> Secrets and build args set in the configuration file will overwrite those set via the command line or environment variables.

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
            config_file: ../config/.dagger/firestarter_build_images.yaml
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
4. Create a configuration file (e.g. `.dagger/firestarter_build_images.yaml`)
5. Manually launch de workflow
