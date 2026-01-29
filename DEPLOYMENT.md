# Deployment Guide

This guide covers different deployment options for the OPD Token Allocation System.

## Table of Contents
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Monitoring](#monitoring)

## Local Development

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Redis 6+

### Quick Setup

```bash
# 1. Clone and navigate
cd opd_token_system

# 2. Run setup script
chmod +x setup.sh
./setup.sh

# 3. Start services (in separate terminals)
# Terminal 1: PostgreSQL (if not running as service)
# Terminal 2: Redis
redis-server

# Terminal 3: Django
python manage.py runserver
```

### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Setup database
createdb opd_tokens
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## Docker Deployment

### Prerequisites
- Docker
- Docker Compose

### Using Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

### Access Points
- API: http://localhost:8000/api/v1/
- Admin: http://localhost:8000/admin/
- Docs: http://localhost:8000/api/docs/

## Production Deployment

### Option 1: Cloud Platform (Recommended)

#### Heroku

```bash
# Install Heroku CLI
# Create app
heroku create opd-token-system

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis
heroku addons:create heroku-redis:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY="your-production-secret-key"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS="your-app.herokuapp.com"

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser
```

#### DigitalOcean App Platform

```yaml
# app.yaml
name: opd-token-system
services:
  - name: web
    github:
      repo: your-username/opd-token-system
      branch: main
    build_command: pip install -r requirements.txt
    run_command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    envs:
      - key: SECRET_KEY
        value: your-secret-key
      - key: DEBUG
        value: "False"
    
databases:
  - name: db
    engine: PG
    version: "15"
  
  - name: redis
    engine: REDIS
    version: "7"
```

#### AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 opd-token-system

# Create environment
eb create opd-production

# Deploy
eb deploy

# Set environment variables
eb setenv SECRET_KEY="your-key" DEBUG=False

# Open app
eb open
```

### Option 2: VPS (Ubuntu Server)

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install dependencies
sudo apt install python3-pip python3-venv postgresql postgresql-contrib redis-server nginx -y

# 3. Create project directory
sudo mkdir -p /var/www/opd_token_system
sudo chown $USER:$USER /var/www/opd_token_system
cd /var/www/opd_token_system

# 4. Clone repository
git clone your-repo-url .

# 5. Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# 6. Configure PostgreSQL
sudo -u postgres psql
CREATE DATABASE opd_tokens;
CREATE USER opduser WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE opd_tokens TO opduser;
\q

# 7. Configure environment
cp .env.example .env
nano .env  # Edit with production values

# 8. Run migrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser

# 9. Setup Gunicorn service
sudo nano /etc/systemd/system/opd.service
```

**Gunicorn Service File:**
```ini
[Unit]
Description=OPD Token System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/opd_token_system
Environment="PATH=/var/www/opd_token_system/venv/bin"
ExecStart=/var/www/opd_token_system/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/var/www/opd_token_system/opd.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Start Gunicorn
sudo systemctl start opd
sudo systemctl enable opd

# 10. Configure Nginx
sudo nano /etc/nginx/sites-available/opd
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/opd_token_system;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/opd_token_system/opd.sock;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/opd /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

# 11. Setup SSL with Let's Encrypt
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## Environment Configuration

### Production Settings

Create `.env` file with production values:

```bash
DEBUG=False
SECRET_KEY=your-very-long-random-secret-key-here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

DATABASE_NAME=opd_tokens
DATABASE_USER=opduser
DATABASE_PASSWORD=secure_database_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Generate Secret Key

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Database Setup

### PostgreSQL Backup

```bash
# Backup
pg_dump -U opduser opd_tokens > backup_$(date +%Y%m%d).sql

# Restore
psql -U opduser opd_tokens < backup_20260129.sql
```

### Redis Backup

```bash
# Redis automatically saves to dump.rdb
# Copy backup
sudo cp /var/lib/redis/dump.rdb /backup/redis_$(date +%Y%m%d).rdb
```

## Monitoring

### Application Logs

```bash
# Django logs
tail -f /var/log/gunicorn/error.log

# Nginx access logs
tail -f /var/log/nginx/access.log

# Nginx error logs
tail -f /var/log/nginx/error.log
```

### System Health

```bash
# Check Gunicorn status
sudo systemctl status opd

# Check Nginx status
sudo systemctl status nginx

# Check PostgreSQL status
sudo systemctl status postgresql

# Check Redis status
sudo systemctl status redis
```

### Setup Monitoring Tools

#### Prometheus + Grafana

```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# Configure prometheus.yml
nano prometheus.yml
```

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'opd-api'
    static_configs:
      - targets: ['localhost:8000']
```

#### Sentry for Error Tracking

```bash
pip install sentry-sdk

# Add to settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
)
```

## Performance Optimization

### Database Optimization

```sql
-- Create indexes
CREATE INDEX idx_tokens_slot_status ON tokens(slot_id, status);
CREATE INDEX idx_tokens_patient_date ON tokens(patient_id, created_at);
CREATE INDEX idx_slots_doctor_date ON slots(doctor_id, start_time);
```

### Redis Configuration

```bash
# Edit /etc/redis/redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### Gunicorn Workers

```bash
# Calculate workers: (2 x CPU cores) + 1
# For 4 CPU cores:
--workers 9
```

## Security Checklist

- [ ] Change SECRET_KEY in production
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Use HTTPS (SSL certificate)
- [ ] Setup firewall (UFW)
- [ ] Enable CSRF protection
- [ ] Use strong database passwords
- [ ] Restrict database access
- [ ] Setup rate limiting
- [ ] Enable Redis password auth
- [ ] Regular security updates
- [ ] Backup strategy in place
- [ ] Monitor logs for suspicious activity

## Firewall Configuration

```bash
# Allow SSH
sudo ufw allow 22

# Allow HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Enable firewall
sudo ufw enable
```

## Auto-scaling (Optional)

### AWS Auto Scaling

```bash
# Create launch template
aws ec2 create-launch-template \
  --launch-template-name opd-template \
  --version-description v1 \
  --launch-template-data file://template.json

# Create auto scaling group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name opd-asg \
  --launch-template LaunchTemplateName=opd-template \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 2
```

## Troubleshooting

### Common Issues

**502 Bad Gateway:**
- Check Gunicorn status: `sudo systemctl status opd`
- Check socket permissions: `ls -l /var/www/opd_token_system/opd.sock`
- Review error logs: `sudo journalctl -u opd -n 50`

**Database Connection Error:**
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify credentials in .env
- Test connection: `psql -U opduser -d opd_tokens`

**Redis Connection Error:**
- Check Redis is running: `sudo systemctl status redis`
- Test connection: `redis-cli ping`

## Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart Gunicorn
sudo systemctl restart opd
```

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration history
python manage.py showmigrations
```

---

**For additional help, refer to:**
- Django Deployment: https://docs.djangoproject.com/en/5.0/howto/deployment/
- PostgreSQL Docs: https://www.postgresql.org/docs/
- Redis Docs: https://redis.io/docs/
