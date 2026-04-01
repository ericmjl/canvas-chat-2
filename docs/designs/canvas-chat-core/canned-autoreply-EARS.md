# Canned Auto-Reply EARS

## Related Documents

- [Canvas Composer and Auto-Reply LLD](./LLD.md)

## Requirements

- **CCHAT-AUTOREPLY-001 (Event-driven)**
  When a non-empty human node is created and canned auto-reply is enabled, the system shall create one AI child node automatically.

- **CCHAT-AUTOREPLY-002 (State-driven)**
  While creating the auto-reply child node, the system shall create an edge from the human node to the AI node so the relationship is visible on the canvas.

- **CCHAT-AUTOREPLY-003 (Unwanted behavior)**
  If a created human node has only whitespace content, the system shall not create a canned auto-reply node.

- **CCHAT-AUTOREPLY-004 (Configuration-driven)**
  If canned auto-reply is disabled by configuration, the system shall not create canned AI nodes on human message creation.
