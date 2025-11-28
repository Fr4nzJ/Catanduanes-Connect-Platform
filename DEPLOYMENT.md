# Deployment Guide for Catanduanes Connect

This guide provides detailed instructions for deploying Catanduanes Connect in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows
- **Memory**: Minimum 4GB RAM (8GB recommended for production)
- **Storage**: Minimum 10GB free space
- **Network**: Stable internet connection

### Software Requirements

- **Python**: 3.11+ with pip
- **Neo4j**: 5.12+ Community or Enterprise Edition
- **Redis**: 7.0+
- **Nginx**: 1.20+ (for production)
- **Docker**: 24.0+ (optional, for containerized deployment)
- **Docker Compose**: 2.0+ (optional)

### Domain & SSL (Production)

- Registered domain name
- SSL certificate (Let's Encrypt recommended)
- DNS management access

## Local Development

### 1. Environment Setup

```bash
# Clone repository
git clone https://github.com/yourusername/catanduanes-connect.git
cd catanduanes-connect

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development tools
```

### 2. Database Setup

#### Option A: Local Neo4j Installation

```bash
# Download and install Neo4j from https://neo4j.com/download/
# Or use package manager:
# Ubuntu: sudo apt install neo4j
# macOS: brew install neo4j

# Start Neo4j
sudo systemctl start neo4j  # Linux
neo4j start                 # macOS

# Set initial password
neo4j-admin set-initial-password password
```

#### Option B: Docker Neo4j

```bash
docker run -d \
  --name neo4j-dev \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS=["apoc"] \
  -v neo4j_data:/data \
  -v neo4j_logs:/logs \
  neo4j:5.12-community
```

### 3. Redis Setup

```bash
# Install Redis
# Ubuntu: sudo apt install redis-server
# macOS: brew install redis

# Start Redis
sudo systemctl start redis  # Linux
redis-server               # macOS

# Test connection
redis-cli ping
```

### 4. Environment Configuration

```bash
# Copy environment template
cp .env.template .env

# Edit .env file with your local settings
# Key variables to configure:
# - SECRET_KEY (generate random string)
# - NEO4J_URI=bolt://localhost:7687
# - NEO4J_USER=neo4j
# - NEO4J_PASSWORD=password
# - REDIS_URL=redis://localhost:6379/0
```

### 5. Database Initialization

```bash
# Initialize database schema and constraints
python -c "from database import init_db; init_db()"

# Seed with demo data
python seed.py
```

### 6. Run Development Server

```bash
# Option A: Flask development server
export FLASK_ENV=development
export FLASK_DEBUG=1
flask run --host=0.0.0.0 --port=5000

# Option B: Gunicorn (more production-like)
gunicorn --bind 0.0.0.0:5000 --reload app:create_app()
```

### 7. Access Application

- **Web Application**: http://localhost:5000
- **Neo4j Browser**: http://localhost:7474
- **API Documentation**: http://localhost:5000/api/docs

## Docker Deployment

### 1. Docker Setup

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Production Configuration

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  app:
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - SESSION_COOKIE_SECURE=true
    volumes:
      - ./static/uploads:/app/static/uploads:ro
    restart: always
    
  neo4j:
    environment:
      - NEO4J_dbms_memory_pagecache_size=1G
      - NEO4J_dbms_memory_heap_initial__size=1G
      - NEO4J_dbms_memory_heap_max__size=1G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    restart: always
    
  nginx:
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/ssl:/etc/nginx/ssl:ro
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    restart: always
```

### 3. SSL Certificate Setup

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Generate SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Copy certificates to Docker volume
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/nginx/ssl/
```

### 4. Deploy with Docker Compose

```bash
# Build and start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f app

# Scale services if needed
docker-compose up -d --scale celery-worker=3
```

### 5. Database Migration

```bash
# Initialize production database
docker-compose exec app python -c "from database import init_db; init_db()"

# Seed with initial data
docker-compose exec app python seed.py
```

## Production Deployment

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git nginx ufw fail2ban

# Configure firewall
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### 2. Application Deployment

#### Option A: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/catanduanes-connect.git
cd catanduanes-connect

# Configure environment
cp .env.template .env
# Edit .env with production settings

# Deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### Option B: Manual Deployment

```bash
# Create application user
sudo useradd -m -s /bin/bash catanduanes
sudo usermod -aG sudo catanduanes

# Install Python
sudo apt install python3 python3-pip python3-venv

# Setup application
sudo mkdir -p /opt/catanduanes-connect
sudo chown catanduanes:catanduanes /opt/catanduanes-connect

# Switch to application user
sudo su - catanduanes

# Setup application
git clone https://github.com/yourusername/catanduanes-connect.git
cd catanduanes-connect

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with production settings

# Setup Gunicorn service
sudo tee /etc/systemd/system/catanduanes-connect.service > /dev/null <<EOF
[Unit]
Description=Catanduanes Connect Flask App
After=network.target

[Service]
User=catanduanes
Group=catanduanes
WorkingDirectory=/opt/catanduanes-connect
Environment="PATH=/opt/catanduanes-connect/venv/bin"
ExecStart=/opt/catanduanes-connect/venv/bin/gunicorn --workers 4 --bind unix:catanduanes-connect.sock -m 007 app:create_app()
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl start catanduanes-connect
sudo systemctl enable catanduanes-connect
```

### 3. Nginx Configuration

Create `/etc/nginx/sites-available/catanduanes-connect`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://unpkg.com; font-src 'self' https://cdnjs.cloudflare.com; img-src 'self' data: https:; connect-src 'self' https://nominatim.openstreetmap.org; frame-ancestors 'none';" always;
    
    # Static files
    location /static/ {
        alias /opt/catanduanes-connect/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Uploads
    location /uploads/ {
        alias /opt/catanduanes-connect/static/uploads/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check
    location /health {
        proxy_pass http://unix:/opt/catanduanes-connect/catanduanes-connect.sock;
        access_log off;
    }
    
    # Main application
    location / {
        proxy_pass http://unix:/opt/catanduanes-connect/catanduanes-connect.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/catanduanes-connect /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### 5. Database Setup

```bash
# Install Neo4j
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable 5.0' | sudo tee -a /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j

# Configure Neo4j
sudo nano /etc/neo4j/neo4j.conf
# Set: dbms.memory.heap.initial_size=1g
# Set: dbms.memory.heap.max_size=1g
# Set: dbms.memory.pagecache.size=1g

# Start Neo4j
sudo systemctl start neo4j
sudo systemctl enable neo4j

# Install Redis
sudo apt install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
# Set: maxmemory 1gb
# Set: maxmemory-policy allkeys-lru

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis
```

## Cloud Deployment

### AWS Deployment

#### 1. EC2 Setup

```bash
# Launch EC2 instance (Ubuntu 20.04, t3.medium minimum)
# Configure security groups:
# - SSH (22): Your IP only
# - HTTP (80): 0.0.0.0/0
# - HTTPS (443): 0.0.0.0/0
```

#### 2. RDS for Neo4j (Alternative)

```bash
# Use AWS Neptune for managed graph database
# Or set up Neo4j on EC2
```

#### 3. ElastiCache for Redis

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
    --cache-cluster-id catanduanes-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1
```

#### 4. Application Load Balancer

```bash
# Create ALB for high availability
aws elbv2 create-load-balancer \
    --name catanduanes-alb \
    --subnets subnet-xxx subnet-yyy \
    --security-groups sg-xxx
```

### Google Cloud Platform

#### 1. Compute Engine

```bash
# Create instance
gcloud compute instances create catanduanes-app \
    --zone=asia-southeast1-a \
    --machine-type=e2-medium \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --tags=http-server,https-server
```

#### 2. Cloud Memorystore (Redis)

```bash
gcloud redis instances create catanduanes-redis \
    --size=1 \
    --tier=basic \
    --region=asia-southeast1
```

### DigitalOcean

#### 1. Droplet Setup

```bash
# Create droplet (minimum 2GB RAM)
# Use Marketplace: Docker or Ubuntu
```

#### 2. Managed Database

```bash
# Create managed Redis cluster
doctl databases create catanduanes-redis --engine redis --region sgp1 --size db-s-1vcpu-1gb
```

## Monitoring & Maintenance

### 1. Health Checks

```bash
# Application health
curl -f http://yourdomain.com/health

# Database health
curl -f http://yourdomain.com/api/health/db

# Redis health
curl -f http://yourdomain.com/api/health/redis
```

### 2. Log Monitoring

```bash
# View application logs
docker-compose logs -f app

# View error logs
tail -f logs/error.log

# Monitor system resources
htop
iostat -x 1
```

### 3. Backup Strategy

#### Database Backup

```bash
# Neo4j backup
docker exec neo4j neo4j-admin backup --backup-dir=/backups --name=catanduanes-backup

# Redis backup
docker exec redis redis-cli BGSAVE
```

#### File Backup

```bash
# Backup uploads
rsync -avz /opt/catanduanes-connect/static/uploads/ backup-server:/backups/uploads/

# Backup configuration
rsync -avz /opt/catanduanes-connect/.env backup-server:/backups/config/
```

### 4. Security Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d

# Update SSL certificates
sudo certbot renew
```

## Troubleshooting

### Common Issues

#### 1. Database Connection

**Problem**: Cannot connect to Neo4j
```bash
# Check Neo4j status
sudo systemctl status neo4j

# Check logs
sudo tail -f /var/log/neo4j/neo4j.log

# Test connection
cypher-shell -u neo4j -p password
```

#### 2. Redis Connection

**Problem**: Cannot connect to Redis
```bash
# Check Redis status
sudo systemctl status redis

# Test connection
redis-cli ping

# Check configuration
sudo nano /etc/redis/redis.conf
```

#### 3. Application Not Starting

**Problem**: Gunicorn fails to start
```bash
# Check service status
sudo systemctl status catanduanes-connect

# View logs
sudo journalctl -u catanduanes-connect -f

# Test manually
cd /opt/catanduanes-connect
source venv/bin/activate
gunicorn --bind 0.0.0.0:5000 app:create_app()
```

#### 4. Permission Issues

```bash
# Fix file permissions
sudo chown -R catanduanes:catanduanes /opt/catanduanes-connect
sudo chmod -R 755 /opt/catanduanes-connect

# Fix socket permissions
sudo chmod 660 /opt/catanduanes-connect/catanduanes-connect.sock
```

### Performance Optimization

#### 1. Database Optimization

```bash
# Neo4j memory configuration
echo "dbms.memory.heap.initial_size=2g" >> /etc/neo4j/neo4j.conf
echo "dbms.memory.heap.max_size=2g" >> /etc/neo4j/neo4j.conf
echo "dbms.memory.pagecache.size=2g" >> /etc/neo4j/neo4j.conf

# Create indexes
cypher-shell -u neo4j -p password <<EOF
CREATE INDEX user_email IF NOT EXISTS FOR (u:User) ON (u.email);
CREATE INDEX business_name IF NOT EXISTS FOR (b:Business) ON (b.name);
CREATE INDEX job_title IF NOT EXISTS FOR (j:Job) ON (j.title);
EOF
```

#### 2. Application Optimization

```python
# config.py
class ProductionConfig(Config):
    # Enable caching
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')
    
    # Optimize database connections
    DATABASE_CONNECTION_POOL_SIZE = 20
    DATABASE_CONNECTION_MAX_OVERFLOW = 30
    
    # Enable compression
    COMPRESS_ALGORITHM = 'gzip'
```

#### 3. Nginx Optimization

```nginx
# /etc/nginx/nginx.conf
http {
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Cache settings
    open_file_cache max=1000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
}
```

### Scaling

#### Horizontal Scaling

```bash
# Load balancer configuration
upstream catanduanes_backend {
    server 10.0.1.10:5000 weight=3;
    server 10.0.1.11:5000 weight=2;
    server 10.0.1.12:5000 weight=1;
}

server {
    location / {
        proxy_pass http://catanduanes_backend;
    }
}
```

#### Vertical Scaling

```bash
# Increase Gunicorn workers
workers = multiprocessing.cpu_count() * 2 + 1

# Increase worker connections
worker_connections = 1000
```

## Support

For deployment support:
- Check application logs: `logs/app.log`
- Review system logs: `/var/log/syslog`
- Monitor resource usage: `htop`, `iostat`
- Check service status: `systemctl status catanduanes-connect`

For additional help, create an issue in the GitHub repository or contact the development team.