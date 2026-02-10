import pg8000.native
import os
from dotenv import load_dotenv

# Load environment to get password
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, "..", ".env")
load_dotenv(env_path)

DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "postgres"
db_url = os.getenv("DATABASE_URL")
if db_url:
    try:
        # Try to parse password from URL: postgresql+pg8000://user:pass@host...
        DB_PASS = db_url.split(":")[2].split("@")[0]
    except:
        DB_PASS = "Admin007420"
else:
    DB_PASS = "Admin007420"

print(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT} as {DB_USER}...")

def init_db():
    try:
        # 1. Connect to default 'postgres' database to create the new db
        conn = pg8000.native.Connection(
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
            database="postgres"
        )
        
        # Check if database exists
        results = conn.run("SELECT 1 FROM pg_database WHERE datname='chatbot_db'")
        
        if not results:
            print("Creating database 'chatbot_db'...")
            conn.run("CREATE DATABASE chatbot_db")
            print("Database created!")
        else:
            print("Database 'chatbot_db' already exists.")
            
        conn.close()
        
        # 2. Connect to the new database to run schema
        print("Connecting to 'chatbot_db' to run schema...")
        conn = pg8000.native.Connection(
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
            database="chatbot_db"
        )
        
        # Read schema file using absolute path relative to this script
        schema_path = os.path.join(os.path.dirname(__file__), "../database/schema.sql")
        with open(schema_path, "r") as f:
            schema_sql = f.read()
            
        # Split by commands (simple split by semicolon might be fragile but works for this schema)
        # Actually, pg8000.native.Connection.run can generally handle multiple statements if supported, 
        # but let's try running them one by one or as a block if possible.
        # pg8000 natively might not support multi-statement in one call easily strictly.
        # safer to just run the whole block? Or use sqlalchemy? 
        # using pg8000 directly for simplicity.
        
        # Let's try running the whole schema content.
        # The schema has comments and multiple statements.
        
        # We'll split logic manually for specific crucial commands like extension
        try:
            print("Enabling pgvector extension...")
            conn.run("CREATE EXTENSION IF NOT EXISTS vector")
        except Exception as e:
            print(f"FAILED to enable pgvector extension: {e}")
            print("WARNING: You might need to install pgvector manually on Windows.")
            # We continue to try creating tables even if vector fails, though embedding column will fail text
            
        commands = schema_sql.split(";")
        for cmd in commands:
            if cmd.strip():
                try:
                    conn.run(cmd)
                except Exception as e:
                    if "already exists" in str(e):
                        continue
                    if "vector" in str(e) and "type" in str(e): 
                        print(f"Skipping vector column due to missing extension: {e}")
                    else:
                        print(f"Error running command: {cmd[:50]}... -> {e}")

        conn.close()
        print("Schema initialization complete.")
        
    except Exception as e:
        print(f"Database initialization failed: {e}")

if __name__ == "__main__":
    init_db()
