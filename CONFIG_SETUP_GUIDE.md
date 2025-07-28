# 🔧 F1 2025 UDP Telemetrie - Komplette Konfigurationsanleitung

## 📋 Übersicht
Diese Anleitung erklärt **genau**, wie du den UDP-Listener für F1 2025 konfigurierst, um automatisch Rundenzeiten an den Discord Bot zu senden.

## 🎯 Was du brauchst

### 1. Discord User ID (18 Ziffern)
**Was ist das?** Deine eindeutige Discord-Nummer zur Identifikation
**Beispiel:** `123456789012345678`

**Wie finde ich meine Discord User ID?**
1. Discord öffnen
2. **Einstellungen** (Zahnrad unten links)
3. **Erweitert** → **Entwicklermodus aktivieren** ✅
4. Zurück zu einem Chat → **Rechtsklick auf deinen Namen**
5. **"Benutzer-ID kopieren"** klicken
6. Die kopierte Nummer ist deine `discord_user_id`

### 2. Bot API URL (Server-Adresse)
**Was ist das?** Die Internetadresse, wo der Discord Bot läuft
**Format:** `https://server-adresse.com/api/telemetry/submit`

**Wo bekomme ich die Bot API URL?**
- Vom **Discord-Server Administrator**
- Vom **Bot-Betreiber**
- Frage: *"Wie lautet die Telemetrie-API URL für den F1-Bot?"*

**Beispiele für Bot API URLs:**
```
https://f1bot.herokuapp.com/api/telemetry/submit
https://f1-lap-bot.railway.app/api/telemetry/submit
http://192.168.1.100:8080/api/telemetry/submit
https://dein-server.de/api/telemetry/submit
```

**⚠️ WICHTIG:** Die URL muss **immer** mit `/api/telemetry/submit` enden!

### 3. Player Name (Optional)
**Was ist das?** Ein Name für die lokalen Logs (wird NICHT in Discord angezeigt)
**Beispiele:** `MaxVerstappen`, `Hamilton44`, `YourNickname`
**Hinweis:** Nur für deine lokale Anzeige, hat NICHTS mit Discord zu tun!

## 📝 Schritt-für-Schritt Konfiguration

### Schritt 1: Konfigurationsdatei erstellen
```bash
# Im f1-lap-bot Ordner
cp config_example.json config.json
```

### Schritt 2: config.json bearbeiten
Öffne `config.json` mit einem Texteditor und fülle die Werte:

```json
{
    "discord_user_id": "HIER_DEINE_18_STELLIGE_DISCORD_ID",
    "bot_api_url": "HIER_DIE_BOT_SERVER_URL",
    "port": 20777,
    "bot_integration": true,
    "player_name": "HIER_DEIN_GEWÜNSCHTER_NAME"
}
```

### Schritt 3: Beispiel mit echten Werten
```json
{
    "discord_user_id": "123456789012345678",
    "bot_api_url": "https://f1bot.herokuapp.com/api/telemetry/submit",
    "port": 20777,
    "bot_integration": true,
    "player_name": "MaxVerstappen"
}
```

## ✅ Validierung der Konfiguration

### Discord User ID prüfen
```bash
# Starte den Listener mit --test Flag
python udp_listener.py --test
```
- **✅ Korrekt:** 18 Ziffern, keine Buchstaben
- **❌ Falsch:** Zu kurz, enthält Buchstaben oder Sonderzeichen

### Bot API URL testen
```bash
# Teste die Verbindung zum Bot-Server
curl -X POST "DEINE_BOT_API_URL" -H "Content-Type: application/json" -d '{"test": true}'
```
- **✅ Korrekt:** Bekommt eine Antwort (auch Fehler ist OK)
- **❌ Falsch:** Timeout oder "Verbindung fehlgeschlagen"

## 🚨 Häufige Fehler und Lösungen

### Fehler: "Discord User ID not configured"
**Problem:** `discord_user_id` ist leer oder falsch
**Lösung:** Discord User ID kopieren und in `config.json` einfügen (in Anführungszeichen!)

### Fehler: "Failed to submit to bot server"
**Problem:** Bot API URL ist falsch oder Bot ist offline
**Lösung:** 
1. Bot API URL vom Administrator erfragen
2. Prüfen ob URL mit `/api/telemetry/submit` endet
3. Server-Status beim Administrator erfragen

### Fehler: "Connection refused"
**Problem:** Bot-Server ist nicht erreichbar
**Lösung:** 
1. Internet-Verbindung prüfen
2. URL nochmals validieren
3. Administrator kontaktieren

### Fehler: Rundenzeiten werden nicht übertragen
**Checkliste:**
- ✅ `bot_integration: true` gesetzt?
- ✅ Discord User ID korrekt?
- ✅ Bot API URL korrekt?
- ✅ Time Trial Mode aktiv?
- ✅ Gültige Runden gefahren?

## 📞 Support und Hilfe

**Bei Problemen:**
1. **Discord Server Administrator** fragen
2. **Bot-Logs** prüfen auf Server-Seite
3. **UDP-Listener Konsole** auf Fehlermeldungen prüfen
4. Diese Anleitung nochmals durchgehen

**Wichtige Infos für Support-Anfragen:**
- Deine Discord User ID (ersten/letzten 4 Ziffern)
- Die verwendete Bot API URL (ohne sensible Teile)
- Fehlermeldung aus der Konsole
- F1 2025 Telemetrie-Einstellungen

---
**🏎️ Viel Erfolg beim Setup! Bei Fragen einfach im Discord-Server nachfragen.**
