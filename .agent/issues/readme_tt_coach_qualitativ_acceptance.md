# TT‑Coach (Time Trial) — Qualitative Spec **mit Akzeptanzkriterien**

Ein Coach für **F1® 25 Time Trial**, der nach jeder gültigen Runde **maximal drei** Kurven auswählt und je Kurve **genau eine** klare, **qualitative** Aktion empfiehlt (z. B. *„früher bremsen“*, *„Druck schneller aufbauen“*, *„früher ans Gas, progressiv öffnen“*, *„Lenkwinkel reduzieren, dann Gas“*).

Der Coach ist **hybrid**:
- **Sicherheits‑Regeln** (Slip/Traction‑Gates, Konfliktauflösung, Phasen‑Priorität) erzeugen sichere Kandidaten.
- Ein **Nutzenschätzer** (leichtes ML, z. B. GBDT) schätzt den erwarteten Zeitgewinn je Kandidat.
- Ein **Bandit** (Thompson Sampling) personalisiert die Auswahl pro Fahrer.
- Ein **Prüfer** bewertet die nächsten 1–3 **gültigen** Runden: *Versuch? Erfolg? Übertrieben?* und steuert Intensität/Themenwechsel.

**Wichtig:** Der Coach **nennt niemals Meter** oder Zahlen im User‑Text. Er spricht in **Intensitätswörtern** („etwas/früher/deutlich“, „sanft/progressiv/zügig“). Intern arbeitet er metrisch.

---

## 0) Zweck & Nicht‑Ziele
**Zweck:** Messbar bessere, realistisch fahrbare Tipps mit klarer Ursache→Maßnahme→Erfolgskontrolle – ohne Informations‑Overload.
**Nicht‑Ziele:** Kein Rennmodus, kein Schaden/Setup‑Coaching, keine generative „freie“ Sprache (nur Templates), keine riskanten Mehrfach‑Tipps in einer Kurve.

---

## 1) Betriebsmodus & Gating
- **TT‑Only:** Es werden ausschließlich **Time‑Trial‑Sessions** verarbeitet.
- **Valid‑Only:** Nur **gültige Runden** fließen in Analyse, Empfehlungen und Lernen.
- **Player‑Only:** Es wird nur das **Spielerfahrzeug** betrachtet.

---

## 2) Eingaben & interne Ableitungen (kurz)
- **Streckenfortschritt** (s), **Telemetrie** (Geschwindigkeit, Bremse, Gas, Lenkwinkel, Gang) pro Frame.
- **Grip/Slip**‑Indikatoren (z. B. Slip‑Ratio/Slip‑Angle/Kräfte) → **Exit‑Slip** & **Entry‑Slip** Ampeln (**grün/gelb/rot**).
- **Marker/Phasen** (intern): Bremsbeginn, Peak‑Druck, Lösen, Gasaufnahme, Apex. → daraus Entry/Min/Exit‑Tempo, Trail‑Dauer, Druck‑Dynamik, Pedal‑Koordination.
- **Referenz je Kurve** (Filter: Assists/Device): **Median (p50)** & **IQR**; bei Mehrfach‑Linien: schnellere **Mode**.

> *Hinweis:* Diese Ableitungen sind **nicht** Teil der Ausgabe – sie steuern nur die Entscheidung.

---

## 3) Entscheidungs‑Pipeline (Overview)
1. **Kurvenranking** via Impact (Deltas gegen Referenz, IQR‑normalisiert).
2. **Kandidaten je Kurve** (max. 3) aus Regeln & Phasen‑Priorität: Entry → Rotation → Exit.
3. **Safety‑Gates:** Slip/Traction prüfen; Konflikte auflösen; eine Aktion pro Kurve.
4. **Nutzenschätzung:** ML‑Schätzer liefert erwarteten Gewinn (mit Unsicherheitsband) je Kandidat; Fallback Heuristik.
5. **Bandit‑Auswahl:** personalisierte Wahl **eines** Kandidaten pro Kurve.
6. **Ausgabe:** Sprach‑Template (qualitativ, ohne Zahlen);
7. **Prüfer:** nächste 1–3 gültige Runden werten; Ergebnis „Versuch/Erfolg/Übertrieben/Kein Versuch“ steuert **Intensität** oder **Themenwechsel**.

---

## 4) Aktions‑Kandidaten & Sprachpolitik
**Entry**
- „**Früher bremsen**“
- „**Druck schneller aufbauen**“ (zügig / schnell / sehr schnell)

**Rotation**
- „**Früher lösen**“ (klar früher lösen)

**Exit**
- „**Früher ans Gas, progressiv öffnen**“ (etwas/früh; sanft/progressiv/sehr sanft)
- „**Lenkwinkel reduzieren, dann Gas**“ (wenn Traktion limitiert)

**Sprachregeln**
- Keine Zahlen/Meter/Zeitangaben im User‑Text.
- Kurze Sätze, klare Verben, maximal eine Aktion pro Kurve.
- Optional ein **Fokus‑Satz** am Ende („Hände ruhig“, „sanft öffnen“).

---

## 5) Safety: Slip/Traction‑Gates & Konflikte
- **Exit‑Ampel**:
  - **Grün** → Exit‑Pace‑Tipps erlaubt.
  - **Gelb** → nur **sanft/progressiv**; keine aggressiven Früh‑Gas‑Formulierungen.
  - **Rot** → **keine** Früh‑Gas‑Tipps; stattdessen „**Lenkwinkel reduzieren, dann Gas**“.
- **Entry‑Ampel**:
  - **Rot** → kein „Druck schneller“; zuerst „**früher bremsen**“.
- **Konfliktregel**: In einer Kurve **nie** zwei Aktionen gleichzeitig coachen; Reihenfolge: Entry → Rotation → Exit.

---

## 6) Nutzenschätzer (ML, leicht)
- **Eingaben:** Kurventyp, Entry/Min/Exit‑Tempo, qualitative Deltas (intern), Slip‑Bänder, Kandidaten‑Typ, Assists, Gerät.
- **Ausgabe:** erwartete Verbesserung des Kurven‑/Sektor‑Splits (mit Konfidenzband).
- **Fallback:** Wenn zu wenig Daten → konservative Heuristik.

---

## 7) Bandit (Personalisierung)
- **Ziel:** Schnell herausfinden, welche Aktion **bei dieser Person** wirkt.
- **Policy:** Thompson Sampling auf diskreten Aktionsklassen.
- **Reward:** gemessener **Per‑Turn‑Split** der **nächsten gültigen** Runde.
- **Cooldown:** dieselbe Kurve nicht in jeder Runde coachen (außer klarer Erfolg/Misserfolg).
- **Exploration nur in Grün/Gelb** (nie in Rot).

---

## 8) Prüfer (Versuch/Erfolg/Übertrieben/Kein Versuch)
- **Fenster:** bis zu **3 gültige** Runden nach einem Tipp.
- **Versuch erkannt**, wenn das qualitative Muster in die gewünschte Richtung zeigt:
  - *Früher bremsen:* Bremsbeginn erkennbar früher, kein endloser Coast.
  - *Druck schneller:* steilerer Druckanstieg, früherer Peak; ohne Front‑Slip rot.
  - *Früher lösen:* Druck vor Apex weg, ruhigere Hände.
  - *Früher Gas, progressiv:* frühere, weichere Gasöffnung ohne Wheelspin.
  - *Lenkwinkel reduzieren, dann Gas:* kleineres Lenkwinkel‑Plateau vor Gas, weniger Gegenlenken.
- **Erfolg:** besseres Apex/Exit‑Tempo **ohne** Slip‑Rot; Sektor nicht schlechter.
- **Übertrieben:** Wheelspin/Übersteuern (Exit) oder starker Front‑Slip (Entry/Rotation), Zeitverlust/Abbruch.
- **Kein Versuch:** Muster unverändert.
- **Reaktion:**
  - *Erfolg* → nächster Engpass oder Konstanz‑Drill.
  - *Übertrieben* → **eine Stufe sanfter** oder Stabilitäts‑Tipp.
  - *Kein Versuch* → Micro‑Drill (gleiches Thema, Fokus), kein Themenwechsel.

---

## 9) Szenarien (Beispiele & Reaktionen)

### A) Exit zögerlich, Grip ok → Tipp „früher ans Gas, progressiv“
- **Kein Versuch** → „Fokus auf **sanftes Öffnen**, Tempo egal.“ (Micro‑Drill)
- **Versuch→Erfolg** → „Gut, weiter so.“ Nächster Engpass.
- **Versuch→Wheelspin** → „**Sanfter** öffnen; **Lenkwinkel** etwas reduzieren, dann Gas.“ (Intensität runter, Safety enger)
- **Versuch→Kein Effekt** → „Zuerst **früher lösen**, dann Gas.“ (Themenwechsel)

### B) Rotation schleppend → Tipp „früher lösen“
- **Erfolg** → höheres Apex‑Tempo, danach ggf. Exit‑Tipp.
- **Übertrieben** (Untersteuern) → „**Ruhiger lösen**, kleinerer Lastwechsel.“ (sanfter)

### C) Entry zu spät/flach → Tipp „Druck schneller aufbauen“
- **Übertrieben** (Front‑Slip rot) → „**Früher bremsen**, dann sauber **lösen**.“ (Stabilität vor Pace)

### D) Slip Rot (Exit)
- **Immer** Stabilitätshinweis: „**Lenkwinkel reduzieren, dann Gas** – **sanft** öffnen.“

---

## 10) **Akzeptanzkriterien**

### 10.1 Funktional
- [ ] Es werden **nur** Time‑Trial‑Sessions verarbeitet; nur **gültige** Runden fließen in Analyse/Lernen.
- [ ] Pro Runde werden **höchstens drei** Kurven gecoacht; pro Kurve **genau eine** Aktion.
- [ ] Sprach‑Ausgaben enthalten **keine Zahlen/Meter/Zeitangaben**; ausschließlich qualitative Intensitäten.
- [ ] Phasen‑Priorität wird eingehalten (Entry → Rotation → Exit).
- [ ] Konfliktregel: keine zwei Aktionen in einer Kurve.

### 10.2 Safety (Slip/Traction)
- [ ] **Exit‑Slip rot** blockiert **immer** Früh‑Gas‑Tipps; stattdessen kommt „Lenkwinkel reduzieren, dann Gas“.
- [ ] **Entry‑Slip rot** blockiert „Druck schneller“; stattdessen „früher bremsen“.
- [ ] Bei **Gelb** werden nur sanfte Varianten gewählt (z. B. „sanft/progressiv“).

### 10.3 Prüfer
- [ ] Der Prüfer beobachtet die **nächsten 1–3 gültigen Runden** nach einem Tipp.
- [ ] Der Prüfer klassifiziert robust: **Versuch / Erfolg / Übertrieben / Kein Versuch**.
- [ ] Bei *Übertrieben* wird die Intensität **reduziert** oder auf Stabilität gewechselt.
- [ ] Bei *Kein Versuch* wird **kein** neues Thema gestartet; Micro‑Drill.

### 10.4 Bandit (Personalisierung)
- [ ] Bandit nutzt **Per‑Turn‑Split** der nächsten gültigen Runde als Reward.
- [ ] **Kein** negatives Lernen bei *Kein Versuch* oder **ungültiger Runde** (Reward neutral).
- [ ] **Cooldown** verhindert Über‑Coaching derselben Kurve.
- [ ] **Exploration** erfolgt **nie** in Slip‑Rot‑Zuständen.

### 10.5 Referenz & Robustheit
- [ ] Referenzen pro Kurve basieren auf **Median** & **IQR** (Filter nach Assists/Device).
- [ ] Bei Mehrfach‑Linien wird die **schnellere Mode** bevorzugt.
- [ ] Bei hoher Fahrer‑Inkonstanz wird **zuerst** ein **Konstanz‑Drill** angeboten.

### 10.6 UX/Text
- [ ] Templates werden verwendet; **keine** freien, generativen Texte.
- [ ] Jede Meldung enthält **Ursache → Maßnahme → Fokushinweis** in 1–3 Sätzen.

### 10.7 Performance & Stabilität
- [ ] Coach‑Report ist **≤ 150 ms** nach Rundenende verfügbar.
- [ ] Paket‑Drops/Telemetry‑Jitter führen zu **keinen** Exceptions; weiche Fenster werden verwendet.
- [ ] Offline‑Replays produzieren **deterministisch** dieselben Entscheidungen.

### 10.8 Logging & Evaluierung
- [ ] Jede Empfehlung wird geloggt (Aktionstyp, Kontext, erwarteter Nutzen, Confidence, Prüfer‑Ergebnis, realer Δ‑Split).
- [ ] KPI‑Dashboard zeigt: Per‑Turn Δ‑Split, Hit‑Rate (Versuch), Success‑Rate (Erfolg ohne Rot), PB/Sektor‑PB‑Rate.

---

## 11) Testplan (szenariobasiert)

### Unit
- Event‑Detektor: Entry/Rotation/Exit‑Muster korrekt (robust gegen Jitter).
- Slip‑Ampel: Grenzfälle richtig (grün/gelb/rot) → blockt/erlaubt passende Tipps.
- Sprache: Keine Zahlentokens in Ausgaben.

### Integration (Replay‑Runs)
1. **A‑Grün Exit, kein Versuch** → Prüfer meldet *Kein Versuch*, Coach wiederholt Fokus („sanft/progressiv“), Bandit neutral.
2. **A‑Grün Exit, Versuch→Wheelspin** → Prüfer *Übertrieben*, Coach „Lenkwinkel reduzieren, dann Gas“; Intensität runter.
3. **B‑Rotation, Versuch→Erfolg** → Folge‑Tipp auf Exit; Bandit verstärkt diese Klasse.
4. **C‑Entry, Versuch→Front‑Slip rot** → Wechsel auf „früher bremsen“, keine Pace‑Eskalation.
5. **D‑Exit Slip rot** → niemals Früh‑Gas‑Tipp; immer Stabilitätshinweis.

### E2E
- 10 Runden gemischt:
  - <=3 Tips/Runde, 1/Kurve;
  - Bandit‑Rewards konsistent;
  - PB/Sektor‑PB‑Rate steigt nach Coaching‑Interventionen signifikant.

---

## 12) Konfiguration (Beispiel)
```yaml
phases_priority: [entry, rotation, exit]
intensity_words:
  entry_earlier:    ["etwas früher bremsen", "früher bremsen", "deutlich früher bremsen"]
  press_faster:     ["Druck zügig aufbauen", "Druck schneller aufbauen", "Druck sehr schnell aufbauen"]
  release_earlier:  ["früher lösen", "klar früher lösen"]
  early_throttle:   ["etwas früher ans Gas, sanft öffnen", "früher ans Gas, progressiv öffnen", "früh ans Gas, sehr sanft öffnen"]
  reduce_steer:     ["Lenkwinkel etwas reduzieren, dann Gas", "Lenkwinkel reduzieren, dann Gas"]
slip_amps:
  exit: {green: [0.0, 0.6], yellow: [0.6, 0.85], red: [0.85, 1.0]}
  entry:{green: [0.0, 0.6], yellow: [0.6, 0.85], red: [0.85, 1.0]}
bandit:
  policy: thompson
  cooldown_laps: 1
  reward_metric: per_turn_split
reviewer:
  window_valid_laps: 3
  outcomes: [attempt, success, overshoot, no_attempt]
```

---

## 13) Definition of Done (DoD)
- Alle **Akzeptanzkriterien** aus §10 erfüllt (grün).
- Testplan (Unit/Integration/E2E) grün.
- Logging & Dashboard liefern KPIs.
- Sprach‑Templates sind vollständig lokalisiert (de/en), **ohne** Zahlen.
- Dokumentation (dieses README) im Repo; Beispiel‑Config vorhanden.

---

## 14) Beispiel‑Ausgaben

**Coach – Runde 18**
1. **T10 – Entry**: „Du kommst **zu spät** in den Druck. **Druck schneller aufbauen** und **früher lösen**.“ *(Confidence: hoch)*
2. **T5 – Rotation**: „Du **trägst Druck** bis in den Apex. **Früher lösen**, damit das Auto freier dreht.“ *(Confidence: mittel)*
3. **T14 – Exit (Grip ok)**: „Du **wartest zu lange** mit dem Gas. **Früher ans Gas, progressiv öffnen**.“ *(Confidence: hoch)*

**Prüfer – nächste Runde**
- **T10:** *Versuch erkannt* – Druck früher/kräftiger, Lösen früher → **Gut, weiter so**.
- **T14:** *Kein Versuch* – nächste Runde **nur** auf sanftes Öffnen achten.
- **T7:** *Übertrieben* – Wheelspin → **eine Stufe sanfter**, erst Lenkwinkel kleiner.

---

**Fazit:**
Dieser Coach verbindet **Sicherheit** (Slip‑Gates, Konfliktregeln), **Lernen** (Nutzenschätzer, Bandit) und **klare Sprache** (Templates). Er funktioniert **sofort** mit wenig Daten, bleibt **robust** bei Inkonstanz und wird **besser**, je mehr ihr fahrt.

