import psycopg2
from psycopg2.extras import RealDictCursor

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "dbname": "transportdb2",
    "user": "adhithi",
    "password": "adi123",
    "port": 5432,
}

# Nodes data from visualizer.js
nodes = [
    { 'id': 'majestic', 'name': 'Majestic', 'type': 'metro', 'coords': [12.9770, 77.5707] },
    { 'id': 'indiranagar', 'name': 'Indiranagar', 'type': 'metro', 'coords': [12.9784, 77.6408] },
    { 'id': 'whitefield', 'name': 'Whitefield', 'type': 'metro', 'coords': [12.9698, 77.7499] },
    { 'id': 'jayanagar', 'name': 'Jayanagar', 'type': 'bus', 'coords': [12.9279, 77.5831] },
    { 'id': 'hebbal', 'name': 'Hebbal', 'type': 'bus', 'coords': [13.0392, 77.5917] },
    { 'id': 'koramangala', 'name': 'Koramangala', 'type': 'bus', 'coords': [12.9279, 77.6271] },
    { 'id': 'silk_board', 'name': 'Silk Board', 'type': 'metro', 'coords': [12.9177, 77.6234] },
    { 'id': 'electronic_city', 'name': 'Electronic City', 'type': 'bus', 'coords': [12.8398, 77.6770] },
    { 'id': 'rajajinagar', 'name': 'Rajajinagar', 'type': 'bus', 'coords': [12.9915, 77.5517] },
    { 'id': 'hsr_layout', 'name': 'HSR Layout', 'type': 'bus', 'coords': [12.9114, 77.6447] },
    { 'id': 'yeshwanthpur', 'name': 'Yeshwanthpur', 'type': 'metro', 'coords': [13.0285, 77.5507] },
    { 'id': 'banashankari', 'name': 'Banashankari', 'type': 'bus', 'coords': [12.9408, 77.5651] },
    { 'id': 'kr_puram', 'name': 'KR Puram', 'type': 'metro', 'coords': [13.0085, 77.7017] },
    { 'id': 'basavanagudi', 'name': 'Basavanagudi', 'type': 'bus', 'coords': [12.9408, 77.5651] },
    { 'id': 'lavelle_road', 'name': 'Lavelle Road', 'type': 'bus', 'coords': [12.9716, 77.5946] },
    { 'id': 'ulsoor', 'name': 'Ulsoor', 'type': 'bus', 'coords': [12.9770, 77.6208] },
    { 'id': 'banerghatta_rd', 'name': 'Banerghatta Road', 'type': 'bus', 'coords': [12.8917, 77.6017] },
    { 'id': 'mg_road', 'name': 'M.G. Road', 'type': 'metro', 'coords': [12.9757, 77.6011] },
    { 'id': 'cox_town', 'name': 'Cox Town', 'type': 'metro', 'coords': [13.0085, 77.6217] },
    { 'id': 'trinity', 'name': 'Trinity Circle', 'type': 'bus', 'coords': [12.9757, 77.6111] }
]

# Edges data from visualizer.js
edges = [
    # Route 1: Majestic → Indiranagar
    { 'from': 'majestic', 'to': 'indiranagar', 'mode': 'metro', 'time': 10, 'cost': 50, 'distance': 3.0 },
    { 'from': 'majestic', 'to': 'indiranagar', 'mode': 'bus', 'time': 40, 'cost': 10, 'distance': 3.0 },
    { 'from': 'majestic', 'to': 'trinity', 'mode': 'bus', 'time': 8, 'cost': 40, 'distance': 2.5 },
    { 'from': 'majestic', 'to': 'trinity', 'mode': 'bus', 'time': 30, 'cost': 10, 'distance': 2.5 },
    { 'from': 'trinity', 'to': 'indiranagar', 'mode': 'metro', 'time': 10, 'cost': 40, 'distance': 3.0 },
    { 'from': 'trinity', 'to': 'indiranagar', 'mode': 'bus', 'time': 40, 'cost': 10, 'distance': 3.0 },
    
    # Route 2: Whitefield → Jayanagar
    { 'from': 'whitefield', 'to': 'majestic', 'mode': 'metro', 'time': 15, 'cost': 60, 'distance': 15.0 },
    { 'from': 'whitefield', 'to': 'majestic', 'mode': 'bus', 'time': 60, 'cost': 15, 'distance': 15.0 },
    { 'from': 'majestic', 'to': 'jayanagar', 'mode': 'bus', 'time': 10, 'cost': 60, 'distance': 5.0 },
    { 'from': 'majestic', 'to': 'jayanagar', 'mode': 'bus', 'time': 40, 'cost': 15, 'distance': 5.0 },
    
    # Route 3: Hebbal → Koramangala
    { 'from': 'hebbal', 'to': 'mg_road', 'mode': 'bus', 'time': 10, 'cost': 40, 'distance': 8.0 },
    { 'from': 'hebbal', 'to': 'mg_road', 'mode': 'bus', 'time': 40, 'cost': 10, 'distance': 8.0 },
    { 'from': 'mg_road', 'to': 'trinity', 'mode': 'metro', 'time': 5, 'cost': 40, 'distance': 1.0 },
    { 'from': 'mg_road', 'to': 'trinity', 'mode': 'bus', 'time': 20, 'cost': 10, 'distance': 1.0 },
    { 'from': 'trinity', 'to': 'koramangala', 'mode': 'bus', 'time': 8, 'cost': 20, 'distance': 3.0 },
    { 'from': 'trinity', 'to': 'koramangala', 'mode': 'bus', 'time': 30, 'cost': 5, 'distance': 3.0 },
    
    # Route 4: Silk Board → Electronic City
    { 'from': 'silk_board', 'to': 'trinity', 'mode': 'metro', 'time': 10, 'cost': 40, 'distance': 4.0 },
    { 'from': 'silk_board', 'to': 'trinity', 'mode': 'bus', 'time': 40, 'cost': 10, 'distance': 4.0 },
    { 'from': 'trinity', 'to': 'electronic_city', 'mode': 'bus', 'time': 10, 'cost': 50, 'distance': 10.0 },
    { 'from': 'trinity', 'to': 'electronic_city', 'mode': 'bus', 'time': 40, 'cost': 12, 'distance': 10.0 },
    
    # Route 5: Rajajinagar → HSR Layout
    { 'from': 'rajajinagar', 'to': 'majestic', 'mode': 'bus', 'time': 10, 'cost': 40, 'distance': 4.0 },
    { 'from': 'rajajinagar', 'to': 'majestic', 'mode': 'bus', 'time': 40, 'cost': 10, 'distance': 4.0 },
    { 'from': 'majestic', 'to': 'indiranagar', 'mode': 'metro', 'time': 10, 'cost': 40, 'distance': 3.0 },
    { 'from': 'majestic', 'to': 'indiranagar', 'mode': 'bus', 'time': 40, 'cost': 10, 'distance': 3.0 },
    { 'from': 'indiranagar', 'to': 'hsr_layout', 'mode': 'bus', 'time': 8, 'cost': 30, 'distance': 2.5 },
    { 'from': 'indiranagar', 'to': 'hsr_layout', 'mode': 'bus', 'time': 30, 'cost': 7, 'distance': 2.5 },
    
    # Route 6: Yeshwanthpur → Banashankari
    { 'from': 'yeshwanthpur', 'to': 'rajajinagar', 'mode': 'metro', 'time': 8, 'cost': 40, 'distance': 3.0 },
    { 'from': 'yeshwanthpur', 'to': 'rajajinagar', 'mode': 'bus', 'time': 30, 'cost': 10, 'distance': 3.0 },
    { 'from': 'rajajinagar', 'to': 'banashankari', 'mode': 'bus', 'time': 8, 'cost': 30, 'distance': 3.0 },
    { 'from': 'rajajinagar', 'to': 'banashankari', 'mode': 'bus', 'time': 30, 'cost': 7, 'distance': 3.0 },
    
    # Route 7: KR Puram → Basavanagudi
    { 'from': 'kr_puram', 'to': 'mg_road', 'mode': 'metro', 'time': 8, 'cost': 40, 'distance': 4.0 },
    { 'from': 'kr_puram', 'to': 'mg_road', 'mode': 'bus', 'time': 30, 'cost': 10, 'distance': 4.0 },
    { 'from': 'mg_road', 'to': 'basavanagudi', 'mode': 'bus', 'time': 7, 'cost': 20, 'distance': 2.0 },
    { 'from': 'mg_road', 'to': 'basavanagudi', 'mode': 'bus', 'time': 26, 'cost': 5, 'distance': 2.0 },
    
    # Route 8: Lavelle Road → Ulsoor
    { 'from': 'lavelle_road', 'to': 'ulsoor', 'mode': 'bus', 'time': 8, 'cost': 30, 'distance': 2.0 },
    { 'from': 'lavelle_road', 'to': 'ulsoor', 'mode': 'bus', 'time': 30, 'cost': 7, 'distance': 2.0 },
    
    # Route 9: Banerghatta Road → MG Road
    { 'from': 'banerghatta_rd', 'to': 'silk_board', 'mode': 'bus', 'time': 10, 'cost': 40, 'distance': 3.0 },
    { 'from': 'banerghatta_rd', 'to': 'silk_board', 'mode': 'bus', 'time': 40, 'cost': 10, 'distance': 3.0 },
    { 'from': 'silk_board', 'to': 'mg_road', 'mode': 'metro', 'time': 9, 'cost': 40, 'distance': 3.0 },
    { 'from': 'silk_board', 'to': 'mg_road', 'mode': 'bus', 'time': 36, 'cost': 10, 'distance': 3.0 },
    
    # Route 10: Cox Town → Whitefield
    { 'from': 'cox_town', 'to': 'majestic', 'mode': 'metro', 'time': 10, 'cost': 40, 'distance': 4.0 },
    { 'from': 'cox_town', 'to': 'majestic', 'mode': 'bus', 'time': 40, 'cost': 10, 'distance': 4.0 },
    { 'from': 'majestic', 'to': 'whitefield', 'mode': 'bus', 'time': 14, 'cost': 70, 'distance': 15.0 },
    { 'from': 'majestic', 'to': 'whitefield', 'mode': 'bus', 'time': 56, 'cost': 17, 'distance': 15.0 }
]

def create_tables():
    """Create the necessary tables if they don't exist"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Create nodes table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            type VARCHAR(20) NOT NULL,
            latitude DECIMAL(10, 7) NOT NULL,
            longitude DECIMAL(10, 7) NOT NULL
        )
    """)
    
    # Create edges table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            id SERIAL PRIMARY KEY,
            from_node VARCHAR(50) REFERENCES nodes(id),
            to_node VARCHAR(50) REFERENCES nodes(id),
            mode VARCHAR(20) NOT NULL,
            time INTEGER NOT NULL,
            cost INTEGER NOT NULL,
            distance DECIMAL(5, 2) NOT NULL
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("Tables created successfully!")

def seed_database():
    """Seed the database with data from visualizer.js"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Clear existing data
    cur.execute("DELETE FROM edges")
    cur.execute("DELETE FROM nodes")
    
    # Insert nodes
    for node in nodes:
        cur.execute("""
            INSERT INTO nodes (id, name, type, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s)
        """, (node['id'], node['name'], node['type'], node['coords'][0], node['coords'][1]))
    
    # Insert edges
    for edge in edges:
        cur.execute("""
            INSERT INTO edges (from_node, to_node, mode, time, cost, distance)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (edge['from'], edge['to'], edge['mode'], edge['time'], edge['cost'], edge['distance']))
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Seeded {len(nodes)} nodes and {len(edges)} edges successfully!")

def main():
    """Main function to seed the database"""
    print("Starting database seeding...")
    
    try:
        create_tables()
        seed_database()
        print("Database seeding completed successfully!")
        
        # Verify the data
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM nodes")
        node_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM edges")
        edge_count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        print(f"Verification: {node_count} nodes and {edge_count} edges in database")
        
    except Exception as e:
        print(f"Error seeding database: {e}")

if __name__ == "__main__":
    main() 