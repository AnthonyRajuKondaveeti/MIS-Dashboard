# Fresh EC2 Deployment Guide - Welleazy MIS Dashboard

## Prerequisites Checklist
- ✅ AWS Account with EC2 access
- ✅ SSH Key: `C:\Users\dell\.ssh\MIS_Key.pem`
- ✅ Code Repository: https://github.com/AnthonyRajuKondaveeti/MIS-Dashboard.git
- ✅ Local Code: `D:\Downloads\Welleazy MIS\`
- ✅ secrets.toml file ready
- ✅ .env file with API endpoint ready

---

## Phase 1: Create New EC2 Instance

### Step 1: Launch Instance (AWS Console)
1. Go to **AWS Console** → **EC2** → **Launch Instance**
2. Configure instance:
   - **Name**: `welleazy-mis-server` (or your preferred name)
   - **AMI**: Ubuntu Server 24.04 LTS (64-bit x86)
   - **Instance Type**: t3.micro (1 vCPU, 1 GB RAM)
   - **Key Pair**: Select your existing key pair or create new
     - If creating new: Download and save to `C:\Users\dell\.ssh\`

### Step 2: Configure Security Group
Create a new security group with these rules:

**Inbound Rules:**
```
Type            Protocol    Port Range    Source          Description
SSH             TCP         22            0.0.0.0/0       SSH access
HTTP            TCP         80            0.0.0.0/0       Web access
HTTPS           TCP         443           0.0.0.0/0       SSL access (future)
```

**Outbound Rules:**
```
All traffic     All         All           0.0.0.0/0       Allow all outbound
```

### Step 3: Configure Storage
- **Storage**: 8 GB (default) or increase to 16-30 GB for more space
- **Volume Type**: gp3 (General Purpose SSD)

### Step 4: Launch Instance
1. Click **Launch Instance**
2. Wait for instance state: **Running**
3. **IMPORTANT**: Note down these details:
   - **Instance ID**: (e.g., i-0123456789abcdef0)
   - **Public IPv4 Address**: (e.g., 13.234.xxx.xxx)
   - **Security Group ID**: (e.g., sg-0123456789abcdef0)

---

## Phase 2: Initial Server Setup

### Step 5: Connect via SSH
```powershell
# Test SSH connection
C:\Windows\System32\OpenSSH\ssh.exe -i "C:\Users\dell\.ssh\MIS_Key.pem" ubuntu@YOUR_NEW_IP
```

**If you get permission denied error:**
```powershell
# Fix key permissions (Windows)
icacls "C:\Users\dell\.ssh\MIS_Key.pem" /inheritance:r
icacls "C:\Users\dell\.ssh\MIS_Key.pem" /grant:r "%USERNAME%:R"
```

### Step 6: Update System
```bash
# Update package list
sudo apt update

# Upgrade packages
sudo apt upgrade -y

# Install essential tools
sudo apt install -y build-essential git curl
```

### Step 7: Install Python 3.12
```bash
# Install Python 3.12
sudo apt install -y python3.12 python3.12-venv python3-pip

# Verify installation
python3 --version  # Should show Python 3.12.x
```

### Step 8: Install Nginx
```bash
# Install Nginx
sudo apt install -y nginx

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Check status
sudo systemctl status nginx
```

---

## Phase 3: Application Deployment

### Step 9: Create Dedicated User
```bash
# Create welleazy user (nologin for security)
sudo useradd -r -s /usr/sbin/nologin welleazy

# Create application directory
sudo mkdir -p /home/welleazy/welleazy-mis
sudo chown -R welleazy:welleazy /home/welleazy
```

### Step 10: Upload Application Files (Direct from Local)
**Exit SSH and run from local Windows PowerShell:**

```powershell
# Navigate to local project
cd "D:\Downloads\Welleazy MIS"

# Upload all Python files
$files = @(
    "welleazy_streamlit_app.py",
    "welleazy_pipeline.py",
    "welleazy_config.py",
    "welleazy_normalization.py",
    "welleazy_validation.py",
    "welleazy_daily_mis.py",
    "welleazy_tat_mis.py",
    "welleazy_pending_mis.py",
    "welleazy_closure_tat_mis.py",
    "veriright_pipeline.py",
    "veriright_config.py",
    "veriright_normalization.py",
    "veriright_daily_mis.py",
    "veriright_reports.py",
    "requirements.txt",
    ".env"
)

foreach ($file in $files) {
    C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\MIS_Key.pem" $file ubuntu@YOUR_NEW_IP:/tmp/
    Write-Host "Uploaded: $file"
}

# Upload secrets.toml
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\MIS_Key.pem" .streamlit\secrets.toml ubuntu@YOUR_NEW_IP:/tmp/
Write-Host "Uploaded: secrets.toml"

Write-Host "`nAll files uploaded successfully!"
```

**Alternative: Upload all files at once**
```powershell
# Single command to upload all Python files
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\MIS_Key.pem" *.py requirements.txt .env ubuntu@YOUR_NEW_IP:/tmp/

# Upload secrets.toml separately
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\MIS_Key.pem" .streamlit\secrets.toml ubuntu@YOUR_NEW_IP:/tmp/
```

### Step 11: Setup Application Directory
**SSH back into server:**

```bash
# Move files to application directory
sudo mv /tmp/welleazy_*.py /home/welleazy/welleazy-mis/
sudo mv /tmp/veriright_*.py /home/welleazy/welleazy-mis/
sudo mv /tmp/requirements.txt /home/welleazy/welleazy-mis/
sudo mv /tmp/.env /home/welleazy/welleazy-mis/

# Create .streamlit directory
sudo mkdir -p /home/welleazy/welleazy-mis/.streamlit
sudo mv /tmp/secrets.toml /home/welleazy/welleazy-mis/.streamlit/

# Set permissions
sudo chown -R welleazy:welleazy /home/welleazy/welleazy-mis
sudo chmod 600 /home/welleazy/welleazy-mis/.streamlit/secrets.toml
```

### Step 12: Create Python Virtual Environment
```bash
# Create venv
sudo -u welleazy python3 -m venv /home/welleazy/welleazy-mis/venv

# Activate and install dependencies
sudo -u welleazy /home/welleazy/welleazy-mis/venv/bin/pip install --upgrade pip
sudo -u welleazy /home/welleazy/welleazy-mis/venv/bin/pip install -r /home/welleazy/welleazy-mis/requirements.txt
```

---

## Phase 4: Configure Services

### Step 13: Create Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/welleazy-mis.service
```

**Paste this configuration:**
```ini
[Unit]
Description=Welleazy MIS Streamlit Dashboard
After=network.target

[Service]
Type=simple
User=welleazy
Group=welleazy
WorkingDirectory=/home/welleazy/welleazy-mis
Environment="PATH=/home/welleazy/welleazy-mis/venv/bin"
ExecStart=/home/welleazy/welleazy-mis/venv/bin/streamlit run welleazy_streamlit_app.py --server.port=8501 --server.address=127.0.0.1 --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Save and enable:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable welleazy-mis

# Start service
sudo systemctl start welleazy-mis

# Check status
sudo systemctl status welleazy-mis
```

### Step 14: Configure Nginx Reverse Proxy
```bash
# Remove default config
sudo rm /etc/nginx/sites-enabled/default

# Create new config
sudo nano /etc/nginx/sites-available/welleazy-mis
```

**Paste this configuration:**
```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

**Enable and restart:**
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/welleazy-mis /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## Phase 5: Security Hardening

### Step 15: Configure UFW Firewall
```bash
# Enable UFW
sudo ufw --force enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS (for future SSL)
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

### Step 16: Verify Streamlit Localhost Binding
```bash
# Check if Streamlit is listening on localhost only
sudo netstat -tuln | grep 8501

# Should show: 127.0.0.1:8501 (NOT 0.0.0.0:8501)
```

---

## Phase 6: Testing & Verification

### Step 17: Test Application
1. **Open browser**: `http://YOUR_NEW_IP`
2. **Login Page**: Should appear without errors
3. **Test Login**: 
   - Username: `admin`
   - Password: `admin123`
4. **Test Features**:
   - Navigate to all tabs (Overview, Clients, Operations, TAT, Daily MIS, etc.)
   - Upload a test CSV file
   - Verify no emojis in tables
   - Check responsive design on mobile
   - Test logout and login again

### Step 18: Check Service Status
```bash
# Check Streamlit service
sudo systemctl status welleazy-mis

# Check Nginx
sudo systemctl status nginx

# Check logs if needed
sudo journalctl -u welleazy-mis -n 50 --no-pager
```

### Step 19: Verify File Integrity
```bash
# Check config file (ensure no emojis)
grep "SERVICE_CATEGORIES" /home/welleazy/welleazy-mis/welleazy_config.py

# Should show: 'drug': 'Drug', 'non_drug': 'Non-Drug'
```

---

## Phase 7: Post-Deployment

### Step 20: Update Documentation
1. Update your local notes with new IP address
2. Update any bookmarks
3. Test from different devices/networks

### Step 21: Optional - Terminate Old Instance
**Only after confirming new instance works perfectly:**

1. AWS Console → EC2 → Instances
2. Select old instance: `i-089ef3f6a2af8de74` (IP: 15.206.211.130)
3. Instance State → Terminate Instance
4. Confirm termination

### Step 22: Optional - Setup SSL (HTTPS)
```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (requires domain name)
# sudo certbot --nginx -d yourdomain.com

# For self-signed certificate (development):
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/nginx-selfsigned.key \
  -out /etc/ssl/certs/nginx-selfsigned.crt
```

---

## Troubleshooting

### Service Won't Start
```bash
# Check detailed logs
sudo journalctl -u welleazy-mis -n 100 --no-pager

# Check Python errors
sudo -u welleazy /home/welleazy/welleazy-mis/venv/bin/python3 -c "import streamlit"

# Restart service
sudo systemctl restart welleazy-mis
```

### Can't Access via Browser
```bash
# Check Nginx status
sudo systemctl status nginx

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check firewall
sudo ufw status

# Test Streamlit directly
curl http://127.0.0.1:8501
```

### Permission Errors
```bash
# Fix ownership
sudo chown -R welleazy:welleazy /home/welleazy/welleazy-mis

# Fix secrets.toml permissions
sudo chmod 600 /home/welleazy/welleazy-mis/.streamlit/secrets.toml
```

### CSS or UI Issues
```bash
# Clear Python cache
sudo rm -rf /home/welleazy/welleazy-mis/__pycache__
sudo rm -rf /home/welleazy/.cache

# Restart service
sudo systemctl restart welleazy-mis

# Clear browser cache: Ctrl+Shift+Delete
```

---

## Quick Command Reference

**SSH Connection:**
```powershell
C:\Windows\System32\OpenSSH\ssh.exe -i "C:\Users\dell\.ssh\MIS_Key.pem" ubuntu@YOUR_NEW_IP
```

**Upload Files:**
```powershell
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\MIS_Key.pem" [local_file] ubuntu@YOUR_NEW_IP:/tmp/
```

**Restart Application:**
```bash
sudo systemctl restart welleazy-mis
```

**View Logs:**
```bash
sudo journalctl -u welleazy-mis -f
```

**Check Application URL:**
```
http://YOUR_NEW_IP
```

---

## Important Notes

1. **Replace YOUR_NEW_IP** with your actual new instance IP in all commands
2. **Keep MIS_Key.pem safe** - back it up securely
3. **Document new IP** in your records
4. **Test thoroughly** before terminating old instance
5. **secrets.toml credentials**:
   - Admin: admin/admin123
   - Manager: manager/manager123
6. **All code is in Git**: https://github.com/AnthonyRajuKondaveeti/MIS-Dashboard.git
7. **Production-ready**: Latest commit c1ecf3e includes all fixes

---

## Success Criteria

✅ Instance running and accessible via SSH
✅ All services active (welleazy-mis, nginx)
✅ Application accessible at http://YOUR_NEW_IP
✅ Login working with admin credentials
✅ No emojis in Daily MIS tables
✅ All tabs loading without errors
✅ File upload working
✅ Mobile responsive design working
✅ No CSS issues or button styling problems

---

**Deployment Date:** February 3, 2026
**Version:** Production (commit c1ecf3e)
**Estimated Time:** 30-45 minutes
