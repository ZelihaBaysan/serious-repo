"""
Library Database Natural Language SQL Query Tool

This script connects to a Microsoft SQL Server database, verifies required tables,
initializes a SQL-to-Natural Language Query Engine using LlamaIndex and Ollama LLM,
and allows users to query the database using natural language.

Modules Used:
- pyodbc: For ODBC-based MSSQL connection
- sqlalchemy: For engine and schema inspection
- llama_index: For natural language SQL generation
- logging: For application-level logging
- time: For measuring query execution time
- tabulate: For formatted display of query results

Example:
    $ python library_query_tool.py
"""

import pyodbc
from tabulate import tabulate
from sqlalchemy import create_engine, inspect, URL, text
from llama_index.core import SQLDatabase
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.llms.ollama import Ollama
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MSSQL connection configuration
server = "ZELIS\\REEDUS"
database = "LibraryDB"
username = "sa"
password = "daryldixon"
driver = "ODBC Driver 17 for SQL Server"
schema = "dbo"

# Construct SQLAlchemy connection URL
connection_url = URL.create(
    "mssql+pyodbc",
    username=username,
    password=password,
    host=server,
    database=database,
    query={"driver": driver}
)

def format_sql_result(rows):
    """
    Format the results of a SQL query using tabulate.

    Parameters:
    - rows (list[tuple]): List of tuples representing query result rows.

    Returns:
    - str: A table-formatted string of results or a message if no data found.

    Example:
        formatted = format_sql_result([(1, "Title"), (2, "Another")])
    """
    if not rows:
        return "Sonuç bulunamadı"

    headers = [f"Col{i}" for i in range(len(rows[0]))]
    return tabulate(rows, headers=headers, tablefmt="grid")

def execute_sql(engine, sql_query):
    """
    Execute a raw SQL query using SQLAlchemy engine.

    Parameters:
    - engine (sqlalchemy.Engine): SQLAlchemy engine instance.
    - sql_query (str): SQL statement to execute.

    Returns:
    - list[tuple] or None: Query results if successful, None on error.

    Example:
        rows = execute_sql(engine, "SELECT * FROM books")
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            return result.fetchall()
    except Exception as e:
        logger.error(f"SQL execution error: {str(e)}")
        return None

# Main application logic
try:
    # Create database engine
    engine = create_engine(connection_url)
    logger.info("Database connection established successfully")

    # Retrieve list of tables
    inspector = inspect(engine)
    available_tables = inspector.get_table_names(schema=schema)
    logger.info(f"Available tables: {available_tables}")

    # Ensure required tables exist
    required_tables = {"books", "inventory"}
    missing_tables = required_tables - set(available_tables)
    if missing_tables:
        logger.warning(f"Missing tables - {missing_tables}")
        raise ValueError(f"Required tables missing: {missing_tables}")

    # Create SQLDatabase wrapper
    sql_database = SQLDatabase(
        engine,
        include_tables=list(required_tables),
        schema=schema
    )

    # System prompt for SQL generation
    sql_prompt = (
        "You are a SQL expert for a library database. Strictly follow these rules:\n"
        "1. Use EXACT table/column names from schema:\n"
        "   - books: [book_id, title, author, isbn, publication_year, genre]\n"
        "   - inventory: [inventory_id, book_id, status, last_checkout, due_date]\n"
        "2. ALWAYS use explicit JOIN syntax:\n"
        "   - books.book_id = inventory.book_id\n"
        "3. Table names MUST be: 'books' and 'inventory' (NEVER modify these names)\n"
        "4. Select relevant columns from BOTH tables when joining\n"
        "5. Use exact string matches: WHERE author = 'George Orwell'\n"
        "6. Return raw SQL ONLY, no explanations\n\n"
        "User question: {user_query}\nSQL:"
    )

    # Initialize the Ollama LLM with system prompt
    llm = Ollama(
        model="gemma3n",
        request_timeout=120.0,
        system_prompt=sql_prompt,
        temperature=0.1
    )

    # Create query engine using LlamaIndex
    query_engine = NLSQLTableQueryEngine(
        sql_database=sql_database,
        tables=list(required_tables),
        llm=llm,
        synthesize_response=False
    )

    # CLI interface
    print("\nLibrary System Ready. Ask questions about books or inventory.")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            user_query = input("\nYour question: ").strip()
            if user_query.lower() in ['exit', 'quit']:
                break
            if not user_query:
                continue

            logger.info(f"User query: {user_query}")
            start_time = time.time()

            # Generate SQL query
            response = query_engine.query(user_query)
            sql_query = response.metadata.get('sql_query', '')
            exec_time = time.time() - start_time

            if not sql_query:
                print("\nFailed to generate SQL")
                continue

            result = execute_sql(engine, sql_query)

            print(f"\nResult ({exec_time:.2f}s):")
            if result is not None:
                print(format_sql_result(result))
            else:
                print("Error while executing query")

            print(f"\nGenerated SQL: {sql_query}")

        except Exception as e:
            logger.error(f"Query processing error: {str(e)}")
            print(f"\nError: Unable to process query. Please try rephrasing.")

    print("Exiting...")

except Exception as e:
    logger.exception("Critical startup error:")
    print(f"System error: {str(e)}")
