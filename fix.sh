#!/bin/bash

# OPD Token System - Quick Fix Script
# This script fixes common issues

echo "🔧 OPD Token System - Quick Fix Script"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo "ℹ️  $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    print_success "Docker is running"
}

# Fix 1: Rebuild containers with updated requirements
fix_missing_dependencies() {
    print_info "Fix 1: Rebuilding containers with all dependencies..."
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    print_success "Containers rebuilt with updated dependencies"
}

# Fix 2: Run migrations properly
fix_database() {
    print_info "Fix 2: Running database migrations..."
    docker-compose exec web python manage.py makemigrations
    docker-compose exec web python manage.py migrate
    print_success "Database migrations complete"
}

# Fix 3: Create proper superuser
fix_admin_login() {
    print_info "Fix 3: Creating admin user..."
    echo ""
    print_warning "Please create admin credentials when prompted:"
    docker-compose exec web python manage.py createsuperuser
    print_success "Admin user created"
}

# Fix 4: Install demo dependencies
fix_demo_script() {
    print_info "Fix 4: Installing demo script dependencies..."
    docker-compose exec web pip install requests
    print_success "Demo dependencies installed"
}

# Fix 5: Verify services are running
check_services() {
    print_info "Checking service status..."
    
    # Check web service
    if docker-compose ps | grep -q "web.*Up"; then
        print_success "Web service is running"
    else
        print_error "Web service is not running"
        return 1
    fi
    
    # Check database
    if docker-compose ps | grep -q "db.*Up"; then
        print_success "Database is running"
    else
        print_error "Database is not running"
        return 1
    fi
    
    # Check Redis
    if docker-compose ps | grep -q "redis.*Up"; then
        print_success "Redis is running"
    else
        print_error "Redis is not running"
        return 1
    fi
}

# Fix 6: Test API connection
test_api() {
    print_info "Testing API connection..."
    
    sleep 3  # Wait for services to be ready
    
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/doctors/)
    
    if [ "$response" = "200" ]; then
        print_success "API is responding correctly"
        return 0
    else
        print_error "API is not responding (HTTP $response)"
        return 1
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "Select an option:"
    echo "1) Fix all issues (recommended)"
    echo "2) Rebuild containers only"
    echo "3) Fix database/migrations"
    echo "4) Create/reset admin user"
    echo "5) Install demo dependencies"
    echo "6) Check service status"
    echo "7) View logs"
    echo "8) Restart all services"
    echo "9) Run demo script"
    echo "0) Exit"
    echo ""
    read -p "Enter option [0-9]: " option
}

# Fix all issues
fix_all() {
    print_info "Running all fixes..."
    echo ""
    
    check_docker
    fix_missing_dependencies
    sleep 5  # Wait for containers to start
    fix_database
    fix_demo_script
    check_services
    test_api
    
    echo ""
    print_success "All fixes applied!"
    echo ""
    print_info "You can now:"
    echo "  - Access API docs: http://localhost:8000/api/docs/"
    echo "  - Access admin: http://localhost:8000/admin/"
    echo "  - Run demo: docker-compose exec web python demo.py"
    echo ""
    print_warning "Don't forget to create an admin user if needed (option 4)"
}

# View logs
view_logs() {
    print_info "Showing service logs (Ctrl+C to exit)..."
    docker-compose logs -f
}

# Restart services
restart_services() {
    print_info "Restarting all services..."
    docker-compose restart
    sleep 3
    check_services
    print_success "Services restarted"
}

# Run demo
run_demo() {
    print_info "Running demo script..."
    echo ""
    print_warning "Make sure you've created an admin user first!"
    echo ""
    docker-compose exec web python demo.py
}

# Main script
main() {
    check_docker
    
    while true; do
        show_menu
        
        case $option in
            1)
                fix_all
                ;;
            2)
                fix_missing_dependencies
                ;;
            3)
                fix_database
                ;;
            4)
                fix_admin_login
                ;;
            5)
                fix_demo_script
                ;;
            6)
                check_services
                test_api
                ;;
            7)
                view_logs
                ;;
            8)
                restart_services
                ;;
            9)
                run_demo
                ;;
            0)
                print_info "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid option. Please try again."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run main function
main
