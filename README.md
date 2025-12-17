# Warehouse Management System 📦

Ett komplett webbaserat lagersystem för hantering av produkter, ordrar, packning och försäljning på marknadsplatser.

## 🌟 Funktioner

### Kärnfunktionalitet
- ✅ **Produktregistrering** med kamera och automatisk bildbeskärning
- ✅ **Hyllplatshantering** med streckkodsskanning
- ✅ **Orderhantering** och smart packning
- ✅ **Marketplace-integration** (Blocket/Tradera)
- ✅ **PDF-export** för etiketter och bilder
- ✅ **Rapporter & Analys** med försäljningsstatistik
- ✅ **Sökfunktion** för produkter

### Teknisk Stack
- **Backend:** Python 3.12+ / Flask 3.0
- **Databas:** SQLite3
- **Frontend:** HTML5, Bootstrap 5, jQuery 3.6
- **Bildbehandling:** OpenCV 4.10
- **Streckkoder:** python-barcode, pyzbar
- **PDF:** ReportLab 4.0
- **Kamera:** WebRTC (browser-baserad)

## 🚀 Installation

### Förutsättningar
- Python 3.12 eller senare
- pip (Python package manager)
- Webbläsare med WebRTC-stöd (Chrome, Firefox, Safari, Edge)

### Steg 1: Klona/Ladda ner projektet
```bash
cd warehouse_system
```

### Steg 2: Skapa virtuell miljö (rekommenderat)
```bash
python -m venv venv

# Aktivera på Windows:
venv\Scripts\activate

# Aktivera på Mac/Linux:
source venv/bin/activate
```

### Steg 3: Installera beroenden
```bash
pip install -r requirements.txt
```

**Viktigt:** Om du får problem med NumPy/OpenCV:
```bash
pip install "numpy>=1.26.0,<2.0"
pip install opencv-python==4.10.0.84
```

### Steg 4: Starta applikationen
```bash
python app.py
```

Systemet startar på: **http://localhost:5000**

## 📱 Användning

### 1. Dashboard (/)
- Översikt av systemstatistik
- Snabblänkar till vanliga funktioner
- Senaste aktivitet

### 2. Registrera Produkt (/register)
**Steg-för-steg:**
1. Klicka "Starta Kamera"
2. Ta bild av produkten
3. Klicka "Auto-Beskär" för att rensa bakgrund
4. Fyll i produktinformation:
   - Artikelnummer (valfritt)
   - Beskrivning (obligatoriskt)
   - Skick (obligatoriskt)
   - Mått (L×B×H cm)
   - Vikt (kg)
   - Pris (SEK, obligatoriskt)
   - Hyllplats
   - Antal för bulk-registrering
5. Klicka "Registrera Produkt"

**Tips:**
- Auto-beskärning justerar sig automatiskt efter ljus och bakgrund
- Bulk-registrering skapar flera identiska produkter med unika ID:n
- Inventory ID genereras automatiskt (INV-000001, INV-000002, etc.)

### 3. Ordrar (/orders)
**Skapa order:**
1. Ange köparinfo (t.ex. "Blocket - Johan S.")
2. Scanna eller skriv Inventory ID
3. Lägg till fler produkter om behövs
4. Klicka "Skapa Order"

### 4. Packning (/packing)
**Packa order:**
1. Klicka "Hämta Nästa Order"
2. Systemet visar:
   - Orderinformation
   - Kartongförslag baserat på produkternas mått
   - Lista med produkter och deras hyllplatser
3. Plocka produkterna från angivna hyllplatser
4. Scanna "SHIPPED" eller klicka "Markera som Skickad"

### 5. Marketplace (/marketplace)
**Ladda upp till marknadsplats:**
1. Ange Inventory ID
2. Välj marketplace (Blocket/Tradera/Båda)
3. Klicka "Skapa Annons"
4. Uppdatera status när produkten säljs

**Exportera bilder:**
1. Markera produkter med checkbox
2. Klicka "Exportera Bilder (ZIP)"
3. Få ZIP-fil med alla produktbilder

### 6. Sök (/search)
- Sök på Inventory ID, artikelnummer eller beskrivning
- Få omedelbar översikt av produktinformation

### 7. Rapporter (/reports)
**Analysera försäljning:**
- Försäljningstrend (graf)
- Mest sålda produkter
- Lagervärde per plats
- Intäkter per period (dag/vecka/månad/år)

### 8. Admin (/admin)
**Hyllplatser:**
- Skapa nya hyllplatser (t.ex. A1, B2, C3)
- Automatisk streckkodsgenerering (LOC-A1-001)

**Kartongstorlekar:**
- Lägg till kartongstorlekar med mått
- Systemet föreslår automatiskt lämplig kartong vid packning

**Bulk Streckkoder:**
- Generera PDF med streckkoder
- Format: PREFIX-000001 till PREFIX-000030
- 3 kolumner × 10 rader per sida (A4)

## 🔧 API Endpoints

### Items
```
POST   /api/items                    - Skapa produkt
POST   /api/items/bulk               - Bulk-registrering
GET    /api/items/<inventory_id>    - Hämta produkt
GET    /api/items/search?q=          - Sök produkter
PUT    /api/items/<id>/location     - Uppdatera hyllplats
PUT    /api/items/<id>/status       - Uppdatera status
```

### Orders
```
GET    /api/orders                   - Lista ordrar
POST   /api/orders                   - Skapa order
GET    /api/orders/next              - Nästa att packa
POST   /api/orders/<id>/ship         - Markera skickad
GET    /api/orders/<id>/items        - Få orderitems
```

### Locations
```
GET    /api/locations                - Lista hyllplatser
POST   /api/locations                - Skapa hyllplats
DELETE /api/locations/<id>           - Ta bort
```

### Marketplace
```
GET    /api/marketplace/listings     - Lista annonser
POST   /api/marketplace/listings     - Skapa annons
PUT    /api/marketplace/listings/<id>/status - Uppdatera status
```

### Reports
```
GET    /api/reports/statistics       - Systemstatistik
GET    /api/reports/sales?period=    - Försäljningsrapport
GET    /api/reports/inventory-value  - Lagervärde
GET    /api/reports/top-items        - Mest sålda
GET    /api/reports/activity         - Aktivitetslogg
```

### Export
```
POST   /api/export/images            - Exportera bilder (ZIP)
POST   /api/export/pdf/labels        - PDF-etiketter
POST   /api/barcodes/bulk-generate   - Bulk streckkoder
```

## 📊 Databasschema

### Tabeller
- **items** - Produkter med inventory_id, beskrivning, mått, pris, status
- **images** - Produktbilder (original + beskuren)
- **locations** - Hyllplatser med streckkoder
- **orders** - Ordrar med köparinfo
- **order_items** - Många-till-många relation order↔items
- **box_sizes** - Kartongstorlekar
- **marketplace_listings** - Marketplace-annonser
- **audit_log** - Händelselogg

## 🎯 Arbetsflöde

### Typiskt arbetsflöde:
1. **Inleverans:**
   - Ta bild av produkt
   - Registrera i systemet
   - Placera på hyllplats
   - Etikett med streckkod printas automatiskt

2. **Försäljning:**
   - Markera produkt för marketplace
   - Exportera bilder
   - Ladda upp till Blocket/Tradera

3. **Order:**
   - Kund köper → Skapa order i systemet
   - Lista visar alla produkter och deras hyllplatser

4. **Packning:**
   - Hämta nästa order
   - Systemet föreslår kartong
   - Plocka produkter från angivna hyllor
   - Scanna SHIPPED → Order färdig

## 🔐 Säkerhet & Best Practices

- Databasen lagras lokalt (warehouse.db)
- Bilder sparas i static/uploads/
- Regelbunden backup rekommenderas
- HTTPS rekommenderas för produktionsmiljö

## 🐛 Felsökning

### Problem: Kameran startar inte
**Lösning:** 
- Kontrollera att webbläsaren har tillgång till kamera
- Använd HTTPS eller localhost (WebRTC-krav)
- Prova annan webbläsare

### Problem: NumPy/OpenCV fel
**Lösning:**
```bash
pip uninstall numpy opencv-python
pip install "numpy>=1.26.0,<2.0"
pip install opencv-python==4.10.0.84
```

### Problem: Port 5000 är upptagen
**Lösning:** Ändra port i app.py:
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

## 📈 Framtida Förbättringar

### Fas 2 (Planerat):
- API-integration med Blocket/Tradera
- Avancerad rapportering och analytics
- QR-kod stöd för snabbare skanning

### Fas 3 (Framtid):
- PostgreSQL för bättre skalbarhet
- Docker containerisering
- Mobilapp (React Native)
- AI-baserad bildigenkänning
- Automatisk prissättning

## 📞 Support

För problem eller frågor:
- Kontrollera dokumentationen ovan
- Kolla felsökningsguiden
- Granska loggfiler i terminalen

## 📄 Licens

Detta projekt är skapat för internt bruk.

---

**Lycka till med ditt lagersystem! 🚀📦**
