# Sidian Deep Agent Overview

Sidian now ships with a deep desktop agent layered on LangGraph. It adds iterative planning, workspace management, and human-in-the-loop safety for desktop actions while keeping the existing RAG/docgen flows.

## Deep Agent Features
- Iterative planning (think–act–observe cycles)
- Safety gates via interrupts for destructive actions (`/approve-action`)
- Ephemeral per-session workspaces with auto-cleanup
- DocGen exposed as a callable tool with eviction for large outputs
- Structured traces merged across parent and subgraphs

### Quick Start
1. Set `DEEP_AGENT_ENABLED=true` in `.env` (see `.env.example` for all flags).  
2. Send a doc generation/desktop request via `/chat/stream`.  
3. Approve destructive actions through `/approve-action` when interrupts are raised.

### Documentation
- [Deep Agent Architecture](Docs/Deep_Agent_Architecture.md)
- [Usage Guide](Docs/Deep_Agent_Usage.md)
- [Interrupt Handling](Docs/Interrupt_Handling.md)
- [Architecture Audit](SIDIAN_ARCHITECTURE_AUDIT.md)
