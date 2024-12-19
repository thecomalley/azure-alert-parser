data "azurerm_client_config" "current" {}

module "regions" {
  source  = "claranet/regions/azurerm"
  version = "7.2.1"

  azure_region = var.location
}

resource "azurerm_resource_group" "main" {
  name     = "${var.workload}-${var.environment}-${module.regions.location_short}-rg"
  location = var.location
  tags = var.tags
}

resource "azurerm_storage_account" "main" {
  name                     = "${replace(var.workload, "-", "")}${var.environment}${module.regions.location_short}st"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = var.location
  account_kind             = "Storage"
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags = var.tags
}

resource "azurerm_application_insights" "main" {
  name                = "${var.workload}-${var.environment}-${module.regions.location_short}-appi"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  application_type    = "other"
  tags = var.tags
}

resource "azurerm_service_plan" "main" {
  name                = "${var.workload}-${var.environment}-${module.regions.location_short}-asp"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "Y1"
  tags = var.tags
}

resource "azurerm_key_vault" "main" {
  name                        = "${var.workload}-${var.environment}-${module.regions.location_short}-kv"
  location                    = azurerm_resource_group.main.location
  resource_group_name         = azurerm_resource_group.main.name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false

  sku_name = "standard"
  tags = var.tags
}

resource "azurerm_key_vault_access_policy" "deployment_user" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = [
    "Backup", "Delete", "Get", "List", "Purge", "Recover", "Restore", "Set"]
}

resource "azurerm_key_vault_access_policy" "function_app" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_linux_function_app.main.identity[0].principal_id

  secret_permissions = [
    "Get"]
}


resource "azurerm_key_vault_secret" "main" {
  for_each = toset([
    "pushover-api-token",
    "pushover-user-key",
  ])
  name         = each.key
  value        = "update-me-in-the-portal"
  key_vault_id = azurerm_key_vault.main.id

  tags = var.tags
  lifecycle {
    ignore_changes = [value]
  }
}

data "archive_file" "azure_function" {
  type             = "zip"
  source_dir       = "${path.module}/../src"
  output_file_mode = "0666"
  output_path      = "${path.module}/files/function.zip"
}

resource "azurerm_linux_function_app" "main" {
  name                        = "${var.workload}-${var.environment}-${module.regions.location_short}-func"
  resource_group_name         = azurerm_resource_group.main.name
  location                    = var.location
  service_plan_id             = azurerm_service_plan.main.id
  storage_account_name        = azurerm_storage_account.main.name
  storage_account_access_key  = azurerm_storage_account.main.primary_access_key
  https_only                  = true
  functions_extension_version = "~4"

  app_settings = {
    "ENABLE_ORYX_BUILD"              = "true"
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    "FUNCTIONS_WORKER_RUNTIME"       = "python"
    "AzureWebJobsFeatureFlags"       = "EnableWorkerIndexing"
    "PUSHOVER_APP_TOKEN"             = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main.name};SecretName=pushover-api-token)"
    "PUSHOVER_USER_KEY"              = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main.name};SecretName=pushover-user-key)"
  }

  site_config {
    application_insights_key = azurerm_application_insights.main.instrumentation_key
    application_stack {
      python_version = "3.11"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  zip_deploy_file = data.archive_file.azure_function.output_path
  tags = var.tags
}

resource "azurerm_monitor_action_group" "main" {
  name                = "${var.workload}-${var.environment}-${module.regions.location_short}-ag"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "pushover"

  azure_function_receiver {
    name                     = "pushover"
    function_app_resource_id = azurerm_linux_function_app.main.id
    function_name            = "parse_alert" # defined in src/function_app.py
    http_trigger_url         = "https://${azurerm_linux_function_app.main.default_hostname}/parse_alert"
    use_common_alert_schema  = true
  }
  tags = var.tags
}