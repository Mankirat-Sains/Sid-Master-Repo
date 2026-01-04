"""
Tools for the text-to-SQL assistant.
Based on Supabase AI assistant tools but adapted for this specific schema.
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import Dict, List, Any, Optional
import json
import logging
import time
from functools import wraps

# Set up logging
logger = logging.getLogger(__name__)


def tool(name: str, description: str):
    """Decorator to register a tool function."""
    def decorator(func):
        func._tool_name = name
        func._tool_description = description
        return func
    return decorator


class DatabaseTools:
    """Collection of database tools for the AI assistant."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    def _execute_query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        conn = None
        try:
            logger.debug(f"🔌 Connecting to database...")
            conn = psycopg2.connect(self.connection_string)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                logger.debug(f"📊 Executing query: {sql[:100]}...")
                start_time = time.time()
                cur.execute(sql, params)
                if cur.description:
                    results = cur.fetchall()
                    elapsed = time.time() - start_time
                    logger.debug(f"✅ Query completed in {elapsed:.2f}s - {len(results)} rows")
                    return [dict(row) for row in results]
                elapsed = time.time() - start_time
                logger.debug(f"✅ Query completed in {elapsed:.2f}s")
                return []
        except Exception as e:
            logger.error(f"❌ Database error: {str(e)}")
            raise Exception(f"Database error: {str(e)}")
        finally:
            if conn:
                conn.close()
                logger.debug("🔌 Database connection closed")
    
    def _get_searchable_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get columns that are good candidates for text search.
        Excludes primary keys, foreign keys, IDs, timestamps, and numeric types.
        Prioritizes columns with names suggesting text content (name, label, description, etc.).
        """
        sql = """
        SELECT 
            c.column_name,
            c.data_type,
            c.character_maximum_length,
            CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key,
            CASE WHEN fk.column_name IS NOT NULL THEN true ELSE false END as is_foreign_key
        FROM information_schema.columns c
        LEFT JOIN (
            SELECT ku.table_schema, ku.table_name, ku.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage ku 
                ON tc.constraint_name = ku.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
        ) pk ON pk.table_schema = c.table_schema 
            AND pk.table_name = c.table_name 
            AND pk.column_name = c.column_name
        LEFT JOIN (
            SELECT ku.table_schema, ku.table_name, ku.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage ku 
                ON tc.constraint_name = ku.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
        ) fk ON fk.table_schema = c.table_schema 
            AND fk.table_name = c.table_name 
            AND fk.column_name = c.column_name
        WHERE c.table_schema = 'public'
        AND c.table_name = %s
        ORDER BY c.ordinal_position;
        """
        
        try:
            results = self._execute_query(sql, (table_name,))
            
            # Filter out non-searchable columns
            searchable = []
            excluded_patterns = [
                'id', '_id', 'uuid', 'guid', 'key', '_key',
                'created_at', 'updated_at', 'deleted_at', 'timestamp',
                'created', 'updated', 'modified', 'date'
            ]
            
            # Prioritized patterns (columns likely to contain domain text)
            prioritized_patterns = [
                'name', 'label', 'title', 'description', 'text', 'content',
                'comment', 'note', 'summary', 'detail', 'info', 'value',
                'type', 'category', 'class', 'kind', 'status', 'state'
            ]
            
            for col in results:
                col_name_lower = col['column_name'].lower()
                
                # Skip primary keys and foreign keys
                if col.get('is_primary_key') or col.get('is_foreign_key'):
                    continue
                
                # Skip columns matching excluded patterns
                if any(pattern in col_name_lower for pattern in excluded_patterns):
                    # But allow if it's clearly a text field (e.g., "type_name", "status_label")
                    if not any(priority in col_name_lower for priority in prioritized_patterns):
                        continue
                
                # Skip non-text data types (unless it's a prioritized column)
                if col['data_type'] not in ('text', 'varchar', 'character varying', 'char'):
                    # Allow numeric types only if they match prioritized patterns
                    if not any(priority in col_name_lower for priority in prioritized_patterns):
                        continue
                
                # Add priority score for sorting
                priority_score = 0
                for pattern in prioritized_patterns:
                    if pattern in col_name_lower:
                        priority_score += 1
                
                col['priority_score'] = priority_score
                searchable.append(col)
            
            # Sort by priority score (highest first), then by column name
            searchable.sort(key=lambda x: (-x['priority_score'], x['column_name']))
            
            return searchable
        except Exception as e:
            logger.error(f"Error getting searchable columns: {e}")
            return []
    
    @tool("list_tables", "Lists all tables in the database with their schemas")
    def list_tables(self, schemas: Optional[List[str]] = None) -> Dict[str, Any]:
        """List tables in specified schemas (default: public)."""
        schema_filter = "AND table_schema = ANY(%s)" if schemas else ""
        params = (schemas,) if schemas else None
        
        sql = f"""
        SELECT 
            table_schema,
            table_name,
            table_type
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        {schema_filter if schemas else "AND table_schema = 'public'"}
        ORDER BY table_schema, table_name;
        """
        
        try:
            results = self._execute_query(sql, params)
            return {
                "tables": results,
                "count": len(results)
            }
        except Exception as e:
            return {"error": str(e), "tables": []}
    
    @tool("get_schema_info", "Get detailed schema information including columns, types, and constraints")
    def get_schema_info(self, table_names: Optional[List[str]] = None, schemas: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get detailed schema information for specified tables."""
        table_filter = "AND t.table_name = ANY(%s)" if table_names else ""
        schema_filter = "AND t.table_schema = ANY(%s)" if schemas else ""
        
        sql = f"""
        SELECT 
            t.table_schema,
            t.table_name,
            c.column_name,
            c.data_type,
            c.character_maximum_length,
            c.is_nullable,
            c.column_default,
            CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key,
            CASE WHEN fk.column_name IS NOT NULL THEN true ELSE false END as is_foreign_key
        FROM information_schema.tables t
        JOIN information_schema.columns c ON c.table_schema = t.table_schema 
            AND c.table_name = t.table_name
        LEFT JOIN (
            SELECT ku.table_schema, ku.table_name, ku.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage ku 
                ON tc.constraint_name = ku.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
        ) pk ON pk.table_schema = t.table_schema 
            AND pk.table_name = t.table_name 
            AND pk.column_name = c.column_name
        LEFT JOIN (
            SELECT ku.table_schema, ku.table_name, ku.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage ku 
                ON tc.constraint_name = ku.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
        ) fk ON fk.table_schema = t.table_schema 
            AND fk.table_name = t.table_name 
            AND fk.column_name = c.column_name
        WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
        {schema_filter if schemas else "AND t.table_schema = 'public'"}
        {table_filter if table_names else ""}
        ORDER BY t.table_schema, t.table_name, c.ordinal_position;
        """
        
        params = []
        if schemas and table_names:
            params = (schemas, table_names)
        elif schemas:
            params = (schemas,)
        elif table_names:
            params = (table_names,)
        
        try:
            results = self._execute_query(sql, params if params else None)
            
            # Group by table
            tables = {}
            for row in results:
                schema_table = f"{row['table_schema']}.{row['table_name']}"
                if schema_table not in tables:
                    tables[schema_table] = {
                        "schema": row['table_schema'],
                        "table": row['table_name'],
                        "columns": []
                    }
                tables[schema_table]["columns"].append({
                    "name": row['column_name'],
                    "type": row['data_type'],
                    "max_length": row['character_maximum_length'],
                    "nullable": row['is_nullable'] == 'YES',
                    "default": row['column_default'],
                    "is_primary_key": row['is_primary_key'],
                    "is_foreign_key": row['is_foreign_key']
                })
            
            return {
                "tables": list(tables.values()),
                "count": len(tables)
            }
        except Exception as e:
            return {"error": str(e), "tables": []}
    
    @tool("list_functions", "List all database functions, especially vector search and graph traversal functions")
    def list_functions(self, schemas: Optional[List[str]] = None) -> Dict[str, Any]:
        """List database functions."""
        schema_filter = "AND n.nspname = ANY(%s)" if schemas else "AND n.nspname = 'public'"
        
        sql = f"""
        SELECT 
            n.nspname as schema,
            p.proname as function_name,
            pg_get_function_arguments(p.oid) as arguments,
            pg_get_function_result(p.oid) as return_type,
            l.lanname as language
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        JOIN pg_language l ON p.prolang = l.oid
        WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
        {schema_filter}
        ORDER BY n.nspname, p.proname;
        """
        
        try:
            results = self._execute_query(sql, (schemas,) if schemas else None)
            return {
                "functions": results,
                "count": len(results)
            }
        except Exception as e:
            return {"error": str(e), "functions": []}
    
    @tool("get_table_comments", "Get table and column comments/descriptions")
    def get_table_comments(self, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get table and column comments."""
        table_filter = "AND c.relname = ANY(%s)" if table_names else ""
        
        sql = f"""
        SELECT 
            n.nspname as schema,
            c.relname as table_name,
            obj_description(c.oid, 'pg_class') as table_comment,
            a.attname as column_name,
            col_description(c.oid, a.attnum) as column_comment
        FROM pg_class c
        JOIN pg_namespace n ON c.relnamespace = n.oid
        LEFT JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped
        WHERE c.relkind = 'r'
        AND n.nspname = 'public'
        {table_filter}
        ORDER BY c.relname, a.attnum;
        """
        
        try:
            results = self._execute_query(sql, (table_names,) if table_names else None)
            
            # Group by table
            tables = {}
            for row in results:
                table_key = f"{row['schema']}.{row['table_name']}"
                if table_key not in tables:
                    tables[table_key] = {
                        "schema": row['schema'],
                        "table": row['table_name'],
                        "comment": row['table_comment'],
                        "columns": []
                    }
                if row['column_name']:
                    tables[table_key]["columns"].append({
                        "name": row['column_name'],
                        "comment": row['column_comment']
                    })
            
            return {
                "tables": list(tables.values()),
                "count": len(tables)
            }
        except Exception as e:
            return {"error": str(e), "tables": []}
    
    @tool("execute_sql", "Execute a SQL query and return results")
    def execute_sql(self, sql: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Execute SQL query. For SELECT queries, results are returned. For other queries, row count is returned."""
        # Add LIMIT if not present and it's a SELECT query
        if limit and "SELECT" in sql.upper() and "LIMIT" not in sql.upper():
            sql = f"{sql.rstrip(';')} LIMIT {limit}"
        
        # Check for destructive operations
        destructive_keywords = ['DROP', 'TRUNCATE', 'DELETE FROM', 'ALTER TABLE DROP']
        sql_upper = sql.upper()
        is_destructive = any(keyword in sql_upper for keyword in destructive_keywords)
        
        if is_destructive:
            return {
                "error": "Destructive operations require explicit user confirmation",
                "requires_confirmation": True,
                "sql": sql
            }
        
        conn = None
        try:
            conn = psycopg2.connect(self.connection_string)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql)
                
                # Check if it's a SELECT query
                if cur.description:
                    results = cur.fetchall()
                    return {
                        "success": True,
                        "rows": [dict(row) for row in results],
                        "row_count": len(results),
                        "query_type": "SELECT"
                    }
                else:
                    # For INSERT, UPDATE, DELETE
                    conn.commit()
                    return {
                        "success": True,
                        "rows_affected": cur.rowcount,
                        "query_type": "MODIFY"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql": sql
            }
        finally:
            if conn:
                conn.close()
    
    @tool("get_indexes", "Get index information for tables to understand query performance")
    def get_indexes(self, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get index information."""
        table_filter = "AND t.relname = ANY(%s)" if table_names else ""
        
        sql = f"""
        SELECT
            n.nspname as schema,
            t.relname as table_name,
            i.relname as index_name,
            pg_get_indexdef(i.oid) as index_definition,
            am.amname as index_type
        FROM pg_index idx
        JOIN pg_class i ON i.oid = idx.indexrelid
        JOIN pg_class t ON t.oid = idx.indrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        JOIN pg_am am ON i.relam = am.oid
        WHERE n.nspname = 'public'
        {table_filter}
        ORDER BY t.relname, i.relname;
        """
        
        try:
            results = self._execute_query(sql, (table_names,) if table_names else None)
            return {
                "indexes": results,
                "count": len(results)
            }
        except Exception as e:
            return {"error": str(e), "indexes": []}
    
    @tool("explore_column_values", "Explore unique values in columns to understand what data they contain. Useful for finding which columns contain specific keywords or values. Use this on text columns, not IDs or primary keys.")
    def explore_column_values(
        self, 
        table_name: str, 
        column_name: str,
        limit: Optional[int] = 50,
        search_pattern: Optional[str] = None,
        min_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get unique values from a column to help understand what data it contains.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column to explore (should be a text column, not an ID or primary key)
            limit: Maximum number of unique values to return (default: 50)
            search_pattern: Optional pattern to filter values (SQL LIKE pattern, e.g., '%lintel%')
            min_length: Optional minimum length of values to include
        
        Returns:
            Dictionary with unique values, counts, and statistics
        """
        # Sanitize inputs to prevent SQL injection
        # Strip existing quotes first, then properly escape and quote
        table_name = table_name.strip('"').replace('"', '""')
        column_name = column_name.strip('"').replace('"', '""')
        
        # Check if this is a searchable column (warn if not)
        searchable_cols = self._get_searchable_columns(table_name)
        col_info = next((c for c in searchable_cols if c['column_name'] == column_name), None)
        
        if not col_info:
            # Check if column exists and get its info
            check_sql = """
            SELECT 
                c.column_name,
                c.data_type,
                CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key
            FROM information_schema.columns c
            LEFT JOIN (
                SELECT ku.table_schema, ku.table_name, ku.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage ku 
                    ON tc.constraint_name = ku.constraint_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
            ) pk ON pk.table_schema = c.table_schema 
                AND pk.table_name = c.table_name 
                AND pk.column_name = c.column_name
            WHERE c.table_schema = 'public'
            AND c.table_name = %s
            AND c.column_name = %s
            """
            try:
                check_result = self._execute_query(check_sql, (table_name, column_name))
                if check_result:
                    col_check = check_result[0]
                    if col_check.get('is_primary_key') or col_check['data_type'] not in ('text', 'varchar', 'character varying', 'char'):
                        return {
                            "warning": f"Column '{column_name}' appears to be a primary key or non-text column. Consider using a text column like 'label', 'name', or 'description' instead.",
                            "column_type": col_check['data_type'],
                            "is_primary_key": col_check.get('is_primary_key', False),
                            "suggestion": "Use get_schema_info to find text columns, or use search_column_values to search across multiple columns."
                        }
            except:
                pass  # Continue with exploration anyway
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        if search_pattern:
            where_clauses.append(f'"{column_name}"::text LIKE %s')
            params.append(search_pattern)
        
        if min_length:
            where_clauses.append(f'LENGTH("{column_name}"::text) >= %s')
            params.append(min_length)
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Query to get unique values with counts
        sql = f"""
        SELECT 
            "{column_name}" as value,
            COUNT(*) as count,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
        FROM "{table_name}"
        {where_sql}
        GROUP BY "{column_name}"
        ORDER BY count DESC, "{column_name}" ASC
        LIMIT %s
        """
        
        params.append(limit)
        
        try:
            results = self._execute_query(sql, tuple(params) if params else None)
            
            # Get total distinct count
            count_sql = f"""
            SELECT COUNT(DISTINCT "{column_name}") as total_distinct
            FROM "{table_name}"
            {where_sql}
            """
            count_params = params[:-1] if len(params) > 1 else None
            count_result = self._execute_query(count_sql, tuple(count_params) if count_params else None)
            total_distinct = count_result[0]['total_distinct'] if count_result else 0
            
            # Get total rows
            total_sql = f'SELECT COUNT(*) as total FROM "{table_name}"'
            total_result = self._execute_query(total_sql, None)
            total_rows = total_result[0]['total'] if total_result else 0
            
            # Extract just the values for easier searching
            values = [row['value'] for row in results]
            
            return {
                "table": table_name,
                "column": column_name,
                "unique_values": results,
                "values_list": values,  # Simple list for easy searching
                "total_distinct": total_distinct,
                "total_rows": total_rows,
                "returned_count": len(results),
                "limit": limit
            }
        except Exception as e:
            logger.error(f"Error exploring column values: {e}")
            return {
                "error": str(e),
                "table": table_name,
                "column": column_name
            }
    
    @tool("search_column_values", "Search for specific text patterns across searchable columns in a table. Automatically filters out primary keys, IDs, and timestamps. Helps find which columns contain specific keywords.")
    def search_column_values(
        self,
        table_name: str,
        search_text: str,
        column_names: Optional[List[str]] = None,
        limit: Optional[int] = 20
    ) -> Dict[str, Any]:
        """
        Search for a text pattern across columns in a table to find which columns contain matching values.
        Automatically excludes primary keys, foreign keys, IDs, timestamps, and non-text columns.
        Prioritizes columns with names suggesting text content (name, label, description, etc.).
        
        Args:
            table_name: Name of the table to search
            search_text: Text pattern to search for (will be used as SQL LIKE pattern with % around it)
            column_names: Optional list of column names to search. If None, automatically selects searchable text columns.
            limit: Maximum number of matching rows to return per column
        
        Returns:
            Dictionary with search results per column
        """
        # Sanitize inputs
        # Strip existing quotes first, then properly escape and quote
        table_name = table_name.strip('"').replace('"', '""')
        search_pattern = f"%{search_text}%"
        
        conn = None
        try:
            conn = psycopg2.connect(self.connection_string)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # If column_names not provided, use smart filtering to get searchable columns
                if not column_names:
                    searchable_cols = self._get_searchable_columns(table_name)
                    column_names = [col['column_name'] for col in searchable_cols]
                    
                    if not column_names:
                        return {
                            "error": f"No searchable text columns found in table {table_name}. All columns appear to be IDs, keys, or non-text types.",
                            "table": table_name,
                            "search_text": search_text,
                            "suggestion": "Use get_schema_info to see all columns and manually specify column_names if needed."
                        }
                else:
                    # Validate that specified columns are searchable (warn if not)
                    searchable_cols = self._get_searchable_columns(table_name)
                    searchable_names = {col['column_name'] for col in searchable_cols}
                    invalid_cols = [c for c in column_names if c not in searchable_names]
                    
                    if invalid_cols:
                        logger.warning(f"Some specified columns may not be searchable: {invalid_cols}")
                
                if not column_names:
                    return {
                        "error": f"No searchable columns found in table {table_name}",
                        "table": table_name,
                        "search_text": search_text
                    }
                
                results = {}
                for col_name in column_names:
                    col_name_safe = col_name.replace('"', '""')
                    search_sql = f"""
                    SELECT 
                        "{col_name_safe}" as value,
                        COUNT(*) as match_count
                    FROM "{table_name}"
                    WHERE "{col_name_safe}"::text ILIKE %s
                    GROUP BY "{col_name_safe}"
                    ORDER BY match_count DESC
                    LIMIT %s
                    """
                    
                    cur.execute(search_sql, (search_pattern, limit))
                    matches = cur.fetchall()
                    
                    if matches:
                        results[col_name] = {
                            "matches": [dict(row) for row in matches],
                            "match_count": len(matches)
                        }
                
                # Get column metadata for context
                searchable_cols = self._get_searchable_columns(table_name)
                col_metadata = {col['column_name']: {
                    "data_type": col['data_type'],
                    "priority_score": col.get('priority_score', 0)
                } for col in searchable_cols if col['column_name'] in column_names}
                
                return {
                    "table": table_name,
                    "search_text": search_text,
                    "columns_searched": column_names,
                    "columns_metadata": col_metadata,
                    "results": results,
                    "columns_with_matches": list(results.keys()),
                    "note": "Only searchable text columns were searched (primary keys, IDs, and timestamps were excluded)"
                }
        except Exception as e:
            logger.error(f"Error searching column values: {e}")
            return {
                "error": str(e),
                "table": table_name,
                "search_text": search_text
            }
        finally:
            if conn:
                conn.close()
    
    @tool("get_logs", "Fetch recent database logs for debugging, error analysis, or monitoring. Returns log entries from PostgreSQL.")
    def get_logs(
        self,
        limit: Optional[int] = 50,
        level: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch recent database logs for debugging or monitoring.
        
        Args:
            limit: Maximum number of log entries to return (default: 50, max: 100)
            level: Filter by log level: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'FATAL', 'PANIC'
            search: Optional text to search for in log messages
        
        Returns:
            Dictionary with log entries and metadata
        """
        # Validate limit
        limit = min(max(1, limit or 50), 100)
        
        # Build query
        where_clauses = []
        params = []
        
        if level:
            level_upper = level.upper()
            if level_upper in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'FATAL', 'PANIC'):
                where_clauses.append("level = %s")
                params.append(level_upper)
        
        if search:
            where_clauses.append("message ILIKE %s")
            params.append(f"%{search}%")
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Query PostgreSQL logs from pg_stat_statements or pg_log
        # Note: This queries pg_stat_statements which shows query statistics
        # For actual log files, you'd need access to pg_log directory or use pg_read_file
        sql = f"""
        SELECT 
            query,
            calls,
            total_exec_time,
            mean_exec_time,
            max_exec_time,
            min_exec_time,
            stddev_exec_time,
            rows,
            100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
        FROM pg_stat_statements
        {where_sql}
        ORDER BY total_exec_time DESC
        LIMIT %s
        """
        
        params.append(limit)
        
        try:
            results = self._execute_query(sql, tuple(params) if params else None)
            
            # Also try to get recent errors from pg_stat_activity if available
            error_sql = """
            SELECT 
                pid,
                usename,
                application_name,
                client_addr,
                state,
                query_start,
                state_change,
                wait_event_type,
                wait_event,
                query
            FROM pg_stat_activity
            WHERE state != 'idle'
            ORDER BY query_start DESC
            LIMIT 10
            """
            
            try:
                active_queries = self._execute_query(error_sql, None)
            except:
                active_queries = []
            
            return {
                "query_statistics": results,
                "active_queries": active_queries,
                "count": len(results),
                "limit": limit,
                "note": "Query statistics from pg_stat_statements. For detailed error logs, check PostgreSQL log files directly."
            }
        except Exception as e:
            logger.error(f"Error fetching logs: {e}")
            # Fallback: try to get basic connection info
            try:
                fallback_sql = """
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity
                WHERE datname = current_database()
                """
                fallback_result = self._execute_query(fallback_sql, None)
                return {
                    "error": f"Could not fetch detailed logs: {str(e)}",
                    "connection_info": fallback_result[0] if fallback_result else {},
                    "note": "For detailed logs, ensure pg_stat_statements extension is enabled and check PostgreSQL log files."
                }
            except:
                return {
                    "error": str(e),
                    "note": "Could not fetch logs. Ensure pg_stat_statements extension is enabled: CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
                }
    
    @tool("execute_function", "Execute a database function and return its results. Use this to call functions like match_documents, keyword_search_chunks, graph traversal functions, etc.")
    def execute_function(
        self,
        function_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a database function with the given arguments.
        
        Args:
            function_name: Name of the function to execute (e.g., 'match_documents', 'keyword_search_chunks')
            arguments: Dictionary of argument names to values matching the function signature
        
        Returns:
            Dictionary with function results
        """
        # Build function call SQL
        # Extract argument values and build the function call
        arg_parts = []
        arg_values = []
        
        # Get function signature to validate arguments
        try:
            sig_sql = """
            SELECT 
                p.proname as function_name,
                pg_get_function_arguments(p.oid) as arguments,
                pg_get_function_result(p.oid) as return_type
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = 'public'
            AND p.proname = %s
            LIMIT 1
            """
            sig_result = self._execute_query(sig_sql, (function_name,))
            
            if not sig_result:
                return {
                    "error": f"Function '{function_name}' not found in public schema",
                    "suggestion": "Use list_functions() to see available functions"
                }
        except Exception as e:
            logger.warning(f"Could not validate function signature: {e}")
        
        # Build function call
        # Handle different argument types
        for arg_name, arg_value in arguments.items():
            if arg_value is None:
                arg_parts.append(f"{arg_name} => NULL")
            elif isinstance(arg_value, (list, tuple)):
                # Array arguments
                if len(arg_value) == 0:
                    arg_parts.append(f"{arg_name} => ARRAY[]::text[]")
                else:
                    # Check if it's a text array
                    if all(isinstance(x, str) for x in arg_value):
                        placeholders = ','.join(['%s'] * len(arg_value))
                        arg_parts.append(f"{arg_name} => ARRAY[{placeholders}]::text[]")
                        arg_values.extend(arg_value)
                    else:
                        # Numeric array
                        placeholders = ','.join(['%s'] * len(arg_value))
                        arg_parts.append(f"{arg_name} => ARRAY[{placeholders}]")
                        arg_values.extend(arg_value)
            elif isinstance(arg_value, bool):
                arg_parts.append(f"{arg_name} => %s::boolean")
                arg_values.append(arg_value)
            elif isinstance(arg_value, (int, float)):
                arg_parts.append(f"{arg_name} => %s")
                arg_values.append(arg_value)
            elif isinstance(arg_value, str):
                # Check if it's a vector string representation (JSON array)
                if arg_value.startswith('[') and arg_value.endswith(']'):
                    try:
                        # Try to parse as JSON array to validate
                        import json
                        parsed = json.loads(arg_value)
                        if isinstance(parsed, list) and len(parsed) > 0:
                            # It's a valid array - determine if it's a vector
                            # For now, assume it needs to be cast to vector
                            # The actual casting will depend on function signature
                            arg_parts.append(f"{arg_name} => %s::vector")
                            arg_values.append(arg_value)
                        else:
                            arg_parts.append(f"{arg_name} => %s")
                            arg_values.append(arg_value)
                    except:
                        arg_parts.append(f"{arg_name} => %s")
                        arg_values.append(arg_value)
                else:
                    arg_parts.append(f"{arg_name} => %s")
                    arg_values.append(arg_value)
            else:
                # JSON or other types
                arg_parts.append(f"{arg_name} => %s")
                arg_values.append(json.dumps(arg_value) if isinstance(arg_value, (dict, list)) else str(arg_value))
        
        # Build SQL
        args_str = ', '.join(arg_parts) if arg_parts else ''
        sql = f"SELECT * FROM {function_name}({args_str})"
        
        try:
            # Execute the function
            conn = None
            try:
                conn = psycopg2.connect(self.connection_string)
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    logger.debug(f"Executing function: {sql}")
                    logger.debug(f"Arguments: {arg_values}")
                    cur.execute(sql, tuple(arg_values) if arg_values else None)
                    
                    if cur.description:
                        results = cur.fetchall()
                        return {
                            "success": True,
                            "function": function_name,
                            "arguments": arguments,
                            "rows": [dict(row) for row in results],
                            "row_count": len(results)
                        }
                    else:
                        return {
                            "success": True,
                            "function": function_name,
                            "arguments": arguments,
                            "message": "Function executed successfully (no return value)"
                        }
            finally:
                if conn:
                    conn.close()
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "function": function_name,
                "arguments": arguments,
                "sql": sql
            }
    
    def get_all_tools(self) -> Dict[str, Any]:
        """Get all available tools."""
        tools = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, '_tool_name'):
                tools[attr._tool_name] = {
                    "name": attr._tool_name,
                    "description": attr._tool_description,
                    "function": attr
                }
        return tools

