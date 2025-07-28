# 🏁 F1 Lap Time Discord Bot

Ein Discord Bot für das Tracking von F1 Rundenzeiten mit Live-Leaderboard, Advanced Analytics, Driver Rivalries und automatischen Benachrichtigungen.

## 🚀 Quick Start

1. **Repository klonen:**
   ```bash
   git clone https://github.com/yourusername/f1-lap-bot.git
   cd f1-lap-bot
   ```

2. **Dependencies installieren:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment konfigurieren:**
   ```bash
   cp .env.example .env
   # .env bearbeiten und Discord Bot Token eintragen
   ```

4. **Bot starten:**
   ```bash
   python src/main.py
   ```

## 📋 Features

### ⚡ Kernfunktionen

- **Rundenzeiten erfassen**  
  Slash-Command `/lap submit <Zeit> <Strecke>` mit automatischer Format- und Plausibilitätsprüfung

- **Live-Leaderboard**  
  Statisch gepinnter Embed im Kanal mit Top-5-Ansicht, automatisches Update bei jeder neuen Eintragung

- **Global Leaderboard**  
  Übersicht aller Streckenrekorde mit farbkodiertem System zur Fahrer-Identifikation

- **Benachrichtigungen bei Überholen**  
  Direkte DM an den bisherigen Führenden, sobald jemand die Spitze übernimmt

- **Hall of Fame & History**  
  Chronologische Logs aller neuen Bestzeiten in separatem Kanal

- **Persönliche Statistiken**  
  Detaillierte Auswertung der eigenen Rundenzeiten mit `/lap stats`

### 📊 Advanced Analytics

- **Analytics Dashboard**  
  Umfassende Performance-Einblicke mit Hall of Fame, Speed Demons, Track Difficulty Analysis und Consistency Rankings

- **Track Heatmap**  
  Visualisierung der Strecken-Popularität mit "heißen" und "kalten" Tracks sowie Speed Zones

- **Driver Rivalries**  
  Head-to-Head Vergleiche zwischen Fahrern mit Rivalry-Rankings und Dominanz-Statistiken

### 🧠 ELO Rating System

- **AI-Powered Skill Assessment**  
  Intelligente Fahrerbeurteilung basierend auf ELO-Rating mit virtuellen Time-Trial Matches

- **Dynamic Skill Levels**  
  7 Skill-Kategorien von Beginner bis Legendary mit automatischem Ranking-Update

- **Competitive Leaderboard**  
  Globale ELO-Rangliste mit Win-Rate und Match-Statistiken

#### 🏆 Skill Levels & Ranks

Das ELO-System verwendet 7 verschiedene Skill-Level mit entsprechenden Symbolen:

| ELO Range | Rank | Symbol | Beschreibung |
|-----------|------|--------|--------------|
| 2200+ | **Legendary** | 👑 | Absolute Elite - Meister der Rennstrecke |
| 2000-2199 | **Master** | 🔥 | Expertenklasse - Konsistent schnelle Zeiten |
| 1800-1999 | **Expert** | ⚡ | Fortgeschrittene Fahrer mit hohem Skill |
| 1600-1799 | **Advanced** | 🎯 | Erfahrene Fahrer mit gutem Verständnis |
| 1400-1599 | **Intermediate** | 📈 | Solide Grundlagen, stetige Verbesserung |
| 1200-1399 | **Novice** | 🌱 | Lernphase - Erste Erfahrungen sammeln |
| 800-1199 | **Beginner** | 🏁 | Einsteiger - Erste Schritte auf der Strecke |

**💡 Pro-Tip:** Dein ELO steigt durch bessere Lap-Times im Vergleich zu anderen Fahrern!

#### 🥇 Leaderboard Symbole

In Leaderboards werden verschiedene Symbole für Positionen verwendet:

- **🥇** - 1. Platz (Gold)
- **🥈** - 2. Platz (Silber)  
- **🥉** - 3. Platz (Bronze)
- **👑** - Dominantester Fahrer (höchste Win-Rate)
- **🏆** - Top 3 in verschiedenen Kategorien
- **🔥🔥🔥** - Intensive Rivalries (sehr ausgeglichen)
- **🔥🔥** - Starke Rivalries (nah beieinander)
- **🔥** - Rivalries (trotzdem interessant)

### 🎮 Verfügbare Commands

#### 🏁 Basis Commands
| Command | Beschreibung |
|---------|-------------|
| `/lap submit <zeit> <strecke>` | Rundenzeit einreichen |
| `/lap leaderboard <strecke>` | Leaderboard für spezifische Strecke |
| `/lap global` | Globales Leaderboard aller Streckenrekorde |
| `/lap stats` | Persönliche Statistiken |
| `/lap tracks` | Alle verfügbaren Strecken auflisten |
| `/lap info <strecke>` | Detaillierte Strecken-Informationen |
| `/lap challenge` | Zufällige Strecken-Challenge |
| `/lap delete <strecke> <zeit>` | Spezifische Zeit löschen |
| `/lap deletelast` | Letzte eingetragene Zeit löschen |
| `/lap deleteall <strecke>` | ALLE eigenen Zeiten für eine Strecke löschen |
| `/lap username <name>` | Display-Namen für alle Einträge ändern |
| `/lap help` | Vollständige Command-Übersicht mit Quick Start Guide |

#### 📊 Analytics Commands
| Command | Beschreibung |
|---------|-------------|
| `/lap analytics` | Advanced Analytics Dashboard |
| `/lap heatmap` | Strecken-Popularität und Performance Heatmap |
| `/lap rivalries` | Driver Rivalries und Head-to-Head Statistiken |

#### 🧠 ELO Rating Commands
| Command | Beschreibung |
|---------|-------------|
| `/lap rating` | AI-powered ELO Skill Rating und Analyse |
| `/lap elo-leaderboard` | Globale ELO-Rangliste der Top-Fahrer |
| `/lap elo-rank-help` | Vollständige ELO-Ranking-System-Anleitung |

#### ⚙️ Admin Commands
| Command | Beschreibung |
|---------|-------------|
| `/lap init [kanal]` | Leaderboard initialisieren (Admin only) |
| `/lap reset <password>` | Datenbank zurücksetzen mit Passwort-Schutz (Admin only) |

### 🏎️ Unterstützte Strecken

Alle 2025 F1-Strecken sind verfügbar mit Länder-/Stadt-Aliases:
- **Bahrain** (bahrain)
- **Saudi-Arabien** (saudi, jeddah)
- **Australien** (australia, albert-park)
- **Baku** (baku, azerbaijan)
- **Miami** (miami, usa-miami)
- **Imola** (imola, italy-imola)
- **Monaco** (monaco)
- **Spanien** (spain, barcelona, catalunya)
- **Kanada** (canada, villeneuve)
- **Österreich** (austria, red-bull-ring)
- **Silverstone** (silverstone, uk, britain)
- **Ungarn** (hungary, hungaroring, budapest)
- **Spa** (spa, spa-francorchamps, belgium)
- **Niederlande** (netherlands, zandvoort)
- **Monza** (monza, italy-monza)
- **Singapur** (singapore, marina-bay)
- **Japan** (japan, suzuka)
- **Katar** (qatar, losail)
- **USA** (usa, cota, austin, houston)
- **Mexiko** (mexico, hermanos-rodriguez)
- **Brasilien** (brazil, interlagos, sao-paulo)
- **Las Vegas** (las-vegas, vegas, nevada)
- **Abu Dhabi** (abu-dhabi, yas-marina, uae)

**💡 Pro-Tip:** Du kannst auch Städtenamen wie "houston", "baku" oder "austin" verwenden!

### 📊 Zeit-Formate

- `1:23.456` (1 Minute, 23.456 Sekunden)
- `83.456` (83.456 Sekunden)

Plausibilitätsprüfung: 30 Sekunden bis 5 Minuten

## 🏗️ Clean Architecture

Das Projekt folgt Clean Architecture Prinzipien:

```
src/
├── domain/                 # Geschäftslogik (innerste Schicht)
│   ├── entities/          # Geschäftsobjekte
│   ├── value_objects/     # Unveränderliche Wertobjekte
│   └── interfaces/        # Ports (Abstrakte Schnittstellen)
├── application/           # Anwendungslogik
│   └── use_cases/         # Anwendungsfälle
├── infrastructure/        # Externe Schnittstellen
│   └── persistence/       # Datenbank-Implementierungen
└── presentation/          # Benutzeroberfläche
    ├── bot/              # Discord Bot
    └── commands/         # Slash Commands
```

### 🔧 Dependency Rule

- Innere Schichten kennen keine äußeren Schichten
- Geschäftslogik ist Framework-unabhängig
- Testbar durch Dependency Injection

## ⚙️ Konfiguration

### Environment Variablen

```env
DISCORD_TOKEN=your_discord_bot_token_here
GUILD_ID=your_discord_guild_id_here
LEADERBOARD_CHANNEL_ID=channel_id_for_leaderboard
HISTORY_CHANNEL_ID=channel_id_for_history
RESET_PASSWORD=your_secure_reset_password_here
```

### Discord Bot Setup

1. Discord Developer Portal öffnen
2. Neue Application erstellen
3. Bot erstellen und Token kopieren
4. Bot Permissions: `Send Messages`, `Use Slash Commands`, `Embed Links`, `Manage Messages`
5. Bot zu Server einladen

## 🗄️ Datenbankschema

SQLite Datenbank mit folgender Struktur:

```sql
CREATE TABLE lap_times (
    lap_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    username TEXT NOT NULL,
    track_key TEXT NOT NULL,
    time_minutes INTEGER NOT NULL,
    time_seconds INTEGER NOT NULL,
    time_milliseconds INTEGER NOT NULL,
    total_milliseconds INTEGER NOT NULL,
    is_personal_best BOOLEAN DEFAULT 0,
    is_overall_best BOOLEAN DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE driver_ratings (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    current_elo INTEGER NOT NULL DEFAULT 1000,
    peak_elo INTEGER NOT NULL DEFAULT 1000,
    matches_played INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    last_updated TEXT NOT NULL
);
```

## 🧪 Testing

```bash
# Unit Tests ausführen
python -m pytest tests/

# Mit Coverage
python -m pytest tests/ --cov=src/
```

## 📝 Development Guidelines

### Code Style
- **Readability First:** Kleine Klassen (≤200 Zeilen), kleine Methoden (≤30 Zeilen)
- **Domain Language:** Vollständige, beschreibende Namen
- **SOLID Prinzipien:** Single Responsibility, Dependency Inversion
- **Auto-Formatting:** Code wird automatisch formatiert

### Testing Strategy
- **Domain Layer:** 90% Branch Coverage, reine Unit Tests
- **Use Case Layer:** 80% Coverage, gemockte Repositories
- **Infrastructure Layer:** Integration Tests mit echten Dependencies
- **Testing Pyramid:** 70% Unit / 20% Integration / 10% E2E

## 🎮 F1 2025 UDP Telemetrie Integration

### Automatische Rundenzeit-Erfassung aus F1 2025

> **⚠️ Wichtig:** Auch wenn der Discord Bot zentral auf dem Server läuft, muss **jeder Spieler** das UDP-Listener Script auf seinem eigenen PC installieren und ausführen!

Der Bot kann automatisch Rundenzeiten direkt aus F1 2025 (Time Trial Mode) über UDP Telemetrie erfassen.

#### 🚀 Setup-Anleitung für Spieler

**Schritt 1: Repository klonen oder UDP-Script herunterladen**
```bash
# Option A: Gesamtes Repository klonen
git clone [repository-url]
cd f1-lap-bot

# Option B: Nur udp_listener.py herunterladen
# Lade udp_listener.py von GitHub herunter
```

**Schritt 2: Python-Abhängigkeiten installieren**
```bash
# Erforderliche Pakete installieren
pip install requests
```

**Schritt 3: F1 2025 Telemetrie aktivieren**
1. Starte F1 2025
2. Gehe zu **Einstellungen** → **Telemetrie**
3. Aktiviere **UDP Telemetrie Output**
4. Port: `20777` (Standard)
5. IP-Adresse: `127.0.0.1` (für lokalen Betrieb)
6. Format: **2025** (neuestes Format)

**Schritt 4: Konfiguration für Bot-Integration erstellen**
```bash
# Konfigurationsdatei erstellen
cp config_example.json config.json

# config.json bearbeiten - siehe detaillierte Erklärung unten!
```

### 📋 Detaillierte Konfigurationserklärung

**config.json Beispiel:**
```json
{
    "discord_user_id": "123456789012345678",
    "bot_api_url": "https://your-bot-server.herokuapp.com/api/telemetry/submit",
    "port": 20777,
    "bot_integration": true,
    "player_name": "MaxVerstappen"
}
```

#### 🔧 Konfigurationswerte erklärt:

**1. `discord_user_id` - Deine Discord Benutzer-ID**
- **Was ist das?** Deine eindeutige Discord-Nummer (18 Ziffern)
- **Wo finde ich die?** 
  1. Discord öffnen → Einstellungen → Erweitert → Entwicklermodus aktivieren
  2. Rechtsklick auf deinen Namen → "Benutzer-ID kopieren"
- **Beispiel:** `"123456789012345678"`
- **Wichtig:** Muss in Anführungszeichen stehen!

**2. `bot_api_url` - Server-URL des zentralen Discord Bots**
- **Was ist das?** Die HTTP-Adresse, wo der Discord Bot auf dem Server läuft
- **Wo bekomme ich die?** Vom Bot-Administrator/Server-Owner
- **Beispiele:**
  - `"https://your-bot-server.herokuapp.com/api/telemetry/submit"`
  - `"http://192.168.1.100:8080/api/telemetry/submit"` (lokales Netzwerk)
  - `"https://f1bot.dein-server.de/api/telemetry/submit"`
- **Wichtig:** Muss `/api/telemetry/submit` am Ende haben!

**3. `player_name` - Dein Spielername (optional)**
- **Was ist das?** Ein Anzeigename für Logs und Debugging
- **Beispiele:** `"MaxVerstappen"`, `"Hamilton44"`, `"YourNickname"`
- **Hinweis:** Wird NUR für lokale Anzeige verwendet, nicht für Discord!

**4. `port` - UDP Port für F1 2025 Telemetrie**
- **Standard:** `20777` (normalerweise nicht ändern)
- **Wann ändern?** Nur wenn F1 2025 anderen Port verwendet

**5. `bot_integration` - Automatische Übertragung**
- **`true`:** Rundenzeiten werden automatisch an Discord Bot gesendet
- **`false`:** Nur lokale Anzeige, keine automatische Übertragung

#### ❓ Häufige Fragen zur Konfiguration:

**F: Woher bekomme ich die `bot_api_url`?**
A: Vom Administrator des Discord-Servers, wo der F1-Bot läuft. Frage nach der "Telemetrie-API URL".

**F: Was passiert, wenn die `discord_user_id` falsch ist?**
A: Der Bot kann deine Rundenzeiten nicht zuordnen und sie werden abgelehnt.

**F: Kann ich mehrere Konfigurationen haben?**
A: Ja! Benenne sie z.B. `config_server1.json`, `config_server2.json` und starte mit:
```bash
python udp_listener.py --config config_server1.json
```

**F: Muss ich `player_name` setzen?**
A: Nein, ist optional. Wird nur für lokale Anzeige verwendet, nicht in Discord.

---

## 🔧 Für Bot-Administratoren: HTTP-Server Setup

> **🚀 Diese Informationen sind für Personen, die den Discord Bot auf einem Server betreiben!**

Der Discord Bot startet automatisch einen HTTP-Server um Telemetrie-Daten von den UDP-Listenern zu empfangen.

### 🌐 HTTP-Server Konfiguration

**Environment-Variablen in `.env`:**
```bash
# HTTP API Server für Telemetrie (optional)
API_HOST=0.0.0.0    # IP-Adresse (0.0.0.0 = alle Interfaces)
API_PORT=8080       # Port für HTTP-Server
```

### 📍 API-Endpunkte

Der Bot stellt folgende HTTP-Endpunkte bereit:

**1. Telemetrie-Daten empfangen:**
```
POST /api/telemetry/submit
Content-Type: application/json

{
  "user_id": "123456789012345678",
  "time": "1:23.456",
  "track": "monaco",
  "source": "telemetry",
  "timestamp": "2025-07-28T13:45:00Z"
}
```

**2. Health Check:**
```
GET /api/health
```

**3. Status Information:**
```
GET /api/status
```

### 🌍 Öffentliche URL bereitstellen

Um die Bot-API-URL für Spieler bereitzustellen:

**Lokaler Server (z.B. über Router-Portweiterleitung):**
```
http://DEINE_IP:8080/api/telemetry/submit
```

**Cloud-Hosting (Heroku, Railway, etc.):**
```
https://dein-f1-bot.herokuapp.com/api/telemetry/submit
https://f1-lap-bot.railway.app/api/telemetry/submit
```

**📢 Diese URL teilst du dann mit deinen Spielern für deren `config.json`!**

**Schritt 5: UDP-Listener auf deinem PC starten**
```bash
# Terminal: UDP-Listener starten (muss auf dem gleichen PC wie F1 2025 laufen!)
python udp_listener.py
```

**Schritt 5: Time Trial Session starten**
1. Wähle **Time Trial** im F1 2025 Hauptmenü
2. Wähle eine Strecke (z.B. Monaco)
3. Fahre gültige Runden
4. **Rundenzeiten werden automatisch an den zentralen Bot gesendet!**

#### ✅ Was wird erfasst?

- ✅ **Nur Time Trial Sessions** - Andere Modi werden ignoriert
- ✅ **Nur gültige Runden** - Corner Cutting, Flashbacks etc. werden gefiltert
- ✅ **Zeitbereich 30s - 5min** - Unrealistische Zeiten werden verworfen
- ✅ **Sektor-Zeiten** - S1, S2, S3 werden mit angezeigt
- ✅ **Track-Erkennung** - Automatische Zuordnung zur richtigen Strecke

#### 🚫 Was wird NICHT erfasst?

- ❌ **Rennen/Qualifying** - Nur Time Trial Mode
- ❌ **Ungültige Runden** - Corner Cutting, Wall Riding, Flashbacks
- ❌ **Practice Sessions** - Nur dedizierte Time Trials
- ❌ **Pause/Replay** - Nur aktive Fahrzeiten

#### 🛠️ Erweiterte Konfiguration

**Bot-Integration aktivieren:**
```python
# udp_listener.py bearbeiten
listener = F1TelemetryListener(port=20777, bot_integration=True)
```

**Custom Port verwenden:**
```python
# Falls F1 2025 einen anderen Port verwendet
listener = F1TelemetryListener(port=CUSTOM_PORT, bot_integration=False)
```

#### 🔧 Troubleshooting

**Problem: Keine Telemetrie-Daten empfangen**
- ✅ F1 2025 UDP Telemetrie ist aktiviert
- ✅ Port 20777 ist nicht blockiert (Firewall)
- ✅ Time Trial Session ist aktiv
- ✅ `udp_listener.py` läuft vor dem Spielstart

**Problem: Runden werden nicht erfasst**
- ✅ Session Type ist "Time Trial" (nicht Practice)
- ✅ Runden sind gültig (keine Corner Cuts)
- ✅ Rundenzeiten liegen zwischen 30s und 5min

**Problem: Falsche Strecke erkannt**
- ✅ Track-Mapping in `udp_listener.py` prüfen
- ✅ F1 2025 Track-IDs entsprechen Bot-Strecken

#### 📊 Ausgabe-Beispiel

```
🏎️ F1 2025 Telemetry Listener started on port 20777
🎯 Monitoring for Time Trial sessions...

🏁 Time Trial session detected!
📍 Track: Monaco (ID: 6)
🎮 Session Type: Time Trial
✅ Ready to capture lap times!

🏆 Valid lap completed!
⏱️  Time: 1:23.456
📍 Track: Monaco
🎯 Sectors: S1: 28.123 | S2: 31.456 | S3: 23.877
💡 Bot integration disabled - lap time not submitted automatically
📝 To submit manually: /lap submit 1:23.456 monaco
```

#### 🔗 Integration mit Discord Bot

Für vollautomatische Integration:
1. `bot_integration=True` in `udp_listener.py` setzen
2. Bot-API-Endpunkt konfigurieren (TODO)
3. User-Mapping einrichten (Discord User ↔ Telemetrie)

---

## 🔄 Changelog

### v1.6.0 (2025-07-24)
- 🔧 **CRITICAL FIX:** Username consistency issue completely resolved
- ✅ **ENHANCED:** New lap time submissions now consistently use custom usernames set with `/lap username`
- 🏗️ **ARCHITECTURE:** Improved user display name resolution with fallback system
- 🛡️ **SECURITY:** Added bot detection to prevent bots from submitting lap times
- 📊 **QUALITY:** Database schema updated with `is_bot` field for better data integrity
- 🎯 **UX:** Seamless username experience - once set, always consistent across all submissions

### v1.5.0 (2025-07-24)
- 👤 **NEW:** `/lap username <name>` command for changing display names
- 🔄 **ENHANCED:** Username validation with length (2-32 chars) and character checks
- 📊 **IMPROVED:** All lap times and ELO ratings automatically updated with new name
- ⚡ **QUALITY:** Automatic leaderboard refresh after username change
- 🏗️ **ARCHITECTURE:** Clean Architecture implementation with UpdateUsernameUseCase

### v1.4.1 (2025-07-22)
- 🚀 **NEW:** `/lap deletelast` command for quick deletion of the most recent lap time
- 🔒 **SECURITY:** Added password protection to the database reset command
- 🔧 **ENHANCED:** Updated environment setup with reset password entry

### v1.3.3 (2025-07-22)
- 🗑️ **NEW:** `/lap deleteall <track>` command für Bulk-Löschung aller eigenen Zeiten
- 🛡️ **NEW:** Interaktive Bestätigung mit Discord-Buttons und Timeout-Schutz
- 📋 **NEW:** Vorschau der zu löschenden Zeiten vor Bestätigung
- 🔧 **ENHANCED:** Vollständiges Delete-System mit spezifischer und Bulk-Löschung

### v1.3.2 (2025-07-22)
- 🧠 **NEW:** ELO-basiertes Fahrer-Bewertungssystem implementiert
- 🏆 **NEW:** ELO-Rangliste mit Skill-Level-Anzeige
- 💬 **NEW:** Slash-Commands `/lap rating` und `/lap elo-leaderboard`

### v1.3.1 (2025-07-22)
- 🚫 **NEW:** Validation verhindert das Einreichen langsamerer Rundenzeiten
- ⚡ **ENHANCED:** Nur schnellere Zeiten als die aktuelle persönliche Bestzeit können eingereicht werden
- 📊 **IMPROVED:** Detaillierte Fehlermeldung zeigt Zeitunterschied bei langsameren Zeiten
- 🎯 **QUALITY:** Sauberere Datenbank durch Vermeidung langsamerer Zeiten

### v1.3.0 (2025-07-22)
- 🏆 **BREAKING:** Leaderboard zeigt jetzt die 10 absolut schnellsten Zeiten (nicht mehr beste pro User)
- 🎯 **NEW:** Ein User kann theoretisch mehrere Einträge in den Top 10 haben
- 📊 **NEW:** Zeit-Abstände zwischen den Positionen werden übersichtlich angezeigt
- ⚡ **IMPROVED:** Präzisere Leaderboard-Performance durch Optimierung der Datenbankabfragen
- 🏁 **ENHANCED:** Bessere Visualisierung von dominanten Performances einzelner Fahrer

### v1.2.0 (2025-07-21)
- 🔥 **NEW:** Advanced Analytics Dashboard mit Hall of Fame, Speed Demons, Track Difficulty
- 🗺️ **NEW:** Track Heatmap mit Popularitäts- und Performance-Analyse
- ⚔️ **NEW:** Driver Rivalries mit Head-to-Head Statistiken
- 🏆 **NEW:** Global Leaderboard mit farbkodiertem System
- 🌍 **NEW:** Erweiterte Strecken-Aliases (Städte/Länder: "houston", "baku", etc.)
- 🎯 **NEW:** Random Track Challenge System
- 📊 **NEW:** Detaillierte Strecken-Informationen mit `/lap info`
- 🗑️ **NEW:** Delete-Funktion für eigene Bestzeiten
- ✨ **IMPROVED:** Kompaktere Global Leaderboard Darstellung
- ✨ **IMPROVED:** Enhanced Color-Legend System

### v1.0.0 (2025-07-21)
- ✅ Initial Release
- ✅ Rundenzeiten-Tracking mit Validierung
- ✅ Live Leaderboard System
- ✅ Persönliche Bestzeiten & Statistiken
- ✅ Überhol-Benachrichtigungen
- ✅ F1 2025 Strecken-Support
- ✅ Clean Architecture Implementation
- ✅ SQLite Persistence
- ✅ Discord Slash Commands

## 🤝 Contributing

1. Fork das Repository
2. Feature Branch erstellen (`git checkout -b feature/amazing-feature`)
3. Changes committen (`git commit -m 'Add amazing feature'`)
4. Branch pushen (`git push origin feature/amazing-feature`)
5. Pull Request öffnen

## 🏆 Credits

Entwickelt mit Clean Architecture Prinzipien für maximale Wartbarkeit und Testbarkeit.

---

**🏁 Ready to race? Start your engines and track those lap times!**
