# 📦 Warehouse Management System

Ett komplett lagerhanteringssystem med streckkodsskanning, bildhantering, orderhantering och marknadsplatsintegrationer.

![GitHub](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10+-green.svg)
![Flask](https://img.shields.io/badge/Flask-Latest-lightgrey.svg)

## ✨ Features

### 📸 Produktregistrering
- USB-kamera integration med OpenCV
- Automatisk bildbeskärning med AI
- Bulk-registrering (flera identiska produkter)
- **Auto-registrering vid hyllplats-scanning** ⚡

### 📦 Lagerhantering
- Streckkodssystem (generering & scanning)
- Hyllplats-hantering med QR-koder
- Produktsökning med autocomplete
- Bulk inventory-hantering

### 🛒 Orderhantering
- 3-stegs orderprocess
- Shopping cart med bulk quantities
- Packningsworkflow med scanning-validering
- **Celebration screen när alla ordrar är packade** 🎉
- PDF-generering för packsedlar

### 🌐 Marknadsplatsintegration
- Blocket listing
- Tradera listing
- Facebook Marketplace
- Custom platforms

### 📊 Rapporter
- Försäljningsrapporter
- Lagerrapporter
- Export till CSV/PDF

### 🔄 Auto-Update System
- Update server & client
- Stable/Testing channels
- Scheduled updates
- **Auto-restart efter update**
- Backup före uppdatering

## 🚀 Installation

### Snabbinstallation (1 kommando)

```bash
curl -sSL https://raw.githubusercontent.com/404-homelab/warehouse_system/main/install.sh | sudo bash
```

### Steg-för-steg

```bash
# 1. Ladda ner installern
wget https://raw.githubusercontent.com/404-homelab/warehouse_system/main/install.sh
chmod +x install.sh

# 2. Kör installation
sudo ./install.sh

# 3. Öppna i webbläsare
http://YOUR_SERVER_IP:5000
```

### Docker Installation

```bash
git clone https://github.com/404-homelab/warehouse_system.git
cd warehouse_system
docker-compose up -d
```

## 📋 Systemkrav

**Minimum:**
- Ubuntu 20.04+ / Debian 11+
- 512 MB RAM
- 5 GB disk
- Python 3.8+

**Rekommenderat:**
- Ubuntu 22.04 LTS
- 2 GB RAM
- 20 GB disk (för bilder)
- Python 3.10+

## 🎯 Quick Start

1. **Efter installation:** Öppna http://YOUR_SERVER_IP:5000
2. **Skapa lagerplatser:** Admin → Locations
3. **Printa streckkoder:** Använd "Bulk Streckkoder" funktionen
4. **Registrera produkter:** Registrera Produkt → Ta bild → Scanna hyllplats
5. **Skapa orders:** Skapa Order → Välj produkter → Packa

## 🛠️ Hantera Tjänsten

```bash
# Status
sudo systemctl status warehouse

# Starta/Stoppa
sudo systemctl start warehouse
sudo systemctl stop warehouse
sudo systemctl restart warehouse

# Loggar
sudo journalctl -u warehouse -f
```

## 🔄 Uppdatera

```bash
# Via installer
sudo ./install.sh --update

# Via Git
cd /opt/warehouse
sudo git pull
sudo systemctl restart warehouse

# Via Update System
cd /opt/warehouse
sudo python3 update_client.py
```

## 📖 Dokumentation

- [INSTALLATION.md](INSTALLATION.md) - Detaljerad installationsguide
- [DOCKER_INSTALLATION.md](DOCKER_INSTALLATION.md) - Docker-specifik guide
- [UPDATE_GUIDE.txt](UPDATE_GUIDE.txt) - Update system
- [AUTO_RESTART_GUIDE.txt](AUTO_RESTART_GUIDE.txt) - Auto-restart
- [AUTO_REGISTRATION_GUIDE.txt](AUTO_REGISTRATION_GUIDE.txt) - Snabb-registrering

## 🏗️ Arkitektur

```
warehouse_system/
├── app.py                  # Flask application
├── database.py             # SQLite database logic
├── barcode_generator.py    # Barcode generation
├── camera_handler.py       # USB camera integration
├── image_processor.py      # Image processing & AI cropping
├── pdf_generator.py        # PDF generation
├── update_client.py        # Update client
├── update_server.py        # Update server
├── templates/              # HTML templates
├── static/                 # CSS, JS, images
└── install.sh              # Auto-installer

Tech Stack:
- Backend: Python 3.10 + Flask
- Database: SQLite
- Frontend: Bootstrap 5 + jQuery
- Image Processing: OpenCV + Pillow
- Barcode: python-barcode
```

## 🐛 Felsökning

### Tjänsten startar inte
```bash
sudo journalctl -u warehouse -n 50
sudo systemctl status warehouse
```

### Bilder visas inte
```bash
sudo chown -R warehouse:warehouse /opt/warehouse/static
sudo chmod -R 755 /opt/warehouse/static
```

### Database locked
```bash
sudo systemctl restart warehouse
```

## 🤝 Contributing

Contributions är välkomna! 

1. Fork repositoryt
2. Skapa en feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit dina ändringar (`git commit -m 'Add some AmazingFeature'`)
4. Push till branchen (`git push origin feature/AmazingFeature`)
5. Öppna en Pull Request

## 📝 License

MIT License - se [LICENSE](LICENSE) för detaljer

## 👤 Author

**404-homelab**

- GitHub: [@404-homelab](https://github.com/404-homelab)
- Repo: [warehouse_system](https://github.com/404-homelab/warehouse_system)

## ⭐ Show your support

Om du tycker projektet är användbart, ge det en stjärna! ⭐

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/404-homelab/warehouse_system/issues)
- **Diskussioner**: [GitHub Discussions](https://github.com/404-homelab/warehouse_system/discussions)

---

**Byggd med ❤️ för enkel lagerhantering**
