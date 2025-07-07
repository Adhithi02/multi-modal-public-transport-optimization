import psycopg2

# Connect to default postgres database to create new database
DB_CONFIG = {
    "host": "localhost",
    "user": "adhithi",
    "password": "adi123",
    "port": 5432,
}

def create_database():
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(**DB_CONFIG, database="postgres")
        conn.autocommit = True
        cur = conn.cursor()
        
        # Create new database
        cur.execute("CREATE DATABASE transportdb2")
        print("Database 'transportdb2' created successfully!")
        
        cur.close()
        conn.close()
        
    except psycopg2.errors.DuplicateDatabase:
        print("Database 'transportdb2' already exists!")
    except Exception as e:
        print(f"Error creating database: {e}")

if __name__ == "__main__":
    create_database() 