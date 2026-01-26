#!/bin/bash
# Deploy AI Agent Connector to GCP Cloud Functions

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"your-project-id"}
REGION=${GCP_REGION:-"us-central1"}
FUNCTION_NAME=${FUNCTION_NAME:-"ai-agent-connector"}
RUNTIME=${RUNTIME:-"python311"}
MEMORY=${MEMORY:-"512MB"}
TIMEOUT=${TIMEOUT:-"300s"}
MIN_INSTANCES=${MIN_INSTANCES:-"1"}  # Keep warm to avoid cold starts

echo "Deploying to GCP Cloud Functions..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Function: $FUNCTION_NAME"

# Set project
gcloud config set project $PROJECT_ID

# Deploy function
gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --runtime=$RUNTIME \
  --region=$REGION \
  --source=../../ \
  --entry-point=cloud_function_handler \
  --trigger-http \
  --allow-unauthenticated \
  --memory=$MEMORY \
  --timeout=$TIMEOUT \
  --min-instances=$MIN_INSTANCES \
  --max-instances=100 \
  --set-env-vars="FLASK_ENV=production,SERVERLESS=true,DATABASE_POOL_SIZE=5" \
  --set-secrets="DATABASE_SECRET=projects/$PROJECT_ID/secrets/db-secret:latest"

echo "Deployment complete!"
echo "Function URL: https://$REGION-$PROJECT_ID.cloudfunctions.net/$FUNCTION_NAME"

