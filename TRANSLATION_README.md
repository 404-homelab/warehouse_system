# Flask-Babel Translation System

## 🎯 Quick Start

### 1. Install Flask-Babel

```bash
pip install Flask-Babel
```

### 2. Initialize Translation Files

```bash
./init_translations.sh
```

This creates:
```
translations/
├── sv/LC_MESSAGES/messages.po
├── en/LC_MESSAGES/messages.po
├── de/LC_MESSAGES/messages.po
├── fr/LC_MESSAGES/messages.po
├── es/LC_MESSAGES/messages.po
├── no/LC_MESSAGES/messages.po
├── da/LC_MESSAGES/messages.po
├── fi/LC_MESSAGES/messages.po
└── pl/LC_MESSAGES/messages.po
```

### 3. Auto-Fill Translations

```bash
python3 fill_translations.py
```

### 4. Compile Translations

```bash
pybabel compile -d translations
```

### 5. Done!

Start the server:
```bash
python3 app.py
```

---

## ✏️ Adding New Strings

### In Templates:

```html
<!-- Simple text -->
<h1>{{ _('Register Product') }}</h1>

<!-- With variable -->
<p>{{ _('Hello, %(name)s!', name=user.name) }}</p>

<!-- In attributes -->
<input placeholder="{{ _('Search...') }}">
```

### In Python Code:

```python
from flask_babel import gettext as _

# In view function
@app.route('/success')
def success():
    message = _('Product registered successfully!')
    return render_template('success.html', message=message)
```

### Update Workflow:

```bash
# 1. Extract new strings
pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot .

# 2. Update all .po files
pybabel update -i messages.pot -d translations

# 3. Edit .po files (or run fill_translations.py)

# 4. Compile
pybabel compile -d translations

# 5. Restart server
```

---

## 📝 Editing .po Files

### Structure:

```po
msgid "Register Product"
msgstr "Registrera Produkt"

msgid "Save"
msgstr "Spara"
```

### With Poedit (GUI):

1. Download Poedit: https://poedit.net/
2. Open `translations/sv/LC_MESSAGES/messages.po`
3. Edit translations visually
4. Save (auto-compiles)

### Manual Editing:

```bash
nano translations/sv/LC_MESSAGES/messages.po
```

After editing:
```bash
pybabel compile -d translations
```

---

## 🌍 Supported Languages

- 🇸🇪 Swedish (sv)
- 🇬🇧 English (en)
- 🇩🇪 German (de)
- 🇫🇷 French (fr)
- 🇪🇸 Spanish (es)
- 🇳🇴 Norwegian (no)
- 🇩🇰 Danish (da)
- 🇫🇮 Finnish (fi)
- 🇵🇱 Polish (pl)

---

## 🔄 Adding More Languages

```bash
pybabel init -i messages.pot -d translations -l it  # Italian
pybabel init -i messages.pot -d translations -l pt  # Portuguese
```

---

## ✅ Advantages

**vs JSON system:**
- ✅ Cleaner templates: `{{ _('Text') }}` instead of `{{ t.section.key }}`
- ✅ Industry standard (.po files)
- ✅ Professional tools (Poedit, Weblate)
- ✅ Auto-extraction from code
- ✅ Context and comments support
- ✅ Plural forms handled automatically

---

## 🐛 Troubleshooting

**"Translation not showing":**
```bash
# Make sure you compiled
pybabel compile -d translations

# Restart server
python3 app.py
```

**"New strings not extracted":**
```bash
# Re-extract
pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot .

# Update .po files
pybabel update -i messages.pot -d translations
```

**"Language not changing":**
- Check browser cookies (clear if needed)
- Verify cookie is set: http://localhost:5000/set-language/en
