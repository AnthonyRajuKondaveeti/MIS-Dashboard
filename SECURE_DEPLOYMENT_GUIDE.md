# Secure AWS EC2 Deployment Guide

**Date:** February 3, 2026  
**Instance Type:** t3.micro (Ubuntu)  
**Security Focus:** Multi-instance account protection

---

## 🔐 Security-First Deployment for Shared AWS Account

Since you have other instances in your AWS account, we'll implement **strict security isolation**.

---

## Phase 1: Secure Your EC2 Instance (30 minutes)

### Step 1.1: Configure Security Group (CRITICAL)

**Create a dedicated Security Group for this application:**

1. **Go to EC2 Console → Security Groups → Create Security Group**
   - Name: `welleazy-mis-sg`
   - Description: `Welleazy MIS Application - Isolated`
   - VPC: Select your VPC

2. **Inbound Rules (Minimal Access):**

   ```
   Type        | Protocol | Port  | Source           | Description
   ------------|----------|-------|------------------|------------------
   SSH         | TCP      | 22    | YOUR_IP_ONLY     | Your office/home IP
   HTTP        | TCP      | 80    | 0.0.0.0/0        | Nginx (public access)
   HTTPS       | TCP      | 443   | 0.0.0.0/0        | SSL traffic
   Custom TCP  | TCP      | 8501  | 127.0.0.1/32     | Streamlit (localhost only)
   ```

   **⚠️ IMPORTANT:**
   - Replace `YOUR_IP_ONLY` with your actual IP address
   - Port 8501 should ONLY be accessible from localhost (127.0.0.1/32)
   - Never expose 8501 to 0.0.0.0/0 in production

3. **Outbound Rules:**

   ```
   Type        | Protocol | Port  | Destination | Description
   ------------|----------|-------|-------------|------------------
   All traffic | All      | All   | 0.0.0.0/0   | Allow updates
   ```

4. **Attach Security Group to Your Instance:**
   - Go to EC2 → Instances → Select your instance
   - Actions → Security → Change Security Groups
   - Add `welleazy-mis-sg`
   - Remove default security group if present

---

### Step 1.2: Set Up SSH Access Securely

**On your Windows machine:**

```powershell
# Move your .pem file to a secure location
mkdir C:\Users\YourUsername\.ssh
move Downloads\your-key.pem C:\Users\YourUsername\.ssh\

# Set restrictive permissions (Windows)
icacls C:\Users\YourUsername\.ssh\your-key.pem /inheritance:r
icacls C:\Users\YourUsername\.ssh\your-key.pem /grant:r "%USERNAME%:R"
```

**Test SSH connection:**

```powershell
# Get your EC2 public IP from AWS Console
ssh -i C:\Users\YourUsername\.ssh\your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

---

## Phase 2: System Setup & Hardening (20 minutes)

### Step 2.1: Initial System Configuration

**Once connected via SSH:**

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install security updates automatically
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure --priority=low unattended-upgrades

# Create dedicated app user (security best practice)
sudo adduser --system --group --disabled-password welleazy
sudo usermod -aG sudo welleazy
```

---

### Step 2.2: Install Required Software

```bash
# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install Nginx (reverse proxy)
sudo apt install nginx -y

# Install certbot for SSL certificates
sudo apt install certbot python3-certbot-nginx -y

# Install git
sudo apt install git -y

# Install firewall
sudo apt install ufw -y
```

---

### Step 2.3: Configure Firewall (UFW)

```bash
# Enable firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (ONLY from your IP - replace with your IP)
sudo ufw allow from YOUR_IP_ADDRESS to any port 22

# Allow HTTP/HTTPS for everyone
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

---

## Phase 3: Application Deployment (25 minutes)

### Step 3.1: Create Application Directory

```bash
# Switch to welleazy user
sudo su - welleazy

# Create app directory
mkdir -p /home/welleazy/welleazy-mis
cd /home/welleazy/welleazy-mis

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate
```

---

### Step 3.2: Upload Application Files

**Option A: Using SCP (from your Windows machine):**

```powershell
# Upload all files
scp -i C:\Users\YourUsername\.ssh\your-key.pem -r "d:\Downloads\Welleazy MIS\*" ubuntu@YOUR_EC2_IP:/tmp/welleazy-temp/

# Then on EC2, move files
ssh -i C:\Users\YourUsername\.ssh\your-key.pem ubuntu@YOUR_EC2_IP
sudo mv /tmp/welleazy-temp/* /home/welleazy/welleazy-mis/
sudo chown -R welleazy:welleazy /home/welleazy/welleazy-mis/
```

**Option B: Using Git (Recommended):**

```bash
# If you have a private Git repository
cd /home/welleazy/welleazy-mis
git clone https://YOUR_GIT_REPO .

# Or initialize and push from local
# (Do this from your Windows machine first)
```

---

### Step 3.3: Install Python Dependencies

```bash
# Activate virtual environment
cd /home/welleazy/welleazy-mis
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r welleazy_requirements.txt

# Verify installation
pip list
```

---

## Phase 4: Secure Configuration (20 minutes)

### Step 4.1: Set Up Secrets Management

**NEVER include config_auth.yaml in production!**

```bash
# Create Streamlit secrets directory
mkdir -p /home/welleazy/welleazy-mis/.streamlit
nano /home/welleazy/welleazy-mis/.streamlit/secrets.toml
```

**Add this content (replace with your actual credentials):**

```toml
# Streamlit Secrets - Production
[credentials]

[credentials.usernames.admin]
email = "admin@welleazy.com"
name = "Admin User"
password = "$2b$12$YOUR_BCRYPT_HASH_HERE"

[credentials.usernames.user1]
email = "user1@welleazy.com"
name = "Regular User"
password = "$2b$12$ANOTHER_BCRYPT_HASH_HERE"

[cookie]
expiry_days = 30
key = "YOUR_RANDOM_SECRET_KEY_HERE"
name = "welleazy_auth_cookie"
```

**Generate bcrypt password hashes:**

```bash
python3 -c "import bcrypt; print(bcrypt.hashpw('YOUR_PASSWORD'.encode(), bcrypt.gensalt()).decode())"
```

**Generate secret key:**

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Secure the secrets file:**

```bash
chmod 600 /home/welleazy/welleazy-mis/.streamlit/secrets.toml
chown welleazy:welleazy /home/welleazy/welleazy-mis/.streamlit/secrets.toml
```

---

### Step 4.2: Remove Sensitive Files

```bash
# Remove any local config files (IMPORTANT)
cd /home/welleazy/welleazy-mis
rm -f config_auth.yaml
rm -f *.csv  # Remove any test data
rm -rf __pycache__
rm -rf output/

# Create necessary directories
mkdir -p logs
```

---

## Phase 5: Run Application as Service (30 minutes)

### Step 5.1: Create Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/welleazy-mis.service
```

**Add this content:**

```ini
[Unit]
Description=Welleazy MIS Streamlit Application
After=network.target

[Service]
Type=simple
User=welleazy
Group=welleazy
WorkingDirectory=/home/welleazy/welleazy-mis
Environment="PATH=/home/welleazy/welleazy-mis/venv/bin"
ExecStart=/home/welleazy/welleazy-mis/venv/bin/streamlit run welleazy_streamlit_app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true

Restart=always
RestartSec=10
StandardOutput=append:/home/welleazy/welleazy-mis/logs/app.log
StandardError=append:/home/welleazy/welleazy-mis/logs/error.log

[Install]
WantedBy=multi-user.target
```

**Enable and start service:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable welleazy-mis

# Start service
sudo systemctl start welleazy-mis

# Check status
sudo systemctl status welleazy-mis

# View logs
tail -f /home/welleazy/welleazy-mis/logs/app.log
```

---

### Step 5.2: Configure Nginx Reverse Proxy

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/welleazy-mis
```

**Add this configuration:**

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Increase timeouts for large file uploads
    client_max_body_size 50M;
    proxy_connect_timeout 600;
    proxy_send_timeout 600;
    proxy_read_timeout 600;
    send_timeout 600;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;

        # WebSocket support for Streamlit
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Forward real IP
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /healthz {
        access_log off;
        return 200 "healthy\n";
    }
}
```

**Enable the site:**

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/welleazy-mis /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

### Step 5.3: Set Up SSL Certificate (HTTPS)

**If you have a domain name:**

```bash
# Replace your-domain.com with your actual domain
sudo certbot --nginx -d your-domain.com

# Follow the prompts:
# - Enter your email
# - Agree to terms
# - Choose to redirect HTTP to HTTPS (recommended)

# Test auto-renewal
sudo certbot renew --dry-run
```

**If you don't have a domain (temporary solution):**

```bash
# Generate self-signed certificate (for testing only)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/nginx-selfsigned.key \
  -out /etc/ssl/certs/nginx-selfsigned.crt

# Update Nginx config to use SSL
sudo nano /etc/nginx/sites-available/welleazy-mis

# Add SSL configuration (after listen 80;):
# listen 443 ssl;
# ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
# ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;
```

---

## Phase 6: Monitoring & Maintenance (15 minutes)

### Step 6.1: Set Up Log Rotation

```bash
sudo nano /etc/logrotate.d/welleazy-mis
```

**Add:**

```
/home/welleazy/welleazy-mis/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    create 0640 welleazy welleazy
}
```

---

### Step 6.2: Create Monitoring Script

```bash
nano /home/welleazy/monitor.sh
```

**Add:**

```bash
#!/bin/bash
# Quick health check script

echo "=== Welleazy MIS Health Check ==="
echo "Date: $(date)"
echo ""

echo "Service Status:"
sudo systemctl status welleazy-mis --no-pager | grep Active

echo ""
echo "Memory Usage:"
free -h

echo ""
echo "Disk Usage:"
df -h /

echo ""
echo "Last 10 Application Logs:"
tail -n 10 /home/welleazy/welleazy-mis/logs/app.log

echo ""
echo "Nginx Status:"
sudo systemctl status nginx --no-pager | grep Active
```

**Make executable:**

```bash
chmod +x /home/welleazy/monitor.sh
```

---

## Phase 7: Testing & Verification (10 minutes)

### Step 7.1: Verify Deployment

```bash
# 1. Check service is running
sudo systemctl status welleazy-mis

# 2. Check Nginx is running
sudo systemctl status nginx

# 3. Test local access
curl http://localhost:8501

# 4. Check firewall rules
sudo ufw status

# 5. Test from your browser
# Open: http://YOUR_EC2_PUBLIC_IP
# Or: https://your-domain.com (if SSL configured)
```

---

### Step 7.2: Security Verification Checklist

```bash
# ✓ Verify port 8501 is NOT exposed publicly
sudo netstat -tulpn | grep 8501
# Should show: 127.0.0.1:8501 (localhost only)

# ✓ Verify secrets file permissions
ls -la /home/welleazy/welleazy-mis/.streamlit/secrets.toml
# Should show: -rw------- (600)

# ✓ Verify no config_auth.yaml exists
ls -la /home/welleazy/welleazy-mis/config_auth.yaml
# Should show: No such file or directory

# ✓ Verify firewall is active
sudo ufw status
# Should show: Status: active
```

---

## Phase 8: Post-Deployment Security (Ongoing)

### Step 8.1: Create Backup Script

```bash
nano /home/welleazy/backup.sh
```

**Add:**

```bash
#!/bin/bash
BACKUP_DIR="/home/welleazy/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup secrets (encrypted)
tar -czf $BACKUP_DIR/secrets_$DATE.tar.gz \
  /home/welleazy/welleazy-mis/.streamlit/secrets.toml

# Backup application code
tar -czf $BACKUP_DIR/app_$DATE.tar.gz \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='logs' \
  /home/welleazy/welleazy-mis/

# Keep only last 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

**Schedule daily backups:**

```bash
chmod +x /home/welleazy/backup.sh
crontab -e

# Add this line:
0 2 * * * /home/welleazy/backup.sh >> /home/welleazy/backup.log 2>&1
```

---

### Step 8.2: Enable CloudWatch Monitoring (Optional)

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure IAM role for EC2 instance
# Go to EC2 Console → Instances → Actions → Security → Modify IAM role
# Attach role: CloudWatchAgentServerRole
```

---

## 🚨 Troubleshooting

### Issue: Cannot connect via SSH

```bash
# Check security group allows your IP on port 22
# Verify .pem file permissions
# Try verbose mode: ssh -vvv -i your-key.pem ubuntu@YOUR_IP
```

### Issue: Application not loading

```bash
# Check service status
sudo systemctl status welleazy-mis

# View error logs
tail -f /home/welleazy/welleazy-mis/logs/error.log

# Restart service
sudo systemctl restart welleazy-mis
```

### Issue: 502 Bad Gateway (Nginx)

```bash
# Check Streamlit is running on 127.0.0.1:8501
curl http://127.0.0.1:8501

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Restart both services
sudo systemctl restart welleazy-mis nginx
```

### Issue: Permission denied

```bash
# Fix ownership
sudo chown -R welleazy:welleazy /home/welleazy/welleazy-mis/

# Fix secrets permissions
chmod 600 /home/welleazy/welleazy-mis/.streamlit/secrets.toml
```

---

## 📋 Quick Command Reference

```bash
# Service Management
sudo systemctl start welleazy-mis      # Start app
sudo systemctl stop welleazy-mis       # Stop app
sudo systemctl restart welleazy-mis    # Restart app
sudo systemctl status welleazy-mis     # Check status

# View Logs
tail -f /home/welleazy/welleazy-mis/logs/app.log    # App logs
tail -f /var/log/nginx/access.log                    # Nginx access
tail -f /var/log/nginx/error.log                     # Nginx errors

# Update Application
cd /home/welleazy/welleazy-mis
source venv/bin/activate
git pull  # If using Git
pip install -r welleazy_requirements.txt
sudo systemctl restart welleazy-mis

# Security
sudo ufw status                        # Check firewall
sudo fail2ban-client status            # Check fail2ban (if installed)
```

---

## 🎯 Final Security Checklist

- [ ] Security Group configured with minimal access
- [ ] SSH restricted to your IP only
- [ ] Port 8501 only accessible from localhost
- [ ] UFW firewall enabled and configured
- [ ] Application running as non-root user (welleazy)
- [ ] Secrets stored in .streamlit/secrets.toml with 600 permissions
- [ ] No config_auth.yaml in production
- [ ] SSL certificate configured (HTTPS)
- [ ] Log rotation configured
- [ ] Automatic security updates enabled
- [ ] Backups scheduled
- [ ] Monitoring script created

---

## 🚀 Access Your Application

**Production URL:**

- HTTP: `http://YOUR_EC2_PUBLIC_IP`
- HTTPS: `https://your-domain.com` (if configured)

**Default Credentials:**

- Use the credentials you set in `.streamlit/secrets.toml`

---

## 📞 Support

If you encounter issues:

1. Check logs: `tail -f /home/welleazy/welleazy-mis/logs/app.log`
2. Verify service: `sudo systemctl status welleazy-mis`
3. Check firewall: `sudo ufw status`
4. Test locally: `curl http://127.0.0.1:8501`

---

**Deployment completed! Your application is now securely running on AWS EC2.**
