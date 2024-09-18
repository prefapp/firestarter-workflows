# State Repo Analyze Changes

## Description

This workflow is used to analyze what changes are present based on the following structure of folders:

```md
apps
└── tenant
    └── app-name
        └── environment
            ├── deployment.yaml
            └── configmap.yaml
sys-services
└── sys-service-name
    └── cluster-name
```

The output of this workflow is a JSON object with the structure below:

* Apps

```json
{
    "<ENVIRONMENT>": {
        "environment": "<ENVIRONMENT>",
        "updated_apps": ["apps/<TENANT>/<APP_NAME>"]
    }
}
```

* Sys Services

```json
{
    "<CLUSTER_NAME>": {
        "cluster_name": "<CLUSTER_NAME>",
        "updated_sys_services": ["sys_services/<SYS_SERVICE_NAME>"]
    }
}
```
