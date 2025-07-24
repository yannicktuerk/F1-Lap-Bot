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

## 🔄 Changelog

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
