📦 WAREHOUSE MANAGEMENT SYSTEM - INSTALLATION GUIDE
====================================================

QUICK START (1 COMMAND)
=======================

På din server, kör:

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_REPO/install.sh | sudo bash
```

KLART! Öppna http://YOUR_SERVER_IP i webbläsaren! 🎉

DETALJERAD INSTALLATION
========================

METOD 1: Automatisk Installation (REKOMMENDERAT) ⭐
---------------------------------------------------

**Steg 1: Ladda ner installern**
```bash
wget https://raw.githubusercontent.com/YOUR_REPO/install.sh
chmod +x install.sh
```

**Steg 2: Kör installation**
```bash
sudo ./install.sh
```

**Steg 3: Öppna i webbläsaren**
```
http://YOUR_SERVER_IP
```

KLART! ✓

METOD 2: Manuell Installation
------------------------------

Om du föredrar att installera steg för steg:

**Steg 1: Installera beroenden**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git nginx sqlite3
```

**Steg 2: Skapa installation directory**
```bash
sudo mkdir -p /opt/warehouse
cd /opt/warehouse
```

**Steg 3: Kopiera filer**
```bash
# Om du har filerna lokalt:
sudo cp -r /path/to/warehouse_system/* /opt/warehouse/

# Eller klona från git:
sudo git clone YOUR_REPO_URL .
```

**Steg 4: Skapa virtual environment**
```bash
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt
```

**Steg 5: Initiera databas**
```bash
sudo venv/bin/python3 -c "from database import init_db; init_db()"
```

**Steg 6: Skapa systemd service**
```bash
sudo nano /etc/systemd/system/warehouse.service
```

Innehåll:
```ini
[Unit]
Description=Warehouse Management System
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/warehouse
Environment="PATH=/opt/warehouse/venv/bin"
ExecStart=/opt/warehouse/venv/bin/python3 /opt/warehouse/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Steg 7: Konfigurera Nginx**
```bash
sudo nano /etc/nginx/sites-available/warehouse
```

Innehåll:
```nginx
server {
    listen 80;
    server_name _;
    
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /static {
        alias /opt/warehouse/static;
        expires 30d;
    }
}
```

Aktivera:
```bash
sudo ln -s /etc/nginx/sites-available/warehouse /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

**Steg 8: Starta tjänsten**
```bash
sudo systemctl daemon-reload
sudo systemctl enable warehouse
sudo systemctl start warehouse
```

**Steg 9: Öppna firewall**
```bash
sudo ufw allow 80/tcp
sudo ufw enable
```

**Steg 10: Testa**
```
http://YOUR_SERVER_IP
```

SYSTEMKRAV
==========

Minimum:
--------
• CPU: 1 core
• RAM: 512 MB
• Disk: 5 GB
• OS: Ubuntu 20.04+ eller Debian 11+
• Python: 3.8+

Rekommenderat:
-------------
• CPU: 2 cores
• RAM: 2 GB
• Disk: 20 GB (för bilder och backups)
• OS: Ubuntu 22.04 LTS
• Python: 3.10+

PORTAR
======

Tjänsten använder:
• 5000 (Flask app, intern)
• 80 (HTTP, via Nginx)
• 443 (HTTPS, framtida)

INSTALLER-ALTERNATIV
=====================

Grundläggande:
```bash
sudo ./install.sh
```

Custom port:
```bash
sudo ./install.sh --port 8080
```

Custom directory:
```bash
sudo ./install.sh --dir /home/myuser/warehouse
```

Visa hjälp:
```bash
./install.sh --help
```

EFTER INSTALLATION
==================

Steg 1: Konfigurera Admin
--------------------------
1. Öppna http://YOUR_SERVER_IP
2. Gå till Admin → Locations
3. Skapa dina lagerplatser
4. Printa streckkoder

Steg 2: Konfigurera Updates (Optional)
---------------------------------------
1. På din dator, starta update server:
   ```bash
   python3 update_server.py
   ```

2. På servern, öppna Admin → Updates
3. Sätt Update Server URL: http://YOUR_COMPUTER_IP:8080
4. Välj kanal: stable
5. Spara

Steg 3: Börja Registrera
-------------------------
1. Gå till "Registrera Produkt"
2. Ta bilder
3. Fyll i info
4. Scanna hyllplats
5. Produkt registrerad! ✓

HANTERA TJÄNSTEN
=================

Status:
```bash
sudo systemctl status warehouse
```

Starta:
```bash
sudo systemctl start warehouse
```

Stoppa:
```bash
sudo systemctl stop warehouse
```

Starta om:
```bash
sudo systemctl restart warehouse
```

Loggar:
```bash
# Realtime logs:
sudo journalctl -u warehouse -f

# Senaste 100 rader:
sudo journalctl -u warehouse -n 100

# Loggar från idag:
sudo journalctl -u warehouse --since today
```

UPPDATERA SYSTEMET
==================

Metod 1: Via Update System (REKOMMENDERAT)
-------------------------------------------
1. På din dator:
   ```bash
   python3 create_update.py --version 1.1.0 --channel stable
   python3 update_server.py
   ```

2. På servern:
   ```bash
   cd /opt/warehouse
   sudo -u warehouse python3 update_client.py
   ```

3. Systemet uppdateras och startar om automatiskt! ✓

Metod 2: Manuell Git Pull
--------------------------
```bash
cd /opt/warehouse
sudo git pull
sudo systemctl restart warehouse
```

Metod 3: Kör Installern Igen
-----------------------------
```bash
sudo ./install.sh --update
```

AVINSTALLERA
============

```bash
sudo ./install.sh --uninstall
```

Detta kommer:
• Stoppa tjänsten
• Ta bort alla filer
• Ta bort användare
• Ta bort Nginx config
• Ta bort databas (ALL DATA FÖRLORAS!)

BACKUP
======

Manuell Backup:
```bash
# Backup allt:
sudo tar -czf warehouse-backup-$(date +%Y%m%d).tar.gz /opt/warehouse

# Endast databas:
sudo cp /opt/warehouse/warehouse.db ~/warehouse-backup.db

# Endast bilder:
sudo tar -czf images-backup.tar.gz /opt/warehouse/static/images
```

Automatisk Backup (dagligen):
```bash
# Skapa backup script:
sudo nano /opt/warehouse/backup.sh
```

Innehåll:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/warehouse/backups"
mkdir -p $BACKUP_DIR

# Backup databas
cp /opt/warehouse/warehouse.db $BACKUP_DIR/warehouse_$DATE.db

# Backup bilder (om stora, gör veckovis istället)
tar -czf $BACKUP_DIR/images_$DATE.tar.gz /opt/warehouse/static/images

# Radera backups äldre än 30 dagar
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

Gör körbar och lägg i cron:
```bash
sudo chmod +x /opt/warehouse/backup.sh
sudo crontab -e
```

Lägg till:
```
0 2 * * * /opt/warehouse/backup.sh
```

Återställ från backup:
```bash
sudo systemctl stop warehouse
sudo cp ~/warehouse-backup.db /opt/warehouse/warehouse.db
sudo systemctl start warehouse
```

FELSÖKNING
==========

Problem: Tjänsten startar inte
-------------------------------
```bash
# Kolla logs:
sudo journalctl -u warehouse -n 50

# Kolla status:
sudo systemctl status warehouse

# Testa köra manuellt:
cd /opt/warehouse
source venv/bin/activate
python3 app.py
```

Problem: 502 Bad Gateway (Nginx)
---------------------------------
```bash
# Kolla att Flask körs:
sudo systemctl status warehouse

# Kolla Nginx config:
sudo nginx -t

# Kolla Nginx logs:
sudo tail -f /var/log/nginx/error.log
```

Problem: Database locked
------------------------
```bash
# Stoppa tjänsten:
sudo systemctl stop warehouse

# Kolla processer:
sudo lsof /opt/warehouse/warehouse.db

# Starta igen:
sudo systemctl start warehouse
```

Problem: Port redan används
----------------------------
```bash
# Kolla vad som använder port 5000:
sudo lsof -i :5000

# Döda process:
sudo kill -9 PID

# Eller ändra port i installer:
sudo ./install.sh --port 8080
```

Problem: Permission denied
---------------------------
```bash
# Fixa permissions:
sudo chown -R warehouse:warehouse /opt/warehouse
sudo chmod +x /opt/warehouse/restart.sh
```

Problem: Bilder visas inte
---------------------------
```bash
# Kolla permissions:
ls -la /opt/warehouse/static/images

# Fixa:
sudo chown -R warehouse:warehouse /opt/warehouse/static
sudo chmod -R 755 /opt/warehouse/static
```

SÄKERHET
========

HTTPS (Certbot):
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

Firewall:
```bash
sudo ufw enable
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
```

Lösenordsskydd (Basic Auth):
```bash
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd username

# Lägg till i Nginx config:
auth_basic "Restricted Access";
auth_basic_user_file /etc/nginx/.htpasswd;
```

PRESTANDA
=========

Optimera för fler användare:
```bash
# Använd Gunicorn istället för Flask dev server:
pip install gunicorn

# I systemd service:
ExecStart=/opt/warehouse/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

Optimera databas:
```bash
# Vacuum databas regelbundet:
sqlite3 /opt/warehouse/warehouse.db "VACUUM;"
```

SUPPORT
=======

Dokumentation:
• README.md - Allmän info
• INSTALLATION.md - Denna fil
• UPDATE_GUIDE.txt - Update system
• AUTO_RESTART_GUIDE.txt - Auto-restart

Loggar:
• Systemd: `sudo journalctl -u warehouse -f`
• Nginx: `sudo tail -f /var/log/nginx/error.log`
• Application: `/var/log/warehouse/warehouse.log`

Testkommando för att verifiera installation:
```bash
# Kolla alla services:
sudo systemctl status warehouse nginx

# Kolla port:
sudo netstat -tlnp | grep :80

# Kolla databas:
sudo sqlite3 /opt/warehouse/warehouse.db "SELECT COUNT(*) FROM inventory;"

# Test HTTP:
curl -I http://localhost
```

NÄSTA STEG
==========

Efter lyckad installation:

1. ✓ Öppna http://YOUR_SERVER_IP
2. ✓ Skapa lagerplatser (Admin → Locations)
3. ✓ Printa streckkoder
4. ✓ Konfigurera update server
5. ✓ Registrera första produkten!

Lycka till! 🚀

VID PROBLEM
===========

Om något går fel:
1. Kolla logs: `sudo journalctl -u warehouse -n 100`
2. Verifiera att alla filer finns: `ls -la /opt/warehouse`
3. Testa manuellt: `cd /opt/warehouse && source venv/bin/activate && python3 app.py`
4. Kör installer igen: `sudo ./install.sh`
5. Som sista utväg: `sudo ./install.sh --uninstall` och installera igen

VANLIGA PROBLEM OCH LÖSNINGAR
==============================

1. **"Address already in use"**
   → Port 5000 upptagen, ändra port: `./install.sh --port 8080`

2. **"Permission denied"**
   → Kör med sudo: `sudo ./install.sh`

3. **"Database is locked"**
   → Stoppa tjänsten: `sudo systemctl stop warehouse`

4. **"502 Bad Gateway"**
   → Flask körs inte, kolla: `sudo systemctl status warehouse`

5. **Bilder laddas inte**
   → Fixa permissions: `sudo chown -R warehouse:warehouse /opt/warehouse/static`

SUCCESS!
========

Om du ser warehouse-systemet i din webbläsare - GRATTIS! 🎉

Du har nu ett fullt fungerande lagerhanteringssystem!

Njut av ditt nya system! 💪
