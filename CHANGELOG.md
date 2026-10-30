# Changelog

## Unreleased

## 0.1.1 - 2026-10-30

- Fixed the sensor platform failing to import: `CURRENCY_REAL` does not exist in
  `homeassistant.const` (bill amount now uses the ISO code `BRL`) and `DeviceInfo`
  is imported from `homeassistant.helpers.device_registry`.
- Modernized for Home Assistant 2026.10 / Python 3.14: `AddConfigEntryEntitiesCallback`,
  `PARALLEL_UPDATES`, removed the unused update listener.
- Added diagnostics (e-mail credentials, PDF password and customer identifiers redacted).
- Added `quality_scale.yaml`, `pyproject.toml` (ruff/pytest), `requirements_test.txt`,
  GitHub workflows (tests, hassfest, HACS validation, release) and integration tests.
- `manifest.json`: `pypdf` pinned to `6.21.4`, `loggers` declared.
- `hacs.json`: minimum Home Assistant `2025.6.0`.

## 0.1.0 - 2026-10-23

First release: reads the Cosern digital bill and distributed-generation statement
PDFs from an IMAP mailbox and exposes them as sensors.
