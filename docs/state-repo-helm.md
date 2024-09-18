# State Repo Helm

## Description

This workflow is used to:

1. Check pull request for changes in the deployments and write the changes in a comment.
2. Deploy the changes to the cluster

## Configuration

There are two workflows that are used to deploy the state repository.

1. **state-repo-helm-apps** - This workflow is used to app services.
2. **state-repo-helm-sys-services** - This workflow is used to deploy system services.

Each of these workflows require a specific configuration file to be present in the repository under the `.github` directory.

1. **apps-config.yaml**.
2. **sys-services-config.yaml**.

Both of these files follow the same structure, some fields vary depending on the cloud provider.

### Azure

```yaml
provider:
  kind: azure
  tenant_id: ca5a6690-2f48-4776-91dd-8fde1d02e7e8
  subscription_id: c8e19171-5128-483c-8a35-e8deabb4f519
helm_registries:
  - cbxacr.azurecr.io
  - acrnoreleases.azurecr.io
  - acrreleases.azurecr.io
environments:
  dev:
    cluster_name: tgss-predev-aks
    resource_group_name: tgss-common-predev
    identifier: bdc3cb69-f169-44fe-8dc2-cfb1e8ee44c9
  pre:
    cluster_name: tgss-predev-aks
    resource_group_name: tgss-common-predev
    identifier: bdc3cb69-f169-44fe-8dc2-cfb1e8ee44c9
  pro:
    cluster_name: tgss-pro-aks
    resource_group_name: tgss-common-pro
    identifier: bdc3cb69-f169-44fe-8dc2-cfb1e8ee44c9
  
```

### AWS

```yaml
provider:
  kind: aws
  role-to-assume: <ROLE_TO_ASSUME_ARN>
  region: us-west-2
helm_registries:
  - <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com
environments:
    dev:
        cluster_name: tgss-dev-eks
        identifier: <IDENTIFIER>
```
