# Kinderanwesenheit

Wer im Wechselmodell Kinder betreut und Bürgergeld/Grundsicherung bezieht wird aufgefordert, die Anwesenheit der Kinder auf Stundenbasis zu protokollieren und vorzulegen. Außerdem werden Fahrten, die für die Erfüllung der Umgangsregelung notwendig sind, gesondert bezahlt. 

Die Streamlit-App ermöglich die schnelle Verbuchung der Zeiten und Fahrten und erzeugt die notwendigen Statistiken.

## Features

- Kinder/Profile anlegen und verwalten
- Tägliche Anwesenheitszeiten erfassen (Beginn, Ende, Dauer)
- Fahrten vermerken (Übergabefahrt, Arztbesuch)
- "Gemeinsam"-Modus halbiert die Anwesenheitszeit automatisch
- Optionales Kommentarfeld pro Tag
- Auswertung über beliebige Zeiträume mit Prozentangabe
- PDF-Export der Auswertung - dem anderen Elternteil zur Unterschrift vorlegen und beim jobcenter abgeben!

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
