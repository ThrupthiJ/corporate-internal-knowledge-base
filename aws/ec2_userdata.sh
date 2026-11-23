#!/bin/bash
# ==============================================================================
# AWS EC2 Bootstrap User Data Script - Corporate Internal Knowledge Base
# Target OS: Ubuntu 22.04 / 24.04 LTS or Amazon Linux 2023
# ==============================================================================

set -e
echo "[+] Starting EC2 Knowledge Base Application Provisioning..."

# Update OS packages
apt-get update -y || yum update -y
apt-get install -y python3 python3-pip python3-venv git nginx sqlite3 || yum install -y python3 python3-pip git nginx sqlite3

# Create application directory
APP_DIR="/opt/cloud-kb-app"
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Clone or copy application code
# (Alternatively unpack app bundle or pull from git)
echo "[+] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install flask boto3 python-dotenv werkzeug gunicorn

# Configure Environment Variables
cat << 'EOF' > "$APP_DIR/.env"
FLASK_ENV=production
SECRET_KEY=corporate-kb-super-secret-key-2026-prod
S3_BUCKET_NAME=corporate-knowledge-base-store
AWS_DEFAULT_REGION=us-east-1
STORAGE_BACKEND=s3
PORT=5000
EOF

# Create Systemd Service for Auto-start
cat << 'EOF' > /etc/systemd/system/cloud-kb.service
[Unit]
Description=Corporate Internal Knowledge Base Web Application
After=network.target

[Service]
User=root
WorkingDirectory=/opt/cloud-kb-app
Environment="PATH=/opt/cloud-kb-app/venv/bin"
ExecStart=/opt/cloud-kb-app/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
systemctl daemon-reload
systemctl enable cloud-kb.service
systemctl start cloud-kb.service || echo "App code pending copy"

# Configure Nginx Reverse Proxy
cat << 'EOF' > /etc/nginx/sites-available/cloud-kb
server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/cloud-kb /etc/nginx/sites-enabled/default || true
systemctl restart nginx

echo "[+] Corporate Internal Knowledge Base provisioning completed successfully!"
