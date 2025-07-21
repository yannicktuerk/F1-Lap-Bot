# 🏁 F1 Lap Time Discord Bot

Ein Discord Bot für das Tracking von F1 Rundenzeiten mit Live-Leaderboard, persönlichen Bestzeiten und automatischen Benachrichtigungen.

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

- **Benachrichtigungen bei Überholen**  
  Direkte DM an den bisherigen Führenden, sobald jemand die Spitze übernimmt

- **Hall of Fame & History**  
  Chronologische Logs aller neuen Bestzeiten in separatem Kanal

- **Persönliche Statistiken**  
  Detaillierte Auswertung der eigenen Rundenzeiten mit `/lap stats`

### 🎮 Verfügbare Commands

| Command | Beschreibung |
|---------|-------------|
| `/lap submit <zeit> <strecke>` | Rundenzeit einreichen |
| `/lap leaderboard <strecke>` | Leaderboard für Strecke anzeigen |
| `/lap stats` | Persönliche Statistiken |
| `/lap tracks` | Alle verfügbaren Strecken auflisten |
| `/lap init [kanal]` | Leaderboard initialisieren (Admin) |

### 🏎️ Unterstützte Strecken

Alle 2025 F1-Strecken sind verfügbar:
- **Bahrain** (bahrain)
- **Saudi-Arabien** (saudi, jeddah)
- **Australien** (australia, albert-park)
- **Baku** (baku)
- **Miami** (miami)
- **Imola** (imola)
- **Monaco** (monaco)
- **Spanien** (spain, barcelona, catalunya)
- **Kanada** (canada, villeneuve)
- **Österreich** (austria, red-bull-ring)
- **Silverstone** (silverstone)
- **Ungarn** (hungary, hungaroring)
- **Spa** (spa, spa-francorchamps)
- **Niederlande** (netherlands, zandvoort)
- **Monza** (monza)
- **Singapur** (singapore, marina-bay)
- **Japan** (japan, suzuka)
- **Katar** (qatar, losail)
- **USA** (usa, cota)
- **Mexiko** (mexico, hermanos-rodriguez)
- **Brasilien** (brazil, interlagos)
- **Las Vegas** (las-vegas, vegas)
- **Abu Dhabi** (abu-dhabi, yas-marina)

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

## 📄 License

Dieses Projekt ist unter der MIT License lizenziert - siehe [LICENSE](LICENSE) Datei für Details.

## 🏆 Credits

Entwickelt mit Clean Architecture Prinzipien für maximale Wartbarkeit und Testbarkeit.

---

**🏁 Ready to race? Start your engines and track those lap times!**
