#!/bin/bash
# Deploy AI Agent Connector to Azure Functions

set -e

RESOURCE_GROUP=${AZURE_RESOURCE_GROUP:-"ai-agent-connector-rg"}
FUNCTION_APP_NAME=${FUNCTION_APP_NAME:-"ai-agent-connector"}
LOCATION=${AZURE_LOCATION:-"eastus"}
RUNTIME=${RUNTIME:-"python:3.11"}

echo "Deploying to Azure Functions..."
echo "Resource Group: $RESOURCE_GROUP"
echo "Function App: $FUNCTION_APP_NAME"
echo "Location: $LOCATION"

# Login (if not already)
# az login

# Create resource group (if not exists)
az group create --name $RESOURCE_GROUP --location $LOCATION || true

# Create storage account (required for Functions)
STORAGE_ACCOUNT="${FUNCTION_APP_NAME}sa$(date +%s | tail -c 5)"
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Create function app
az functionapp create \
  --resource-group $RESOURCE_GROUP \
  --consumption-plan-location $LOCATION \
  --runtime $RUNTIME \
  --functions-version 4 \
  --name $FUNCTION_APP_NAME \
  --storage-account $STORAGE_ACCOUNT \
  --os-type Linux \
  --min-instances 1 \
  --max-burst 20

# Configure app settings
az functionapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP_NAME \
  --settings \
    FLASK_ENV=production \
    SERVERLESS=true \
    DATABASE_POOL_SIZE=5 \
    WEBSITE_TIME_ZONE=UTC

# Deploy function code
cd ../../
func azure functionapp publish $FUNCTION_APP_NAME --python

echo "Deployment complete!"
echo "Function URL: https://$FUNCTION_APP_NAME.azurewebsites.net"

