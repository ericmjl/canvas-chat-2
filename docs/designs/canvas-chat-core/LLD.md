# Canvas Composer and Auto-Reply LLD

## Context

This LLD covers the message-composer behavior and canned auto-reply behavior for Canvas Chat MVP.

## Component Overview

- **Composer UI (`frontend/src/routes/+page.svelte`)**
  - Textarea-based message entry.
  - `Enter` sends, `Shift+Enter` inserts newline.
  - Sends `POST /conversations/{id}/nodes` with `role=human`.
- **Graph API (`canvas_chat_2/api/routes_graph.py`)**
  - Creates requested node.
  - Optionally creates canned AI child node and linking edge for non-empty human messages.
- **Persistence (`canvas_chat_2/api/models.py`)**
  - `MessageNode.parent_node_id` records parent-child lineage.
  - `MessageEdge` persists visible graph connection.

## Data and Interface Contracts

### Create Node Request

- Endpoint: `POST /conversations/{conversation_id}/nodes`
- Body:
  - `role`: `human | ai | system`
  - `content`: string
  - `x`, `y`: float coordinates
  - `parent_node_id`: optional

### Canned Auto-Reply Rules

- Triggered only when all conditions are true:
  - `CANVAS_CHAT_ENABLE_CANNED_AUTOREPLY=true`
  - role is `human`
  - content has non-whitespace characters
- Behavior:
  - Create AI child node with `parent_node_id=<human_node_id>`
  - Create edge from human node to AI node with label `auto-reply`

## Error Handling

- Parent validation errors remain `404` if parent node is missing/outside conversation.
- Auto-reply creation occurs in same transaction as human node creation for coherence.
- If transaction fails, neither human nor auto-reply artifacts are persisted.

## Dependencies

- FastAPI
- SQLAlchemy
- SvelteKit + Svelte Flow

## Related Documents

- [High-Level Design](../../high-level-design.md)
- [Composer Input EARS](./composer-input-EARS.md)
- [Canned Auto-Reply EARS](./canned-autoreply-EARS.md)
