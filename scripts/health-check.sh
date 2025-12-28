#!/bin/bash

# RoadSense Health Check Script
# Usage: ./health-check.sh <environment>
# Example: ./health-check.sh staging

set -e

ENVIRONMENT=$1

if [ -z "$ENVIRONMENT" ]; then
    echo "❌ Usage: ./health-check.sh <environment>"
    echo "   Example: ./health-check.sh staging"
    exit 1
fi

if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo "❌ Environment must be 'staging' or 'production'"
    exit 1
fi

echo "🏥 Running health checks for $ENVIRONMENT environment"
echo "================================================"

# Set host based on environment
if [ "$ENVIRONMENT" == "staging" ]; then
    HOST="localhost"
elif [ "$ENVIRONMENT" == "production" ]; then
    HOST="localhost"
fi

FAILED_CHECKS=0

# Health check function with retries
check_service() {
    local name=$1
    local url=$2
    local max_attempts=10
    local attempt=1
    
    echo "🔍 Checking $name..."
    
    while [ $attempt -le $max_attempts ]; do
        http_code=$(curl -s -o /dev/null -w "%{http_code}" $url 2>/dev/null || echo "000")
        
        if [ "$http_code" == "200" ]; then
            echo "✅ $name is healthy (HTTP $http_code)"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - HTTP $http_code"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $name failed health check"
    return 1
}

# Check Detection Service
check_service "Detection Service" "http://$HOST:8001/health" || FAILED_CHECKS=$((FAILED_CHECKS + 1))

# Check Ingestion Service
check_service "Ingestion Service" "http://$HOST:8003/health" || FAILED_CHECKS=$((FAILED_CHECKS + 1))

# Check Dashboard
check_service "Dashboard" "http://$HOST:3000" || FAILED_CHECKS=$((FAILED_CHECKS + 1))

# Check PostgreSQL
echo "🔍 Checking PostgreSQL..."
if docker exec roadsense-postgres pg_isready -U roadsense > /dev/null 2>&1; then
    echo "✅ PostgreSQL is healthy"
else
    echo "❌ PostgreSQL failed health check"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check Redis
echo "🔍 Checking Redis..."
if docker exec roadsense-redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis failed health check"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check MinIO
echo "🔍 Checking MinIO..."
if curl -f http://$HOST:9000/minio/health/live > /dev/null 2>&1; then
    echo "✅ MinIO is healthy"
else
    echo "❌ MinIO failed health check"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Additional checks: Test actual functionality
echo ""
echo "🧪 Running functional tests..."

# Test detection endpoint
echo "🔍 Testing detection endpoint..."
if curl -f -X POST http://$HOST:8001/api/v1/detection/models > /dev/null 2>&1; then
    echo "✅ Detection API is functional"
else
    echo "❌ Detection API test failed"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Display resource usage
echo ""
echo "📊 Resource Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep roadsense

echo "================================================"

if [ $FAILED_CHECKS -eq 0 ]; then
    echo "✅ All health checks passed!"
    exit 0
else
    echo "❌ $FAILED_CHECKS health check(s) failed"
    exit 1
fi
