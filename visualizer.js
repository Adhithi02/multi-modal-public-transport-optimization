// Core variables
let map;
let currentTileLayer;
let routeLayer;
let vehicleMarker;
let isSimulating = false;
let simulationInterval;
let clickMarker;
let currentRoute;

// Define nodes (stations and stops) - will be loaded from API
let nodes = [];
let edges = [];

// Transport mode colors and icons
const transportModes = {
    metro: { 
        color: '#00cc7d', 
        icon: '🚇',
        name: 'Metro',
        transferColor: '#00ff9d'
    },
    bus: { 
        color: '#0066cc', 
        icon: '🚌',
        name: 'Bus',
        transferColor: '#00aaff'
    },
    walk: { 
        color: '#ffcc00', 
        icon: '🚶',
        name: 'Walk',
        transferColor: '#ffdd44'
    },
    transfer: {
        color: '#ff0000',
        icon: '🔄',
        name: 'Transfer',
        transferColor: '#ff0000'
    }
};

let markers = [];
let polylines = [];
let vehicleMarkers = [];

// Node coordinates - will be populated from API data
let nodeCoordinates = {};

// Performance tracking
let algorithmPerformance = {
    dijkstra: { nodesExplored: 0, time: 0 },
    astar: { nodesExplored: 0, time: 0 }
};

// Initialize application
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Initializing application...');
    await loadDataFromAPI();
    initializeMap();
    populateDropdowns();
    setupEventListeners();
    drawNetwork();
});

// Load data from API
async function loadDataFromAPI() {
    try {
        // Load nodes
        const nodesResponse = await fetch('http://localhost:5000/api/nodes');
        nodes = await nodesResponse.json();
        
        // Load edges
        const edgesResponse = await fetch('http://localhost:5000/api/edges');
        edges = await edgesResponse.json();
        
        // Populate nodeCoordinates for map clicks
        nodes.forEach(node => {
            nodeCoordinates[node.id] = node.coords;
        });
        
        console.log(`Loaded ${nodes.length} nodes and ${edges.length} edges from API`);
    } catch (error) {
        console.error('Error loading data from API:', error);
        alert('Failed to load data from API. Please make sure the Flask server is running.');
    }
}

// Initialize map
function initializeMap() {
    if (map) return;
    
    map = L.map('map', {
        center: [12.9716, 77.5946],
        zoom: 12,
        zoomControl: false
    });
    
    L.control.zoom({
        position: 'bottomright'
    }).addTo(map);
    
    currentTileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);

    // Add click handler for map
    map.on('click', handleMapClick);
}

// Handle map click
function handleMapClick(e) {
    const clickedLatLng = e.latlng;
    
    // Find nearest node
    let nearestNode = null;
    let minDistance = Infinity;
    
    for (const [nodeId, coords] of Object.entries(nodeCoordinates)) {
        const distance = map.distance(clickedLatLng, coords);
        if (distance < minDistance && distance < 500) { // 500m threshold
            minDistance = distance;
            nearestNode = nodeId;
        }
    }
    
    if (nearestNode) {
        // Update source/destination based on which is empty
        const sourceSelect = document.getElementById('source');
        const destSelect = document.getElementById('destination');
        
        if (!sourceSelect.value) {
            sourceSelect.value = nearestNode;
        } else if (!destSelect.value) {
            destSelect.value = nearestNode;
        }
        
        // Show click marker
        if (clickMarker) {
            map.removeLayer(clickMarker);
        }
        
        clickMarker = L.marker(clickedLatLng, {
            icon: L.divIcon({
                className: 'click-marker',
                html: `<div style="background-color: var(--primary-color); width: 12px; height: 12px; border-radius: 50%;"></div>`
            })
        }).addTo(map);
    }
}

// Update map theme
function updateMapTheme(isDark) {
    if (!map) return;
    
    const newTileLayer = L.tileLayer(
        isDark ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png' : 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 19
        }
    );
    
    if (currentTileLayer) {
        map.removeLayer(currentTileLayer);
    }
    
    currentTileLayer = newTileLayer.addTo(map);
}

// Populate dropdowns
function populateDropdowns() {
    const sourceSelect = document.getElementById('source');
    const destinationSelect = document.getElementById('destination');

    // Sort nodes by name for better organization
    const sortedNodes = [...nodes].sort((a, b) => a.name.localeCompare(b.name));
    
    sortedNodes.forEach(node => {
        const sourceOption = new Option(node.name, node.id);
        const destOption = new Option(node.name, node.id);
        sourceSelect.add(sourceOption);
        destinationSelect.add(destOption);
    });
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('visualize-btn').addEventListener('click', () => {
        const source = document.getElementById('source').value;
        const destination = document.getElementById('destination').value;
        const criteria = document.querySelector('input[name="criteria"]:checked').value;
        const algorithm = document.getElementById('algorithm') ? document.getElementById('algorithm').value : 'dijkstra';
        if (!source || !destination) {
            alert('Please select both source and destination');
            return;
        }
        if (source === destination) {
            alert('Source and destination cannot be the same');
            return;
        }
        let route;
        if (algorithm === 'astar') {
            route = findRouteAStar(source, destination, criteria);
        } else {
            route = findRoute(source, destination, criteria);
        }
        if (route) {
            visualizeRoute(route);
            updateRouteInfo(route);
        } else {
            alert('No route found');
        }
    });
    
    document.getElementById('reset-btn').addEventListener('click', () => {
        if (routeLayer) {
            map.removeLayer(routeLayer);
        }
        if (vehicleMarker) {
            map.removeLayer(vehicleMarker);
        }
        document.getElementById('route-info').style.display = 'none';
        map.setView([12.9716, 77.5946], 12);
    });
}

// Draw network
function drawNetwork() {
    // Clear existing markers and polylines
    markers.forEach(marker => map.removeLayer(marker));
    polylines.forEach(polyline => map.removeLayer(polyline));
    markers = [];
    polylines = [];

    // Draw nodes as transport icons (no edges)
    nodes.forEach(node => {
        // Create custom icon for each transport type
        const iconHtml = `
            <div style="
                background: ${transportModes[node.type].color};
                border: 3px solid #fff;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                color: #fff;
                font-weight: bold;
            ">
                ${transportModes[node.type].icon}
            </div>
        `;
        
        const customIcon = L.divIcon({
            html: iconHtml,
            className: 'transport-station-icon',
            iconSize: [30, 30],
            iconAnchor: [15, 15],
            popupAnchor: [0, -15]
        });
        
        const marker = L.marker(node.coords, { icon: customIcon }).addTo(map);
        
        // Enhanced tooltip with transport info
        marker.bindTooltip(`
            <div style="text-align: center; font-weight: bold;">
                <div style="font-size: 18px; margin-bottom: 5px;">${transportModes[node.type].icon}</div>
                <div style="color: ${transportModes[node.type].color}; font-size: 14px;">${node.name}</div>
                <div style="font-size: 12px; color: #888; margin-top: 3px;">${node.type.toUpperCase()} Station</div>
            </div>
        `, {
            permanent: false,
            direction: 'top',
            className: 'station-tooltip'
        });
        
        // Add click functionality to select stations
        marker.on('click', () => {
            const sourceSelect = document.getElementById('source');
            const destSelect = document.getElementById('destination');
            
            if (!sourceSelect.value) {
                sourceSelect.value = node.id;
                sourceSelect.dispatchEvent(new Event('change'));
            } else if (!destSelect.value) {
                destSelect.value = node.id;
                destSelect.dispatchEvent(new Event('change'));
            }
        });
        
        markers.push(marker);
    });
}

// Improved Haversine distance calculation
function haversineDistance(coord1, coord2) {
    const toRad = deg => deg * Math.PI / 180;
    const [lat1, lon1] = coord1;
    const [lat2, lon2] = coord2;
    const R = 6371; // Earth radius in km
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a = Math.sin(dLat/2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon/2) ** 2;
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

// Improved A* Algorithm with better heuristic and performance tracking
function findRouteAStar(source, destination, criteria) {
    const startTime = performance.now();
    let nodesExplored = 0;
    
    // Create adjacency list
    const graph = {};
    nodes.forEach(node => {
        graph[node.id] = [];
    });
    edges.forEach(edge => {
        graph[edge.from].push({
            to: edge.to,
            mode: edge.mode,
            time: edge.time,
            cost: edge.cost,
            distance: edge.distance
        });
        graph[edge.to].push({
            to: edge.from,
            mode: edge.mode,
            time: edge.time,
            cost: edge.cost,
            distance: edge.distance
        });
    });

    // Priority queue for A* (using array with sorting for simplicity)
    const openSet = [{ id: source, f: 0, g: 0 }];
    const cameFrom = {};
    const gScore = {};
    const fScore = {};
    
    // Initialize scores
    nodes.forEach(node => {
        gScore[node.id] = Infinity;
        fScore[node.id] = Infinity;
    });
    
    gScore[source] = 0;
    
    // Get destination coordinates for heuristic
    const destCoords = nodes.find(n => n.id === destination).coords;
    const sourceCoords = nodes.find(n => n.id === source).coords;
    
    // Improved heuristic: use actual distance as base, then scale by criteria
    const baseHeuristic = haversineDistance(sourceCoords, destCoords);
    const avgSpeed = criteria === 'fastest' ? 30 : 20; // km/h for time-based, cost-based scaling
    const heuristicMultiplier = criteria === 'fastest' ? (60 / avgSpeed) : 1; // Convert to minutes for time
    
    fScore[source] = baseHeuristic * heuristicMultiplier;
    
    while (openSet.length > 0) {
        // Sort by f-score and get the best node
        openSet.sort((a, b) => a.f - b.f);
        const current = openSet.shift();
        
        nodesExplored++;
        
        if (current.id === destination) {
            // Reconstruct path
            const path = [];
            let curr = destination;
            while (cameFrom[curr]) {
                path.unshift({ ...cameFrom[curr], to: curr });
                curr = cameFrom[curr].from;
            }
            
            // Calculate route details
            const totalTime = path.reduce((sum, edge) => sum + edge.time, 0);
            const totalCost = path.reduce((sum, edge) => sum + edge.cost, 0);
            const totalDistance = path.reduce((sum, edge) => sum + edge.distance, 0);
            const transfers = path.filter((edge, i, arr) => i > 0 && edge.mode !== arr[i-1].mode).length;
            
            const endTime = performance.now();
            algorithmPerformance.astar = {
                nodesExplored: nodesExplored,
                time: endTime - startTime
            };
            
            return {
                routeNumber: Math.floor(Math.random() * 10) + 1,
                details: path,
                totalTime,
                totalCost,
                totalDistance,
                transfers,
                algorithm: 'A* Search',
                performance: algorithmPerformance.astar
            };
        }
        
        for (const edge of graph[current.id]) {
            const neighbor = edge.to;
            const weight = criteria === 'fastest' ? edge.time : edge.cost;
            const tentativeG = gScore[current.id] + weight;
            
            if (tentativeG < gScore[neighbor]) {
                cameFrom[neighbor] = { from: current.id, ...edge };
                gScore[neighbor] = tentativeG;
                
                // Calculate heuristic for neighbor
                const neighborCoords = nodes.find(n => n.id === neighbor).coords;
                const heuristic = haversineDistance(neighborCoords, destCoords) * heuristicMultiplier;
                fScore[neighbor] = tentativeG + heuristic;
                
                // Add to open set if not already there
                if (!openSet.find(node => node.id === neighbor)) {
                    openSet.push({ id: neighbor, f: fScore[neighbor], g: tentativeG });
                }
            }
        }
    }
    
    const endTime = performance.now();
    algorithmPerformance.astar = {
        nodesExplored: nodesExplored,
        time: endTime - startTime
    };
    
    return null;
}

// Improved Dijkstra's Algorithm with performance tracking
function findRoute(source, destination, criteria) {
    const startTime = performance.now();
    let nodesExplored = 0;
    
    // Create adjacency list
    const graph = {};
    nodes.forEach(node => {
        graph[node.id] = [];
    });
    edges.forEach(edge => {
        graph[edge.from].push({
            to: edge.to,
            mode: edge.mode,
            time: edge.time,
            cost: edge.cost,
            distance: edge.distance
        });
        graph[edge.to].push({
            to: edge.from,
            mode: edge.mode,
            time: edge.time,
            cost: edge.cost,
            distance: edge.distance
        });
    });
    
    // Initialize distances and previous nodes
    const distances = {};
    const previous = {};
    const visited = new Set();
    
    nodes.forEach(node => {
        distances[node.id] = Infinity;
        previous[node.id] = null;
    });
    
    distances[source] = 0;
    
    while (true) {
        let current = null;
        let minDistance = Infinity;
        
        // Find unvisited node with minimum distance
        for (const nodeId in distances) {
            if (!visited.has(nodeId) && distances[nodeId] < minDistance) {
                minDistance = distances[nodeId];
                current = nodeId;
            }
        }
        
        if (current === null || current === destination) {
            break;
        }
        
        visited.add(current);
        nodesExplored++;
        
        for (const edge of graph[current] || []) {
            const neighbor = edge.to;
            const weight = criteria === 'fastest' ? edge.time : edge.cost;
            const distance = distances[current] + weight;
            
            if (distance < distances[neighbor]) {
                distances[neighbor] = distance;
                previous[neighbor] = { from: current, ...edge };
            }
        }
    }
    
    if (distances[destination] === Infinity) {
        const endTime = performance.now();
        algorithmPerformance.dijkstra = {
            nodesExplored: nodesExplored,
            time: endTime - startTime
        };
        return null;
    }
    
    // Reconstruct path
    const path = [];
    let current = destination;
    while (current !== source) {
        const edge = previous[current];
        if (!edge) break;
        path.unshift(edge);
        current = edge.from;
    }
    
    const totalTime = path.reduce((sum, edge) => sum + edge.time, 0);
    const totalCost = path.reduce((sum, edge) => sum + edge.cost, 0);
    const totalDistance = path.reduce((sum, edge) => sum + edge.distance, 0);
    const transfers = path.filter((edge, i, arr) => i > 0 && edge.mode !== arr[i-1].mode).length;
    
    const endTime = performance.now();
    algorithmPerformance.dijkstra = {
        nodesExplored: nodesExplored,
        time: endTime - startTime
    };
    
    return {
        routeNumber: Math.floor(Math.random() * 10) + 1,
        details: path,
        totalTime,
        totalCost,
        totalDistance,
        transfers,
        algorithm: 'Dijkstra\'s Algorithm',
        performance: algorithmPerformance.dijkstra
    };
}

function visualizeRoute(routeData) {
    // Clear existing route
    if (routeLayer) {
        map.removeLayer(routeLayer);
    }
    if (vehicleMarker) {
        map.removeLayer(vehicleMarker);
    }
    
    // Create route layer group
    routeLayer = L.layerGroup().addTo(map);
    
    // Draw route segments
    routeData.details.forEach((segment, index) => {
        const fromNode = nodes.find(n => n.id === segment.from);
        const toNode = nodes.find(n => n.id === segment.to);
        
        if (fromNode && toNode) {
            const isTransfer = index > 0 && segment.mode !== routeData.details[index - 1].mode;
            const color = isTransfer ? transportModes.transfer.color : transportModes[segment.mode].color;
            
            // Draw route line
            const polyline = L.polyline(
                [fromNode.coords, toNode.coords],
                {
                    color: color,
                    weight: 4,
                    opacity: 0.8,
                    dashArray: segment.mode === 'walk' ? '5, 10' : null
                }
            ).addTo(routeLayer);
            
            // Add transfer marker if needed
            if (isTransfer) {
                const transferMarker = L.circleMarker(fromNode.coords, {
                    radius: 8,
                    fillColor: transportModes.transfer.color,
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }).addTo(routeLayer);

                transferMarker.bindPopup(`
                    <div class="transfer-popup">
                        Transfer to ${transportModes[segment.mode].icon} ${segment.mode.toUpperCase()}
                    </div>
                `);
            }
        }
    });
    
    // Update route information
    updateRouteInfo(routeData);
    
    // Start vehicle simulation
    startSimulation(routeData);
}

function updateRouteInfo(routeData) {
    const infoDiv = document.getElementById('route-info');
    infoDiv.style.display = 'block';
    let html = `
        <div class="route-summary">
            <h3>Route ${routeData.routeNumber} - ${routeData.algorithm}</h3>
            <div class="summary-grid">
                <div class="summary-item">
                    <i class="fas fa-clock"></i>
                    <span>${routeData.totalTime} min</span>
                </div>
                <div class="summary-item">
                    <i class="fas fa-rupee-sign"></i>
                    <span>₹${routeData.totalCost}</span>
                </div>
                <div class="summary-item">
                    <i class="fas fa-exchange-alt"></i>
                    <span>${routeData.transfers} transfers</span>
                </div>
                <div class="summary-item">
                    <i class="fas fa-road"></i>
                    <span>${routeData.totalDistance.toFixed(1)} km</span>
                </div>
            </div>
        </div>
    `;
    
    // Add performance metrics
    if (routeData.performance) {
        html += `
            <div class="performance-metrics">
                <h4>Algorithm Performance</h4>
                <div class="performance-grid">
                    <div class="perf-item">
                        <span class="perf-label">Nodes Explored:</span>
                        <span class="perf-value">${routeData.performance.nodesExplored}</span>
                    </div>
                    <div class="perf-item">
                        <span class="perf-label">Execution Time:</span>
                        <span class="perf-value">${routeData.performance.time.toFixed(2)} ms</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Route segments with icons only
    html += `<div class="route-segments">`;
    routeData.details.forEach((segment, index) => {
        const isTransfer = index > 0 && segment.mode !== routeData.details[index - 1].mode;
        const fromNode = nodes.find(n => n.id === segment.from);
        const toNode = nodes.find(n => n.id === segment.to);
        html += `
            <div class="route-segment ${isTransfer ? 'transfer-segment' : ''}">
                <div class="segment-header">
                    <span class="mode-icon">${transportModes[segment.mode].icon}</span>
                    <strong>${fromNode.name} → ${toNode.name}</strong>
                    ${isTransfer ? '<span class="transfer-badge">🔄</span>' : ''}
                </div>
                <div class="segment-details">
                    <p><i class="fas fa-clock"></i> ${segment.time} min</p>
                    <p><i class="fas fa-road"></i> ${segment.distance.toFixed(1)} km</p>
                    ${segment.cost > 0 ? `<p><i class="fas fa-rupee-sign"></i> ₹${segment.cost}</p>` : ''}
                </div>
            </div>
        `;
    });
    html += `</div>`;

    // Enhanced algorithm comparison with proper formatting
    const source = document.getElementById('source').value;
    const destination = document.getElementById('destination').value;
    const criteria = document.querySelector('input[name="criteria"]:checked').value;
    
    // Run both algorithms for comparison
    const dijkstraRoute = findRoute(source, destination, criteria);
    const astarRoute = findRouteAStar(source, destination, criteria);
    
    function routeSignature(route) {
        return route.details.map(e => e.from + '-' + e.to + '-' + e.mode).join('|');
    }
    
    const sameRoute = dijkstraRoute && astarRoute && routeSignature(dijkstraRoute) === routeSignature(astarRoute);
    
    html += `
        <div class="algorithm-comparison">
            <h4>🔬 Algorithm Performance</h4>
            
            <div class="comparison-stats">
                <div class="stat-card dijkstra">
                    <div class="stat-header">
                        <span class="algorithm-name">Dijkstra's</span>
                        <span class="algorithm-icon">🎯</span>
                    </div>
                    <div class="stat-content">
                        <div class="stat-row">
                            <span class="stat-label">Nodes:</span>
                            <span class="stat-value">${dijkstraRoute ? dijkstraRoute.performance.nodesExplored : '-'}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Time:</span>
                            <span class="stat-value">${dijkstraRoute ? dijkstraRoute.performance.time.toFixed(2) + ' ms' : '-'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="stat-card astar">
                    <div class="stat-header">
                        <span class="algorithm-name">A* Search</span>
                        <span class="algorithm-icon">⭐</span>
                    </div>
                    <div class="stat-content">
                        <div class="stat-row">
                            <span class="stat-label">Nodes:</span>
                            <span class="stat-value">${astarRoute ? astarRoute.performance.nodesExplored : '-'}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Time:</span>
                            <span class="stat-value">${astarRoute ? astarRoute.performance.time.toFixed(2) + ' ms' : '-'}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="comparison-winner">
                <div class="winner-item">
                    <span class="winner-label">Efficiency:</span>
                    <span class="winner-value ${dijkstraRoute && astarRoute ? 
                        (astarRoute.performance.nodesExplored < dijkstraRoute.performance.nodesExplored ? 'winner' : 'loser') : ''}">
                        ${dijkstraRoute && astarRoute ? 
                            (astarRoute.performance.nodesExplored < dijkstraRoute.performance.nodesExplored ? 'A* Better' : 'Dijkstra Better') : '-'}
                    </span>
                </div>
                <div class="winner-item">
                    <span class="winner-label">Route Quality:</span>
                    <span class="winner-value ${sameRoute ? 'winner' : 'neutral'}">
                        ${sameRoute ? 'Identical Routes' : 'Different Routes'}
                    </span>
                </div>
            </div>
        </div>
    `;
    
    infoDiv.innerHTML = html;
}

function startSimulation(routeData) {
    if (simulationInterval) {
        clearInterval(simulationInterval);
    }
    
    let currentSegment = 0;
    let progress = 0;
    
    // Create vehicle icon based on current transport mode
    const currentMode = routeData.details[0].mode;
    const vehicleIconHtml = `
        <div style="
            background: ${transportModes[currentMode].color};
            border: 3px solid #fff;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.4);
            color: #fff;
            font-weight: bold;
            animation: pulse 1.5s infinite;
        ">
            ${transportModes[currentMode].icon}
        </div>
    `;
    
    const vehicleIcon = L.divIcon({
        html: vehicleIconHtml,
        className: 'vehicle-marker',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });
    
    const fromNode = nodes.find(n => n.id === routeData.details[0].from);
    vehicleMarker = L.marker(fromNode.coords, { icon: vehicleIcon }).addTo(map);
    
    simulationInterval = setInterval(() => {
        if (currentSegment >= routeData.details.length) {
            clearInterval(simulationInterval);
            return;
        }

        const segment = routeData.details[currentSegment];
        const fromNode = nodes.find(n => n.id === segment.from);
        const toNode = nodes.find(n => n.id === segment.to);
        
        progress += 0.02;
        if (progress >= 1) {
            progress = 0;
            currentSegment++;
            if (currentSegment < routeData.details.length) {
                const nextSegment = routeData.details[currentSegment];
                // Update vehicle icon for new transport mode
                const newVehicleIconHtml = `
                    <div style="
                        background: ${transportModes[nextSegment.mode].color};
                        border: 3px solid #fff;
                        border-radius: 50%;
                        width: 24px;
                        height: 24px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 14px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
                        color: #fff;
                        font-weight: bold;
                        animation: pulse 1.5s infinite;
                    ">
                        ${transportModes[nextSegment.mode].icon}
                    </div>
                `;
                
                const newVehicleIcon = L.divIcon({
                    html: newVehicleIconHtml,
                    className: 'vehicle-marker',
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                });
                
                vehicleMarker.setIcon(newVehicleIcon);
            }
            return;
        }
        
        // Calculate position along the route
        const lat = fromNode.coords[0] + (toNode.coords[0] - fromNode.coords[0]) * progress;
        const lng = fromNode.coords[1] + (toNode.coords[1] - fromNode.coords[1]) * progress;
        
        vehicleMarker.setLatLng([lat, lng]);
    }, 100);
}