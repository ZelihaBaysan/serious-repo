---

# 📚 Library Natural Language SQL Query System

This project is a Python-based application that allows you to query a library database using natural language. It automatically translates your questions into SQL queries using **LlamaIndex** and **Ollama**, executes them on an MS SQL Server database, and returns results in a clean tabular format.

## 🚀 Features

* 💬 **Natural Language Querying** — Ask your questions in natural language (English or Turkish).
* 🤖 **LLM-Powered SQL Generation** — Automatically generates SQL queries with the Ollama `gemma3n` model.
* 🗃️ **MSSQL Database Integration** — Direct connection to SQL Server databases via SQLAlchemy and pyodbc.
* 📝 **SQL Query Display** — Shows you both the generated SQL and the resulting data.
* ⚠️ **Detailed Logging & Error Handling**

## 📢 Important Notes

* ✅ The AI performs **significantly better with English queries**. For more accurate and complex SQL generation, it is **recommended to ask questions in English**.
* ✅ You can create the **same database schema** used in this project by running the SQL queries inside the file [`create_database.txt`](./create_database.txt) on your own SQL Server.

## 📁 Project Structure

```
📦 project_root
 ┣ 📜 library_query_engine.py
 ┣ 📜 requirements.txt
 ┣ 📜 create_database.txt
 ┗ 📜 README.md
```

## 💻 Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Setup

Create a database named `LibraryDB` in your SQL Server instance and run the SQL queries in [`create_database.txt`](./create_database.txt) to create the required tables and seed data.

#### Required Tables:

##### Table: `books`

\| book\_id | title | author | isbn | publication\_year | genre |

##### Table: `inventory`

\| inventory\_id | book\_id | status | last\_checkout | due\_date |

### 3. Configure Database Connection

Edit the connection parameters in `library_query_engine.py` if needed:

```python
server = "ZELIS\\REEDUS"
database = "LibraryDB"
username = "sa"
password = "daryldixon"
driver = "ODBC Driver 17 for SQL Server"
```

## ▶️ Usage

```bash
python library_query_engine.py
```

### Example Queries:

* **English (Recommended):**

  * `List books written by George Orwell.`
  * `Show available inventory of Science Fiction books.`
* **Turkish (Supported but less optimal):**

  * `George Orwell'in kitaplarını göster.`

To exit, type `exit` or `quit`.

## 📦 Major Python Packages Used

| Package     | Purpose                        |
| ----------- | ------------------------------ |
| llama-index | LLM-based SQL query generation |
| ollama      | Ollama API integration         |
| sqlalchemy  | Database connection & ORM      |
| pyodbc      | MSSQL ODBC connectivity        |
| tabulate    | Beautiful CLI table outputs    |
| logging     | Robust logging system          |

For the full dependency list, see [`requirements.txt`](./requirements.txt).

## 📝 Example Output

```plaintext
Your Query: List books published in 2020
Result (1.18s):
+--------+----------------------+-----------------+-----------------+-------------------+------------------+
| Col0   | Col1                 | Col2            | Col3            | Col4              | Col5             |
+--------+----------------------+-----------------+-----------------+-------------------+------------------+
| 7      | Example Book Title   | Example Author  | 9781234567890   | 2020              | Fiction          |
+--------+----------------------+-----------------+-----------------+-------------------+------------------+

Generated SQL:
SELECT ...
```

## ✅ Requirements

* Python 3.9+
* SQL Server with ODBC Driver 17 installed
* Ollama installed and the `gemma3n` model available locally or via Ollama API
* Optional: English queries for better performance
