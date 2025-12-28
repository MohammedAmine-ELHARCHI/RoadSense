#!/bin/bash

# RoadSense Deployment Script
# Usage: ./deploy.sh <environment> <image_tag>
# Example: ./deploy.sh staging v1.0.0-abc1234

set -e  # Exit on error

ENVIRONMENT=$1
IMAGE_TAG=$2

if [ -z "$ENVIRONMENT" ] || [ -z "$IMAGE_TAG" ]; then
    echo "❌ Usage: ./deploy.sh <environment> <image_tag>"
    echo "   Example: ./deploy.sh staging v1.0.0-abc1234"
    exit 1
fi

if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo "❌ Environment must be 'staging' or 'production'"
    exit 1
fi

echo "🚀 Starting deployment to $ENVIRONMENT with image tag: $IMAGE_TAG"
echo "================================================"

# Set environment-specific variables
if [ "$ENVIRONMENT" == "staging" ]; then
    COMPOSE_FILE="docker-compose.staging.yml"
    HOST="staging.roadsense.local"
elif [ "$ENVIRONMENT" == "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    HOST="roadsense.local"
fi

echo "📋 Using compose file: $COMPOSE_FILE"

# Export image tag for docker-compose
export IMAGE_TAG=$IMAGE_TAG

# Pull latest images from registry
echo "📦 Pulling images from Docker Registry..."
docker pull roadsense/detection-service:${IMAGE_TAG}
docker pull roadsense/ingestion-service:${IMAGE_TAG}
docker pull roadsense/dashboard:${IMAGE_TAG}

# Create backup of current deployment
echo "💾 Creating backup of current deployment..."
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
docker-compose -f $COMPOSE_FILE ps > $BACKUP_DIR/containers.txt
docker-compose -f $COMPOSE_FILE config > $BACKUP_DIR/config.yml

# Stop old containers gracefully
echo "🛑 Stopping old containers..."
docker-compose -f $COMPOSE_FILE down --remove-orphans

# Start new containers
echo "▶️ Starting new containers..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health check function
health_check() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    echo "🏥 Checking health of $service on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:$port/health > /dev/null 2>&1; then
            echo "✅ $service is healthy"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service failed health check"
    return 1
}

# Perform health checks
echo "🏥 Running health checks..."
HEALTH_CHECK_FAILED=0

health_check "Detection Service" 8001 || HEALTH_CHECK_FAILED=1
health_check "Ingestion Service" 8003 || HEALTH_CHECK_FAILED=1
health_check "Dashboard" 3000 || HEALTH_CHECK_FAILED=1

if [ $HEALTH_CHECK_FAILED -eq 1 ]; then
    echo "❌ Health checks failed - Rolling back..."
    
    # Rollback to previous version
    docker-compose -f $COMPOSE_FILE down
    
    # Restore from backup (if previous images exist)
    echo "🔄 Attempting rollback..."
    docker-compose -f $COMPOSE_FILE up -d
    
    echo "❌ Deployment failed - rolled back to previous version"
    exit 1
fi

# Display running containers
echo "📊 Current running containers:"
docker-compose -f $COMPOSE_FILE ps

# Display logs
echo "📝 Recent logs:"
docker-compose -f $COMPOSE_FILE logs --tail=20

echo "================================================"
echo "✅ Deployment to $ENVIRONMENT completed successfully!"
echo "🌐 Application URL: http://$HOST"
echo "📊 Dashboard: http://$HOST:3000"
echo "🔍 Detection API: http://$HOST:8001"
echo "📹 Ingestion API: http://$HOST:8003"
echo "================================================"
