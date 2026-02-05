# Welleazy MIS Deployment - Commands Only

**Server Details:**
- IP Address: `13.127.233.154`
- SSH Key: `C:\Users\dell\.ssh\mis-key.pem`

---

## PART 1: AWS CONSOLE (Manual Steps)

1. Go to AWS Console → EC2 → Launch Instance
2. Name: `welleazy-mis-server`
3. AMI: Ubuntu Server 24.04 LTS (64-bit x86)
4. Instance Type: t3.micro
5. Key Pair: Select existing or create new
6. Security Group Rules:
   - SSH (22) - Source: 0.0.0.0/0
   - HTTP (80) - Source: 0.0.0.0/0
   - HTTPS (443) - Source: 0.0.0.0/0
7. Storage: 8 GB (or more)
8. Launch Instance
9. **Copy the Public IPv4 Address - YOU NEED THIS!**

---

## PART 2: SSH CONNECTION (Windows PowerShell)

**IMPORTANT: Run these commands in Windows PowerShell, NOT in SSH!**

```powershell
# Fix .pem file permissions FIRST (run in Windows PowerShell on your local computer)
icacls "C:\Users\dell\.ssh\mis-key.pem" /inheritance:r
icacls "C:\Users\dell\.ssh\mis-key.pem" /grant:r "%USERNAME%:R"

# Now test SSH connection
C:\Windows\System32\OpenSSH\ssh.exe -i "C:\Users\dell\.ssh\mis-key.pem" ubuntu@13.127.233.154
```

**Note:** The icacls commands are Windows commands - run them in PowerShell on your local computer before connecting to SSH.

---

## PART 3: SERVER SETUP (In SSH Terminal)

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python 3.12 and tools
sudo apt install -y python3.12 python3.12-venv python3-pip build-essential git curl

# Install Nginx
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Create application user and directory
sudo useradd -r -s /usr/sbin/nologin welleazy
sudo mkdir -p /home/welleazy/welleazy-mis
sudo chown -R welleazy:welleazy /home/welleazy
```

---

## PART 4: UPLOAD FILES (Exit SSH, run in PowerShell)

```powershell
# Type 'exit' to close SSH connection first
exit

# Navigate to your project folder
cd "D:\Downloads\Welleazy MIS"

# Upload all Python files
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" welleazy_streamlit_app.py ubuntu@13.127.233.154:/tmp/
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" welleazy_pipeline.py ubuntu@13.127.233.154:/tmp/
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" welleazy_config.py ubuntu@13.127.233.154:/tmp/
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" welleazy_normalization.py ubuntu@13.127.233.154:/tmp/
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" welleazy_validation.py ubuntu@13.127.233.154:/tmp/
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" welleazy_daily_mis.py ubuntu@13.127.233.154:/tmp/
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" welleazy_tat_mis.py ubuntu@13.127.233.154:/tmp/
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" welleazy_pending_mis.py ubuntu@13.127.233.154:/tmp/
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" welleazy_closure_tat_mis.py ubuntu@13.127.233.154:/tmp/
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" veriright_pipeline.py ubuntu@13.127.233.154:/tmp/
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" veriright_config.py ubuntu@13.127.233.154:/tmp/
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" veriright_normalization.py ubuntu@13.127.233.154:/tmp/
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" veriright_daily_mis.py ubuntu@13.127.233.154:/tmp/
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" veriright_reports.py ubuntu@13.127.233.154:/tmp/
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" requirements.txt ubuntu@13.127.233.154:/tmp/
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" .env ubuntu@13.127.233.154:/tmp/
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" .streamlit\secrets.toml ubuntu@13.127.233.154:/tmp/
```

---

## PART 5: SSH BACK AND ORGANIZE FILES

```powershell
# SSH back to server
C:\Windows\System32\OpenSSH\ssh.exe -i "C:\Users\dell\.ssh\mis-key.pem" ubuntu@13.127.233.154
```

```bash
# Move files to application directory
sudo mv /tmp/welleazy_*.py /home/welleazy/welleazy-mis/
sudo mv /tmp/veriright_*.py /home/welleazy/welleazy-mis/
sudo mv /tmp/requirements.txt /home/welleazy/welleazy-mis/
sudo mv /tmp/.env /home/welleazy/welleazy-mis/

# Create .streamlit directory and move secrets
sudo mkdir -p /home/welleazy/welleazy-mis/.streamlit
sudo mv /tmp/secrets.toml /home/welleazy/welleazy-mis/.streamlit/

# Set ownership and permissions
sudo chown -R welleazy:welleazy /home/welleazy/welleazy-mis
sudo chmod 600 /home/welleazy/welleazy-mis/.streamlit/secrets.toml
```

---

## PART 6: INSTALL PYTHON PACKAGES

```bash
# Create virtual environment
sudo -u welleazy python3 -m venv /home/welleazy/welleazy-mis/venv

# Upgrade pip
sudo -u welleazy /home/welleazy/welleazy-mis/venv/bin/pip install --upgrade pip

# Install dependencies (takes 2-3 minutes)
sudo -u welleazy /home/welleazy/welleazy-mis/venv/bin/pip install -r /home/welleazy/welleazy-mis/requirements.txt
```

---

## PART 7: CREATE SYSTEMD SERVICE

```bash
# Create service file
sudo nano /etc/systemd/system/welleazy-mis.service
```

**Copy and paste this entire block into nano:**

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

**Press Ctrl+X, then Y, then Enter**

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable welleazy-mis
sudo systemctl start welleazy-mis
sudo systemctl status welleazy-mis
```

---

## PART 8: CONFIGURE NGINX

```bash
# Remove default config
sudo rm /etc/nginx/sites-enabled/default

# Create new config
sudo nano /etc/nginx/sites-available/welleazy-mis
```

**Copy and paste this into nano:**

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

**Press Ctrl+X, then Y, then Enter**

```bash
# Enable site and restart Nginx
sudo ln -s /etc/nginx/sites-available/welleazy-mis /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## PART 9: CONFIGURE FIREWALL

```bash
# Enable and configure UFW
sudo ufw --force enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

---

## PART 10: TEST

**Open browser and go to:**
```
http://13.127.233.154
```

**Login:**
- Username: `admin`
- Password: `admin123`

---

## TROUBLESHOOTING COMMANDS

```bash
# Check service status
sudo systemctl status welleazy-mis

# View logs
sudo journalctl -u welleazy-mis -n 50

# Restart service
sudo systemctl restart welleazy-mis

# Clear Python cache
sudo rm -rf /home/welleazy/welleazy-mis/__pycache__
sudo rm -rf /home/welleazy/.cache
sudo systemctl restart welleazy-mis

# Check Nginx
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log

# Check if port is in use
sudo netstat -tuln | grep 8501
```

---

## QUICK REFERENCE

**SSH:**
```powershell
C:\Windows\System32\OpenSSH\ssh.exe -i "C:\Users\dell\.ssh\mis-key.pem" ubuntu@13.127.233.154
```

**Upload single file:**
```powershell
C:\Windows\System32\OpenSSH\scp.exe -i "C:\Users\dell\.ssh\mis-key.pem" filename.py ubuntu@13.127.233.154:/tmp/
```

**Restart app:**
```bash
sudo systemctl restart welleazy-mis
```

**View live logs:**
```bash
sudo journalctl -u welleazy-mis -f
```

---

**All commands are ready to copy-paste! Your application will be live at: http://13.127.233.154**
