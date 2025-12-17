# 🚀 WAREHOUSE MANAGEMENT SYSTEM - INSTALLATION

## VÄLJ DIN INSTALLATIONS-METOD

### ⚡ METOD 1: Automatisk Installation (REKOMMENDERAD)

**Perfekt för:** Produktions-servrar, Ubuntu/Debian

**Installation i 1 kommando:**
```bash
curl -sSL https://raw.githubusercontent.com/YOUR_REPO/install.sh | sudo bash
```

**Eller steg-för-steg:**
```bash
wget https://raw.githubusercontent.com/YOUR_REPO/install.sh
chmod +x install.sh
sudo ./install.sh
```

✅ Installerar allt automatiskt
✅ Konfigurerar Nginx + Systemd
✅ Sätter upp firewall
✅ Klart på 5 minuter!

📖 [Läs INSTALLATION.md för detaljer →](INSTALLATION.md)

---

### 🐳 METOD 2: Docker Installation

**Perfekt för:** Snabb setup, utveckling, flera miljöer

**Installation i 3 kommandon:**
```bash
git clone YOUR_REPO warehouse
cd warehouse
docker-compose up -d
```

✅ Isolerad miljö
✅ Enkel portabilitet
✅ Inga systemändringar
✅ Perfekt för utveckling!

📖 [Läs DOCKER_INSTALLATION.md för detaljer →](DOCKER_INSTALLATION.md)

---

### 🛠️ METOD 3: Manuell Installation

**Perfekt för:** Custom setup, avancerade användare

**Steg-för-steg process:**
1. Installera Python, Nginx, SQLite
2. Klona repository
3. Skapa virtual environment
4. Konfigurera systemd
5. Konfigurera Nginx
6. Starta tjänsten

📖 [Läs INSTALLATION.md → Manuell Installation](INSTALLATION.md#metod-2-manuell-installation)

---

## JÄMFÖRELSE

| Feature | Automatisk | Docker | Manuell |
|---------|-----------|--------|---------|
| **Tid** | 5 min | 3 min | 20 min |
| **Svårighet** | ⭐ Enkel | ⭐ Enkel | ⭐⭐⭐ Avancerad |
| **Produktion** | ✅ Perfekt | ⚠️ OK | ✅ Perfekt |
| **Utveckling** | ⚠️ OK | ✅ Perfekt | ⚠️ OK |
| **Systemd** | ✅ Ja | ❌ Nej | ✅ Ja |
| **Isolation** | ❌ Nej | ✅ Ja | ❌ Nej |
| **Prestanda** | ✅ 100% | ⚠️ 95% | ✅ 100% |

---

## SYSTEMKRAV

**Minimum:**
- OS: Ubuntu 20.04+ / Debian 11+
- CPU: 1 core
- RAM: 512 MB
- Disk: 5 GB
- Python: 3.8+

**Rekommenderat:**
- OS: Ubuntu 22.04 LTS
- CPU: 2 cores
- RAM: 2 GB
- Disk: 20 GB
- Python: 3.10+

---

## SNABBSTART

### För Ubuntu/Debian Server:

```bash
# 1. Ladda ner och kör installer
curl -sSL https://raw.githubusercontent.com/YOUR_REPO/install.sh | sudo bash

# 2. Öppna i webbläsare
http://YOUR_SERVER_IP
```

### För Docker:

```bash
# 1. Klona repo
git clone YOUR_REPO warehouse && cd warehouse

# 2. Starta med Docker
docker-compose up -d

# 3. Öppna i webbläsare
http://localhost
```

---

## EFTER INSTALLATION

### Steg 1: Konfigurera System
1. Öppna http://YOUR_SERVER_IP
2. Gå till **Admin → Locations**
3. Skapa lagerplatser
4. Printa streckkoder

### Steg 2: Registrera Första Produkten
1. Gå till **Registrera Produkt**
2. Ta bild
3. Fyll i information
4. Scanna hyllplats
5. Klart! 🎉

### Steg 3: Konfigurera Updates (Optional)
1. Starta update server på din dator
2. Gå till **Admin → Updates**
3. Sätt server URL
4. Välj kanal (stable/testing)

---

## HANTERA TJÄNSTEN

### Automatisk Installation:

```bash
# Status
sudo systemctl status warehouse

# Starta
sudo systemctl start warehouse

# Stoppa
sudo systemctl stop warehouse

# Starta om
sudo systemctl restart warehouse

# Loggar
sudo journalctl -u warehouse -f
```

### Docker:

```bash
# Status
docker-compose ps

# Starta
docker-compose up -d

# Stoppa
docker-compose down

# Starta om
docker-compose restart

# Loggar
docker-compose logs -f
```

---

## UPPDATERA SYSTEMET

### Via Update System:
```bash
# På server:
cd /opt/warehouse
sudo python3 update_client.py
```

### Via Git:
```bash
cd /opt/warehouse
sudo git pull
sudo systemctl restart warehouse
```

### Docker:
```bash
docker-compose down
git pull
docker-compose build
docker-compose up -d
```

---

## FELSÖKNING

### Problem: Tjänsten startar inte

**Automatisk:**
```bash
sudo journalctl -u warehouse -n 50
sudo systemctl status warehouse
```

**Docker:**
```bash
docker-compose logs warehouse
docker-compose ps
```

### Problem: 502 Bad Gateway
```bash
# Kolla att app körs
sudo systemctl status warehouse  # eller docker-compose ps

# Kolla Nginx
sudo nginx -t
sudo systemctl restart nginx
```

### Problem: Bilder visas inte
```bash
# Fixa permissions
sudo chown -R warehouse:warehouse /opt/warehouse/static
sudo chmod -R 755 /opt/warehouse/static
```

---

## BACKUP

```bash
# Automatisk installation:
sudo cp /opt/warehouse/warehouse.db ~/warehouse-backup.db

# Docker:
cp warehouse.db warehouse-backup.db
```

---

## AVINSTALLERA

### Automatisk:
```bash
sudo ./install.sh --uninstall
```

### Docker:
```bash
docker-compose down -v  # OBS: Raderar volumes!
rm -rf warehouse/
```

---

## SUPPORT

📖 **Dokumentation:**
- [INSTALLATION.md](INSTALLATION.md) - Detaljerad guide
- [DOCKER_INSTALLATION.md](DOCKER_INSTALLATION.md) - Docker-specifik guide
- [README.md](README.md) - Allmän info
- [UPDATE_GUIDE.txt](UPDATE_GUIDE.txt) - Update system

💬 **Hjälp:**
- Kolla logs först
- Läs felsökningsguiden
- Testa om det fungerar manuellt

---

## VIKTIGA FILER

```
warehouse_system/
├── install.sh              ← Automatisk installer
├── docker-compose.yml      ← Docker setup
├── Dockerfile              ← Docker image
├── INSTALLATION.md         ← Denna guide
├── DOCKER_INSTALLATION.md  ← Docker guide
├── app.py                  ← Huvudapplikation
├── requirements.txt        ← Python dependencies
└── warehouse.db            ← Databas (skapas vid start)
```

---

## LYCKA TILL! 🚀

Välj din metod ovan och följ guiden!

Vid problem, kolla felsökningsavsnittet eller läs den fullständiga dokumentationen.

**Njut av ditt nya lagerhanteringssystem!** 💪
