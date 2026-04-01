# Canvas Chat High-Level Design

## Problem Statement

Canvas Chat aims to support non-linear AI conversations where each message is a node on an infinite canvas and relationships are explicit edges. Users should be able to branch, connect, and revisit reasoning paths visually instead of being constrained to a single chat timeline.

## Goals

- Provide a simple canvas-native chat interface where messages are nodes.
- Persist conversation graph data (nodes + edges) so sessions survive restarts.
- Support provider-based LLM routing via LiteLLM for future real inference.
- Allow safe demos without live secrets by supporting canned auto-replies.

## Target Users

- Developers prototyping agent interaction patterns.
- Educators/demo hosts showing branching AI conversations live.
- Knowledge workers exploring non-linear prompt iteration.

## Architecture Overview

- **Frontend**: SvelteKit + Svelte Flow to render and edit graph nodes/edges.
- **Backend**: FastAPI REST API for graph CRUD, provider config, and reply generation.
- **Storage**: SQLite (single-file persistence for MVP).
- **LLM Routing**: LiteLLM abstraction with provider config rows.

## Key Decisions and Trade-Offs

- **REST over websockets**: easier MVP implementation and debugging, less real-time capability.
- **SQLite over external DB**: faster setup and demos, limited concurrency.
- **Node-level role model (`human|ai|system`)**: explicit semantics, simple rendering.
- **Canned auto-reply support**: enables demos without API keys, not representative of model quality.

## Non-Goals

- Multi-user collaboration.
- Authentication/authorization.
- Advanced graph algorithms or layout automation.
- Streaming token-by-token model output.

## Related Designs

- [Canvas Composer and Auto-Reply LLD](./designs/canvas-chat-core/LLD.md)
