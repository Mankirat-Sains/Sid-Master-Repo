"""
Assistant response generator that combines prompts and tools.
Based on Supabase's generate-assistant-response but adapted for Python/OpenAI.
"""

import os
import json
import re
import logging
import sys
import time
from typing import List, Dict, Any, Optional
from openai import OpenAI
from tools import DatabaseTools
from prompts import (
    SCHEMA_PROMPT,
    SYSTEM_PROMPT,
    TOOLS_PROMPT
)

# Custom formatter that removes emojis for Windows console compatibility
class NoEmojiFormatter(logging.Formatter):
    """Formatter that removes emojis for Windows console compatibility."""
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "]+", flags=re.UNICODE
    )
    
    def format(self, record):
        # Remove emojis from message
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self.EMOJI_PATTERN.sub('', record.msg)
        return super().format(record)

# Set up logging with UTF-8 encoding for file and emoji removal for console
file_handler = logging.FileHandler('assistant.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(NoEmojiFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)


class TextToSQLAssistant:
    """Main assistant class that generates SQL from natural language queries."""
    
    def __init__(
        self,
        connection_string: str,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o"
    ):
        """
        Initialize the assistant.
        
        Args:
            connection_string: PostgreSQL connection string
            openai_api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model: OpenAI model to use (default: gpt-4o)
        """
        self.connection_string = connection_string
        self.model = model
        
        # Initialize OpenAI client
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var or pass openai_api_key parameter.")
        
        self.client = OpenAI(api_key=api_key)
        
        # Initialize database tools
        self.db_tools = DatabaseTools(connection_string)
        self.tools = self.db_tools.get_all_tools()
        
        # Schema cache
        self._schema_cache = None
        self._schema_cache_time = None
        self._schema_cache_ttl = 300  # Cache for 5 minutes
        
        # Build system prompt
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build the complete system prompt from all prompt components."""
        return f"""
{SCHEMA_PROMPT}

{SYSTEM_PROMPT}

{TOOLS_PROMPT}
"""
    
    def _get_schema_summary(self) -> str:
        """Get a summary of the database schema (cached)."""
        # Check cache
        current_time = time.time()
        if (self._schema_cache is not None and 
            self._schema_cache_time is not None and 
            (current_time - self._schema_cache_time) < self._schema_cache_ttl):
            logger.info(f"Using cached schema summary (age: {current_time - self._schema_cache_time:.1f}s)")
            return self._schema_cache
        
        logger.info("Fetching schema summary from database...")
        start_time = time.time()
        try:
            tables_result = self.db_tools.list_tables()
            if "error" in tables_result:
                logger.warning("Error fetching tables")
                return "Unable to retrieve schema information."
            
            table_names = [t["table_name"] for t in tables_result.get("tables", [])]
            logger.info(f"Found {len(table_names)} tables: {', '.join(table_names[:5])}{'...' if len(table_names) > 5 else ''}")
            
            schema_info = self.db_tools.get_schema_info(table_names=table_names)
            if "error" in schema_info:
                logger.warning("Error fetching schema info")
                schema_summary = f"Available tables: {', '.join(table_names)}"
            else:
                summary_parts = ["Available tables:"]
                for table_info in schema_info.get("tables", []):
                    table_name = table_info["table"]
                    columns = [col["name"] for col in table_info.get("columns", [])]
                    summary_parts.append(f"- {table_name}: {', '.join(columns[:10])}{'...' if len(columns) > 10 else ''}")
                schema_summary = "\n".join(summary_parts)
            
            # Cache the result
            self._schema_cache = schema_summary
            self._schema_cache_time = time.time()
            
            elapsed = time.time() - start_time
            logger.info(f"Schema summary fetched in {elapsed:.2f}s (cached for {self._schema_cache_ttl}s)")
            return schema_summary
        except Exception as e:
            logger.error(f"Error retrieving schema: {str(e)}")
            return f"Error retrieving schema: {str(e)}"
    
    def _format_tool_messages(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format tool calls for OpenAI API."""
        messages = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("arguments", {})
            
            if tool_name in self.tools:
                tool_func = self.tools[tool_name]["function"]
                try:
                    result = tool_func(**tool_args)
                    messages.append({
                        "role": "tool",
                        "content": json.dumps(result, default=str),
                        "tool_call_id": tool_call.get("id", "")
                    })
                except Exception as e:
                    messages.append({
                        "role": "tool",
                        "content": json.dumps({"error": str(e)}, default=str),
                        "tool_call_id": tool_call.get("id", "")
                    })
        return messages
    
    def _get_openai_tools(self) -> List[Dict[str, Any]]:
        """Convert our tools to OpenAI tool format."""
        openai_tools = []
        
        tool_descriptions = {
            "execute_sql": "Execute a SQL query and return results. Use this to run SQL queries.",
            "execute_function": "Execute a database function (e.g., match_documents, keyword_search_chunks). Provide function_name and arguments as a dictionary matching the function signature.",
            "search_column_values": "Search for text patterns across columns to find which columns contain specific keywords. Use when user mentions specific values to discover relevant columns.",
            "explore_column_values": "Explore unique values in a text column. CRITICAL: Use this BEFORE generating queries when user mentions specific values/terms. Identify relevant columns based on column names and context, then explore to see actual data values and correlate with user's question.",
            "get_schema_info": "Get detailed schema information. Use only if you need schema details not already in your context.",
            "get_logs": "Fetch database logs for debugging and error analysis. Use when queries fail to understand what went wrong. Filter by level (ERROR, WARNING) or search for specific error keywords.",
            "list_functions": "List all database functions. Use if you need to discover available functions.",
            "list_tables": "List all tables. Use only if schema may have changed.",
            "get_table_comments": "Get table and column comments. Use only if user asks about documentation.",
            "get_indexes": "Get index information. Use only for performance analysis."
        }
        
        for tool_name, description in tool_descriptions.items():
            if tool_name in self.tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": description,
                        "parameters": {
                            "type": "object",
                            "properties": self._get_tool_parameters(tool_name),
                            "required": []
                        }
                    }
                })
        
        return openai_tools
    
    def _get_tool_parameters(self, tool_name: str) -> Dict[str, Any]:
        """Get parameter schema for a tool."""
        param_schemas = {
            "list_tables": {
                "schemas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of schema names to list tables from (default: ['public'])"
                }
            },
            "get_schema_info": {
                "table_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of table names to get schema info for"
                },
                "schemas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of schema names (default: ['public'])"
                }
            },
            "list_functions": {
                "schemas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of schema names (default: ['public'])"
                }
            },
            "get_table_comments": {
                "table_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of table names to get comments for"
                }
            },
            "execute_sql": {
                "sql": {
                    "type": "string",
                    "description": "The SQL query to execute"
                },
                "limit": {
                    "type": "integer",
                    "description": "Optional limit for SELECT queries"
                }
            },
            "execute_function": {
                "function_name": {
                    "type": "string",
                    "description": "Name of the database function to execute (e.g., 'match_documents', 'keyword_search_chunks', 'get_neighbors')"
                },
                "arguments": {
                    "type": "object",
                    "description": "Dictionary of function arguments matching the function signature. For example: {'query_embedding': '[...]', 'match_count': 10, 'project_keys': ['project_key']}"
                }
            },
            "get_indexes": {
                "table_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of table names to get indexes for"
                }
            },
            "search_column_values": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table to search"
                },
                "search_text": {
                    "type": "string",
                    "description": "Text pattern to search for"
                },
                "column_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of column names to search. If not provided, automatically searches all searchable text columns."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of matching rows to return per column (default: 20)"
                }
            },
            "explore_column_values": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table"
                },
                "column_name": {
                    "type": "string",
                    "description": "Name of the column to explore (should be a text column, not an ID or primary key)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of unique values to return (default: 50)"
                },
                "search_pattern": {
                    "type": "string",
                    "description": "Optional SQL LIKE pattern to filter values (e.g., '%lintel%')"
                },
                "min_length": {
                    "type": "integer",
                    "description": "Optional minimum length of values to include"
                }
            },
            "get_logs": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of log entries to return (default: 50, max: 100)"
                },
                "level": {
                    "type": "string",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "FATAL", "PANIC"],
                    "description": "Filter by log level"
                },
                "search": {
                    "type": "string",
                    "description": "Optional text to search for in log messages"
                }
            }
        }
        return param_schemas.get(tool_name, {})
    
    def generate_response(
        self,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate SQL query from natural language.
        
        Args:
            user_query: Natural language query
            conversation_history: Previous conversation messages (optional)
        
        Returns:
            Dictionary with SQL query, explanation, and results
        """
        # Build messages
        messages = [
            {
                "role": "system",
                "content": self.system_prompt + f"\n\nCurrent schema summary:\n{self._get_schema_summary()}"
            }
        ]
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user query
        messages.append({
            "role": "user",
            "content": user_query
        })
        
        # Get OpenAI tools
        openai_tools = self._get_openai_tools()
        logger.info(f"🛠️ Available tools: {[t['function']['name'] for t in openai_tools]}")
        
        # Call OpenAI with tool support
        try:
            logger.info("🤖 Making FIRST LLM API call...")
            logger.info(f"📤 User query: {user_query}")
            logger.info(f"📝 System prompt length: {len(messages[0]['content'])} characters")
            
            llm_start_time = time.time()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=openai_tools,
                tool_choice="auto",
                temperature=0.1  # Lower temperature for more deterministic SQL
            )
            llm_elapsed = time.time() - llm_start_time
            
            assistant_message = response.choices[0].message
            logger.info(f"✅ First LLM call completed in {llm_elapsed:.2f}s")
            logger.info(f"📥 Full LLM response content:")
            logger.info(f"{'='*80}")
            logger.info(assistant_message.content if assistant_message.content else "No content")
            logger.info(f"{'='*80}")
            
            # Handle tool calls
            tool_calls = assistant_message.tool_calls or []
            tool_results = []
            
            if tool_calls:
                logger.info(f"🔧 LLM requested {len(tool_calls)} tool call(s)")
                for i, tool_call in enumerate(tool_calls, 1):
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    logger.info(f"  {i}. Tool: {tool_name}")
                    logger.info(f"     Tool Call ID: {tool_call.id}")
                    logger.info(f"     Arguments: {json.dumps(tool_args, indent=2)}")
                
                # Execute tool calls once
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    if tool_name in self.tools:
                        logger.info(f"⚙️ Executing tool: {tool_name}")
                        tool_start_time = time.time()
                        tool_func = self.tools[tool_name]["function"]
                        try:
                            result = tool_func(**tool_args)
                            tool_elapsed = time.time() - tool_start_time
                            logger.info(f"✅ Tool {tool_name} completed in {tool_elapsed:.2f}s")
                            logger.info(f"   Full result:")
                            logger.info(f"{'='*80}")
                            logger.info(json.dumps(result, indent=2, default=str))
                            logger.info(f"{'='*80}")
                            tool_results.append({
                                "tool": tool_name,
                                "result": result
                            })
                        except Exception as e:
                            tool_elapsed = time.time() - tool_start_time
                            logger.error(f"❌ Tool {tool_name} failed after {tool_elapsed:.2f}s: {str(e)}")
                            tool_results.append({
                                "tool": tool_name,
                                "error": str(e)
                            })
                
                # Check what types of tools were called
                exploration_tools = ["search_column_values", "explore_column_values", "get_schema_info", "list_functions"]
                debugging_tools = ["get_logs"]
                execute_sql_called = any(tc.function.name == "execute_sql" for tc in tool_calls)
                exploration_tools_called = any(tc.function.name in exploration_tools for tc in tool_calls)
                debugging_tools_called = any(tc.function.name in debugging_tools for tc in tool_calls)
                
                # Extract SQL from tool calls (handle multiple execute_sql calls)
                sql_queries = []
                execute_sql_results = []
                # Collect SQL queries from tool calls
                for tool_call in tool_calls:
                    if tool_call.function.name == "execute_sql":
                        tool_args = json.loads(tool_call.function.arguments)
                        sql = tool_args.get("sql")
                        if sql:
                            sql_queries.append(sql)
                
                # Collect corresponding results (tool_results are in same order as tool_calls)
                for tr in tool_results:
                    if tr.get("tool") == "execute_sql" and tr.get("result"):
                        execute_sql_results.append(tr.get("result"))
                
                # Check if all execute_sql calls succeeded
                all_execute_sql_succeeded = len(execute_sql_results) > 0 and all(
                    r.get("success", False) for r in execute_sql_results
                )
                
                # Extract reasoning from assistant message if available
                reasoning = assistant_message.content or ""
                logger.info(f"📝 Full reasoning from first LLM call:")
                logger.info(f"{'='*80}")
                logger.info(reasoning)
                logger.info(f"{'='*80}")
                
                # Decision: Make second LLM call if:
                # 1. Exploration tools were used (model was unsure and gathering info)
                # 2. execute_sql failed (need error handling and debugging)
                # 3. No SQL was generated but exploration happened (model needs to generate SQL after exploration)
                # 4. Debugging tools were used (model is checking logs to understand errors)
                should_make_second_call = (
                    exploration_tools_called or  # Model explored data first
                    debugging_tools_called or  # Model is checking logs for errors
                    (execute_sql_called and not all_execute_sql_succeeded) or  # SQL failed - need to debug
                    (exploration_tools_called and not execute_sql_called)  # Explored but didn't generate SQL yet
                )
                
                if not should_make_second_call and sql_queries:
                    # Return directly - model is confident and SQL was generated successfully
                    logger.info(f"✅ Returning SQL + reasoning directly - {len(sql_queries)} query/queries")
                    for i, sql in enumerate(sql_queries, 1):
                        logger.info(f"{'='*80}")
                        logger.info(f"  Query {i} (FULL):")
                        logger.info(f"{'='*80}")
                        logger.info(sql)
                        logger.info(f"{'='*80}")
                    
                    # Log final summary
                    logger.info(f"{'='*80}")
                    logger.info("📊 FINAL SUMMARY (First Call)")
                    logger.info(f"{'='*80}")
                    logger.info(f"Tools Called: {[tc.function.name for tc in tool_calls]}")
                    logger.info(f"SQL Queries Generated: {len(sql_queries)}")
                    for i, sql in enumerate(sql_queries, 1):
                        logger.info(f"  Query {i}: {sql}")
                    logger.info(f"Reasoning: {reasoning}")
                    logger.info(f"{'='*80}")
                    
                    return {
                        "sql": sql_queries[0] if len(sql_queries) == 1 else None,  # Backward compatibility
                        "sql_queries": sql_queries,  # New: list of all SQL queries
                        "reasoning": reasoning,  # Changed from explanation to reasoning
                        "tool_calls": tool_calls,
                        "tool_results": tool_results,
                        "final_message": None  # No second call made
                    }
                
                # Make second LLM call with exploration results
                logger.info("🤖 Making SECOND LLM API call with exploration results...")
                messages.append(assistant_message)
                
                # Add tool results to messages
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    # Find the result for this tool call
                    tool_result = None
                    for tr in tool_results:
                        if tr.get("tool") == tool_name:
                            if "error" in tr:
                                tool_result = {"error": tr["error"]}
                            else:
                                tool_result = tr.get("result")
                            break
                    
                    if tool_result is not None:
                        messages.append({
                            "role": "tool",
                            "content": json.dumps(tool_result, default=str),
                            "tool_call_id": tool_call.id
                        })
                
                # Add instruction for second call
                has_errors = any(tr.get("error") or (tr.get("result") and not tr.get("result", {}).get("success", True)) for tr in tool_results)
                if has_errors:
                    messages.append({
                        "role": "user",
                        "content": "Some queries failed or returned errors. Please analyze the errors, use get_logs if needed to understand what went wrong, and generate corrected SQL queries. If you see domain terms (materials, building types, etc.), use explore_column_values first to see actual values, then reason semantically about relationships."
                    })
                else:
                    messages.append({
                        "role": "user",
                        "content": "Based on the exploration results above, please generate the final SQL queries to answer the user's question. Use the information gathered to create accurate queries. If you see domain terms (materials, building types, etc.), reason semantically about relationships and use OR conditions to match related values."
                    })
                
                llm_start_time = time.time()
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto",
                    temperature=0.1
                )
                llm_elapsed = time.time() - llm_start_time
                
                final_message = final_response.choices[0].message
                logger.info(f"✅ Second LLM call completed in {llm_elapsed:.2f}s")
                logger.info(f"📥 Full Second LLM response content:")
                logger.info(f"{'='*80}")
                logger.info(final_message.content if final_message.content else "No content")
                logger.info(f"{'='*80}")
                
                # Check if second LLM call made additional tool calls (e.g., execute_sql)
                final_tool_calls = final_message.tool_calls or []
                if final_tool_calls:
                    logger.info(f"🔧 Second LLM call requested {len(final_tool_calls)} additional tool call(s)")
                    # Execute additional tool calls
                    for tool_call in final_tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        logger.info(f"  Additional tool: {tool_name}")
                        logger.info(f"     Tool Call ID: {tool_call.id}")
                        logger.info(f"     Arguments: {json.dumps(tool_args, indent=2)}")
                        
                        if tool_name in self.tools:
                            logger.info(f"⚙️ Executing additional tool: {tool_name}")
                            tool_start_time = time.time()
                            tool_func = self.tools[tool_name]["function"]
                            try:
                                result = tool_func(**tool_args)
                                tool_elapsed = time.time() - tool_start_time
                                logger.info(f"✅ Additional tool {tool_name} completed in {tool_elapsed:.2f}s")
                                logger.info(f"   Full result:")
                                logger.info(f"{'='*80}")
                                logger.info(json.dumps(result, indent=2, default=str))
                                logger.info(f"{'='*80}")
                                tool_results.append({
                                    "tool": tool_name,
                                    "result": result
                                })
                                tool_calls.append(tool_call)
                                
                                # Extract SQL if it's execute_sql
                                if tool_name == "execute_sql":
                                    sql = tool_args.get("sql")
                                    if sql:
                                        sql_queries.append(sql)
                            except Exception as e:
                                tool_elapsed = time.time() - tool_start_time
                                logger.error(f"❌ Additional tool {tool_name} failed after {tool_elapsed:.2f}s: {str(e)}")
                                tool_results.append({
                                    "tool": tool_name,
                                    "error": str(e)
                                })
                                tool_calls.append(tool_call)
                
                # Extract SQL from final message or tool calls
                if not sql_queries:
                    extracted_sql = self._extract_sql_from_message(final_message)
                    if extracted_sql:
                        sql_queries = extracted_sql if isinstance(extracted_sql, list) else [extracted_sql]
                
                # Get final reasoning (combine original and final if needed)
                final_reasoning = final_message.content or reasoning
                logger.info(f"📝 Full reasoning from second LLM call:")
                logger.info(f"{'='*80}")
                logger.info(final_reasoning)
                logger.info(f"{'='*80}")
                
                if sql_queries:
                    logger.info(f"SQL extracted: {len(sql_queries)} query/queries")
                    for i, sql in enumerate(sql_queries, 1):
                        logger.info(f"{'='*80}")
                        logger.info(f"  Query {i} (FULL):")
                        logger.info(f"{'='*80}")
                        logger.info(sql)
                        logger.info(f"{'='*80}")
                else:
                    logger.warning("No SQL found in tool calls or final response")
                
                # Log final summary
                logger.info(f"{'='*80}")
                logger.info("📊 FINAL SUMMARY (Second Call)")
                logger.info(f"{'='*80}")
                logger.info(f"Tools Called: {[tc.function.name for tc in tool_calls]}")
                logger.info(f"SQL Queries Generated: {len(sql_queries)}")
                for i, sql in enumerate(sql_queries, 1):
                    logger.info(f"  Query {i}: {sql}")
                logger.info(f"Reasoning: {final_reasoning}")
                logger.info(f"{'='*80}")
                
                return {
                    "sql": sql_queries[0] if len(sql_queries) == 1 else None,  # Backward compatibility
                    "sql_queries": sql_queries,  # New: list of all SQL queries
                    "reasoning": final_reasoning,  # Changed from explanation to reasoning
                    "tool_calls": tool_calls,
                    "tool_results": tool_results,
                    "final_message": final_message.content
                }
            else:
                logger.info("✅ No tool calls needed - SQL generated directly")
                extracted_sql = self._extract_sql_from_message(assistant_message)
                sql_queries = []
                if extracted_sql:
                    sql_queries = [extracted_sql] if isinstance(extracted_sql, str) else extracted_sql
                    logger.info(f"📝 SQL extracted: {len(sql_queries)} query/queries")
                    for i, sql in enumerate(sql_queries, 1):
                        logger.info(f"{'='*80}")
                        logger.info(f"  Query {i} (FULL):")
                        logger.info(f"{'='*80}")
                        logger.info(sql)
                        logger.info(f"{'='*80}")
                
                reasoning = assistant_message.content or ""
                logger.info(f"📝 Full reasoning:")
                logger.info(f"{'='*80}")
                logger.info(reasoning)
                logger.info(f"{'='*80}")
                
                # Log final summary
                logger.info(f"{'='*80}")
                logger.info("📊 FINAL SUMMARY (No Tool Calls)")
                logger.info(f"{'='*80}")
                logger.info(f"Tools Called: []")
                logger.info(f"SQL Queries Generated: {len(sql_queries)}")
                for i, sql in enumerate(sql_queries, 1):
                    logger.info(f"  Query {i}: {sql}")
                logger.info(f"Reasoning: {reasoning}")
                logger.info(f"{'='*80}")
                
                return {
                    "sql": sql_queries[0] if len(sql_queries) == 1 else None,  # Backward compatibility
                    "sql_queries": sql_queries,  # New: list of all SQL queries
                    "reasoning": assistant_message.content or "",  # Changed from explanation to reasoning
                    "tool_calls": [],
                    "tool_results": []
                }
        
        except Exception as e:
            logger.error(f"❌ Error in generate_response: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "sql": None,
                "reasoning": None
            }
    
    def _extract_sql_from_message(self, message) -> List[str]:
        """Extract SQL queries from assistant message. Returns a list of SQL queries."""
        content = message.content or ""
        sql_queries = []
        
        # Look for SQL in code blocks (can have multiple)
        import re
        sql_pattern = r"```sql\s*(.*?)\s*```"
        matches = re.findall(sql_pattern, content, re.DOTALL)
        if matches:
            sql_queries.extend([m.strip() for m in matches if m.strip()])
        
        # Look for SQL in execute_sql tool calls (can have multiple)
        if message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call.function.name == "execute_sql":
                    args = json.loads(tool_call.function.arguments)
                    sql = args.get("sql")
                    if sql:
                        sql_queries.append(sql)
        
        return sql_queries if sql_queries else []
    
    def query(self, user_query: str) -> Dict[str, Any]:
        """
        Simple query interface that generates and executes SQL.
        
        Args:
            user_query: Natural language query
        
        Returns:
            Dictionary with SQL, results, and explanation
        """
        logger.info("="*80)
        logger.info(f"Starting query: {user_query}")
        logger.info("="*80)
        query_start_time = time.time()
        
        # Generate SQL
        response = self.generate_response(user_query)
        
        if "error" in response:
            logger.error(f"Error in generate_response: {response['error']}")
            return response
        
        # Get SQL queries (support both single and multiple)
        sql_queries = response.get("sql_queries", [])
        sql = response.get("sql")  # Backward compatibility
        
        # If sql_queries is empty but sql exists, use sql
        if not sql_queries and sql:
            sql_queries = [sql]
        
        # Check if SQL was already executed via execute_sql tool(s)
        tool_results = response.get("tool_results", [])
        execute_results = []
        
        # Collect all execute_sql results
        for tr in tool_results:
            if tr.get("tool") == "execute_sql":
                result = tr.get("result")
                if result:
                    execute_results.append(result)
                    logger.info(f"SQL was already executed via execute_sql tool - {result.get('row_count', 0) if result.get('query_type') == 'SELECT' else result.get('rows_affected', 0)} rows")
        
        # If SQL wasn't executed via tool, execute it now
        if not execute_results:
            if not sql_queries:
                logger.warning("No SQL generated")
                return {
                    "error": "No SQL generated",
                    "reasoning": response.get("reasoning", "")
                }
            
            # Execute all SQL queries
            logger.info(f"Executing {len(sql_queries)} SQL query/queries...")
            for i, sql_query in enumerate(sql_queries, 1):
                logger.info(f"Query {i}/{len(sql_queries)}: {sql_query[:100]}...")
                execute_start_time = time.time()
                execute_result = self.db_tools.execute_sql(sql_query)
                execute_elapsed = time.time() - execute_start_time
                execute_results.append(execute_result)
                
                if execute_result.get("success"):
                    if execute_result.get("query_type") == "SELECT":
                        logger.info(f"  Query {i} executed successfully in {execute_elapsed:.2f}s - {execute_result.get('row_count', 0)} rows returned")
                    else:
                        logger.info(f"  Query {i} executed successfully in {execute_elapsed:.2f}s - {execute_result.get('rows_affected', 0)} rows affected")
                else:
                    logger.error(f"  Query {i} execution failed: {execute_result.get('error')}")
        
        total_elapsed = time.time() - query_start_time
        logger.info(f"Total query time: {total_elapsed:.2f}s")
        logger.info("="*80)
        
        return {
            "sql": sql_queries[0] if len(sql_queries) == 1 else None,  # Backward compatibility
            "sql_queries": sql_queries,  # New: list of all SQL queries
            "reasoning": response.get("reasoning", ""),  # Changed from explanation to reasoning
            "results": execute_results[0] if len(execute_results) == 1 else None,  # Backward compatibility
            "results_list": execute_results,  # New: list of all execution results
            "tool_calls": response.get("tool_calls", []),
            "tool_results": response.get("tool_results", [])
        }

