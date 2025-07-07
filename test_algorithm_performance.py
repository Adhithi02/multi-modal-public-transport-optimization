import time
import psycopg2
from psycopg2.extras import RealDictCursor
import heapq
import math
import itertools
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import tracemalloc
import random

DB_CONFIG = {
    "host": "localhost",
    "dbname": "transportdb2",
    "user": "adhithi",
    "password": "adi123",
    "port": 5432,
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_all_nodes():
    """Fetches all node IDs from the database."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM nodes")
    nodes = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return nodes

def haversine_distance(coord1, coord2):
    """Calculate haversine distance between two coordinates"""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371  # Earth radius in km
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def build_graph():
    """Build graph from database"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get nodes with coordinates
    cur.execute("SELECT id, latitude, longitude FROM nodes")
    nodes = {row['id']: [row['latitude'], row['longitude']] for row in cur.fetchall()}
    
    # Get edges
    cur.execute("SELECT from_node, to_node, time, cost, mode, distance FROM edges")
    edges = cur.fetchall()
    
    # Build adjacency list
    graph = {}
    for edge in edges:
        from_node = edge['from_node']
        to_node = edge['to_node']
        
        if from_node not in graph:
            graph[from_node] = {}
        if to_node not in graph:
            graph[to_node] = {}
            
        graph[from_node][to_node] = {
            'time': edge['time'],
            'cost': edge['cost'],
            'mode': edge['mode'],
            'distance': float(edge['distance'])
        }
        graph[to_node][from_node] = {
            'time': edge['time'],
            'cost': edge['cost'],
            'mode': edge['mode'],
            'distance': float(edge['distance'])
        }
    
    cur.close()
    conn.close()
    return graph, nodes

def dijkstra_algorithm(graph, start, end, criteria='fastest', allowed_modes=None):
    """Dijkstra's algorithm implementation with mode filtering."""
    start_time = time.time()
    nodes_explored = 0
    
    distances = {node: float('infinity') for node in graph}
    distances[start] = 0
    pq = [(0, start, [start])]
    visited = set()

    while pq:
        current_distance, current_node, path = heapq.heappop(pq)
        nodes_explored += 1
        
        if current_node == end:
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            return path, current_distance, nodes_explored, execution_time
        
        if current_node in visited:
            continue
            
        visited.add(current_node)
        
        for neighbor, weight in graph[current_node].items():
            if allowed_modes and weight['mode'] not in allowed_modes:
                continue

            distance = current_distance + (weight['time'] if criteria == 'fastest' else weight['cost'])
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(pq, (distance, neighbor, path + [neighbor]))
    
    execution_time = (time.time() - start_time) * 1000
    return None, float('infinity'), nodes_explored, execution_time

def astar_algorithm(graph, nodes, start, end, criteria='fastest', allowed_modes=None):
    """A* algorithm implementation with mode filtering."""
    start_time = time.time()
    nodes_explored = 0
    
    # Priority queue for A*
    open_set = [(0, start, [start])]  # (f_score, node, path)
    came_from = {}
    g_score = {node: float('infinity') for node in graph}
    f_score = {node: float('infinity') for node in graph}
    
    g_score[start] = 0
    
    # Calculate heuristic for start node
    start_coords = nodes[start]
    end_coords = nodes[end]
    base_heuristic = haversine_distance(start_coords, end_coords)
    avg_speed = 30 if criteria == 'fastest' else 20  # km/h
    heuristic_multiplier = (60 / avg_speed) if criteria == 'fastest' else 1
    
    f_score[start] = base_heuristic * heuristic_multiplier
    
    while open_set:
        # Sort by f_score and get the best node
        open_set.sort(key=lambda x: x[0])
        current_f, current_node, path = open_set.pop(0)
        nodes_explored += 1
        
        if current_node == end:
            execution_time = (time.time() - start_time) * 1000
            return path, current_f, nodes_explored, execution_time
        
        for neighbor, weight in graph[current_node].items():
            if allowed_modes and weight['mode'] not in allowed_modes:
                continue

            weight_value = weight['time'] if criteria == 'fastest' else weight['cost']
            tentative_g = g_score[current_node] + weight_value
            
            if tentative_g < g_score[neighbor]:
                came_from[neighbor] = current_node
                g_score[neighbor] = tentative_g
                
                # Calculate heuristic for neighbor
                neighbor_coords = nodes[neighbor]
                heuristic = haversine_distance(neighbor_coords, end_coords) * heuristic_multiplier
                f_score[neighbor] = tentative_g + heuristic
                
                # Add to open set if not already there
                if not any(node[1] == neighbor for node in open_set):
                    open_set.append((f_score[neighbor], neighbor, path + [neighbor]))
    
    execution_time = (time.time() - start_time) * 1000
    return None, float('infinity'), nodes_explored, execution_time

def generate_report(results):
    """Generates a detailed report from the performance results."""
    df = pd.DataFrame(results)
    
    # --- Tabulated Data ---
    print("\n" + "="*100)
    print(" DETAILED ALGORITHM PERFORMANCE REPORT")
    print("="*100)
    print(df.to_string())
    
    # --- Overall Summary Statistics ---
    print("\n" + "="*100)
    print(" OVERALL SUMMARY STATISTICS")
    print("="*100)
    
    summary = df[[
        'dijkstra_time_ms', 'astar_time_ms', 
        'dijkstra_nodes', 'astar_nodes',
        'dijkstra_cost', 'astar_cost'
    ]].describe()
    print(summary)

    # --- Categorical Analysis ---
    print("\n" + "="*100)
    print(" CATEGORICAL PERFORMANCE ANALYSIS (by route length)")
    print("="*100)
    
    df['route_len_category'] = pd.cut(df['dijkstra_path_len'],
                                      bins=[0, 3, 6, np.inf],
                                      labels=['Short (<=3 nodes)', 'Medium (4-6 nodes)', 'Long (>6 nodes)'])
    
    categorical_summary = df.groupby('route_len_category')[[
        'dijkstra_time_ms', 'astar_time_ms', 'dijkstra_nodes', 'astar_nodes'
    ]].mean()
    
    print(categorical_summary)

    # --- Overall Analysis ---
    print("\n" + "="*100)
    print(" OVERALL PERFORMANCE ANALYSIS")
    print("="*100)
    
    avg_dijkstra_time = df['dijkstra_time_ms'].mean()
    avg_astar_time = df['astar_time_ms'].mean()
    avg_dijkstra_nodes = df['dijkstra_nodes'].mean()
    avg_astar_nodes = df['astar_nodes'].mean()

    print(f"Average Dijkstra Time: {avg_dijkstra_time:.4f} ms")
    print(f"Average A* Time: {avg_astar_time:.4f} ms")
    print(f"Average Dijkstra Nodes Explored: {avg_dijkstra_nodes:.2f}")
    print(f"Average A* Nodes Explored: {avg_astar_nodes:.2f}")

    if avg_astar_time < avg_dijkstra_time:
        if avg_dijkstra_time > 0:
            time_diff = ((avg_dijkstra_time - avg_astar_time) / avg_dijkstra_time) * 100
            print(f"\n=> A* is on average {time_diff:.2f}% faster than Dijkstra's.")
    else:
        if avg_astar_time > 0:
            time_diff = ((avg_astar_time - avg_dijkstra_time) / avg_astar_time) * 100
            print(f"\n=> Dijkstra's is on average {time_diff:.2f}% faster than A*.")

    if avg_astar_nodes < avg_dijkstra_nodes:
        if avg_dijkstra_nodes > 0:
            nodes_diff = ((avg_dijkstra_nodes - avg_astar_nodes) / avg_dijkstra_nodes) * 100
            print(f"=> A* explores on average {nodes_diff:.2f}% fewer nodes than Dijkstra's.")
    else:
        if avg_astar_nodes > 0:
            nodes_diff = ((avg_astar_nodes - avg_dijkstra_nodes) / avg_dijkstra_nodes) * 100
            print(f"=> Dijkstra's explores on average {nodes_diff:.2f}% fewer nodes than A*.")
        
    # Find best/worst cases for A*
    df['time_improvement'] = df['dijkstra_time_ms'] - df['astar_time_ms']
    df['nodes_improvement'] = df['dijkstra_nodes'] - df['astar_nodes']

    # Filter out cases where path was not found by one of the algorithms
    valid_df = df[df['dijkstra_path_len'] > 0]
    if not valid_df.empty:
        best_time_case = valid_df.loc[valid_df['time_improvement'].idxmax()]
        worst_time_case = valid_df.loc[valid_df['time_improvement'].idxmin()]
        best_nodes_case = valid_df.loc[valid_df['nodes_improvement'].idxmax()]
        worst_nodes_case = valid_df.loc[valid_df['nodes_improvement'].idxmin()]

        print("\n--- A* Performance Highlights ---")
        print(f"Best time improvement vs Dijkstra: Route {best_time_case['start_node']} -> {best_time_case['end_node']} ({best_time_case['time_improvement']:.2f} ms faster)")
        print(f"Worst time improvement vs Dijkstra: Route {worst_time_case['start_node']} -> {worst_time_case['end_node']} ({abs(worst_time_case['time_improvement']):.2f} ms slower)")
        print(f"Best nodes improvement vs Dijkstra: Route {best_nodes_case['start_node']} -> {best_nodes_case['end_node']} ({best_nodes_case['nodes_improvement']} fewer nodes)")
        print(f"Worst nodes improvement vs Dijkstra: Route {worst_nodes_case['start_node']} -> {worst_nodes_case['end_node']} ({abs(worst_nodes_case['nodes_improvement'])} more nodes)")
    print("="*100)


def plot_performance_by_category(df, category_name, filename):
    """Helper function to create a bar plot for a specific category of routes."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
    fig.suptitle(f'Algorithm Performance for {category_name} Routes', fontsize=16)

    bar_width = 0.35
    index = np.arange(len(df))
    
    route_labels = [f"{row['start_node']}\n->\n{row['end_node']}" for index, row in df.iterrows()]

    # Bar chart for Execution Time
    ax1.bar(index, df['dijkstra_time_ms'], bar_width, label='Dijkstra', color='skyblue')
    ax1.bar(index + bar_width, df['astar_time_ms'], bar_width, label='A*', color='lightcoral')
    ax1.set_ylabel('Execution Time (ms)')
    ax1.set_title('Execution Time Comparison')
    ax1.set_xticks(index + bar_width / 2)
    ax1.set_xticklabels(route_labels, rotation=45, ha="right", fontsize=8)
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Bar chart for Nodes Explored
    ax2.bar(index, df['dijkstra_nodes'], bar_width, label='Dijkstra', color='skyblue')
    ax2.bar(index + bar_width, df['astar_nodes'], bar_width, label='A*', color='lightcoral')
    ax2.set_ylabel('Nodes Explored')
    ax2.set_title('Nodes Explored Comparison')
    ax2.set_xticks(index + bar_width / 2)
    ax2.set_xticklabels(route_labels, rotation=45, ha="right", fontsize=8)
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    
    # Save the plot
    plt.savefig(filename)
    print(f"📊 Visualization saved to {filename}")
    plt.close(fig) # Close the figure to free memory


def generate_visualizations(results):
    """Generates and saves visualizations of the performance data."""
    df = pd.DataFrame(results)

    # Remove routes where no path was found by Dijkstra
    df = df[df['dijkstra_path_len'] > 0].copy()

    if df.empty:
        print("\nNo valid routes found to generate visualizations.")
        return

    # Categorize routes
    df['route_len_category'] = pd.cut(df['dijkstra_path_len'],
                                      bins=[0, 3, 6, np.inf],
                                      labels=['Short', 'Medium', 'Long'])

    # Generate a plot for each category
    for category in df['route_len_category'].unique():
        if pd.isna(category):
            continue
        print(f"\n--- Generating plot for {category} routes ---")
        category_df = df[df['route_len_category'] == category]
        plot_filename = f'algorithm_performance_{category.lower()}_routes.png'
        plot_performance_by_category(category_df, category, plot_filename)


def generate_heatmap(df, value_col, title, filename):
    """Generates and saves a heatmap for a given performance metric."""
    if df.empty:
        print(f"Skipping heatmap '{title}' due to empty data.")
        return
        
    heatmap_data = df.pivot_table(index='start_node', columns='end_node', values=value_col)
    
    plt.figure(figsize=(18, 15))
    sns.heatmap(heatmap_data, cmap="viridis", annot=False)
    plt.title(title, fontsize=16)
    plt.xlabel("Destination Node")
    plt.ylabel("Source Node")
    plt.tight_layout()
    plt.savefig(filename)
    print(f"📊 Heatmap saved to {filename}")
    plt.close()

def analyze_scaling(graph_builder):
    """Analyzes algorithm performance as the number of nodes increases."""
    print("\n" + "="*100)
    print(" SCALING ANALYSIS (TIME & MEMORY)")
    print("="*100)

    full_graph, full_nodes = graph_builder()
    all_node_ids = list(full_nodes.keys())
    
    results = []
    node_counts = sorted(list(range(5, len(all_node_ids) + 1, 5)))
    if node_counts[-1] != len(all_node_ids):
        node_counts.append(len(all_node_ids))

    for count in node_counts:
        print(f"Testing with a subgraph of {count} nodes...")
        
        # Create a subgraph
        sample_node_ids = random.sample(all_node_ids, count)
        subgraph = {node: full_graph[node] for node in sample_node_ids if node in full_graph}
        for node in subgraph:
             subgraph[node] = {neighbor: data for neighbor, data in subgraph[node].items() if neighbor in sample_node_ids}

        if count < 2:
            continue

        # Test on a sample of routes within the subgraph
        sample_routes = list(itertools.permutations(sample_node_ids, 2))
        if len(sample_routes) > 50: # Limit to 50 random routes to keep it fast
            sample_routes = random.sample(sample_routes, 50)

        dijkstra_times, astar_times = [], []
        dijkstra_mem, astar_mem = [], []

        for start_node, end_node in sample_routes:
            if start_node not in subgraph or end_node not in subgraph:
                continue

            # Measure Dijkstra
            tracemalloc.start()
            _, _, _, d_time = dijkstra_algorithm(subgraph, start_node, end_node)
            d_mem = tracemalloc.get_traced_memory()[1] / 1024 # in KB
            tracemalloc.stop()
            dijkstra_times.append(d_time)
            dijkstra_mem.append(d_mem)

            # Measure A*
            tracemalloc.start()
            _, _, _, a_time = astar_algorithm(subgraph, full_nodes, start_node, end_node)
            a_mem = tracemalloc.get_traced_memory()[1] / 1024 # in KB
            tracemalloc.stop()
            astar_times.append(a_time)
            astar_mem.append(a_mem)

        results.append({
            'nodes': count,
            'dijkstra_time_avg': np.mean(dijkstra_times),
            'astar_time_avg': np.mean(astar_times),
            'dijkstra_mem_avg_kb': np.mean(dijkstra_mem),
            'astar_mem_avg_kb': np.mean(astar_mem),
        })

    scaling_df = pd.DataFrame(results)
    print(scaling_df)

    # Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    fig.suptitle('Algorithm Scaling Analysis', fontsize=16)

    # Time vs. Nodes
    ax1.plot(scaling_df['nodes'], scaling_df['dijkstra_time_avg'], 'o-', label='Dijkstra', color='skyblue')
    ax1.plot(scaling_df['nodes'], scaling_df['astar_time_avg'], 'o-', label='A*', color='lightcoral')
    ax1.set_xlabel('Number of Nodes in Graph')
    ax1.set_ylabel('Average Execution Time (ms)')
    ax1.set_title('Execution Time vs. Graph Size')
    ax1.legend()
    ax1.grid(True)

    # Memory vs. Nodes
    ax2.plot(scaling_df['nodes'], scaling_df['dijkstra_mem_avg_kb'], 'o-', label='Dijkstra', color='skyblue')
    ax2.plot(scaling_df['nodes'], scaling_df['astar_mem_avg_kb'], 'o-', label='A*', color='lightcoral')
    ax2.set_xlabel('Number of Nodes in Graph')
    ax2.set_ylabel('Average Memory Usage (KB)')
    ax2.set_title('Memory Usage vs. Graph Size')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    filename = "algorithm_scaling_analysis.png"
    plt.savefig(filename)
    print(f"\n📊 Scaling analysis plot saved to {filename}")
    plt.close()


def test_algorithm_performance():
    """Test and compare algorithm performance for all routes."""
    print("=" * 100)
    print(" COMPREHENSIVE ALGORITHM PERFORMANCE ANALYSIS")
    print("=" * 100)
    
    # Build graph and get all nodes
    graph, nodes_coords = build_graph()
    all_node_ids = list(nodes_coords.keys())
    
    # --- 1. Full Analysis (All Modes) ---
    print("\n--- Running Full Analysis (All Modes Allowed) ---")
    test_routes = list(itertools.permutations(all_node_ids, 2))
    results = []
    
    for i, (start_node, end_node) in enumerate(test_routes):
        # Test Dijkstra's
        d_path, d_cost, d_nodes, d_time = dijkstra_algorithm(graph, start_node, end_node, 'fastest')
        # Test A*
        a_path, a_cost, a_nodes, a_time = astar_algorithm(graph, nodes_coords, start_node, end_node, 'fastest')
        
        results.append({
            'route_index': i, 'start_node': start_node, 'end_node': end_node,
            'dijkstra_time_ms': d_time, 'astar_time_ms': a_time,
            'dijkstra_nodes': d_nodes, 'astar_nodes': a_nodes,
            'dijkstra_cost': d_cost, 'astar_cost': a_cost,
            'dijkstra_path_len': len(d_path) if d_path else 0,
            'astar_path_len': len(a_path) if a_path else 0,
        })

    results_df = pd.DataFrame(results)
    valid_results_df = results_df[results_df['dijkstra_path_len'] > 0].copy()

    generate_report(valid_results_df)
    generate_visualizations(valid_results_df)
    
    # --- 2. Generate Heatmaps ---
    print("\n" + "="*100)
    print(" GENERATING HEATMAPS")
    print("="*100)
    valid_results_df['time_diff'] = valid_results_df['dijkstra_time_ms'] - valid_results_df['astar_time_ms']
    generate_heatmap(valid_results_df, 'astar_time_ms', 'A* Execution Time (ms)', 'heatmap_astar_time.png')
    generate_heatmap(valid_results_df, 'dijkstra_time_ms', 'Dijkstra Execution Time (ms)', 'heatmap_dijkstra_time.png')
    generate_heatmap(valid_results_df, 'time_diff', 'A* vs Dijkstra Time Improvement (ms)', 'heatmap_time_improvement.png')

    # --- 3. Mode-Specific Analysis ---
    print("\n" + "="*100)
    print(" MODE-SPECIFIC PERFORMANCE ANALYSIS")
    print("="*100)
    
    mode_results = []
    modes_to_test = [['bus'], ['metro']]
    sample_routes = random.sample(test_routes, min(len(test_routes), 50)) # Test on a sample

    for mode in modes_to_test:
        print(f"\n--- Testing with mode: {mode[0].upper()} ---")
        for start_node, end_node in sample_routes:
            # Test Dijkstra's
            d_path, d_cost, _, _ = dijkstra_algorithm(graph, start_node, end_node, 'fastest', allowed_modes=mode)
            # Test A*
            a_path, a_cost, _, _ = astar_algorithm(graph, nodes_coords, start_node, end_node, 'fastest', allowed_modes=mode)
            
            if d_path:
                mode_results.append({'route': f'{start_node[:5]}->{end_node[:5]}', 'algorithm': 'Dijkstra', 'cost': d_cost, 'mode': mode[0]})
            if a_path:
                mode_results.append({'route': f'{start_node[:5]}->{end_node[:5]}', 'algorithm': 'A*', 'cost': a_cost, 'mode': mode[0]})

    mode_df = pd.DataFrame(mode_results)
    if not mode_df.empty:
        plt.figure(figsize=(18, 10))
        sns.barplot(data=mode_df, x='route', y='cost', hue='mode', palette='muted')
        plt.title('Path Cost Comparison for Bus vs. Metro Routes', fontsize=16)
        plt.ylabel('Path Cost (Time)')
        plt.xlabel('Sample Routes')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig("algorithm_mode_comparison.png")
        print("\n📊 Mode comparison plot saved to algorithm_mode_comparison.png")
        plt.close()

    # --- 4. Scaling Analysis ---
    analyze_scaling(build_graph)

    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    test_algorithm_performance() 