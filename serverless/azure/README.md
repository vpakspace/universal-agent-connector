# Azure Functions Deployment Guide

Complete guide for deploying AI Agent Connector to Azure Functions.

## Prerequisites

- Azure Subscription
- Azure CLI installed and configured
- Azure Database for PostgreSQL or MySQL
- Python 3.11
- Azure Functions Core Tools (`npm install -g azure-functions-core-tools@4`)

## Step 1: Set Up Azure Database

### Create PostgreSQL Database

```bash
az postgres flexible-server create \
  --resource-group ai-agent-connector-rg \
  --name ai-agent-connector-db \
  --location eastus \
  --admin-user adminuser \
  --admin-password YourPassword123! \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --version 15 \
  --storage-size 32
```

### Create Database

```bash
az postgres flexible-server db create \
  --resource-group ai-agent-connector-rg \
  --server-name ai-agent-connector-db \
  --database-name ai_agent_connector
```

### Configure Firewall

```bash
az postgres flexible-server firewall-rule create \
  --resource-group ai-agent-connector-rg \
  --name ai-agent-connector-db \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

## Step 2: Configure Key Vault

### Create Key Vault

```bash
az keyvault create \
  --name ai-agent-connector-kv \
  --resource-group ai-agent-connector-rg \
  --location eastus
```

### Store Database Secret

```bash
az keyvault secret set \
  --vault-name ai-agent-connector-kv \
  --name db-connection-string \
  --value "host=ai-agent-connector-db.postgres.database.azure.com port=5432 dbname=ai_agent_connector user=adminuser password=YourPassword123! sslmode=require"
```

### Grant Access to Function App

```bash
az functionapp identity assign \
  --name ai-agent-connector \
  --resource-group ai-agent-connector-rg

PRINCIPAL_ID=$(az functionapp identity show \
  --name ai-agent-connector \
  --resource-group ai-agent-connector-rg \
  --query principalId --output tsv)

az keyvault set-policy \
  --name ai-agent-connector-kv \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list
```

## Step 3: Deploy Function

### Using Deployment Script

```bash
cd serverless/azure
chmod +x deploy.sh
export AZURE_RESOURCE_GROUP=ai-agent-connector-rg
export FUNCTION_APP_NAME=ai-agent-connector
./deploy.sh
```

### Manual Deployment

```bash
# Create resource group
az group create --name ai-agent-connector-rg --location eastus

# Create storage account
az storage account create \
  --name aiagentconnectorsa \
  --resource-group ai-agent-connector-rg \
  --location eastus \
  --sku Standard_LRS

# Create function app
az functionapp create \
  --resource-group ai-agent-connector-rg \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name ai-agent-connector \
  --storage-account aiagentconnectorsa \
  --os-type Linux \
  --min-instances 1 \
  --max-burst 20

# Configure app settings
az functionapp config appsettings set \
  --resource-group ai-agent-connector-rg \
  --name ai-agent-connector \
  --settings \
    FLASK_ENV=production \
    SERVERLESS=true \
    DATABASE_POOL_SIZE=5 \
    AzureWebJobsStorage=$(az storage account show-connection-string \
      --name aiagentconnectorsa \
      --resource-group ai-agent-connector-rg \
      --query connectionString --output tsv)

# Deploy function code
cd ../../
func azure functionapp publish ai-agent-connector --python
```

## Step 4: Configure Private Endpoints (Optional)

### Create Private Endpoint

```bash
az network private-endpoint create \
  --name ai-agent-connector-pe \
  --resource-group ai-agent-connector-rg \
  --vnet-name ai-agent-connector-vnet \
  --subnet default \
  --private-connection-resource-id $(az postgres flexible-server show \
    --resource-group ai-agent-connector-rg \
    --name ai-agent-connector-db \
    --query id --output tsv) \
  --group-id postgresqlServer \
  --connection-name ai-agent-connector-connection
```

## Step 5: Test Deployment

### Get Function URL

```bash
az functionapp show \
  --name ai-agent-connector \
  --resource-group ai-agent-connector-rg \
  --query defaultHostName \
  --output tsv
```

### Test Health Endpoint

```bash
curl https://ai-agent-connector.azurewebsites.net/api/health
```

### Test API

```bash
curl https://ai-agent-connector.azurewebsites.net/api/api/health
```

## Configuration

### Environment Variables

- `FLASK_ENV`: production
- `SERVERLESS`: true
- `DATABASE_POOL_SIZE`: 5
- `DATABASE_MAX_OVERFLOW`: 10

### Cold Start Optimization

1. **Always On**: Enable in Consumption plan (costs apply)
2. **Minimum Instances**: Set to 1+
3. **Memory**: 1.5GB (default, adjust in plan)
4. **Timeout**: 5 minutes (max)

### Connection Pooling

- Pool size: 5 connections
- Max overflow: 10 connections
- Use connection string from Key Vault

## Monitoring

### Application Insights

```bash
az monitor app-insights component create \
  --app ai-agent-connector-insights \
  --location eastus \
  --resource-group ai-agent-connector-rg

az functionapp config appsettings set \
  --resource-group ai-agent-connector-rg \
  --name ai-agent-connector \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=$(az monitor app-insights component show \
    --app ai-agent-connector-insights \
    --resource-group ai-agent-connector-rg \
    --query instrumentationKey --output tsv)
```

### Log Analytics

- Function executions
- Execution time
- Error rate
- Cold starts

## Cost Optimization

### Consumption Plan
- Pay per execution
- Free tier: 1M requests/month
- Always-on: ~$0.20/day (optional)

### Always-On
- Prevents cold starts
- Additional cost
- Recommended for production

### Memory Allocation
- Default: 1.5GB
- Adjust in App Service Plan
- Higher memory = faster CPU

## Troubleshooting

### Cold Start Too Long
- Enable Always-On
- Set minimum instances > 0
- Reduce package size
- Optimize imports (lazy loading)

### Database Connection Issues
- Check firewall rules
- Verify Key Vault access
- Test connection from function
- Check private endpoint configuration

### Timeout Issues
- Increase timeout (max 5 min)
- Optimize database queries
- Use connection pooling
- Check database performance

## Cleanup

```bash
az group delete --name ai-agent-connector-rg --yes
```

## Next Steps

- Set up Application Insights alerts
- Configure Azure Front Door for CDN
- Set up CI/CD pipeline
- Monitor costs and optimize

