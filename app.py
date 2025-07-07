from flask import Flask, jsonify, request
import psycopg2
from flask_cors import CORS
import heapq
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    "host": "localhost",
    "dbname": "transportdb2",
    "user": "adhithi",
    "password": "adi123",
    "port": 5432,
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# Get current time for simulation
def get_current_time():
    return datetime.now().time()

# Get next available transport time
def get_next_available_time(current_time, frequency):
    next_time = datetime.combine(datetime.today(), current_time) + timedelta(minutes=frequency)
    return next_time.time()

# Dijkstra's algorithm for fastest route
def find_fastest_route(graph, start, end):
    distances = {node: float('infinity') for node in graph}
    distances[start] = 0
    pq = [(0, start, [start])]
    visited = set()

    while pq:
        current_distance, current_node, path = heapq.heappop(pq)
        
        if current_node == end:
            return path, current_distance
        
        if current_node in visited:
            continue
            
        visited.add(current_node)
        
        for neighbor, weight in graph[current_node].items():
            distance = current_distance + weight['time']
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(pq, (distance, neighbor, path + [neighbor]))
    
    return None, float('infinity')

# Modified Dijkstra's for cheapest route
def find_cheapest_route(graph, start, end):
    costs = {node: float('infinity') for node in graph}
    costs[start] = 0
    pq = [(0, start, [start])]
    visited = set()

    while pq:
        current_cost, current_node, path = heapq.heappop(pq)
        
        if current_node == end:
            return path, current_cost
        
        if current_node in visited:
            continue
            
        visited.add(current_node)
        
        for neighbor, weight in graph[current_node].items():
            cost = current_cost + weight['cost']
            if cost < costs[neighbor]:
                costs[neighbor] = cost
                heapq.heappush(pq, (cost, neighbor, path + [neighbor]))
    
    return None, float('infinity')

@app.route('/api/nodes')
def get_nodes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, type, latitude, longitude FROM nodes ORDER BY name")
    nodes = [{
        "id": id, 
        "name": name, 
        "type": type, 
        "coords": [float(latitude), float(longitude)]
    } for id, name, type, latitude, longitude in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(nodes)

@app.route('/api/edges')
def get_edges():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT from_node, to_node, mode, time, cost, distance
        FROM edges
    """)
    edges = [{
        "from": from_node,
        "to": to_node,
        "mode": mode,
        "time": time,
        "cost": cost,
        "distance": float(distance)
    } for from_node, to_node, mode, time, cost, distance in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(edges)

@app.route('/api/route/<source>/<destination>')
def get_route(source, destination):
    criteria = request.args.get('criteria', 'fastest')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Build graph from database
    cur.execute("""
        SELECT from_node, to_node, time, cost, mode, distance
        FROM edges
    """)
    
    graph = {}
    for from_node, to_node, time, cost, mode, distance in cur.fetchall():
        if from_node not in graph:
            graph[from_node] = {}
        if to_node not in graph:
            graph[to_node] = {}
            
        graph[from_node][to_node] = {
            'time': time,
            'cost': cost,
            'mode': mode,
            'distance': float(distance)
        }
        graph[to_node][from_node] = {
            'time': time,
            'cost': cost,
            'mode': mode,
            'distance': float(distance)
        }
    
    # Find route based on criteria
    if criteria == 'fastest':
        path, total_time = find_fastest_route(graph, source, destination)
    else:  # cheapest
        path, total_cost = find_cheapest_route(graph, source, destination)
    
    if not path:
        return jsonify({"error": "No route found"}), 404
    
    # Get route details
    route_details = []
    
    for i in range(len(path) - 1):
        current_node = path[i]
        next_node = path[i + 1]
        edge = graph[current_node][next_node]
        
        route_details.append({
            'from': current_node,
            'to': next_node,
            'mode': edge['mode'],
            'time': edge['time'],
            'cost': edge['cost'],
            'distance': edge['distance']
        })
    
    cur.close()
    conn.close()
    
    return jsonify({
        'routeNumber': 1,
        'details': route_details,
        'totalTime': total_time if criteria == 'fastest' else sum(d['time'] for d in route_details),
        'totalCost': total_cost if criteria == 'cheapest' else sum(d['cost'] for d in route_details),
        'totalDistance': sum(d['distance'] for d in route_details),
        'transfers': len([i for i in range(1, len(route_details)) if route_details[i]['mode'] != route_details[i-1]['mode']])
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000) 