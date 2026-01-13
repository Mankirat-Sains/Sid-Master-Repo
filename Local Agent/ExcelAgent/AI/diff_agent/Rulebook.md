# LangGraph Agent System Documentation
=====================================

## Overview
The LangGraph Agent System is a modular, node-based architecture that replaces the monolithic Excel agent with a clear, debuggable, and extensible system.

## Architecture

### Node Structure
```
START → PLANNING_NODE → KB_BUILD_NODE → [CONDITIONAL ROUTING] → EXECUTION_NODE → END
                           |
                           v
                    [FILE_OPERATIONS]
                    - SAVE_NODE
                    - LOOK_NODE  
                    - PARSE_NODE
                    - EDIT_NODE
                    - KB_UPDATE_NODE
```

### Node Descriptions

#### 1. PLANNING_NODE (`planning_node`)
- **Purpose**: Initial sub-planning to determine best route and tools
- **Function**: `_planning_node()`
- **Responsibilities**:
  - Analyze user query
  - Detect parsed documents
  - Create execution plan
  - Determine route and tools
- **Logging**: `[PLANNING]` prefix with 🎯 emoji

#### 2. KB_BUILD_NODE (`kb_build_node`)
- **Purpose**: Build and maintain knowledge base
- **Function**: `_knowledge_base_node()`
- **Responsibilities**:
  - Load existing knowledge base
  - Update with new files
  - Save knowledge base
- **Logging**: `[KNOWLEDGE_BASE]` prefix with 📚 emoji

#### 3. KB_UPDATE_NODE (`kb_update_node`)
- **Purpose**: Learn from user interactions
- **Function**: `_knowledge_update_node()`
- **Responsibilities**:
  - Extract learning data
  - Apply learning updates
  - Update knowledge base
- **Logging**: `[KNOWLEDGE_UPDATE]` prefix with 🧠 emoji

#### 4. SAVE_NODE (`save_node`)
- **Purpose**: Save files to appropriate locations
- **Function**: `_file_save_node()`
- **Responsibilities**:
  - Execute save operations
  - Save to Desktop
  - Track saved files
- **Logging**: `[FILE_SAVE]` prefix with 💾 emoji

#### 5. LOOK_NODE (`look_node`)
- **Purpose**: Examine and analyze files
- **Function**: `_file_look_node()`
- **Responsibilities**:
  - Execute look operations
  - Analyze file structure
  - Extract metadata
- **Logging**: `[FILE_LOOK]` prefix with 👀 emoji

#### 6. PARSE_NODE (`parse_node`)
- **Purpose**: Parse Excel files to understand structure
- **Function**: `_file_parse_node()`
- **Responsibilities**:
  - Execute parse operations
  - Understand Excel structure
  - Extract capabilities
- **Logging**: `[FILE_PARSE]` prefix with 📊 emoji

#### 7. EDIT_NODE (`edit_node`)
- **Purpose**: Modify files with intelligent operations
- **Function**: `_file_edit_node()`
- **Responsibilities**:
  - Execute edit operations
  - Intelligent modifications
  - Track changes
- **Logging**: `[FILE_EDIT]` prefix with ✏️ emoji

#### 8. EXECUTION_NODE (`execution_node`)
- **Purpose**: Execute planned operations and generate response
- **Function**: `_execution_node()`
- **Responsibilities**:
  - Compile results
  - Generate final response
  - Create suggestions and actions
- **Logging**: `[EXECUTION]` prefix with 🚀 emoji

## State Management

### AgentState TypedDict
```python
class AgentState(TypedDict):
    # Input
    user_query: str
    chat_history: List[Dict[str, Any]]
    document_context: Dict[str, Any]
    
    # Planning
    execution_plan: Dict[str, Any]
    selected_tools: List[str]
    route_decision: str
    
    # Knowledge Base
    knowledge_base: Dict[str, Any]
    knowledge_updates: List[Dict[str, Any]]
    
    # File Operations
    target_files: List[str]
    file_operations: List[Dict[str, Any]]
    parsed_content: Dict[str, Any]
    
    # Execution
    results: List[Dict[str, Any]]
    errors: List[str]
    
    # Output
    final_response: str
    suggestions: List[str]
    actions: List[str]
```

## Logging System

### Colored Terminal Output
- **DEBUG**: Cyan (`\033[36m`)
- **INFO**: Green (`\033[32m`)
- **WARNING**: Yellow (`\033[33m`)
- **ERROR**: Red (`\033[31m`)
- **CRITICAL**: Magenta (`\033[35m`)

### Node-Specific Logging
Each node has its own logger with:
- Node name prefix (e.g., `[PLANNING]`)
- Emoji indicators
- Clear status messages
- Error tracking

### Example Log Output
```
2025-10-17 17:09:24,519 - SidianLangGraph.PLANNING - [32mINFO[0m - 🎯 Starting planning phase...
2025-10-17 17:09:24,520 - SidianLangGraph.PLANNING - [32mINFO[0m - 📄 Parsed document detected: xxx.txt
2025-10-17 17:09:32,441 - SidianLangGraph.PLANNING - [32mINFO[0m - 🛤️  Route decision: file_operations
2025-10-17 17:09:32,457 - SidianLangGraph.FILE_EDIT - [32mINFO[0m - ✏️  Editing files...
2025-10-17 17:09:32,462 - SidianLangGraph.EXECUTION - [32mINFO[0m - 🚀 Executing final operations...
```

## Cursor Markers

### Code Structure Markers
The code includes clear markers for Cursor IDE navigation:

```python
# ====================================================================
# CURSOR MARKER: Agent Initialization Complete
# ====================================================================

# ====================================================================
# CURSOR MARKER: Building LangGraph Structure
# ====================================================================

# ====================================================================
# CURSOR MARKER: Planning Node Execution
# ====================================================================

# ====================================================================
# CURSOR MARKER: Knowledge Base Node Execution
# ====================================================================

# ====================================================================
# CURSOR MARKER: File Save Node Execution
# ====================================================================

# ====================================================================
# CURSOR MARKER: File Look Node Execution
# ====================================================================

# ====================================================================
# CURSOR MARKER: File Parse Node Execution
# ====================================================================

# ====================================================================
# CURSOR MARKER: File Edit Node Execution
# ====================================================================

# ====================================================================
# CURSOR MARKER: Execution Node - Final Phase
# ====================================================================

# ====================================================================
# CURSOR MARKER: Main Query Processing Start
# ====================================================================

# ====================================================================
# CURSOR MARKER: Query Processing Complete
# ====================================================================

# ====================================================================
# CURSOR MARKER: LangGraph Agent System Complete
# ====================================================================
```

## Usage

### Integration with AI Service
The LangGraph agent is integrated into the AI service:

```python
def _create_agent(self, agent_type: str) -> Any:
    if agent_type == "excel":
        # Use LangGraph agent for Excel operations
        from agents.langgraph_agent import SidianLangGraphAgent
        return SidianLangGraphAgent()
```

### Testing
Use the test script to verify functionality:

```bash
cd Mantle/sidian-backend
source ../../venv/bin/activate
python test_langgraph_agent.py
```

## Benefits

### 1. Modularity
- Each node has a single responsibility
- Easy to add new nodes
- Clear separation of concerns

### 2. Debuggability
- Clear terminal logging
- Node-specific error tracking
- Step-by-step execution visibility

### 3. Extensibility
- Easy to add new file operations
- Simple to modify routing logic
- Clear state management

### 4. Maintainability
- Cursor markers for navigation
- Well-documented code structure
- Type hints throughout

## Future Enhancements

### 1. Additional Nodes
- **VALIDATION_NODE**: Validate file operations
- **BACKUP_NODE**: Create backups before modifications
- **NOTIFICATION_NODE**: Send notifications to users

### 2. Advanced Routing
- **CONDITIONAL_ROUTING**: More sophisticated routing logic
- **PARALLEL_EXECUTION**: Run multiple nodes simultaneously
- **ERROR_RECOVERY**: Automatic error recovery mechanisms

### 3. Performance Optimization
- **CACHING**: Cache knowledge base updates
- **ASYNC_OPERATIONS**: Async file operations
- **BATCH_PROCESSING**: Process multiple files at once

## Conclusion

The LangGraph Agent System provides a robust, modular, and debuggable foundation for Excel operations. With clear logging, Cursor markers, and a well-structured architecture, it's easy to understand, debug, and extend.

