"""
Interactive testing script with comprehensive logging.
"""

import os
import sys
import re
from dotenv import load_dotenv
from assistant import TextToSQLAssistant
import logging

# Load environment variables
load_dotenv()

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
file_handler = logging.FileHandler('test_interactive.log', encoding='utf-8')
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

def print_result(result, show_full=False):
    """Pretty print result."""
    print("\n" + "="*80)
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return
    
    print(f"SQL Generated:")
    print("-" * 80)
    sql = result.get("sql", "No SQL generated")
    print(sql)
    
    print(f"\nExplanation:")
    print("-" * 80)
    explanation = result.get("explanation", "")
    print(explanation[:500] + "..." if len(explanation) > 500 else explanation)
    
    tool_calls = result.get("tool_calls", [])
    print(f"\nTool Calls: {len(tool_calls)}")
    for i, tc in enumerate(tool_calls, 1):
        tool_name = tc.function.name if hasattr(tc, 'function') else tc.get('function', {}).get('name', 'unknown')
        print(f"  {i}. {tool_name}")
    
    tool_results = result.get("tool_results", [])
    if tool_results:
        print(f"\nTool Results:")
        for i, tr in enumerate(tool_results, 1):
            tool_name = tr.get("tool", "unknown")
            if "error" in tr:
                print(f"  {i}. {tool_name}: ERROR - {tr['error']}")
            else:
                result_data = tr.get("result", {})
                if isinstance(result_data, dict):
                    if "tables" in result_data:
                        count = result_data.get("count", len(result_data.get("tables", [])))
                        print(f"  {i}. {tool_name}: OK - {count} items")
                    elif "success" in result_data:
                        print(f"  {i}. {tool_name}: OK - Success")
                    else:
                        print(f"  {i}. {tool_name}: OK - Result received")
                else:
                    print(f"  {i}. {tool_name}: OK - Result received")
    
    if result.get("results"):
        results = result["results"]
        if results.get("success"):
            if results.get("query_type") == "SELECT":
                row_count = results.get('row_count', 0)
                print(f"\nQuery Results: {row_count} rows")
                if show_full and results.get("rows"):
                    print("\nFirst few rows:")
                    for row in results["rows"][:5]:
                        print(f"  {row}")
            else:
                print(f"\nRows affected: {results.get('rows_affected', 0)}")
        else:
            print(f"\nExecution error: {results.get('error')}")
    
    print("="*80)

def main():
    """Interactive testing with custom query input."""
    logger.info("="*80)
    logger.info("Starting Interactive Test")
    logger.info("="*80)
    
    # Get connection string
    connection_string = os.getenv("SUPABASE_DB_URL")
    if not connection_string:
        print("ERROR: SUPABASE_DB_URL not set in .env file")
        return
    
    # Initialize assistant
    print("Initializing Text-to-SQL Assistant...")
    try:
        assistant = TextToSQLAssistant(
            connection_string=connection_string,
            model="gpt-4o"
        )
        print("Assistant initialized successfully!")
    except Exception as e:
        print(f"Failed to initialize assistant: {e}")
        return
    
    # Example queries for reference
    example_queries = [
        "List all tables in the database",
        "Count all projects",
        "Search for documents containing 'structural beam'",
        "Find chunks for project PROJ001",
        "Show me all projects in Kitchener",
        "Search for documents about concrete strength",
    ]
    
    print("\n" + "="*80)
    print("Interactive Text-to-SQL Assistant")
    print("="*80)
    print("\nType your questions in natural language.")
    print("Commands:")
    print("  - Type your question and press Enter to execute")
    print("  - Type 'examples' to see example queries")
    print("  - Type 'generate' to generate SQL without executing")
    print("  - Type 'quit' or 'exit' to exit")
    print("="*80)
    
    query_count = 0
    
    while True:
        try:
            # Get user input
            print("\n" + "-"*80)
            user_input = input("\nEnter your query: ").strip()
            
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nExiting...")
                break
            
            if user_input.lower() == 'examples':
                print("\nExample queries:")
                for i, eq in enumerate(example_queries, 1):
                    print(f"  {i}. {eq}")
                continue
            
            # Check if user wants to generate only (without execution)
            generate_only = user_input.lower().startswith('generate')
            if generate_only:
                query = user_input[8:].strip()  # Remove 'generate' prefix
                if not query:
                    query = input("Enter query to generate SQL for: ").strip()
            else:
                query = user_input
            
            if not query:
                continue
            
            query_count += 1
            print(f"\n[Query #{query_count}] Processing: {query}")
            print("-" * 80)
            
            try:
                if generate_only:
                    # Generate SQL only
                    result = assistant.generate_response(query)
                    print("\nSQL Generated (not executed):")
                    print("-" * 80)
                    sql = result.get("sql", "No SQL generated")
                    print(sql)
                    
                    if result.get("explanation"):
                        print("\nExplanation:")
                        print("-" * 80)
                        print(result["explanation"][:500] + "..." if len(result["explanation"]) > 500 else result["explanation"])
                else:
                    # Execute query
                    result = assistant.query(query)
                    print_result(result, show_full=True)
                    
            except KeyboardInterrupt:
                print("\n\nQuery interrupted by user.")
                continue
            except Exception as e:
                print(f"\nException: {e}")
                logger.error(f"Exception in query: {e}", exc_info=True)
        
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except EOFError:
            print("\n\nExiting...")
            break
    
    print("\n" + "="*80)
    print(f"Session completed! Processed {query_count} queries.")
    print("="*80)
    print("\nCheck 'assistant.log' and 'test_interactive.log' for detailed logs")

if __name__ == "__main__":
    main()

