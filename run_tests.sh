#!/bin/bash

# Comprehensive test script for Celery setup
echo "=== Celery Setup Test Script ==="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
    fi
}

# Function to print info
print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if Docker is running
print_info "Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi
print_status 0 "Docker is running"

# Check if docker-compose is available
print_info "Checking docker-compose..."
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ docker-compose is not installed or not in PATH${NC}"
    exit 1
fi
print_status 0 "docker-compose is available"

# Build containers
print_info "Building Docker containers..."
docker-compose build --no-cache
print_status $? "Docker containers built"

# Start services
print_info "Starting services..."
docker-compose up -d
print_status $? "Services started"

# Wait for services to be ready
print_info "Waiting for services to be ready..."
sleep 30

# Check service health
print_info "Checking service health..."
docker-compose ps

# Test Redis connection
print_info "Testing Redis connection..."
docker-compose exec -T redis redis-cli ping
print_status $? "Redis connection"

# Test Redis from host (since backend and worker use host network)
print_info "Testing Redis from host network..."
redis-cli -h localhost -p 6379 ping 2>/dev/null || echo "Redis not accessible from host"

# Test PostgreSQL connection
print_info "Testing PostgreSQL connection..."
docker-compose exec -T vaakshakti-db pg_isready -U vaakshakti_user -d vaakshakti_db
print_status $? "PostgreSQL connection"

# Test backend API
print_info "Testing backend API..."
sleep 5
curl -s -o /dev/null -w "%{http_code}" http://localhost:1212/docs | grep -q "200"
print_status $? "Backend API accessible"

# Test frontend
print_info "Testing frontend..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:1213 | grep -q "200"
print_status $? "Frontend accessible"

# Run comprehensive Celery tests
print_info "Running comprehensive Celery tests..."
docker-compose exec -T speech-tutor python test_full_setup.py
TEST_RESULT=$?
print_status $TEST_RESULT "Comprehensive Celery tests"

# Test simple task dispatch
print_info "Testing simple task dispatch..."
docker-compose exec -T speech-tutor python test_task_dispatch.py
DISPATCH_RESULT=$?
print_status $DISPATCH_RESULT "Simple task dispatch"

# Check worker logs
print_info "Checking worker logs (last 20 lines)..."
docker-compose logs --tail=20 celery-worker

# Check backend logs
print_info "Checking backend logs (last 20 lines)..."
docker-compose logs --tail=20 speech-tutor

# Final summary
echo ""
echo "=== Test Summary ==="
if [ $TEST_RESULT -eq 0 ] && [ $DISPATCH_RESULT -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Your Celery setup is working correctly.${NC}"
    echo ""
    echo "Your services are running at:"
    echo "  - Frontend: http://localhost:1213"
    echo "  - Backend API: http://localhost:1212"
    echo "  - API Documentation: http://localhost:1212/docs"
    echo ""
    echo "To stop services: docker-compose down"
    echo "To view logs: docker-compose logs -f [service-name]"
else
    echo -e "${RED}❌ Some tests failed. Please review the output above.${NC}"
    echo ""
    echo "Troubleshooting commands:"
    echo "  - Check service status: docker-compose ps"
    echo "  - View logs: docker-compose logs [service-name]"
    echo "  - Restart services: docker-compose restart"
    echo "  - Stop services: docker-compose down"
fi

exit $((TEST_RESULT + DISPATCH_RESULT))