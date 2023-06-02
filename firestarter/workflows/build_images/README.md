# Build images

Python package for [run-dagger-py](https://github.com/prefapp/run-dagger-py) that allows users to build multiple docker images using dagger based on a configuration file.

## Configuration file

The configuration file needed by this package needs the following structure.
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

* repo_name: Used to label the container
* from_point: Used to tag and label the container
* on_premises: List of premises to build (separated by commas)

Additionally there are some variables:

* container_structure_filename: path of the docker [container-structure-test](https://github.com/GoogleContainerTools/container-structure-test) filename (if not set no tests are checked)
    
    > Highly recommended! ⚠️
* publish: publish the docker image to the registry


## Secrets

Secrets can be used the same way is recommended in [docker documentation](https://docs.docker.com/build/ci/github-actions/secrets/).

To do so add secret variables similarly as you would do with any other [run-dagger-py] module. Then mount the secret using buildkit secrets feature:

```Dockerfile
RUN --mount=type=secret,id=github_token,dst=/run/secrets/github_token \
    echo "The secret token is: $(cat /run/secrets/github_token)"
```

> Remember to make sure the secret key name and secret id are the same

## Example

1. Create a repository that uses run-dagger-py (check [docs](https://github.com/prefapp/run-dagger-py/blob/main/docs/index.md) for more details).
2. Add a github workflow that uses this particular module, see example below.
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
              login_required=false

            secrets: |
              github_token="${{ github.token }}"
  ```
  > Note that in the example it checkouts twice the repo to use the configuration file updated with HEAD.
4. Create a configuration file (e.g. `.dagger/firestarter_build_images.yaml`)

