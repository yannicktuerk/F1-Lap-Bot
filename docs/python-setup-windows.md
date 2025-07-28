# Python Setup für Windows - Problemlösung

## 🐍 Problem: "python" wird nicht erkannt

Wenn du die Fehlermeldung bekommst:
```
'python' is not recognized as an internal or external command
```

## 🔧 Lösungen (in dieser Reihenfolge probieren):

### Lösung 1: Python über Microsoft Store installieren (Empfohlen)
1. **Microsoft Store öffnen** (Windows-Taste + "Store")
2. Nach **"Python"** suchen
3. **Python 3.12** oder neuste Version installieren
4. ✅ **Automatisch zu PATH hinzugefügt!**

### Lösung 2: Python von python.org installieren
1. Gehe zu: https://www.python.org/downloads/
2. **Download Python** (neueste Version)
3. ⚠️ **WICHTIG**: Bei Installation **"Add Python to PATH"** anhaken!
4. Installation durchführen

### Lösung 3: Python PATH manuell hinzufügen
Falls Python installiert ist, aber nicht im PATH:

#### Schritt 1: Python Installation finden
```powershell
# Häufige Installationspfade prüfen:
Get-ChildItem "C:\Users\$env:USERNAME\AppData\Local\Programs\Python" -ErrorAction SilentlyContinue
Get-ChildItem "C:\Python*" -ErrorAction SilentlyContinue
Get-ChildItem "C:\Program Files\Python*" -ErrorAction SilentlyContinue
```

#### Schritt 2: PATH Variable bearbeiten
1. **Windows-Taste + R** → `sysdm.cpl` eingeben → Enter
2. **"Erweitert"** Tab → **"Umgebungsvariablen"**
3. Bei **"Benutzervariablen"** → **"Path"** auswählen → **"Bearbeiten"**
4. **"Neu"** → Python Pfad hinzufügen (z.B. `C:\Python312`)
5. **"Neu"** → Scripts Pfad hinzufügen (z.B. `C:\Python312\Scripts`)
6. **OK** → **OK** → **OK**
7. **PowerShell/CMD neu starten!**

### Lösung 4: Python direkt über vollständigen Pfad aufrufen

Wenn nichts anderes funktioniert, erstelle eine **start.bat** Datei:

```batch
@echo off
echo 🏎️ F1 2025 UDP Telemetry Listener
echo =====================================

REM Versuche verschiedene Python-Pfade
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" (
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" udp_listener.py
    goto :end
)

if exist "C:\Users\%USERNAME%\AppData\Local\Microsoft\WindowsApps\python.exe" (
    "C:\Users\%USERNAME%\AppData\Local\Microsoft\WindowsApps\python.exe" udp_listener.py
    goto :end
)

if exist "C:\Python312\python.exe" (
    "C:\Python312\python.exe" udp_listener.py
    goto :end
)

echo ❌ Python nicht gefunden!
echo 📝 Bitte Python installieren: https://www.python.org/downloads/
echo ⚙️ Oder PATH Variable korrekt setzen
pause

:end
pause
```

## 🧪 Python Installation testen

Nach der Installation/Konfiguration testen:

```powershell
# Python Version prüfen
python --version

# Pip (Package Manager) prüfen  
pip --version

# Wenn python nicht geht, versuche:
python3 --version
py --version
```

## 📦 Abhängigkeiten installieren

Sobald Python funktioniert:

```powershell
# Benötigte Pakete installieren
pip install requests f1-packets

# Oder falls pip nicht funktioniert:
python -m pip install requests f1-packets
```

## 🚀 UDP Listener starten

```powershell
# Mit Python starten
python udp_listener.py

# Alternative wenn 'python' nicht geht:
python3 udp_listener.py
py udp_listener.py

# Mit vollständigem Pfad (Notlösung):
"C:\Users\%USERNAME%\AppData\Local\Microsoft\WindowsApps\python.exe" udp_listener.py
```

## ⚠️ Häufige Probleme

### Problem: "No module named 'requests'"
```powershell
# Lösung:
pip install requests f1-packets
```

### Problem: "Access denied" bei pip install
```powershell
# Lösung: Als Administrator oder mit --user flag
pip install --user requests f1-packets
```

### Problem: Mehrere Python Versionen
```powershell
# Spezifische Version verwenden:
py -3.12 udp_listener.py
```

## 🎯 Schnell-Check: Ist alles bereit?

Erstelle eine **test.py** Datei:

```python
import sys
import requests
print(f"✅ Python {sys.version}")
print("✅ requests library verfügbar")
print("🚀 Bereit für F1 UDP Listener!")
```

Ausführen mit: `python test.py`

## 💡 Alternative: Portable Python

Falls gar nichts funktioniert, verwende **WinPython** (portable):
1. Download: https://winpython.github.io/
2. Entpacken (z.B. nach `C:\WinPython`)
3. `WinPython Command Prompt` öffnen
4. Dort läuft Python garantiert!

---

## 🆘 Wenn gar nichts funktioniert

**Discord Support**: Schicke Screenshot der Fehlermeldung
**Alternative**: Verwende die exe-Version (falls verfügbar)

**Tipp**: Die Microsoft Store Version ist am einfachsten und funktioniert meist sofort! 🎯
