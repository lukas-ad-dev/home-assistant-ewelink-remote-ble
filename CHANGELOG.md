# Changelog

## 0.4.0

- Offer unknown R5 remotes as discovered devices instead of creating them
  automatically.
- Require a fresh physical button press before a discovered remote is added.
- Keep previously configured remotes and their existing names, areas, entities,
  and automations working after the update.
- Add a 60-second confirmation screen with retry support.

## 0.3.1

- Add original six-button brand artwork for Home Assistant and GitHub.
- Add a button icon to all R5 event entities.
- Clarify that the separate BLE Passthrough project is not required.

## 0.3.0

- Add six localized event entities per R5.
- Keep all device automation triggers for short, double, hold, repeat, and release.
- Restore known R5 devices and their entities after a Home Assistant restart.
- Keep one assignable Home Assistant device per physical remote.

## 0.2.0

- Add config-flow setup and Home Assistant device discovery.
- Add 30 device triggers for all six buttons and five action phases.
- Support multiple R5 remotes automatically.

## 0.1.0

- Initial passive R5 advertisement decoder.
- Add deduplication across multiple BLE receivers.
- Add synthetic release detection for held buttons.
