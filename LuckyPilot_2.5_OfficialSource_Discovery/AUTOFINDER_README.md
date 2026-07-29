# LuckyPilot 2.4 AutoFinder

## Was automatisch geschieht

- GitHub Actions startet täglich.
- Nur in `site/data/sources.json` ausdrücklich freigegebene RSS/Atom- oder JSON-Feeds werden gelesen.
- Doppelte Einträge werden erkannt.
- Abgelaufene Einträge werden entfernt.
- Kurzbeschreibungen werden als neutrale LuckyPilot-Vorlage erzeugt.
- Fremde Bilder, Logos, Volltexte und Teilnahmebedingungen werden nicht kopiert.

## Was bewusst nicht geschieht

- Kein allgemeines Crawling oder Scraping fremder Webseiten.
- Keine automatische Teilnahme an Gewinnspielen.
- Keine CAPTCHA-Umgehung.
- Keine Veröffentlichung ungeklärter Quellen.

## Wichtig

Die Technik ist vollständig vorbereitet. Damit echte neue Einträge erscheinen, müssen zulässige strukturierte Quellen (RSS/Atom/JSON/API) in `site/data/sources.json` eingetragen und mit `permission_status: "approved"` freigegeben werden. Die Quellenrecherche übernimmt das LuckyPilot-Projekt; Nutzer müssen keine Gewinnspiele von Hand suchen oder hinzufügen.
