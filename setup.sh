#!/bin/bash

echo "🏥 OPD Token Allocation System - Quick Start"
echo "==========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt -q

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "✏️  Please edit .env with your database credentials"
fi

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser prompt
echo ""
echo "👤 Create admin user? (y/n)"
read -r create_admin
if [ "$create_admin" = "y" ]; then
    python manage.py createsuperuser
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To start the server, run:"
echo "   python manage.py runserver"
echo ""
echo "📚 Access the API documentation at:"
echo "   http://localhost:8000/api/docs/"
echo ""
echo "🔐 Access the admin panel at:"
echo "   http://localhost:8000/admin/"
echo ""
