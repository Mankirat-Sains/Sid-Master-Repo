Tracing the flow from question to final response:
1. User asks question → Frontend sends request
Frontend: Frontend/Frontend/pages/workspace.vue
User types in the prompt input (around line 500)
handleSend() is called (around line 2400)
Calls sendChatMessageStream() from useChat.ts (line 2457)
Sends POST to /chat/stream with message and session_id
Backend: Backend/api_server.py
/chat/stream endpoint (line 783) → chat_stream_handler()
Starts generate_stream() async generator (line 819)
2. Backend processes query → Hits interrupt
Backend: Backend/api_server.py
generate_stream() invokes graph (line 960): graph.astream(..., stream_mode=["updates", "custom", "messages"])
Graph execution flows through nodes
Backend: Backend/nodes/router_dispatcher.py
node_router_dispatcher() (line 67) selects "rag" router
Calls call_db_retrieval_subgraph() directly (line 75)
Backend: Backend/graph/subgraphs/db_retrieval_subgraph.py
call_db_retrieval_subgraph() (line 67) invokes the DBRetrieval subgraph
Backend: Backend/nodes/DBRetrieval/SQLdb/retrieve.py
node_retrieve() (line 67) retrieves code documents
After retrieval (around line 200), checks if code_docs exist and code_verification_response is None
Calls interrupt() (line 220) with payload:
  interrupt({      "type": "code_verification",      "question": state.user_query,      "codes": retrieved_filenames,      "code_count": len(retrieved_filenames),      "chunk_count": len(code_docs)  })
Backend: Backend/api_server.py
generate_stream() catches GraphInterrupt (line 1531)
Extracts interrupt payload and sends to frontend (line 1554):
  yield f"data: {json.dumps(interrupt_data)}\n\n"
Returns to stop streaming (line 1556)
3. Frontend receives interrupt → Shows UI
Frontend: Frontend/Frontend/composables/useChat.ts
sendChatMessageStream() processes SSE stream (line 161)
Detects data.type === 'interrupt' (line 203)
Calls callbacks?.onInterrupt() (line 204)
Frontend: Frontend/Frontend/pages/workspace.vue
onInterrupt callback (line 2488) receives interrupt data
Stores in interruptState.value (line 2489)
Adds interrupt message to conversation.chatLog (line 2500):
  conversation.chatLog.push({      id: interruptMessageId,      role: 'assistant',      content: '',      interrupt: { type, question, codes, ... }  })
Frontend: Frontend/Frontend/pages/workspace.vue
Template renders interrupt message (line 558)
Shows codes list and Approve/Reject buttons (line 560-580)
4. User clicks Approve → Frontend calls resume
Frontend: Frontend/Frontend/pages/workspace.vue
handleApproveCodesForEntry() (line 2520) calls resumeFromInterrupt('approved', entry)
resumeFromInterrupt() (line 2339):
Marks entry as processing (line 2351)
Calls POST /chat/resume (line 2356) with:
    {        "session_id": session_id,        "response": "approved",        "interrupt_id": interrupt_id    }
Handles streaming response (line 2389)
5. Backend resumes → Continues execution
Backend: Backend/api_server.py
/chat/resume endpoint (line 1576) → chat_resume()
Extracts user_response = "approved" (line 1589)
Creates Command(resume=user_response) (line 1614)
Starts generate_resume_stream() (line 1611)
Backend: Backend/api_server.py
generate_resume_stream() streams graph execution (line 1614)
Filters tokens from "answer" node only (line 1624)
Tracks final state in updates mode (line 1630)
Backend: Backend/nodes/DBRetrieval/SQLdb/retrieve.py
node_retrieve() resumes (line 67)
Checks if code_verification_response == "approved" (line 80)
Returns existing code_docs (line 85) — no re-retrieval
Backend: Graph continues through:
node_retrieve() → returns code_docs
node_grade() → grades documents
node_answer() → synthesizes answer (streams tokens)
node_verify() → verifies answer
node_correct() → finalizes
router_dispatcher → completes
6. Backend sends completion → Frontend displays
Backend: Backend/api_server.py
generate_resume_stream() detects router_dispatcher completion (line 1636)
Breaks from loop (line 1638)
Extracts answer from final_state (line 1645):
  answer = final_state.get("db_retrieval_result") or ...  code_answer = final_state.get("db_retrieval_code_answer") or ...
Builds response_data (line 1680)
Sends completion (line 1720):
  yield f"data: {json.dumps({'type': 'complete', 'result': response_data})}\n\n"
Frontend: Frontend/Frontend/pages/workspace.vue
resumeFromInterrupt() processes SSE stream (line 2403)
On data.type === 'token' (line 2408): appends to response message (line 2423)
On data.type === 'complete' (line 2466): marks interrupt as completed (line 2469)
Frontend: Frontend/Frontend/pages/workspace.vue
Template shows response message (line 558)
getFormattedMessage() formats markdown (line 558)
Response appears below the interrupt message
Key files summary:
Frontend:
Frontend/Frontend/pages/workspace.vue - Main UI, interrupt handling, resume logic
Frontend/Frontend/composables/useChat.ts - SSE stream processing, interrupt detection
Backend:
Backend/api_server.py - /chat/stream and /chat/resume endpoints
Backend/nodes/DBRetrieval/SQLdb/retrieve.py - Interrupt logic
Backend/nodes/router_dispatcher.py - Routes to subgraph
Backend/graph/subgraphs/db_retrieval_subgraph.py - Subgraph execution
The flow: Frontend → Backend stream → Interrupt → Frontend UI → Resume → Backend continues → Completion → Frontend displays.