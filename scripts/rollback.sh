#!/bin/bash

# RoadSense Rollback Script
# Usage: ./rollback.sh <environment> <backup_timestamp>
# Example: ./rollback.sh staging 20250127_143022

set -e  # Exit on error

ENVIRONMENT=$1
BACKUP_TIMESTAMP=$2

if [ -z "$ENVIRONMENT" ]; then
    echo "❌ Usage: ./rollback.sh <environment> [backup_timestamp]"
    echo "   Example: ./rollback.sh staging 20250127_143022"
    echo ""
    echo "Available backups:"
    ls -lt backups/ | grep "^d" | head -10
    exit 1
fi

if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo "❌ Environment must be 'staging' or 'production'"
    exit 1
fi

echo "🔄 Starting rollback for $ENVIRONMENT"
echo "================================================"

# Set environment-specific variables
if [ "$ENVIRONMENT" == "staging" ]; then
    COMPOSE_FILE="docker-compose.staging.yml"
elif [ "$ENVIRONMENT" == "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

# If no backup timestamp provided, use the latest
if [ -z "$BACKUP_TIMESTAMP" ]; then
    BACKUP_DIR=$(ls -t backups/ | head -1)
    echo "⚠️ No backup timestamp provided, using latest: $BACKUP_DIR"
else
    BACKUP_DIR=$BACKUP_TIMESTAMP
fi

BACKUP_PATH="backups/$BACKUP_DIR"

if [ ! -d "$BACKUP_PATH" ]; then
    echo "❌ Backup not found: $BACKUP_PATH"
    echo ""
    echo "Available backups:"
    ls -lt backups/
    exit 1
fi

echo "📁 Using backup: $BACKUP_PATH"

# Confirm rollback
read -p "⚠️ Are you sure you want to rollback to $BACKUP_DIR? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Rollback cancelled"
    exit 0
fi

# Stop current containers
echo "🛑 Stopping current containers..."
docker-compose -f $COMPOSE_FILE down --remove-orphans

# Get previous image tags from backup
if [ -f "$BACKUP_PATH/image_tags.txt" ]; then
    echo "📦 Restoring previous image versions..."
    source $BACKUP_PATH/image_tags.txt
    
    export IMAGE_TAG=$PREVIOUS_IMAGE_TAG
    
    echo "   Detection Service: roadsense/detection-service:$PREVIOUS_IMAGE_TAG"
    echo "   Ingestion Service: roadsense/ingestion-service:$PREVIOUS_IMAGE_TAG"
    echo "   Dashboard: roadsense/dashboard:$PREVIOUS_IMAGE_TAG"
else
    echo "⚠️ No image_tags.txt found, using 'latest' tag"
    export IMAGE_TAG=latest
fi

# Pull previous images
echo "📦 Pulling previous images..."
docker pull roadsense/detection-service:${IMAGE_TAG} || echo "⚠️ Could not pull detection-service"
docker pull roadsense/ingestion-service:${IMAGE_TAG} || echo "⚠️ Could not pull ingestion-service"
docker pull roadsense/dashboard:${IMAGE_TAG} || echo "⚠️ Could not pull dashboard"

# Start containers with previous version
echo "▶️ Starting containers with previous version..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 15

# Health check function
health_check() {
    local service=$1
    local port=$2
    local max_attempts=20
    local attempt=1
    
    echo "🏥 Checking health of $service..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:$port/health > /dev/null 2>&1; then
            echo "✅ $service is healthy"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts..."
        sleep 3
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service failed health check after rollback"
    return 1
}

# Perform health checks
echo "🏥 Running health checks..."
HEALTH_CHECK_FAILED=0

health_check "Detection Service" 8001 || HEALTH_CHECK_FAILED=1
health_check "Ingestion Service" 8003 || HEALTH_CHECK_FAILED=1
health_check "Dashboard" 3000 || HEALTH_CHECK_FAILED=1

if [ $HEALTH_CHECK_FAILED -eq 1 ]; then
    echo "❌ Rollback health checks failed!"
    echo "📝 Checking logs..."
    docker-compose -f $COMPOSE_FILE logs --tail=50
    exit 1
fi

# Display running containers
echo "📊 Current running containers:"
docker-compose -f $COMPOSE_FILE ps

# Display recent logs
echo "📝 Recent logs:"
docker-compose -f $COMPOSE_FILE logs --tail=20

echo "================================================"
echo "✅ Rollback to $BACKUP_DIR completed successfully!"
echo "🔄 System restored to previous version"
echo "================================================"
