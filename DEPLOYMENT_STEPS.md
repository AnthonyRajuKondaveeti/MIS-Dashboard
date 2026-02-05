# Welleazy MIS - Complete Deployment Steps

**Deployment Method:** Direct from Local Computer (No Git Required)  
**Date:** February 3, 2026  
**Time Required:** 30-45 minutes

---

## PART 1: CREATE EC2 INSTANCE (AWS Console)

### Step 1: Launch New Instance
1. Open **AWS Console** → Go to **EC2** → Click **Launch Instance**

2. **Configure Instance:**
   - **Name:** `welleazy-mis-server`
   - **Application and OS Images:** 
     - Click **Ubuntu**
     - Select **Ubuntu Server 24.04 LTS**
     - Architecture: **64-bit (x86)**
   
   - **Instance Type:** 
     - Select **t3.micro** (1 vCPU, 1 GB RAM)
   
   - **Key Pair:**
     - Select your existing key pair
     - OR click **Create new key pair** if you don't have one
     - If creating new, save it to `C:\Users\dell\.ssh\`
   
   - **Network Settings:**
     - Click **Edit** next to Network settings
     - **Firewall (security groups):** Select **Create security group**
     - **Security group name:** `welleazy-mis-sg`
     - **Add Security Group Rules:**
       - ✅ **SSH** (Port 22, Source: 0.0.0.0/0)
       - ✅ **HTTP** (Port 80, Source: 0.0.0.0/0)
       - Click **Add security group rule** → **HTTPS** (Port 443, Source: 0.0.0.0/0)
   
   - **Configure Storage:**
     - **Size:** 8 GB (or increase to 16-20 GB if needed)
     - **Volume Type:** gp3

3. Click **Launch Instance**

4. **IMPORTANT - Note These Down:**
   - Wait for instance to show **Running** state
   - Click on your instance
   - **Copy these details:**
     - ✅ **Public IPv4 Address:** (e.g., 13.234.xx.xxx) - **YOU NEED THIS!**
     - ✅ **Instance ID:** (e.g., i-0123456789abcdef0)

---

## PART 2: CONNECT TO SERVER

### Step 2: Test SSH Connection
Open **PowerShell** and run:

```powershell
C:\Windows\System32\OpenSSH\ssh.exe -i "C:\Users\dell\.ssh\MIS_Key.pem" ubuntu@YOUR_IP_ADDRESS
```

**Replace `YOUR_IP_ADDRESS` with your actual IP from Step 1!**

**If you get "permission denied" error:**
```powershell
icacls "C:\Users\dell\.ssh\MIS_Key.pem" /inheritance:r
icacls "C:\Users\dell\.ssh\MIS_Key.pem" /grant:r "%USERNAME%:R"
```

**Then try SSH again.**

When prompted "Are you sure you want to continue connecting?", type **yes** and press Enter.

---

## PART 3: SETUP SERVER (Run these commands in SSH)

### Step 3: Update System
```bash
sudo apt update
sudo apt upgrade -y
```

### Step 4: Install Required Software
```bash
# Install Python 3.12 and tools
sudo apt install -y python3.12 python3.12-venv python3-pip build-essential git curl

# Install Nginx web server
sudo apt install -y nginx

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Step 5: Create Application User
```bash
# Create dedicated user for security
sudo useradd -r -s /usr/sbin/nologin welleazy

# Create application directory
sudo mkdir -p /home/welleazy/welleazy-mis
sudo chown -R welleazy:welleazy /home/welleazy
```

---

## PART 4: UPLOAD YOUR FILES

### Step 6: Upload Application Files from Local Computer
**Type `exit` to close SSH connection**

**Then in PowerShell, navigate to your project folder:**

```powershell
cd "D:\Downloads\Welleazy MIS"
```

**Upload all files (copy this entire block and run):**

```powershell
# Upload all Python files
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" welleazy_streamlit_app.py ubuntu@YOUR_IP_ADDRESS:/tmp/
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" welleazy_pipeline.py ubuntu@YOUR_IP_ADDRESS:/tmp/
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" welleazy_config.py ubuntu@YOUR_IP_ADDRESS:/tmp/
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" welleazy_normalization.py ubuntu@YOUR_IP_ADDRESS:/tmp/
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" welleazy_validation.py ubuntu@YOUR_IP_ADDRESS:/tmp/
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" welleazy_daily_mis.py ubuntu@YOUR_IP_ADDRESS:/tmp/
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" welleazy_tat_mis.py ubuntu@YOUR_IP_ADDRESS:/tmp/
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" welleazy_pending_mis.py ubuntu@YOUR_IP_ADDRESS:/tmp/
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" welleazy_closure_tat_mis.py ubuntu@YOUR_IP_ADDRESS:/tmp/
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" veriright_pipeline.py ubuntu@YOUR_IP_ADDRESS:/tmp/
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" veriright_config.py ubuntu@YOUR_IP_ADDRESS:/tmp/
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" veriright_normalization.py ubuntu@YOUR_IP_ADDRESS:/tmp/
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" veriright_daily_mis.py ubuntu@YOUR_IP_ADDRESS:/tmp/
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" veriright_reports.py ubuntu@YOUR_IP_ADDRESS:/tmp/
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" requirements.txt ubuntu@YOUR_IP_ADDRESS:/tmp/
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" .env ubuntu@YOUR_IP_ADDRESS:/tmp/

# Upload secrets file
scp -i "C:\Users\dell\.ssh\MIS_Key.pem" .streamlit\secrets.toml ubuntu@YOUR_IP_ADDRESS:/tmp/

Write-Host "All files uploaded successfully!"
```

**Remember to replace `YOUR_IP_ADDRESS` in each command!**

---

## PART 5: ORGANIZE FILES ON SERVER

### Step 7: SSH Back to Server
```powershell
C:\Windows\System32\OpenSSH\ssh.exe -i "C:\Users\dell\.ssh\MIS_Key.pem" ubuntu@YOUR_IP_ADDRESS
```

### Step 8: Move Files to Proper Locations
```bash
# Move Python files
sudo mv /tmp/welleazy_*.py /home/welleazy/welleazy-mis/
sudo mv /tmp/veriright_*.py /home/welleazy/welleazy-mis/
sudo mv /tmp/requirements.txt /home/welleazy/welleazy-mis/
sudo mv /tmp/.env /home/welleazy/welleazy-mis/

# Create .streamlit directory and move secrets
sudo mkdir -p /home/welleazy/welleazy-mis/.streamlit
sudo mv /tmp/secrets.toml /home/welleazy/welleazy-mis/.streamlit/

# Set correct ownership
sudo chown -R welleazy:welleazy /home/welleazy/welleazy-mis

# Secure secrets file
sudo chmod 600 /home/welleazy/welleazy-mis/.streamlit/secrets.toml
```

---

## PART 6: INSTALL PYTHON PACKAGES

### Step 9: Create Virtual Environment and Install Dependencies
```bash
# Create Python virtual environment
sudo -u welleazy python3 -m venv /home/welleazy/welleazy-mis/venv

# Upgrade pip
sudo -u welleazy /home/welleazy/welleazy-mis/venv/bin/pip install --upgrade pip

# Install all required packages (this takes 2-3 minutes)
sudo -u welleazy /home/welleazy/welleazy-mis/venv/bin/pip install -r /home/welleazy/welleazy-mis/requirements.txt
```

**Wait for installation to complete. You'll see packages being installed.**

---

## PART 7: CREATE SYSTEMD SERVICE

### Step 10: Create Service File
```bash
sudo nano /etc/systemd/system/welleazy-mis.service
```

**Copy and paste this entire configuration:**

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

**Press `Ctrl+X`, then `Y`, then `Enter` to save**

### Step 11: Enable and Start Service
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable welleazy-mis

# Start the service
sudo systemctl start welleazy-mis

# Check if it's running
sudo systemctl status welleazy-mis
```

**You should see "active (running)" in green.**

**If you see errors, check logs:**
```bash
sudo journalctl -u welleazy-mis -n 50
```

---

## PART 8: CONFIGURE NGINX

### Step 12: Remove Default Nginx Config
```bash
sudo rm /etc/nginx/sites-enabled/default
```

### Step 13: Create New Nginx Config
```bash
sudo nano /etc/nginx/sites-available/welleazy-mis
```

**Copy and paste this configuration:**

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

**Press `Ctrl+X`, then `Y`, then `Enter` to save**

### Step 14: Enable Nginx Site
```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/welleazy-mis /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

**You should see "syntax is ok" and "test is successful"**

---

## PART 9: SETUP FIREWALL

### Step 15: Configure UFW Firewall
```bash
# Enable firewall
sudo ufw --force enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS (for future SSL)
sudo ufw allow 443/tcp

# Check firewall status
sudo ufw status
```

---

## PART 10: TEST YOUR APPLICATION

### Step 16: Open in Browser
1. Open your web browser
2. Go to: `http://YOUR_IP_ADDRESS`
3. You should see the **Welleazy MIS Login Page**

### Step 17: Test Login
**Login with these credentials:**
- **Username:** `admin`
- **Password:** `admin123`

### Step 18: Test All Features
✅ Check all tabs load: Overview, Clients, Operations, TAT, Pending, Closure, Daily MIS  
✅ Upload a test CSV file  
✅ Verify no emojis appear in tables  
✅ Test on mobile (responsive design)  
✅ Logout and login again  

---

## TROUBLESHOOTING

### If Application Won't Load:

**Check service status:**
```bash
sudo systemctl status welleazy-mis
```

**View recent logs:**
```bash
sudo journalctl -u welleazy-mis -n 50
```

**Restart service:**
```bash
sudo systemctl restart welleazy-mis
```

### If Nginx Shows Error:

**Check Nginx logs:**
```bash
sudo tail -f /var/log/nginx/error.log
```

**Restart Nginx:**
```bash
sudo systemctl restart nginx
```

### If You See Emojis or CSS Issues:

**Clear Python cache:**
```bash
sudo rm -rf /home/welleazy/welleazy-mis/__pycache__
sudo rm -rf /home/welleazy/.cache
sudo systemctl restart welleazy-mis
```

**Clear browser cache:** Press `Ctrl+Shift+Delete`

### If Service Fails to Start:

**Check if port 8501 is already in use:**
```bash
sudo netstat -tuln | grep 8501
```

**Check Python errors:**
```bash
sudo -u welleazy /home/welleazy/welleazy-mis/venv/bin/python3 -c "import streamlit"
```

---

## QUICK REFERENCE COMMANDS

**SSH into server:**
```powershell
C:\Windows\System32\OpenSSH\ssh.exe -i "C:\Users\dell\.ssh\MIS_Key.pem" ubuntu@YOUR_IP_ADDRESS
```

**Restart application:**
```bash
sudo systemctl restart welleazy-mis
```

**View live logs:**
```bash
sudo journalctl -u welleazy-mis -f
```

**Check service status:**
```bash
sudo systemctl status welleazy-mis
sudo systemctl status nginx
```

**Your application URL:**
```
http://YOUR_IP_ADDRESS
```

---

## SUCCESS CHECKLIST

✅ EC2 instance created and running  
✅ SSH connection working  
✅ All files uploaded from local computer  
✅ Python packages installed  
✅ Systemd service running  
✅ Nginx configured and running  
✅ Firewall configured  
✅ Application accessible in browser  
✅ Login working  
✅ All features tested  

---

## IMPORTANT NOTES

1. **Replace `YOUR_IP_ADDRESS`** everywhere with your actual EC2 IP address
2. **Keep your SSH key safe:** `C:\Users\dell\.ssh\MIS_Key.pem`
3. **Login credentials:**
   - Admin: admin/admin123
   - Manager: manager/manager123
4. **Application runs on port 8501** (localhost only, proxied via Nginx)
5. **Nginx listens on port 80** (public access)

---

## NEXT STEPS (Optional)

### Setup HTTPS/SSL:
After confirming everything works, you can add SSL for HTTPS access.

### Terminate Old Instance:
Once you confirm the new instance works perfectly:
1. Go to AWS Console → EC2 → Instances
2. Select old instance (i-089ef3f6a2af8de74)
3. Instance State → Terminate

---

**Deployment Complete! 🎉**

Your Welleazy MIS Dashboard is now live at: `http://YOUR_IP_ADDRESS`
