#!/bin/bash

# AWS Lightsail Deployment Script for Hong Kong Species API
# This script helps deploy the application to AWS Lightsail

echo "🚀 Hong Kong Species API - AWS Lightsail Deployment"
echo "=================================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI first:"
    echo "   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first"
    exit 1
fi

echo "✅ AWS CLI configured"

# Variables
INSTANCE_NAME="hk-species-api"
BLUEPRINT_ID="ubuntu_20_04"
BUNDLE_ID="nano_2_0"  # $3.50/month
REGION="us-east-1"
KEY_PAIR_NAME="hk-species-key"

echo ""
echo "📋 Deployment Configuration:"
echo "   Instance Name: $INSTANCE_NAME"
echo "   Blueprint: $BLUEPRINT_ID"
echo "   Bundle: $BUNDLE_ID"
echo "   Region: $REGION"
echo ""

read -p "Continue with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 1
fi

# Create key pair if it doesn't exist
echo "🔑 Creating SSH key pair..."
if ! aws lightsail get-key-pair --key-pair-name $KEY_PAIR_NAME --region $REGION &> /dev/null; then
    aws lightsail create-key-pair \
        --key-pair-name $KEY_PAIR_NAME \
        --region $REGION \
        --query 'privateKeyBase64' \
        --output text > ${KEY_PAIR_NAME}.pem
    
    chmod 600 ${KEY_PAIR_NAME}.pem
    echo "✅ Key pair created: ${KEY_PAIR_NAME}.pem"
else
    echo "✅ Key pair already exists"
fi

# Create Lightsail instance
echo "🖥️  Creating Lightsail instance..."
aws lightsail create-instances \
    --instance-names $INSTANCE_NAME \
    --availability-zone ${REGION}a \
    --blueprint-id $BLUEPRINT_ID \
    --bundle-id $BUNDLE_ID \
    --region $REGION \
    --user-data file://lightsail-userdata.sh

if [ $? -eq 0 ]; then
    echo "✅ Instance creation initiated"
else
    echo "❌ Failed to create instance"
    exit 1
fi

# Wait for instance to be running
echo "⏳ Waiting for instance to be running..."
while true; do
    STATE=$(aws lightsail get-instance --instance-name $INSTANCE_NAME --region $REGION --query 'instance.state.name' --output text)
    if [ "$STATE" = "running" ]; then
        break
    fi
    echo "   Instance state: $STATE"
    sleep 10
done

# Get instance IP
INSTANCE_IP=$(aws lightsail get-instance --instance-name $INSTANCE_NAME --region $REGION --query 'instance.publicIpAddress' --output text)

echo "✅ Instance is running!"
echo "📍 Public IP: $INSTANCE_IP"

# Open port 8000 for the API
echo "🔓 Opening port 8000..."
aws lightsail put-instance-public-ports \
    --instance-name $INSTANCE_NAME \
    --port-infos fromPort=8000,toPort=8000,protocol=TCP \
    --region $REGION

echo ""
echo "🎉 Deployment Complete!"
echo "================================"
echo "Instance Name: $INSTANCE_NAME"
echo "Public IP: $INSTANCE_IP"
echo "SSH Command: ssh -i ${KEY_PAIR_NAME}.pem ubuntu@$INSTANCE_IP"
echo "API URL: http://$INSTANCE_IP:8000"
echo "Frontend URL: http://$INSTANCE_IP:8000/frontend.html"
echo ""
echo "📝 Next Steps:"
echo "1. Wait 2-3 minutes for the application to start"
echo "2. Update frontend.html API_BASE URL to: http://$INSTANCE_IP:8000/api"
echo "3. Test the API: curl http://$INSTANCE_IP:8000/health"
echo ""
echo "🔧 To SSH into the instance:"
echo "   ssh -i ${KEY_PAIR_NAME}.pem ubuntu@$INSTANCE_IP"
echo ""
echo "💰 Cost: ~$3.50/month for nano instance"