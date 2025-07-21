# Deployment Guide

## 🚀 Production Deployment Options

### 1. Docker Deployment (Recommended)

#### Dockerfile
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads chroma_db logs

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  pdf-qa-app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./chroma_db:/app/chroma_db
      - ./logs:/app/logs
      - ./documents_metadata.json:/app/documents_metadata.json
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
      - ALLOWED_ORIGINS=["https://yourdomain.com"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - pdf-qa-app
    restart: unless-stopped
```

#### Build and Deploy
```bash
# Build the image
docker build -t pdf-qa-app .

# Run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f pdf-qa-app
```

### 2. Traditional Server Deployment

#### Prerequisites
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx

# CentOS/RHEL
sudo yum update
sudo yum install python3 python3-pip nginx
```

#### Application Setup
```bash
# Create application user
sudo adduser --system --group pdfqa

# Clone application
sudo -u pdfqa git clone <repo> /opt/pdf-qa-app
cd /opt/pdf-qa-app

# Setup virtual environment
sudo -u pdfqa python3 -m venv venv
sudo -u pdfqa ./venv/bin/pip install -r requirements.txt

# Create directories
sudo -u pdfqa mkdir -p uploads chroma_db logs

# Set permissions
sudo chown -R pdfqa:pdfqa /opt/pdf-qa-app
```

#### Systemd Service
```ini
# /etc/systemd/system/pdf-qa-app.service
[Unit]
Description=PDF QA Application
After=network.target

[Service]
Type=exec
User=pdfqa
Group=pdfqa
WorkingDirectory=/opt/pdf-qa-app
Environment=PATH=/opt/pdf-qa-app/venv/bin
ExecStart=/opt/pdf-qa-app/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

#### Start Service
```bash
# Enable and start service
sudo systemctl enable pdf-qa-app
sudo systemctl start pdf-qa-app

# Check status
sudo systemctl status pdf-qa-app
sudo journalctl -u pdf-qa-app -f
```

### 3. Cloud Platform Deployment

#### Heroku
```yaml
# app.json
{
  "name": "PDF QA App",
  "description": "PDF Question-Answering Application",
  "image": "heroku/python",
  "buildpacks": [
    {
      "url": "heroku/python"
    }
  ],
  "env": {
    "DEBUG": {
      "value": "false"
    },
    "ALLOWED_ORIGINS": {
      "value": "[\"https://yourapp.herokuapp.com\"]"
    }
  },
  "formation": {
    "web": {
      "quantity": 1,
      "size": "basic"
    }
  }
}
```

```bash
# Procfile
web: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
```

#### AWS EC2
```bash
# User data script for EC2 instance
#!/bin/bash
yum update -y
yum install -y python3 python3-pip git nginx

# Clone and setup application
cd /opt
git clone <repo> pdf-qa-app
cd pdf-qa-app

python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# Setup systemd service (use service file above)
cp pdf-qa-app.service /etc/systemd/system/
systemctl enable pdf-qa-app
systemctl start pdf-qa-app
```

#### Google Cloud Run
```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/pdf-qa-app', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/pdf-qa-app']
  - name: 'gcr.io/cloud-builders/gcloud'
    args: [
      'run', 'deploy', 'pdf-qa-app',
      '--image', 'gcr.io/$PROJECT_ID/pdf-qa-app',
      '--region', 'us-central1',
      '--platform', 'managed',
      '--allow-unauthenticated'
    ]
```

## 🔧 Nginx Configuration

### Basic Configuration
```nginx
# /etc/nginx/sites-available/pdf-qa-app
server {
    listen 80;
    server_name yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # File upload size
    client_max_body_size 50M;

    # Backend proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for large file uploads
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Enable Configuration
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/pdf-qa-app /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

## 🔒 Security Configuration

### Environment Variables
```bash
# Production environment variables
export DEBUG=false
export ALLOWED_ORIGINS='["https://yourdomain.com"]'
export LOG_LEVEL=WARNING
export MAX_FILE_SIZE=52428800

# Database URLs (if using external services)
export CHROMA_DB_URL=postgresql://user:pass@host:port/db
```

### Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# iptables
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP  # Block direct access
```

### SSL/TLS Setup
```bash
# Let's Encrypt (Certbot)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Application Security
```python
# In main.py, add security middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com"])
app.add_middleware(HTTPSRedirectMiddleware)
```

## 📊 Monitoring and Logging

### Application Monitoring
```python
# Add health checks and metrics
from prometheus_client import Counter, Histogram, generate_latest

upload_counter = Counter('pdf_uploads_total', 'Total PDF uploads')
question_counter = Counter('questions_total', 'Total questions asked')
response_time = Histogram('response_time_seconds', 'Response time')

@app.get("/metrics")
async def metrics():
    return generate_latest()
```

### Log Management
```bash
# Logrotate configuration
# /etc/logrotate.d/pdf-qa-app
/opt/pdf-qa-app/logs/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    create 644 pdfqa pdfqa
    postrotate
        systemctl reload pdf-qa-app
    endscript
}
```

### System Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Monitor application
htop  # CPU and memory usage
iotop  # Disk I/O
nethogs  # Network usage

# Check logs
sudo journalctl -u pdf-qa-app -f
tail -f /opt/pdf-qa-app/logs/app.log
```

## 🔄 Backup and Recovery

### Data Backup
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/pdf-qa-app"

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup files
cp -r /opt/pdf-qa-app/uploads "$BACKUP_DIR/$DATE/"
cp -r /opt/pdf-qa-app/chroma_db "$BACKUP_DIR/$DATE/"
cp /opt/pdf-qa-app/documents_metadata.json "$BACKUP_DIR/$DATE/"

# Compress
tar -czf "$BACKUP_DIR/pdf-qa-app-$DATE.tar.gz" -C "$BACKUP_DIR" "$DATE"
rm -rf "$BACKUP_DIR/$DATE"

# Keep only 30 days of backups
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

### Automated Backup
```bash
# Add to crontab
sudo crontab -e
# Add: 0 2 * * * /opt/scripts/backup.sh
```

### Disaster Recovery
```bash
#!/bin/bash
# restore.sh
BACKUP_FILE=$1
RESTORE_DIR="/opt/pdf-qa-app"

# Stop application
sudo systemctl stop pdf-qa-app

# Extract backup
tar -xzf "$BACKUP_FILE" -C /tmp/

# Restore files
cp -r /tmp/pdf-qa-app-*/uploads "$RESTORE_DIR/"
cp -r /tmp/pdf-qa-app-*/chroma_db "$RESTORE_DIR/"
cp /tmp/pdf-qa-app-*/documents_metadata.json "$RESTORE_DIR/"

# Fix permissions
sudo chown -R pdfqa:pdfqa "$RESTORE_DIR"

# Start application
sudo systemctl start pdf-qa-app
```

## 🚦 Performance Optimization

### Application Tuning
```python
# In main.py
# Increase worker processes for CPU-bound tasks
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # Adjust based on CPU cores
        loop="uvloop",  # Faster event loop
        access_log=False  # Disable in production
    )
```

### Database Optimization
```python
# In vector_store.py
# Optimize ChromaDB settings
self.client = chromadb.PersistentClient(
    path=self.persist_directory,
    settings=Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=self.persist_directory,
        anonymized_telemetry=False
    )
)
```

### Caching
```python
# Add Redis caching for frequently asked questions
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_response(expiry=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"qa:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expiry, json.dumps(result))
            return result
        return wrapper
    return decorator
```

## 📈 Scaling Considerations

### Horizontal Scaling
- Use load balancer (nginx, HAProxy, or cloud load balancer)
- Shared storage for uploads and vector database
- Session affinity not required (stateless application)

### Vertical Scaling
- Increase CPU for faster text processing
- Increase RAM for larger models and more workers
- SSD storage for faster vector database operations

### External Services
- Use cloud storage (S3, Google Cloud Storage) for PDF files
- Consider managed vector databases (Pinecone, Weaviate)
- Use external AI services (OpenAI, Anthropic) for better answers

## 🔍 Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check memory usage
   free -h
   sudo systemctl status pdf-qa-app
   
   # Solutions:
   # - Reduce worker count
   # - Use smaller embedding model
   # - Implement pagination for large responses
   ```

2. **Slow Response Times**
   ```bash
   # Check CPU usage
   top
   
   # Solutions:
   # - Increase worker count
   # - Use faster storage (SSD)
   # - Optimize database queries
   ```

3. **Upload Failures**
   ```bash
   # Check disk space
   df -h
   
   # Check file permissions
   ls -la uploads/
   
   # Solutions:
   # - Increase disk space
   # - Fix file permissions
   # - Check nginx upload limits
   ```

### Log Analysis
```bash
# Check application logs
grep "ERROR" /opt/pdf-qa-app/logs/app.log
grep "upload" /opt/pdf-qa-app/logs/app.log | tail -100

# Check system logs
sudo journalctl -u pdf-qa-app --since "1 hour ago"

# Check nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```