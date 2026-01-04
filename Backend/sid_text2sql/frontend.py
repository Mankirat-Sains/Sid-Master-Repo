"""
Simple Streamlit frontend for text-to-SQL assistant.
"""

import streamlit as st
import os
from dotenv import load_dotenv
from assistant import TextToSQLAssistant
import json
import time

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Text-to-SQL Assistant",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if "assistant" not in st.session_state:
    st.session_state.assistant = None
if "query_history" not in st.session_state:
    st.session_state.query_history = []

def initialize_assistant(connection_string: str, model: str = "gpt-4o"):
    """Initialize the assistant."""
    try:
        return TextToSQLAssistant(
            connection_string=connection_string,
            model=model
        )
    except Exception as e:
        st.error(f"Failed to initialize assistant: {e}")
        return None

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Connection string
    connection_string = st.text_input(
        "Database Connection String",
        value=os.getenv("SUPABASE_DB_URL", ""),
        type="password",
        help="PostgreSQL connection string"
    )
    
    # Model selection
    model = st.selectbox(
        "OpenAI Model",
        ["gpt-4o", "gpt-4-turbo-preview", "gpt-3.5-turbo"],
        index=0
    )
    
    # Initialize button
    if st.button("🔌 Initialize Assistant"):
        if connection_string:
            with st.spinner("Initializing assistant..."):
                st.session_state.assistant = initialize_assistant(connection_string, model)
                if st.session_state.assistant:
                    st.success("✅ Assistant initialized!")
        else:
            st.error("Please enter a connection string")
    
    # Status
    st.divider()
    st.subheader("Status")
    if st.session_state.assistant:
        st.success("✅ Ready")
    else:
        st.warning("⚠️ Not initialized")
    
    # Query history
    st.divider()
    st.subheader("Query History")
    if st.session_state.query_history:
        for i, q in enumerate(reversed(st.session_state.query_history[-10:]), 1):
            st.text(f"{i}. {q[:50]}...")
    else:
        st.text("No queries yet")

# Main content
st.title("🔍 Text-to-SQL Assistant")
st.markdown("Convert natural language questions into SQL queries")

# Check if assistant is initialized
if not st.session_state.assistant:
    st.warning("⚠️ Please initialize the assistant in the sidebar first.")
    st.stop()

# Query input
query = st.text_input(
    "Enter your question:",
    placeholder="e.g., List all tables in the database",
    key="query_input"
)

col1, col2 = st.columns([1, 4])

with col1:
    execute_query = st.button("🚀 Execute Query", type="primary")
with col2:
    generate_only = st.button("📝 Generate SQL Only")

# Process query
if execute_query or generate_only:
    if not query:
        st.error("Please enter a query")
        st.stop()
    
    # Add to history
    st.session_state.query_history.append(query)
    
    # Create tabs for results
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Results", "📝 SQL", "🤖 LLM Response", "🔧 Tools", "📋 Logs"])
    
    with st.spinner("Processing query..."):
        start_time = time.time()
        
        try:
            if execute_query:
                result = st.session_state.assistant.query(query)
            else:
                result = st.session_state.assistant.generate_response(query)
                result["results"] = None
            
            elapsed_time = time.time() - start_time
            
            # Results tab
            with tab1:
                st.subheader("Query Results")
                
                if "error" in result:
                    st.error(f"❌ Error: {result['error']}")
                else:
                    # Handle multiple queries/results
                    results_list = result.get("results_list", [])
                    single_result = result.get("results")
                    
                    # If we have multiple results, show them all
                    if results_list:
                        st.write(f"**Executed {len(results_list)} query/queries:**")
                        for i, res in enumerate(results_list, 1):
                            with st.expander(f"Query {i} Results", expanded=(i == 1)):
                                if res.get("success"):
                                    if res.get("query_type") == "SELECT":
                                        row_count = res.get("row_count", 0)
                                        st.success(f"✅ Query {i} executed successfully - {row_count} rows returned")
                                        
                                        if res.get("rows"):
                                            st.dataframe(res["rows"], use_container_width=True)
                                    else:
                                        rows_affected = res.get("rows_affected", 0)
                                        st.success(f"✅ Query {i} executed successfully - {rows_affected} rows affected")
                                else:
                                    st.error(f"❌ Query {i} execution error: {res.get('error')}")
                    elif single_result:
                        # Backward compatibility: single result
                        if single_result.get("success"):
                            if single_result.get("query_type") == "SELECT":
                                row_count = single_result.get("row_count", 0)
                                st.success(f"✅ Query executed successfully - {row_count} rows returned")
                                
                                if single_result.get("rows"):
                                    st.dataframe(single_result["rows"], use_container_width=True)
                            else:
                                rows_affected = single_result.get("rows_affected", 0)
                                st.success(f"✅ Query executed successfully - {rows_affected} rows affected")
                        else:
                            st.error(f"❌ Execution error: {single_result.get('error')}")
                    else:
                        st.info("SQL generated but not executed")
                    
                    # Explanation
                    if result.get("explanation"):
                        st.markdown("### Explanation")
                        st.markdown(result["explanation"])
            
            # SQL tab
            with tab2:
                st.subheader("Generated SQL")
                sql_queries = result.get("sql_queries", [])
                sql = result.get("sql")  # Backward compatibility
                
                # If we have multiple queries, show them all
                if sql_queries:
                    st.write(f"**Generated {len(sql_queries)} SQL query/queries:**")
                    all_sql = ""
                    for i, sql_query in enumerate(sql_queries, 1):
                        st.markdown(f"### Query {i}")
                        st.code(sql_query, language="sql")
                        all_sql += f"-- Query {i}\n{sql_query}\n\n"
                    
                    # Download all queries
                    st.download_button(
                        "📥 Download All SQL",
                        all_sql,
                        file_name="queries.sql",
                        mime="text/plain"
                    )
                elif sql:
                    # Backward compatibility: single SQL
                    st.code(sql, language="sql")
                    st.download_button(
                        "📥 Download SQL",
                        sql,
                        file_name="query.sql",
                        mime="text/plain"
                    )
                else:
                    st.warning("No SQL generated")
            
            # LLM Response tab (NEW - shows full LLM responses)
            with tab3:
                st.subheader("Full LLM Response")
                
                # Show explanation (full text)
                if result.get("explanation"):
                    st.markdown("### Final LLM Response")
                    st.markdown(result["explanation"])
                    st.download_button(
                        "📥 Download Response",
                        result["explanation"],
                        file_name="llm_response.txt",
                        mime="text/plain"
                    )
                
                # Show final message if available
                if result.get("final_message"):
                    st.markdown("---")
                    st.markdown("### Complete Final Message")
                    st.text_area("Full response text:", result["final_message"], height=300)
                
                # Show tool calls that led to SQL generation
                tool_calls = result.get("tool_calls", [])
                if tool_calls:
                    st.markdown("---")
                    st.markdown("### Tool Calls Made by LLM")
                    for i, tc in enumerate(tool_calls, 1):
                        tool_name = tc.function.name if hasattr(tc, 'function') else tc.get('function', {}).get('name', 'unknown')
                        tool_args = json.loads(tc.function.arguments) if hasattr(tc, 'function') else tc.get('arguments', {})
                        
                        st.markdown(f"**{i}. {tool_name}**")
                        st.json(tool_args)
                        
                        # If this is execute_sql, highlight it
                        if tool_name == "execute_sql":
                            sql_from_tool = tool_args.get("sql", "")
                            if sql_from_tool:
                                st.code(sql_from_tool, language="sql")
            
            # Tools tab
            with tab4:
                st.subheader("Tool Usage & Results")
                
                tool_calls = result.get("tool_calls", [])
                tool_results = result.get("tool_results", [])
                
                if tool_calls:
                    st.write(f"**Tools Called:** {len(tool_calls)}")
                    for i, tc in enumerate(tool_calls, 1):
                        tool_name = tc.function.name if hasattr(tc, 'function') else tc.get('function', {}).get('name', 'unknown')
                        tool_args = json.loads(tc.function.arguments) if hasattr(tc, 'function') else tc.get('arguments', {})
                        
                        with st.expander(f"{i}. {tool_name} - Click to see details", expanded=(tool_name == "execute_sql")):
                            st.markdown("**Arguments:**")
                            st.json(tool_args)
                            
                            # Show result if available
                            if i <= len(tool_results):
                                tr = tool_results[i-1]
                                st.markdown("**Result:**")
                                if "error" in tr:
                                    st.error(f"Error: {tr['error']}")
                                else:
                                    result_data = tr.get("result", {})
                                    if isinstance(result_data, dict):
                                        # Show summary first
                                        if "success" in result_data:
                                            if result_data.get("query_type") == "SELECT":
                                                st.success(f"✅ Executed successfully - {result_data.get('row_count', 0)} rows returned")
                                            else:
                                                st.success(f"✅ Executed successfully - {result_data.get('rows_affected', 0)} rows affected")
                                        
                                        # Show full result in expandable section
                                        with st.expander("View full result JSON"):
                                            st.json(result_data)
                                        
                                                        # If it's execute_sql result with rows, show them
                                        if result_data.get("rows"):
                                            st.markdown("**Query Results:**")
                                            st.dataframe(result_data["rows"], use_container_width=True)
                                        
                                        # Show SQL if available
                                        if tool_name == "execute_sql" and tool_args.get("sql"):
                                            st.markdown("**SQL Executed:**")
                                            st.code(tool_args["sql"], language="sql")
                                    else:
                                        st.text(str(result_data))
                else:
                    st.info("No tools were called")
            
            # Logs tab
            with tab5:
                st.subheader("Execution Logs & Metrics")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("⏱️ Total Time", f"{elapsed_time:.2f}s")
                
                tool_calls = result.get("tool_calls", [])
                with col2:
                    st.metric("🔧 Tools Called", len(tool_calls))
                
                # LLM calls (estimate: 1 if no tools, 2 if tools)
                llm_calls = 2 if tool_calls else 1
                with col3:
                    st.metric("🤖 LLM Calls", llm_calls)
                
                st.divider()
                
                # Read log file if exists
                if os.path.exists("assistant.log"):
                    st.markdown("### Recent Log Entries")
                    with open("assistant.log", "r", encoding="utf-8") as f:
                        logs = f.readlines()
                        # Show last 100 lines for better visibility
                        recent_logs = logs[-100:]
                        st.code("".join(recent_logs), language=None)
                    
                    # Download log button
                    with open("assistant.log", "r", encoding="utf-8") as f:
                        log_content = f.read()
                    st.download_button(
                        "📥 Download Full Log",
                        log_content,
                        file_name=f"assistant_log_{int(time.time())}.log",
                        mime="text/plain"
                    )
                else:
                    st.info("No log file found")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.exception(e)

# Example queries
st.divider()
st.subheader("💡 Example Queries")

example_queries = [
    "List all tables in the database",
    "Count all projects",
    "Search for documents containing 'structural beam'",
    "Find chunks for project PROJ001",
    "Show me all projects in Kitchener",
    "Search for documents about concrete strength",
]

cols = st.columns(3)
for i, example in enumerate(example_queries):
    with cols[i % 3]:
        if st.button(example, key=f"example_{i}", use_container_width=True):
            st.session_state.query_input = example
            st.rerun()

