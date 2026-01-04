"""
Example usage of the text-to-SQL assistant.
"""

import os
from dotenv import load_dotenv
from assistant import TextToSQLAssistant

# Load environment variables
load_dotenv()

# Get connection string from environment or use default
CONNECTION_STRING = os.getenv(
    "SUPABASE_DB_URL",
    "postgresql://user:password@localhost:5432/dbname"
)

def main():
    """Example usage of the text-to-SQL assistant."""
    
    # Initialize assistant
    print("Initializing Text-to-SQL Assistant...")
    assistant = TextToSQLAssistant(
        connection_string=CONNECTION_STRING,
        model="gpt-4o"
    )
    
    # Example queries
    queries = [
        "List all tables in the database",
        "Find all projects with more than 100 document chunks",
        "Search for documents similar to 'structural beam design'",
        "Find chunks containing 'concrete strength' in project 'PROJ001'",
        "Show me all projects in Kitchener",
        "Count total number of document chunks"
    ]
    
    print("\n" + "="*60)
    print("Example Queries")
    print("="*60)
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 60)
        
        try:
            result = assistant.query(query)
            
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"SQL: {result.get('sql', 'N/A')}")
                print(f"Explanation: {result.get('explanation', 'N/A')[:200]}...")
                
                if result.get("results"):
                    results = result["results"]
                    if results.get("success"):
                        if results.get("query_type") == "SELECT":
                            print(f"Rows returned: {results.get('row_count', 0)}")
                            if results.get("rows"):
                                print(f"Sample row: {results['rows'][0]}")
                        else:
                            print(f"Rows affected: {results.get('rows_affected', 0)}")
                    else:
                        print(f"Execution error: {results.get('error')}")
        
        except Exception as e:
            print(f"Exception: {str(e)}")
        
        print()

if __name__ == "__main__":
    main()

