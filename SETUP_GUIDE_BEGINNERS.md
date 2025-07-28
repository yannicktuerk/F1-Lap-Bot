# 🏁 F1 UDP Telemetrie - Komplette Anfänger-Anleitung

> **🎯 Für alle, die noch nie Python verwendet haben!**

Diese Anleitung erklärt **jeden einzelnen Schritt** von der Installation bis zur ersten automatischen Rundenzeit-Übertragung.

## 📋 **Was du brauchst:**
- ✅ **Windows PC** (Windows 10/11)
- ✅ **F1 2025** (Steam/Epic/etc.)
- ✅ **Discord Account**
- ✅ **Internet-Verbindung**
- ✅ **30 Minuten Zeit** für das Setup

---

## 🛠️ **Schritt 1: Python installieren (falls nicht vorhanden)**

### 🔍 **Prüfen ob Python bereits installiert ist:**
1. **Windows-Taste + R** drücken
2. **`cmd`** eingeben und Enter drücken
3. **`python --version`** eingeben und Enter drücken

**✅ Falls du sowas siehst:** `Python 3.11.5` → **Python ist installiert, weiter zu Schritt 2!**  
**❌ Falls Fehler kommt:** → **Python installieren:**

### 📥 **Python installieren:**
1. **Gehe zu:** https://www.python.org/downloads/
2. **"Download Python 3.12.x" klicken** (neueste Version)
3. **Datei herunterladen** (ca. 25 MB)
4. **Installer ausführen** (python-3.12.x-amd64.exe)
5. **⚠️ WICHTIG:** ✅ **"Add Python to PATH"** ankreuzen!
6. **"Install Now"** klicken
7. **Warten bis fertig** (ca. 2 Minuten)
8. **"Close"** klicken

### ✅ **Python-Installation testen:**
1. **Neues CMD-Fenster öffnen** (Windows+R → cmd)
2. **`python --version`** eingeben
3. **Sollte zeigen:** `Python 3.12.x`

---

## 📦 **Schritt 2: Git installieren (für Repository-Download)**

### 🔍 **Git prüfen:**
1. **CMD öffnen** (Windows+R → cmd)
2. **`git --version`** eingeben

**✅ Falls Version angezeigt wird** → **Weiter zu Schritt 3!**  
**❌ Falls "git ist nicht erkannt"** → **Git installieren:**

### 📥 **Git installieren:**
1. **Gehe zu:** https://git-scm.com/download/win
2. **"Click here to download"** klicken
3. **Installer herunterladen** (ca. 50 MB)
4. **Git-2.xx.x-64-bit.exe ausführen**
5. **Alle Einstellungen Standard lassen** → **"Next, Next, Next..."**
6. **"Install"** klicken
7. **Warten bis fertig**
8. **"Finish"** klicken

---

## 💾 **Schritt 3: F1-Lap-Bot herunterladen**

### 📁 **Ordner erstellen:**
1. **Desktop** öffnen
2. **Rechtsklick** → **"Neuer Ordner"**
3. **Name:** `F1-TelemetryBot`

### ⬇️ **Repository downloaden:**
1. **CMD öffnen** (Windows+R → cmd)
2. **Zum Desktop navigieren:**
   ```bash
   cd Desktop\F1-TelemetryBot
   ```
3. **Repository klonen:**
   ```bash
   git clone https://github.com/yannicktuerk/F1-Lap-Bot.git
   ```
4. **In den Ordner wechseln:**
   ```bash
   cd F1-Lap-Bot
   ```
5. **Richtigen Branch wechseln:**
   ```bash
   git checkout develop-v2-udp-telemetry
   ```

---

## 🐍 **Schritt 4: Python-Abhängigkeiten installieren**

### 📦 **Dependencies installieren:**
```bash
pip install -r requirements.txt
```

**⏳ Das dauert ca. 2-3 Minuten** (lädt Pakete herunter)

### ✅ **Installation prüfen:**
```bash
python -c "import discord; import aiohttp; import requests; print('✅ Alle Pakete installiert!')"
```

**Sollte zeigen:** `✅ Alle Pakete installiert!`

---

## 🔑 **Schritt 5: Discord User ID herausfinden**

### 📱 **Discord User ID ermitteln:**
1. **Discord öffnen** (Desktop oder Browser)
2. **Einstellungen öffnen** (Zahnrad unten links)
3. **"Erweitert"** klicken (in der linken Liste)
4. **"Entwicklermodus"** aktivieren ✅
5. **Zurück** zu einem Chat/Server
6. **Rechtsklick auf deinen eigenen Namen**
7. **"Benutzer-ID kopieren"** klicken
8. **ID notieren** (18 Ziffern, z.B. `123456789012345678`)

---

## ⚙️ **Schritt 6: Konfiguration erstellen**

### 📝 **Config-Datei erstellen:**
1. **Im F1-Lap-Bot Ordner:**
   ```bash
   copy config_example.json config.json
   ```

2. **config.json mit Texteditor öffnen** (Notepad, VS Code, etc.)

3. **Folgende Werte ändern:**
   ```json
   {
       "discord_user_id": "HIER_DEINE_18_STELLIGE_USER_ID",
       "bot_api_url": "http://159.69.90.26:5000/api/telemetry/submit",
       "port": 20777,
       "bot_integration": true,
       "player_name": "DeinGewünschterName"
   }
   ```

### 📋 **Beispiel config.json:**
```json
{
    "discord_user_id": "123456789012345678",
    "bot_api_url": "http://159.69.90.26:5000/api/telemetry/submit",
    "port": 20777,
    "bot_integration": true,
    "player_name": "MaxVerstappen"
}
```

**💾 Datei speichern!**

---

## 🎮 **Schritt 7: F1 2025 UDP-Einstellungen**

### ⚙️ **F1 2025 Telemetrie aktivieren:**
1. **F1 2025 starten**
2. **Hauptmenü** → **Einstellungen** (Settings)
3. **Telemetrie** (Telemetry) Tab
4. **Folgende Einstellungen setzen:**

```
✅ UDP Telemetrie Output: AN (ON)
✅ UDP Format: 2025
✅ UDP Port: 20777
✅ UDP IP Address: 127.0.0.1
✅ UDP Send Rate: 60 Hz

✅ Car Telemetry Data: AN
✅ Car Status Data: AN
✅ Motion Data: AN
✅ Session Data: AN
✅ Lap Data: AN (WICHTIG!)
✅ Event Data: AN
✅ Participants Data: AN
```

5. **Einstellungen speichern**

---

## 🚀 **Schritt 8: Erstes Test - UDP-Listener starten**

### 🎯 **UDP-Listener starten:**
1. **CMD im F1-Lap-Bot Ordner öffnen**
2. **UDP-Listener starten:**
   ```bash
   python udp_listener.py
   ```

3. **Du solltest sehen:**
   ```
   🏎️ F1 2025 Telemetry Listener started on port 20777
   🎯 Monitoring for Time Trial sessions...
   ⚠️  Make sure F1 2025 UDP telemetry is enabled in game settings!
   📡 Waiting for telemetry data...
   ```

### 🏁 **Time Trial fahren:**
1. **F1 2025:** **Time Trial** Mode wählen
2. **Monaco** oder andere Strecke auswählen
3. **Gültige Runde fahren** (keine Corner Cuts!)

### ✅ **Bei erfolgreicher Übertragung siehst du:**
```
🏁 Time Trial session detected!
📍 Track: Monaco (ID: 6)
🎮 Session Type: Time Trial
✅ Ready to capture lap times!

🏆 Valid lap completed!
⏱️  Time: 1:23.456
📍 Track: Monaco
🎯 Sectors: S1: 28.123 | S2: 31.456 | S3: 23.877
🆕 Personal Best (🎉 First time on this track!)
🤖 Submitting to central bot server: 1:23.456 on monaco
📊 Telemetry lap received: MaxVerstappen - 1:23.456 on monaco
```

---

## 🚨 **Troubleshooting - Wenn es nicht funktioniert**

### ❌ **"python ist nicht erkannt"**
**Problem:** Python nicht im PATH  
**Lösung:** Python neu installieren mit "Add to PATH" ✅

### ❌ **"pip ist nicht erkannt"**
**Problem:** pip nicht installiert  
**Lösung:** 
```bash
python -m ensurepip --upgrade
```

### ❌ **"No module named 'discord'"**
**Problem:** Dependencies nicht installiert  
**Lösung:**
```bash
pip install -r requirements.txt
```

### ❌ **"Keine Telemetrie-Daten empfangen"**
**Checkliste:**
- ✅ F1 2025 UDP Telemetrie ist **AN**
- ✅ UDP Port ist **20777**
- ✅ UDP IP ist **127.0.0.1**
- ✅ **Time Trial** Mode (nicht Practice!)
- ✅ UDP-Listener läuft **vor** F1 2025 Start

### ❌ **"Runden werden nicht erkannt"**
**Problem:** Ungültige Runden  
**Lösung:**
- ✅ **Time Trial** Session fahren
- ✅ **Keine Corner Cuts**
- ✅ **Keine Flashbacks**
- ✅ Rundenzeit zwischen **30s - 5min**

### ❌ **"Failed to submit to bot server"**
**Problem:** Server nicht erreichbar  
**Lösung:**
- ✅ Internet-Verbindung prüfen
- ✅ `bot_api_url` in config.json prüfen
- ✅ `discord_user_id` korrekt?

---

## 🎯 **Optimal Settings - Kurz-Checkliste**

### ✅ **F1 2025 Settings:**
```
UDP Telemetrie: AN
UDP IP: 127.0.0.1
UDP Port: 20777
Format: 2025
Alle Daten: AN
```

### ✅ **config.json:**
```json
{
    "discord_user_id": "DEINE_18_STELLIGE_ID",
    "bot_api_url": "http://159.69.90.26:5000/api/telemetry/submit",
    "port": 20777,
    "bot_integration": true,
    "player_name": "DeinName"
}
```

### ✅ **Game Mode:**
- **Time Trial** (nicht Practice!)
- **Einzelspieler**
- **Gültige Runden** fahren

---

## 🎉 **Erfolgreich? Glückwunsch!**

Wenn alles funktioniert, siehst du deine Rundenzeiten automatisch im Discord Bot!

### 🔄 **Für die Zukunft:**
1. **UDP-Listener starten:** `python udp_listener.py`
2. **F1 2025 Time Trial fahren**
3. **Automatische Übertragung genießen!** 🏎️

### 📞 **Support:**
Bei Problemen im Discord-Server nachfragen oder GitHub Issues erstellen.

---

**🏁 Viel Erfolg beim Fahren und Happy Racing!** 🚀
