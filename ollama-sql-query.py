import pyodbc
from tabulate import tabulate
from sqlalchemy import create_engine, inspect, URL, text
from llama_index.core import SQLDatabase
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.llms.ollama import Ollama
import time
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MSSQL connection settings
server = "ZELIS\\REEDUS"
database = "LibraryDB"
username = "sa"
password = "daryldixon"
driver = "ODBC Driver 17 for SQL Server"
schema = "dbo"

# SQLAlchemy connection URL
connection_url = URL.create(
    "mssql+pyodbc",
    username=username,
    password=password,
    host=server,
    database=database,
    query={"driver": driver}
)

# SQL result formatter
def format_sql_result(rows):
    """Format SQL result with tabulate for cleaner output"""
    if not rows:
        return "Sonuç bulunamadı"

    headers = [f"Col{i}" for i in range(len(rows[0]))]  # Default headers
    return tabulate(rows, headers=headers, tablefmt="grid")

# Execute raw SQL query
def execute_sql(engine, sql_query):
    """Execute SQL query and return results"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            rows = result.fetchall()
            return rows
    except Exception as e:
        logger.error(f"SQL execution error: {str(e)}")
        return None

# Ana uygulama bloğu
try:
    # Create engine
    engine = create_engine(connection_url)
    logger.info("Database connection established successfully")
    
    # Check available tables
    inspector = inspect(engine)
    available_tables = inspector.get_table_names(schema=schema)
    logger.info(f"Available tables: {available_tables}")

    # Check for required tables
    required_tables = {"books", "inventory"}
    missing_tables = required_tables - set(available_tables)
    if missing_tables:
        logger.warning(f"Missing tables - {missing_tables}")
        raise ValueError(f"Required tables missing: {missing_tables}")

    # SQLDatabase wrapper
    sql_database = SQLDatabase(
        engine,
        include_tables=list(required_tables),
        schema=schema
    )

    # System prompt
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

    # Configure Ollama
    llm = Ollama(
        model="gemma3n",
        request_timeout=120.0,
        system_prompt=sql_prompt,
        temperature=0.1
    )

    query_engine = NLSQLTableQueryEngine(
        sql_database=sql_database,
        tables=list(required_tables),
        llm=llm,
        synthesize_response=False
    )

    print("\nKütüphane Sistemi Hazır. Kitap ve envanter hakkında soru sorabilirsiniz.")
    print("Çıkmak için 'exit' yazın.\n")

    while True:
        try:
            user_query = input("\nSorgunuz: ").strip()
            if user_query.lower() in ['exit', 'quit']:
                break
            if not user_query:
                continue

            logger.info(f"Sorgu: {user_query}")
            start_time = time.time()
            
            # SQL üretimi
            response = query_engine.query(user_query)
            sql_query = response.metadata.get('sql_query', '')
            exec_time = time.time() - start_time

            if not sql_query:
                print("\nSQL oluşturulamadı")
                continue

            result = execute_sql(engine, sql_query)

            print(f"\nSonuç ({exec_time:.2f}s):")
            if result is not None:
                print(format_sql_result(result))
            else:
                print("Sorgu çalıştırılırken hata oluştu")

            print(f"\nOluşturulan SQL: {sql_query}")

        except Exception as e:
            logger.error(f"Sorgu hatası: {str(e)}")
            print(f"\nHata: Sorgu işlenemedi. Lütfen farklı şekilde ifade edin")

    print("Çıkılıyor...")

except Exception as e:
    logger.exception("Kritik başlatma hatası:")
    print(f"Sistem hatası: {str(e)}")
