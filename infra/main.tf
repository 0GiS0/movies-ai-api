# terraform {
#   backend "azurerm" {
#     key = "tour-of-heroes-ghc-extension.tfstate"

#   }
# }

provider "azurerm" {

  subscription_id = var.subscription_id

  features {

  }
}

resource "random_pet" "name" {
  length = 2
}

resource "azurerm_resource_group" "rg" {
  name     = "movie-api-rg"
  location = "spaincentral"
}

resource "azurerm_service_plan" "plan" {
  name                = "movies-api-service-plan"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"
  sku_name            = "S1"
}

resource "azurerm_linux_web_app" "web" {

  name                = "movies-api-${random_pet.name.id}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  service_plan_id     = azurerm_service_plan.plan.id

  site_config {
    application_stack {
      python_version = "3.9"
    }
  }
}