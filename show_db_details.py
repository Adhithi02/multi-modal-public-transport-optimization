import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": "localhost",
    "dbname": "transportdb2",
    "user": "adhithi",
    "password": "adi123",
    "port": 5432,
}

def show_database_details():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 80)
    print("COMPLETE DATABASE DETAILS - transportdb2")
    print("=" * 80)
    
    # Show table counts
    cur.execute("SELECT COUNT(*) as count FROM nodes")
    node_count = cur.fetchone()['count']
    
    cur.execute("SELECT COUNT(*) as count FROM edges")
    edge_count = cur.fetchone()['count']
    
    print(f"\n📊 TABLE COUNTS:")
    print(f"   Nodes: {node_count}")
    print(f"   Edges: {edge_count}")
    
    # Show all nodes
    print(f"\n📍 ALL NODES ({node_count} total):")
    print("-" * 80)
    cur.execute("SELECT id, name, type, latitude, longitude FROM nodes ORDER BY name")
    nodes = cur.fetchall()
    
    for node in nodes:
        print(f"   {node['id']:15} | {node['name']:20} | {node['type']:8} | [{node['latitude']:.4f}, {node['longitude']:.4f}]")
    
    # Show ALL edges (not just sample)
    print(f"\n🛤️  ALL EDGES ({edge_count} total):")
    print("-" * 80)
    cur.execute("""
        SELECT from_node, to_node, mode, time, cost, distance 
        FROM edges 
        ORDER BY from_node, to_node, mode
    """)
    edges = cur.fetchall()
    
    for edge in edges:
        print(f"   {edge['from_node']:15} → {edge['to_node']:15} | {edge['mode']:6} | {edge['time']:2}min | ₹{edge['cost']:2} | {edge['distance']:.1f}km")
    
    # Show transport mode distribution
    print(f"\n🚌 TRANSPORT MODE DISTRIBUTION:")
    print("-" * 80)
    cur.execute("""
        SELECT mode, COUNT(*) as count, 
               AVG(time) as avg_time, 
               AVG(cost) as avg_cost, 
               AVG(distance) as avg_distance,
               MIN(time) as min_time,
               MAX(time) as max_time,
               MIN(cost) as min_cost,
               MAX(cost) as max_cost
        FROM edges 
        GROUP BY mode
    """)
    modes = cur.fetchall()
    
    for mode in modes:
        print(f"   {mode['mode']:8} | {mode['count']:2} routes | {mode['avg_time']:.1f}min avg | ₹{mode['avg_cost']:.1f} avg | {mode['avg_distance']:.1f}km avg")
        print(f"           | Time range: {mode['min_time']}-{mode['max_time']}min | Cost range: ₹{mode['min_cost']}-{mode['max_cost']}")
    
    # Show node type distribution
    print(f"\n🏢 NODE TYPE DISTRIBUTION:")
    print("-" * 80)
    cur.execute("""
        SELECT type, COUNT(*) as count
        FROM nodes 
        GROUP BY type
    """)
    types = cur.fetchall()
    
    for type_info in types:
        print(f"   {type_info['type']:8} | {type_info['count']:2} stations")
    
    # Show ALL unique route combinations
    print(f"\n🗺️  ALL UNIQUE ROUTE COMBINATIONS:")
    print("-" * 80)
    cur.execute("""
        SELECT DISTINCT from_node, to_node, COUNT(*) as route_count
        FROM edges 
        GROUP BY from_node, to_node
        ORDER BY from_node, to_node
    """)
    unique_routes = cur.fetchall()
    
    for route in unique_routes:
        print(f"   {route['from_node']:15} → {route['to_node']:15} | {route['route_count']} transport options")
    
    # Show detailed route analysis for each unique connection
    print(f"\n🔍 DETAILED ROUTE ANALYSIS:")
    print("-" * 80)
    
    for route in unique_routes:
        from_node = route['from_node']
        to_node = route['to_node']
        
        cur.execute("""
            SELECT mode, time, cost, distance
            FROM edges 
            WHERE from_node = %s AND to_node = %s
            ORDER BY cost, time
        """, (from_node, to_node))
        
        routes = cur.fetchall()
        
        print(f"\n   {from_node} → {to_node} ({len(routes)} options):")
        for i, route_detail in enumerate(routes, 1):
            print(f"     {i}. {route_detail['mode']:6} | {route_detail['time']:2}min | ₹{route_detail['cost']:2} | {route_detail['distance']:.1f}km")
    
    # Show cost analysis
    print(f"\n💰 COST ANALYSIS:")
    print("-" * 80)
    cur.execute("""
        SELECT 
            MIN(cost) as min_cost,
            MAX(cost) as max_cost,
            AVG(cost) as avg_cost,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cost) as median_cost
        FROM edges
    """)
    cost_stats = cur.fetchone()
    
    print(f"   Minimum cost: ₹{cost_stats['min_cost']}")
    print(f"   Maximum cost: ₹{cost_stats['max_cost']}")
    print(f"   Average cost: ₹{cost_stats['avg_cost']:.1f}")
    print(f"   Median cost: ₹{cost_stats['median_cost']}")
    
    # Show time analysis
    print(f"\n⏰ TIME ANALYSIS:")
    print("-" * 80)
    cur.execute("""
        SELECT 
            MIN(time) as min_time,
            MAX(time) as min_time,
            AVG(time) as avg_time,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY time) as median_time
        FROM edges
    """)
    time_stats = cur.fetchone()
    
    print(f"   Minimum time: {time_stats['min_time']} minutes")
    print(f"   Maximum time: {time_stats['min_time']} minutes")
    print(f"   Average time: {time_stats['avg_time']:.1f} minutes")
    print(f"   Median time: {time_stats['median_time']} minutes")
    
    # Show distance analysis
    print(f"\n📏 DISTANCE ANALYSIS:")
    print("-" * 80)
    cur.execute("""
        SELECT 
            MIN(distance) as min_distance,
            MAX(distance) as max_distance,
            AVG(distance) as avg_distance,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY distance) as median_distance
        FROM edges
    """)
    distance_stats = cur.fetchone()
    
    print(f"   Minimum distance: {distance_stats['min_distance']:.1f} km")
    print(f"   Maximum distance: {distance_stats['max_distance']:.1f} km")
    print(f"   Average distance: {distance_stats['avg_distance']:.1f} km")
    print(f"   Median distance: {distance_stats['median_distance']:.1f} km")
    
    # Show fastest routes
    print(f"\n⚡ FASTEST ROUTES (Top 10):")
    print("-" * 80)
    cur.execute("""
        SELECT from_node, to_node, mode, time, cost, distance
        FROM edges 
        ORDER BY time ASC
        LIMIT 10
    """)
    fastest_routes = cur.fetchall()
    
    for i, route in enumerate(fastest_routes, 1):
        print(f"   {i:2}. {route['from_node']:15} → {route['to_node']:15} | {route['mode']:6} | {route['time']:2}min | ₹{route['cost']:2} | {route['distance']:.1f}km")
    
    # Show cheapest routes
    print(f"\n💸 CHEAPEST ROUTES (Top 10):")
    print("-" * 80)
    cur.execute("""
        SELECT from_node, to_node, mode, time, cost, distance
        FROM edges 
        ORDER BY cost ASC
        LIMIT 10
    """)
    cheapest_routes = cur.fetchall()
    
    for i, route in enumerate(cheapest_routes, 1):
        print(f"   {i:2}. {route['from_node']:15} → {route['to_node']:15} | {route['mode']:6} | {route['time']:2}min | ₹{route['cost']:2} | {route['distance']:.1f}km")
    
    # Show longest routes
    print(f"\n🛣️  LONGEST ROUTES (Top 10):")
    print("-" * 80)
    cur.execute("""
        SELECT from_node, to_node, mode, time, cost, distance
        FROM edges 
        ORDER BY distance DESC
        LIMIT 10
    """)
    longest_routes = cur.fetchall()
    
    for i, route in enumerate(longest_routes, 1):
        print(f"   {i:2}. {route['from_node']:15} → {route['to_node']:15} | {route['mode']:6} | {route['time']:2}min | ₹{route['cost']:2} | {route['distance']:.1f}km")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("Complete database details finished!")
    print("=" * 80)

if __name__ == "__main__":
    show_database_details() 