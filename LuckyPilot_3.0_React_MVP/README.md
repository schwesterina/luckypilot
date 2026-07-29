# LuckyPilot 3.0 – React MVP

Modernes React/Vite-Frontend für ein transparentes Verzeichnis externer Gewinnspiele.

## Wichtige Grundsätze

- keine automatische Teilnahme
- keine Aussage zur Gewinnwahrscheinlichkeit
- keine ungeklärte Übernahme fremder Bilder, Logos, Volltexte oder Teilnahmebedingungen
- direkte Links nur zur offiziellen Veranstalterseite
- eigene, sachliche Kurzbeschreibungen

## GitHub-Installation ohne lokale Software

1. Den bisherigen Repository-Inhalt vorher sichern.
2. Alle Dateien dieses Pakets in das Hauptverzeichnis des Repositorys hochladen.
3. Unter **Settings → Pages → Build and deployment** als Quelle **GitHub Actions** auswählen.
4. Unter **Actions** den Workflow „Deploy LuckyPilot to GitHub Pages“ starten oder auf einen automatischen Lauf nach dem Commit warten.
5. Nach erfolgreichem Lauf die Seite mit Strg + F5 aktualisieren.

## Achtung zum Repository-Namen

In `vite.config.js` ist `/luckypilot/` eingetragen. Bei einem anderen Repository-Namen muss dieser Pfad angepasst werden.

## Daten

Die Website lädt ihre Einträge aus:

`public/data/gewinnspiele.json`

Die zwei enthaltenen Einträge sind ausdrücklich nur Demos.
