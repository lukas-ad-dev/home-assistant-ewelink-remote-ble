# eWeLink Remote BLE for Home Assistant

[English](#english) | [Deutsch](#deutsch)

## English

Local Home Assistant support for the **SONOFF SwitchMan R5** without an
eWeLink-Remote gateway.

The integration decodes the R5's passive Bluetooth advertisements and exposes
every physical remote as a normal Home Assistant device. Each R5 can be named,
assigned to an area, and used in device-based automations.

## Features

- One Home Assistant device per physical R5
- Automatic discovery of additional R5 remotes
- Six event entities per R5, with their physical positions in the name
- Device automation triggers for every button and action
- Short press, double press, hold start, hold repeat, and hold release
- Fully local operation; no eWeLink account or cloud connection
- Multiple BLE receivers/proxies can hear the same remote without duplicate events
- English and German translations

## Button layout

| Position | Top row | Bottom row |
| --- | --- | --- |
| Left | Button 1 | Button 4 |
| Middle | Button 2 | Button 5 |
| Right | Button 3 | Button 6 |

Each button exposes these event types:

| Event type | Meaning |
| --- | --- |
| `single` | Short press |
| `double` | Double press |
| `hold_start` | Long press started |
| `hold_repeat` | Additional packet while held |
| `hold_release` | Button was released after a hold |

The R5 does not transmit a dedicated release packet. `hold_release` is therefore
generated locally after 1.6 seconds without another hold packet. This makes the
event useful for dimming and cover stop actions, but it has a small intentional
delay.

## Requirements

- Home Assistant with the Bluetooth integration enabled
- A receiver that forwards the **raw BLE advertisement** to Home Assistant
- The [BLE Passthrough integration](https://github.com/iHost-Open-Source-Project/ble_passthrough)
  or an equivalent source that supplies `BluetoothServiceInfoBleak.raw`

Tested with Home Assistant 2026.11 and an SMLIGHT SLZB-MR4U running SLZB-OS.

> [!IMPORTANT]
> A Bluetooth proxy is not the same thing as an eWeLink-Remote gateway. This
> integration does not pair the R5 and does not emulate the proprietary gateway.
> It passively decodes the R5 broadcasts that a compatible receiver forwards to
> Home Assistant.

## Installation with HACS

1. Open HACS in Home Assistant.
2. Open **Integrations**, then **Custom repositories**.
3. Add `https://github.com/lukas-ad-dev/home-assistant-ewelink-remote-ble` as an
   **Integration** repository.
4. Install **eWeLink Remote BLE** and restart Home Assistant.
5. Open **Settings → Devices & services → Add integration**.
6. Search for **eWeLink Remote BLE** and complete the empty setup form.
7. Press any R5 button once. The remote appears as a new device with six event
   entities.

## Manual installation

Copy the directory
`custom_components/ewelink_remote_ble` into your Home Assistant configuration
directory, restart Home Assistant, and then add the integration from
**Settings → Devices & services**.

## Areas and multiple remotes

Every physical R5 has its own stable device identifier. Open the device, select
**Edit**, and choose its area. A second R5 is discovered as a separate device and
can be assigned to another area. The six buttons remain entities of that remote;
they are not incorrectly created as six separate devices.

## Automation example

For a cover, a typical setup is:

- Button 1 `single`: open the cover completely
- Button 1 `hold_start`: start opening
- Button 1 `hold_release`: stop
- Button 3 `single`: close the cover completely
- Button 3 `hold_start`: start closing
- Button 3 `hold_release`: stop

Choose the R5 under **Device** when creating an automation, then select the
button and action. The event entities can also be used directly as state/event
triggers.

## Troubleshooting

- **Device does not appear:** verify that BLE Passthrough receives raw
  advertisements, then press an R5 button.
- **Device exists but has no entities:** restart Home Assistant after updating
  this integration to version 0.3.0 or later.
- **Hold release feels delayed:** this is expected because the R5 has no release
  packet; the integration waits 1.6 seconds after the last hold broadcast.
- **Duplicate receivers:** duplicates from multiple gateways are suppressed using
  the R5 sequence counter.

## Credits and disclaimer

Protocol research and the public test vector were informed by
[Flobul/Tasmota-eWeLinkRemote](https://github.com/Flobul/Tasmota-eWeLinkRemote).
BLE forwarding is provided by the separate BLE Passthrough project.

This is an independent community integration and is not affiliated with SONOFF
or CoolKit/eWeLink.

## License

MIT License. See [LICENSE](LICENSE).

---

## Deutsch

Lokale Home-Assistant-Unterstützung für den **SONOFF SwitchMan R5** ohne ein
eWeLink-Remote-Gateway.

Die Integration wertet die passiven Bluetooth-Werbeaussendungen des R5 aus und
stellt jede physische Fernbedienung als normales Home-Assistant-Gerät bereit.
Jeder R5 kann benannt, einem Bereich zugeordnet und in gerätebasierten
Automatisierungen verwendet werden.

### Funktionen

- Ein Home-Assistant-Gerät pro physischem R5
- Automatische Erkennung weiterer R5-Fernbedienungen
- Sechs Ereignis-Entitäten pro R5, deren Namen die jeweilige Tastenposition
  enthalten
- Geräteauslöser für jede Taste und jede Betätigungsart
- Einfachdruck, Doppeldruck, Beginn des Langdrucks, Langdruck-Wiederholung und
  Loslassen nach einem Langdruck
- Vollständig lokaler Betrieb ohne eWeLink-Konto oder Cloud-Verbindung
- Mehrere BLE-Empfänger beziehungsweise Proxys können denselben R5 empfangen,
  ohne doppelte Ereignisse auszulösen
- Englische und deutsche Übersetzungen

### Tastenbelegung

| Position | Obere Reihe | Untere Reihe |
| --- | --- | --- |
| Links | Taste 1 | Taste 4 |
| Mitte | Taste 2 | Taste 5 |
| Rechts | Taste 3 | Taste 6 |

Jede Taste stellt folgende Ereignistypen bereit:

| Ereignistyp | Bedeutung |
| --- | --- |
| `single` | Kurzer Tastendruck |
| `double` | Doppeldruck |
| `hold_start` | Langdruck wurde begonnen |
| `hold_repeat` | Weiteres Datenpaket während des Gedrückthaltens |
| `hold_release` | Taste wurde nach einem Langdruck losgelassen |

Der R5 sendet kein eigenes Datenpaket beim Loslassen. `hold_release` wird deshalb
lokal erzeugt, wenn 1,6 Sekunden lang kein weiteres Langdruck-Paket empfangen
wurde. Dadurch eignet sich das Ereignis für das Stoppen von Dimm- und
Jalousiefahrten, hat aber eine kleine technisch bedingte Verzögerung.

### Voraussetzungen

- Home Assistant mit aktivierter Bluetooth-Integration
- Ein Empfänger, der die **rohen BLE-Werbeaussendungen** an Home Assistant
  weiterleitet
- Die Integration
  [BLE Passthrough](https://github.com/iHost-Open-Source-Project/ble_passthrough)
  oder eine gleichwertige Quelle, die `BluetoothServiceInfoBleak.raw`
  bereitstellt

Getestet mit Home Assistant 2026.11 und einem SMLIGHT SLZB-MR4U mit SLZB-OS.

> [!IMPORTANT]
> Ein Bluetooth-Proxy ist nicht dasselbe wie ein eWeLink-Remote-Gateway. Diese
> Integration koppelt den R5 nicht und bildet das proprietäre Gateway nicht
> nach. Sie wertet passiv die Aussendungen des R5 aus, die ein kompatibler
> Empfänger an Home Assistant weiterleitet.

### Installation mit HACS

1. HACS in Home Assistant öffnen.
2. **Integrationen** und anschließend **Benutzerdefinierte Repositories**
   öffnen.
3. `https://github.com/lukas-ad-dev/home-assistant-ewelink-remote-ble` als
   Repository vom Typ **Integration** hinzufügen.
4. **eWeLink Remote BLE** installieren und Home Assistant neu starten.
5. **Einstellungen → Geräte & Dienste → Integration hinzufügen** öffnen.
6. Nach **eWeLink Remote BLE** suchen und das leere Einrichtungsformular
   abschließen.
7. Einmal eine beliebige Taste des R5 drücken. Die Fernbedienung erscheint als
   neues Gerät mit sechs Ereignis-Entitäten.

### Manuelle Installation

Den Ordner `custom_components/ewelink_remote_ble` in das
Home-Assistant-Konfigurationsverzeichnis kopieren, Home Assistant neu starten
und die Integration anschließend unter **Einstellungen → Geräte & Dienste**
hinzufügen.

### Bereiche und mehrere Fernbedienungen

Jeder physische R5 erhält eine eigene stabile Gerätekennung. Das Gerät öffnen,
**Bearbeiten** wählen und den gewünschten Bereich festlegen. Ein weiterer R5
wird als separates Gerät erkannt und kann einem anderen Bereich zugeordnet
werden. Die sechs Tasten bleiben Entitäten der jeweiligen Fernbedienung und
werden nicht fälschlicherweise als sechs einzelne Geräte angelegt.

### Beispiel für eine Automatisierung

Eine typische Belegung für eine Jalousie oder ein Rollo ist:

- Taste 1 `single`: vollständig öffnen
- Taste 1 `hold_start`: Öffnen starten
- Taste 1 `hold_release`: stoppen
- Taste 3 `single`: vollständig schließen
- Taste 3 `hold_start`: Schließen starten
- Taste 3 `hold_release`: stoppen

Beim Erstellen einer Automatisierung den R5 unter **Gerät** auswählen und danach
Taste und Betätigungsart festlegen. Alternativ lassen sich die
Ereignis-Entitäten direkt als Auslöser verwenden.

### Fehlerbehebung

- **Das Gerät erscheint nicht:** Prüfen, ob BLE Passthrough rohe
  Werbeaussendungen empfängt, und anschließend eine R5-Taste drücken.
- **Das Gerät ist vorhanden, hat aber keine Entitäten:** Home Assistant nach
  einer Aktualisierung auf Version 0.3.0 oder neuer neu starten.
- **Das Loslassen wird verzögert erkannt:** Das ist zu erwarten, da der R5 kein
  Loslass-Paket sendet. Die Integration wartet 1,6 Sekunden nach der letzten
  Langdruck-Aussendung.
- **Mehrere Empfänger:** Doppelte Meldungen mehrerer Gateways werden anhand des
  R5-Sequenzzählers unterdrückt.

### Danksagung und Haftungsausschluss

Die Protokollanalyse und der öffentliche Testvektor basieren unter anderem auf
[Flobul/Tasmota-eWeLinkRemote](https://github.com/Flobul/Tasmota-eWeLinkRemote).
Die BLE-Weiterleitung erfolgt durch das separate BLE-Passthrough-Projekt.

Dies ist eine unabhängige Community-Integration und steht in keiner Verbindung
zu SONOFF oder CoolKit/eWeLink.

### Lizenz

MIT-Lizenz. Siehe [LICENSE](LICENSE).
