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

Beyond the configuration file which is mandatory, there are some other extra variables that must be set.

* `repo_name`: The image_name to be used.
* `from_point` : The commit SHA, tag or branch used to create the image, from the user's repository. This point will define the image tag.
* `on_premises`: List of flavours to build (separated by commas). An `*` is accepted to build and publish all of them.

Additionally there are some optional variables:

* `dereference_enabled`: whether the `from` value is dereferenced into a short sha before building (defaults to `true`). Set it to `false` to use the raw `from` value as-is.
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

