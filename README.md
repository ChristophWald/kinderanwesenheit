# Kinderanwesenheit

Eine Web-App zur Erfassung und Auswertung von Anwesenheitszeiten, gebaut mit Python und Streamlit.

## Features

- Kinder/Profile anlegen und verwalten
- Tägliche Anwesenheitszeiten erfassen (Beginn, Ende, Dauer)
- Fahrten vermerken (Übergabefahrt, Arztbesuch)
- "Gemeinsam"-Modus halbiert die Anwesenheitszeit automatisch
- Optionales Kommentarfeld pro Tag
- Auswertung über beliebige Zeiträume mit Prozentangabe
- PDF-Export der Auswertung

## Tech Stack

- [Streamlit](https://streamlit.io/) – Web-Oberfläche
- MySQL – Datenbank
- pandas – Datenverarbeitung
- fpdf2 – PDF-Export

## Installation

```bash
pip install -r requirements.txt
```

MySQL-Zugangsdaten in `db.py` anpassen:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'DEIN_USER',
    'password': 'DEIN_PASSWORT',
    'database': 'zeiterfassung'
}
```

## Starten

```bash
streamlit run app.py
```
