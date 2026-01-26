# GCP Cloud Functions Deployment Guide

Complete guide for deploying AI Agent Connector to GCP Cloud Functions.

## Prerequisites

- GCP Project with billing enabled
- gcloud CLI installed and configured
- Cloud SQL instance (PostgreSQL or MySQL)
- Python 3.11

## Step 1: Set Up Cloud SQL

### Create Cloud SQL Instance

```bash
gcloud sql instances create ai-agent-connector-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=YourPassword123!
```

### Create Database

```bash
gcloud sql databases create ai_agent_connector \
  --instance=ai-agent-connector-db
```

### Create User

```bash
gcloud sql users create app_user \
  --instance=ai-agent-connector-db \
  --password=YourPassword123!
```

## Step 2: Configure Secret Manager

Store database credentials:

```bash
echo -n '{
  "host": "/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME",
  "port": 5432,
  "database": "ai_agent_connector",
  "username": "app_user",
  "password": "YourPassword123!"
}' | gcloud secrets create db-secret --data-file=-
```

Grant access to Cloud Functions:

```bash
gcloud secrets add-iam-policy-binding db-secret \
  --member="serviceAccount:PROJECT_ID@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Step 3: Deploy Function

### Using Deployment Script

```bash
cd serverless/gcp
chmod +x deploy.sh
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=us-central1
./deploy.sh
```

### Manual Deployment

```bash
gcloud functions deploy ai-agent-connector \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=../../ \
  --entry-point=cloud_function_handler \
  --trigger-http \
  --allow-unauthenticated \
  --memory=512MB \
  --timeout=300s \
  --min-instances=1 \
  --max-instances=100 \
  --set-env-vars="FLASK_ENV=production,SERVERLESS=true" \
  --set-secrets="DATABASE_SECRET=projects/PROJECT_ID/secrets/db-secret:latest" \
  --vpc-connector=projects/PROJECT_ID/locations/REGION/connectors/CONNECTOR_NAME
```

## Step 4: Configure Cloud SQL Proxy

### Create VPC Connector

```bash
gcloud compute networks vpc-access connectors create connector \
  --region=us-central1 \
  --subnet=default \
  --subnet-project=PROJECT_ID \
  --min-instances=2 \
  --max-instances=3
```

### Grant Cloud SQL Access

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:PROJECT_ID@appspot.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

## Step 5: Test Deployment

### Get Function URL

```bash
gcloud functions describe ai-agent-connector \
  --gen2 \
  --region=us-central1 \
  --format="value(serviceConfig.uri)"
```

### Test Health Endpoint

```bash
curl https://REGION-PROJECT_ID.cloudfunctions.net/ai-agent-connector/health
```

### Test API

```bash
curl https://REGION-PROJECT_ID.cloudfunctions.net/ai-agent-connector/api/health
```

## Configuration

### Environment Variables

- `FLASK_ENV`: production
- `SERVERLESS`: true
- `DATABASE_POOL_SIZE`: 5
- `DATABASE_MAX_OVERFLOW`: 10

### Cold Start Optimization

1. **Minimum Instances**: Set to 1+ to keep warm
2. **Memory**: 512MB (adjust based on needs)
3. **Timeout**: 300 seconds (max)
4. **Cloud SQL Proxy**: Use for connection pooling

### Connection Pooling

- Use Cloud SQL Proxy connector
- Pool size: 5 connections
- Max overflow: 10 connections

## Monitoring

### Cloud Logging

```bash
gcloud functions logs read ai-agent-connector \
  --gen2 \
  --region=us-central1 \
  --limit=50
```

### Cloud Monitoring

- Function invocations
- Execution time
- Error rate
- Cold starts

### Cloud Trace

Enable distributed tracing:
```bash
gcloud functions deploy ai-agent-connector \
  --gen2 \
  --set-env-vars="ENABLE_TRACE=true"
```

## Cost Optimization

### Minimum Instances
- Cost: ~$0.0000025/GB-second
- Keep 1 instance warm to avoid cold starts
- Scale based on traffic

### Cloud SQL Proxy
- Reduces connection overhead
- Better connection pooling
- Lower latency

### Memory Allocation
- Start with 512MB
- Monitor and adjust
- Higher memory = faster CPU

## Troubleshooting

### Cold Start Too Long
- Set minimum instances > 0
- Reduce package size
- Optimize imports (lazy loading)
- Use Cloud SQL Proxy

### Database Connection Issues
- Check VPC connector configuration
- Verify Cloud SQL access permissions
- Test connection from function
- Check firewall rules

### Timeout Issues
- Increase timeout (max 300s)
- Optimize database queries
- Use connection pooling
- Check Cloud SQL performance

## Cleanup

```bash
gcloud functions delete ai-agent-connector \
  --gen2 \
  --region=us-central1
```

## Next Steps

- Set up Cloud Monitoring alerts
- Configure Cloud Armor for security
- Set up CI/CD pipeline
- Monitor costs and optimize

