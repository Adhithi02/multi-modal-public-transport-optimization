import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "dbname": "transportdb2",
    "user": "adhithi",
    "password": "adi123",
    "port": 5432,
}

def check_schema():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Check if tables exist
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print("Existing tables:", [table[0] for table in tables])
        
        # Check nodes table structure
        if ('nodes',) in tables:
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'nodes'
            """)
            columns = cur.fetchall()
            print("Nodes table columns:", columns)
        
        # Check edges table structure
        if ('edges',) in tables:
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'edges'
            """)
            columns = cur.fetchall()
            print("Edges table columns:", columns)
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema() 