import requests
import json

def test_api():
    base_url = "http://localhost:5000"
    
    try:
        # Test nodes endpoint
        print("Testing /api/nodes...")
        response = requests.get(f"{base_url}/api/nodes")
        if response.status_code == 200:
            nodes = response.json()
            print(f"✅ Nodes API working! Found {len(nodes)} nodes")
            print(f"First node: {nodes[0] if nodes else 'No nodes'}")
        else:
            print(f"❌ Nodes API failed with status {response.status_code}")
        
        # Test edges endpoint
        print("\nTesting /api/edges...")
        response = requests.get(f"{base_url}/api/edges")
        if response.status_code == 200:
            edges = response.json()
            print(f"✅ Edges API working! Found {len(edges)} edges")
            print(f"First edge: {edges[0] if edges else 'No edges'}")
        else:
            print(f"❌ Edges API failed with status {response.status_code}")
        
        # Test route endpoint
        print("\nTesting /api/route/majestic/indiranagar...")
        response = requests.get(f"{base_url}/api/route/majestic/indiranagar?criteria=fastest")
        if response.status_code == 200:
            route = response.json()
            print(f"✅ Route API working!")
            print(f"Route details: {route}")
        else:
            print(f"❌ Route API failed with status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server. Make sure it's running on port 5000.")
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    test_api() 