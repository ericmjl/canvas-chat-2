# Composer Input EARS

## Related Documents

- [Canvas Composer and Auto-Reply LLD](./LLD.md)

## Requirements

- **CCHAT-COMPOSER-001 (Ubiquitous)**
  The system shall provide a message composer textarea in the canvas side panel.

- **CCHAT-COMPOSER-002 (Event-driven)**
  When the user presses `Enter` in the composer without `Shift`, the system shall submit the current composer text as a human message.

- **CCHAT-COMPOSER-003 (Event-driven)**
  When the user presses `Shift+Enter` in the composer, the system shall insert a newline and shall not submit the message.

- **CCHAT-COMPOSER-004 (State-driven)**
  While a submit request is in progress, the system shall disable composer submission controls.

- **CCHAT-COMPOSER-005 (Event-driven)**
  When submission succeeds, the system shall clear the composer text and refresh the graph view.
