import pyodbc
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
database = "LibraryDB"  # Veritabanı ismi değişti
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

try:
    # Create engine
    engine = create_engine(connection_url)
    logger.info("Database connection established successfully")
    
    # Check available tables
    inspector = inspect(engine)
    available_tables = inspector.get_table_names(schema=schema)
    logger.info(f"Available tables: {available_tables}")

    # Check for required tables (kütüphane tabloları)
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

    # Yeni veritabanı yapısı için optimize edilmiş sistem istemi
    sql_prompt = (
        "You are a SQL expert for a library database. Strictly follow these rules:\n"
        "1. Use EXACT table/column names from schema:\n"
        "   - books: [book_id, title, author, isbn, publication_year, genre]\n"
        "   - inventory: [inventory_id, book_id, status, last_checkout, due_date]\n"
        "2. Always use explicit JOIN syntax with aliases:\n"
        "   - books.book_id = inventory.book_id\n"
        "3. Use parameterized WHERE clauses: WHERE title = 'The Hobbit' (EXACT title match)\n"
        "4. NEVER use LIKE unless specified\n"
        "5. Select ONLY necessary columns\n"
        "6. Handle NULL values with IS NULL/IS NOT NULL\n"
        "7. Use DISTINCT when fetching unique books\n"
        "8. Return raw SQL ONLY, no explanations\n\n"
        "User question: {user_query}\nSQL:"
    )

    # Configure Ollama LLM
    llm = Ollama(
        model="gemma3n",
        request_timeout=120.0,
        system_prompt=sql_prompt,
        temperature=0.1
    )

    # Create query engine with schema context
    query_engine = NLSQLTableQueryEngine(
        sql_database=sql_database,
        tables=list(required_tables),
        llm=llm,
        synthesize_response=False
    )

    print("\nKütüphane Sistemi Hazır. Kitap ve envanter hakkında soru sorabilirsiniz.")
    print("Çıkmak için 'exit' yazın.\n")

    def format_sql_result(result):
        """SQL sonuçlarını daha okunabilir hale getir"""
        if not result:
            return "Sonuç bulunamadı"
        
        if isinstance(result, list):
            # Tek sütunlu sonuçlar
            if len(result) > 0 and isinstance(result[0], tuple) and len(result[0]) == 1:
                return "\n".join([str(row[0]) for row in result])
            # Çok sütunlu sonuçlar
            return "\n".join(["\t".join(map(str, row)) for row in result])
        return str(result)

    while True:
        try:
            user_query = input("\nSorgunuz: ").strip()
            if user_query.lower() in ['exit', 'quit']:
                break
            if not user_query:
                continue

            logger.info(f"Sorgu: {user_query}")
            start_time = time.time()
            
            # Execute query
            response = query_engine.query(user_query)
            exec_time = time.time() - start_time

            # Extract and format results
            sql_query = response.metadata.get('sql_query', '')
            result = response.metadata.get('result', [])
            
            print(f"\nSonuç ({exec_time:.2f}s):")
            print(format_sql_result(result))
            
            if sql_query:
                print(f"\nOluşturulan SQL: {sql_query}")
            else:
                print("\nSQL oluşturulamadı")

        except Exception as e:
            logger.error(f"Sorgu hatası: {str(e)}")
            print(f"\nHata: Sorgu işlenemedi. Lütfen farklı şekilde ifade edin")

    print("Çıkılıyor...")

except Exception as e:
    logger.exception("Kritik başlatma hatası:")
    print(f"Sistem hatası: {str(e)}")