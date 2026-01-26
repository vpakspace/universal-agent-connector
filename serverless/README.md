# Serverless Deployment Guide

One-click serverless deployment for AI Agent Connector on AWS Lambda, GCP Cloud Functions, and Azure Functions.

## 🚀 Quick Start

### Prerequisites

- **AWS**: AWS CLI, SAM CLI, AWS account
- **GCP**: gcloud CLI, GCP project with billing enabled
- **Azure**: Azure CLI, Azure subscription

### AWS Lambda Deployment

```bash
cd serverless/aws
sam build
sam deploy --guided
```

### GCP Cloud Functions Deployment

```bash
cd serverless/gcp
chmod +x deploy.sh
./deploy.sh
```

### Azure Functions Deployment

```bash
cd serverless/azure
chmod +x deploy.sh
./deploy.sh
```

## 📋 Features

### ✅ Stateless API
- No session storage required
- All state stored in managed database
- Horizontal scaling without sticky sessions

### ✅ Managed Database Support
- **AWS**: RDS PostgreSQL/MySQL, Aurora
- **GCP**: Cloud SQL (PostgreSQL/MySQL)
- **Azure**: Azure Database for PostgreSQL/MySQL

### ✅ Cold Start Optimization
- **Target**: <2 seconds
- Lazy imports
- Connection pooling
- Provisioned concurrency (AWS)
- Minimum instances (GCP/Azure)

## 🏗️ Architecture

### AWS Lambda
- API Gateway → Lambda Function
- Secrets Manager for database credentials
- VPC configuration for RDS access
- Provisioned concurrency for consistent performance

### GCP Cloud Functions
- Cloud Functions Gen2 (HTTP trigger)
- Secret Manager for database credentials
- Cloud SQL Proxy for secure connections
- Minimum instances to avoid cold starts

### Azure Functions
- Azure Functions (HTTP trigger)
- Key Vault for database credentials
- Private endpoints for database access
- Always-on instances

## ⚙️ Configuration

### Environment Variables

All platforms support:
- `FLASK_ENV`: Environment (production/staging/development)
- `SERVERLESS`: Set to 'true'
- `DATABASE_POOL_SIZE`: Connection pool size (default: 5)
- `DATABASE_MAX_OVERFLOW`: Max overflow connections (default: 10)

### Database Configuration

#### AWS
- Store credentials in Secrets Manager
- Configure VPC for RDS access
- Use RDS Proxy for connection pooling

#### GCP
- Store credentials in Secret Manager
- Use Cloud SQL Proxy
- Configure authorized networks

#### Azure
- Store credentials in Key Vault
- Use private endpoints
- Configure firewall rules

## 🔐 Security

### Secrets Management
- **AWS**: Secrets Manager
- **GCP**: Secret Manager
- **Azure**: Key Vault

### Network Security
- VPC/Private endpoints for database access
- IAM roles with least privilege
- No public database endpoints

## 💰 Cost Optimization

### AWS Lambda
- Pay per request
- Provisioned concurrency: ~$0.015/hour per concurrency
- Free tier: 1M requests/month

### GCP Cloud Functions
- Pay per invocation
- Minimum instances: ~$0.0000025/GB-second
- Free tier: 2M invocations/month

### Azure Functions
- Consumption plan: Pay per execution
- Always-on: ~$0.20/day
- Free tier: 1M requests/month

## 📊 Performance

### Cold Start Optimization
1. **Lazy Imports**: Only load what's needed
2. **Connection Pooling**: Reuse database connections
3. **Provisioned Concurrency**: Keep functions warm (AWS)
4. **Minimum Instances**: Keep instances running (GCP/Azure)

### Target Metrics
- **Cold Start**: <2 seconds
- **Warm Invocation**: <100ms
- **Database Connection**: <50ms (pooled)

## 🧪 Testing

### Local Testing

#### AWS (SAM Local)
```bash
sam local start-api
```

#### GCP (Functions Framework)
```bash
functions-framework --target=cloud_function_handler
```

#### Azure (Functions Core Tools)
```bash
func start
```

## 📚 Detailed Guides

- [AWS Lambda Deployment Guide](aws/README.md)
- [GCP Cloud Functions Deployment Guide](gcp/README.md)
- [Azure Functions Deployment Guide](azure/README.md)

## 🔧 Troubleshooting

### Cold Start Issues
- Increase provisioned concurrency (AWS)
- Set minimum instances > 0 (GCP/Azure)
- Reduce package size
- Use Lambda layers (AWS)

### Database Connection Issues
- Check VPC/network configuration
- Verify security groups/firewall rules
- Test connection from function
- Check connection pool settings

### Performance Issues
- Enable connection pooling
- Use managed database proxies
- Monitor function metrics
- Optimize code paths

## 📈 Monitoring

### AWS
- CloudWatch Logs
- X-Ray tracing
- Lambda metrics

### GCP
- Cloud Logging
- Cloud Trace
- Cloud Monitoring

### Azure
- Application Insights
- Log Analytics
- Function metrics

## 🔄 Updates

### Update Function Code
```bash
# AWS
sam build && sam deploy

# GCP
./deploy.sh

# Azure
func azure functionapp publish <app-name>
```

### Update Configuration
- Modify environment variables
- Update secrets in respective secret managers
- Redeploy function

## 🎯 Best Practices

1. **Use Connection Pooling**: Always enable for managed databases
2. **Keep Functions Warm**: Use provisioned concurrency/min instances
3. **Monitor Cold Starts**: Track and optimize initialization time
4. **Secure Secrets**: Never hardcode credentials
5. **Optimize Package Size**: Minimize dependencies
6. **Use Layers**: Share common dependencies (AWS)

## 📖 Next Steps

1. Set up managed database (RDS/Cloud SQL/Azure Database)
2. Configure secrets in secret manager
3. Deploy function using platform-specific guide
4. Test cold start performance
5. Monitor and optimize

