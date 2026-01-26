# AWS Lambda Deployment Guide

Complete guide for deploying AI Agent Connector to AWS Lambda with API Gateway.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI installed and configured
- SAM CLI installed (`pip install aws-sam-cli`)
- RDS or Aurora database instance
- Python 3.11

## Step 1: Set Up RDS Database

### Create RDS Instance

```bash
aws rds create-db-instance \
  --db-instance-identifier ai-agent-connector-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password YourPassword123! \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name default
```

### Or Use Aurora Serverless

```bash
aws rds create-db-cluster \
  --db-cluster-identifier ai-agent-connector-cluster \
  --engine aurora-postgresql \
  --master-username admin \
  --master-user-password YourPassword123! \
  --database-name ai_agent_connector
```

## Step 2: Configure Secrets Manager

Store database credentials in Secrets Manager:

```bash
aws secretsmanager create-secret \
  --name ai-agent-connector-db-secret \
  --secret-string '{
    "host": "your-db-endpoint.rds.amazonaws.com",
    "port": 5432,
    "database": "ai_agent_connector",
    "username": "admin",
    "password": "YourPassword123!"
  }'
```

## Step 3: Deploy with SAM

### Build

```bash
cd serverless/aws
sam build
```

### Deploy (Guided)

```bash
sam deploy --guided
```

This will prompt for:
- Stack name
- AWS Region
- Database endpoint
- Database credentials
- Environment name

### Deploy (Automated)

```bash
sam deploy \
  --stack-name ai-agent-connector \
  --parameter-overrides \
    DatabaseEndpoint=your-db.rds.amazonaws.com \
    DatabaseName=ai_agent_connector \
    DatabaseUsername=admin \
  --capabilities CAPABILITY_IAM \
  --resolve-s3
```

## Step 4: Configure VPC (if needed)

If your RDS is in a VPC, configure Lambda VPC access:

1. Update `template.yaml` with VPC configuration:
```yaml
VpcConfig:
  SecurityGroupIds:
    - sg-xxxxx
  SubnetIds:
    - subnet-xxxxx
    - subnet-yyyyy
```

2. Add VPC permissions to IAM role

## Step 5: Test Deployment

### Get API URL

```bash
aws cloudformation describe-stacks \
  --stack-name ai-agent-connector \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text
```

### Test Health Endpoint

```bash
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/production/health
```

### Test API

```bash
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/production/api/health
```

## Configuration

### Environment Variables

Set in `template.yaml`:
- `FLASK_ENV`: production
- `SERVERLESS`: true
- `DATABASE_POOL_SIZE`: 5
- `DATABASE_MAX_OVERFLOW`: 10

### Cold Start Optimization

1. **Provisioned Concurrency**: Set in template
2. **Lambda Layers**: Dependencies in layer
3. **Memory**: 512MB (adjust based on needs)
4. **Timeout**: 30 seconds

### Connection Pooling

- Pool size: 5 connections
- Max overflow: 10 connections
- Connections reused across invocations

## Monitoring

### CloudWatch Logs

```bash
aws logs tail /aws/lambda/ai-agent-connector-api --follow
```

### CloudWatch Metrics

- Invocations
- Duration
- Errors
- Throttles
- Cold starts

### X-Ray Tracing

Enable in `template.yaml`:
```yaml
Tracing: Active
```

## Cost Optimization

### Provisioned Concurrency
- Cost: ~$0.015/hour per concurrency
- Use for consistent performance
- Start with 2, scale as needed

### Reserved Concurrency
- Limit max concurrent executions
- Prevents cost spikes
- Set based on expected load

### Lambda Layers
- Share dependencies
- Reduce package size
- Faster deployments

## Troubleshooting

### Cold Start Too Long
- Increase memory allocation
- Use provisioned concurrency
- Optimize imports (lazy loading)
- Reduce package size

### Database Connection Issues
- Check VPC configuration
- Verify security groups
- Test connection from Lambda
- Check Secrets Manager permissions

### Timeout Issues
- Increase timeout (max 15 min)
- Optimize database queries
- Use connection pooling
- Check RDS performance

## Cleanup

```bash
sam delete --stack-name ai-agent-connector
```

## Next Steps

- Set up CloudWatch alarms
- Configure API Gateway throttling
- Set up CI/CD pipeline
- Monitor costs and optimize

