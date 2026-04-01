# Canvas Composer and Auto-Reply LLD

## Context

This LLD covers message-composer behavior, canned auto-reply behavior, and role-based high-contrast node styling for Canvas Chat MVP.

## Component Overview

- **Composer UI (`frontend/src/routes/+page.svelte`)**
  - Textarea-based message entry.
  - `Enter` sends, `Shift+Enter` inserts newline.
  - Sends `POST /conversations/{id}/nodes` with `role=human`.
  - Applies role-specific visual styling for node contrast and semantics.
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

### Node Visual Contrast Rules

- Each node role maps to a distinct palette in the frontend:
  - `human`: blue/cyan range
  - `ai`: indigo/purple range
  - `system`: amber/yellow range
- Selected node uses a stronger outline/ring than non-selected nodes.
- Text and border contrast must remain readable on dark canvas backgrounds.

## Error Handling

- Parent validation errors remain `404` if parent node is missing/outside conversation.
- Auto-reply creation occurs in same transaction as human node creation for coherence.
- If transaction fails, neither human nor auto-reply artifacts are persisted.
- If style mapping is missing for a role, fallback visual style should still render readable text and borders.

## Dependencies

- FastAPI
- SQLAlchemy
- SvelteKit + Svelte Flow

## Related Documents

- [High-Level Design](../../high-level-design.md)
- [Composer Input EARS](./composer-input-EARS.md)
- [Canned Auto-Reply EARS](./canned-autoreply-EARS.md)
- [Node Visual Contrast EARS](./node-visual-contrast-EARS.md)
