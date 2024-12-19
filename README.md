# Azure Alert Parser

This project parses Azure Monitor alerts and sends them to an external service (in my case Pushover) for notifications. This repo can be used as a boilerplate for other alerting services, ie ITSM systems.

## Deployment
`iac` contains the terraform code to deploy the function app to Azure. terraform will provide a ZIP file of the `src` directory to the function app, that then runs a remote build to install the required packages.

Post deployment you will need to update the value of the following secrets:
- `pushover-api-token`
- `pushover-user-key`

## Development

The various types of alert payloads are stored in `src/tests/payloads` these align with the "Test Action Group" option in the Azure Portal. pytest will trigger an end to end test for each of these payloads when run.


## References
- [Common alert schema](https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/alerts-common-schema)