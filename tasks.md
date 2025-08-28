# 1) Paket-Header & IDs (Pflichtwissen)

* **Header lesen** (Little Endian, packed). Wichtige Felder:
  `m_packetId` (Typ, siehe Tabelle), `m_sessionUID`, `m_sessionTime`, `m_frameIdentifier`, `m_playerCarIndex` (Index deines Autos in Arrays).&#x20;
* **Packet IDs (Auszug, TT-relevant):**
  `1=Session`, `2=Lap Data`, `6=Car Telemetry`, `13=Motion Ex` (nur Player-Car), `14=Time Trial`.&#x20;
* **Vehicle-Index bleibt stabil**; max. 22 Fahrzeuge. Für *aktive* Fahrzeuge s. `m_numActiveCars` (Participants).&#x20;

---

# 2) Nur die Pakete, die der TT-Coach wirklich braucht

> In jedem Paket: erst `PacketHeader` prüfen, dann Daten für `m_playerCarIndex` ziehen (außer Time Trial, siehe unten).

## (A) Session (ID=1) — 2 Hz

**Zweck:** Session-Kontext & Erkennung von TT, Trackdaten, Sektor-Grenzen, Assist-Flags.

* **Felder:**
  `m_trackLength` (m), `m_trackId`, `m_gameMode`, `m_sessionType`, `m_ruleSet`, `m_sector2LapDistanceStart`, `m_sector3LapDistanceStart`, diverse Assist-Flags (`m_steeringAssist`, `m_brakingAssist`, `m_gearboxAssist`, `m_dynamicRacingLine`, …).  &#x20;
* **TT-Erkennung:** *Game Mode IDs*: **Time Trial = 5**; *Session Types*: **Time Trial = 18**. Nutze beides als Gate.  &#x20;

## (B) Lap Data (ID=2) — Menü-Rate (z. B. 60 Hz)

**Zweck:** **Achse „Strecken-Position“** + Lap-Status.

* **Felder (pro Car):**
  `m_lapDistance` (m, kann <0 vor Start/Ziellinie), `m_currentLapTimeInMS`, `m_currentLapInvalid` (0=valid, 1=invalid), `m_sector` (0/1/2).&#x20;
* **TT-Spezial in PacketLapData (am Ende):** `m_timeTrialPBCarIdx`, `m_timeTrialRivalCarIdx` (255 wenn nicht gesetzt).&#x20;

## (C) Car Telemetry (ID=6) — Menü-Rate

**Zweck:** **Fahrereingaben & Geschwindigkeit** → Brems-/Gas-Events & Profile.

* **Felder (pro Car):**
  `m_speed` (km/h), `m_throttle` (0..1), `m_steer` (-1..1), `m_brake` (0..1), `m_gear` (N=0, R=-1), `m_engineRPM`, `m_drs`, … (plus Temp/Drücke falls benötigt). &#x20;
* **Hinweis Rate:** „**Rate as specified in menus**“.&#x20;

## (D) Motion Ex (ID=13) — Menü-Rate, **nur Player-Car**

**Zweck:** Feine Dynamik für Lern-Features (Lokalgschw., Winkel-Dynamik, Wheel-Slip).

* **Felder (nur **dein** Auto):**
  `m_localVelocityX/Y/Z` (m/s), `m_angularVelocity*`, `m_angularAcceleration*`, `m_frontWheelsAngle`, `m_wheelSpeed[4]`, `m_wheelSlipRatio[4]`, `m_wheelSlipAngle[4]`, `m_wheelLat/LongForce[4]`, etc. &#x20;

## (E) Time Trial (ID=14) — **1 Hz**

**Zweck:** **PB/Session-Best/Rival** + **Assist-Zustand** + **Valid-Flag** für TT.

* **Struktur:** `PacketTimeTrialData` mit drei `TimeTrialDataSet`: *playerSessionBest*, *personalBest*, *rival*. Pro DataSet:
  `m_carIdx`, `m_teamId`, `m_lapTimeInMS`, `m_sector1/2/3TimeInMS`, `m_tractionControl`, `m_gearboxAssist`, `m_antiLockBrakes`, `m_equalCarPerformance`, `m_customSetup`, **`m_valid` (0/1)**. Nur in **TT-Mode** gesendet. &#x20;

---

# 3) Minimaler Datenfluss (TT-Gate, Indizierung, Extraktion)

**Gate (TT-only):** Verarbeite Pakete **nur**, wenn
`Session.m_gameMode==5` **oder** `Session.m_sessionType==18`.  &#x20;

**Indexierung:** Für Array-Pakete nutze immer `m_playerCarIndex`, um **dein** Fahrzeug aus `m_*[22]` zu nehmen.&#x20;

**Zentrale Lesewege (Pseudocode-Mapping):**

* **Distanz & Lap-Status:**
  `LapData = PacketLapData.m_lapData[playerIdx];`
  `s = LapData.m_lapDistance;` • `lapInvalid = LapData.m_currentLapInvalid==1;`&#x20;
* **Driver I/O (pro Frame):**
  `Tel = PacketCarTelemetryData.m_carTelemetryData[playerIdx];`
  `v_kph=Tel.m_speed; throttle=Tel.m_throttle; brake=Tel.m_brake; steer=Tel.m_steer; gear=Tel.m_gear; rpm=Tel.m_engineRPM;`&#x20;
* **Feindynamik (optional für Lernmodelle):**
  `ME = PacketMotionExData;` (player-only) → `localVx/Vy/Vz`, `angVel*`, `angAcc*`, `frontWheelsAngle`, `wheelSlipRatio[4]`, …&#x20;
* **TT-Meta & Validität:**
  `TT = PacketTimeTrialData;` → `TT.m_personalBestDataSet.m_valid` (0/1) sowie PB/Session-Best/Rival Lap/Sektorzeiten.&#x20;

---

# 4) DB-Schema (kompakt, genau das Nötige) + Feld-Quelle

## 4.1 `laps`

* `session_uid` (Header)&#x20;
* `track_id`, `track_length_m` (Session)&#x20;
* `game_mode`, `session_type`, `rule_set` (Session) &#x20;
* `assist_flags_json` (Session-Assists)&#x20;
* `lap_time_ms`, `s1_ms`, `s2_ms`, `s3_ms` (aus **TT-DataSet.personalBest** *oder* *LapHistory*, falls gewünscht) &#x20;
* `is_valid` (**TT-valid** *und* `LapData.m_currentLapInvalid==0`) &#x20;

## 4.2 `track_curves`

* `track_id`, `turn_number`, `s_entry_m`, `s_apex_m`, `s_exit_m`
  (wird von dir aus **LapData.m\_lapDistance** + Telemetry-Ereignissen erzeugt; Sektor-Starts helfen beim Normalisieren). &#x20;

## 4.3 `lap_curve_metrics` (Coach-Kern)

* pro Kurve:
  `brake_start_m`, `apex_m`, `throttle_on_m`, `trail_end_m`,
  `v_entry_ms`, `v_min_ms`, `v_exit_ms`, `peak_decel_ms2`, `brake_peak`,
  `time_in_turn_ms`, `anomalies_json`
  (abgeleitet aus **Car Telemetry** + **LapData.m\_lapDistance**; optional Feinschliff mit **Motion Ex**).  &#x20;

## 4.4 `reference_profiles` (Median-Profile je Turn & Setup)

* `filter_hash` (Assist-Zustand + Wetter/Surface falls gebraucht), `p50_*`, `iqr_*`, `basis_count`, `updated_at`.
  (Assist-Zustände sowohl aus **Session** als auch **TT-DataSet** verfügbar). &#x20;

---

# 5) Online-Detektion für Coaching (TT)

**Eingang:** pro Frame **Lap Data + Car Telemetry** (ggf. Motion Ex).
**Indices:** `playerIdx = PacketHeader.m_playerCarIndex`.&#x20;

**Events (robust, jitter-arm):**

* **Brake-On:** `Tel.m_brake` steigt über \~0.06 **und** (optional) Long-a < −1.0 m/s² (aus `localVelocity`-Ableitung, falls ME genutzt). Quelle Werte: Brake 0..1, Local-Vel vorhanden. &#x20;
* **Brake-Peak / Trail-End:** Minimum Long-a während Bremsphase, Ende wenn `m_brake<0.06` bzw. Long-a > −0.2 m/s². (Datenbasis s. oben) &#x20;
* **Throttle-On:** `Tel.m_throttle` > \~0.25 für ≥120 ms.&#x20;
* **Geschwindigkeiten:** `v_entry/v_min/v_exit` aus `m_speed` entlang **`m_lapDistance`**. &#x20;

**Valid-Runden-Filter:**

* Rundendaten nur persistieren/lernen, wenn **`TT.m_personalBestDataSet.m_valid==1`** *und* `LapData.m_currentLapInvalid==0`. &#x20;

---

# 6) TT-Coach: was er daraus live/coaching-seitig macht

* **Bremspunkt-Feedback:** Vergleiche `brake_start_m` mit deinem Referenz-Median (`reference_profiles`) je Kurve und gib **Delta-Meter** & **Delta-Zeit** aus (positive Werte = zu spät). Basisdaten siehe oben.
* **Kurven-Tempo:** Melde pro Turn `v_min_ms`-Abweichung zu Ref, plus *Exit*-Tempo (`v_exit_ms`) für bessere Carry-Speed-Hinweise.
* **Pedal-Koordination:** Detektiere **Overlap** (Trail-Braking bis `trail_end_m` und Zeitpunkt `throttle_on_m`).
* **Runden-/Sektor-Kontext:** Nutze `TT.m_playerSessionBestDataSet` & `Lap Data`-Sektorstatus, um gezielt die größten Zeitverluste anzuzeigen. &#x20;

---

# 7) Felder-Spickzettel (quick lookup)

* **Session (ID 1, 2 Hz):** `m_trackLength`, `m_trackId`, `m_gameMode`, `m_sessionType`, `m_ruleSet`, `m_sector2LapDistanceStart`, `m_sector3LapDistanceStart`, Assist-Flags.  &#x20;
* **Lap Data (ID 2, Menü-Rate):** `m_lapDistance`, `m_currentLapTimeInMS`, `m_currentLapInvalid`, `m_sector`, `m_timeTrialPBCarIdx`, `m_timeTrialRivalCarIdx`. &#x20;
* **Car Telemetry (ID 6, Menü-Rate):** `m_speed`, `m_throttle`, `m_brake`, `m_steer`, `m_gear`, `m_engineRPM`, `m_drs`.&#x20;
* **Motion Ex (ID 13, Menü-Rate):** `m_localVelocity*`, `m_angularVelocity*`, `m_angularAcceleration*`, `m_frontWheelsAngle`, `m_wheelSlipRatio[4]`, … (nur Player-Car).&#x20;
* **Time Trial (ID 14, 1 Hz):** `m_*BestDataSet`, `m_rivalDataSet` → Zeiten, Assists, **`m_valid`**.&#x20;

---

## Bonus (nur wenn nötig, aber Quelle parat)

* **„Restricted data“ Liste** (welche Felder bei Fremd-Autos 0 werden) + *du siehst dein Auto immer*.&#x20;
* **Track IDs / Game Mode IDs / Session Types** (für UI/Mapping).  &#x20;

---

### TL;DR Implement-Reihenfolge (Warp)

1. **UDP Listener** (Binary, Little Endian, packed) → Header → `switch(m_packetId)`.&#x20;
2. **Session gate** (TT prüfen) → `playerIdx` cachen. &#x20;
3. **Lap Data + Car Telemetry** streamen → Event-Detektor → metrische Punkte je Turn sammeln. &#x20;
4. **TT-Packet** (1 Hz) für PB/Validität & Assist-State mergen. &#x20;
5. **DB schreiben** (Schemas oben) → **Coach** vergleicht vs. Referenzprofil und spricht konkrete „zu spät/früh, Tempo am Apex/Exit“ Deltas aus.

Wenn du möchtest, schreibe ich dir direkt die Parser-Structs (C#/Go/TS) und die DB-Migrations passend zu diesem Plan.
