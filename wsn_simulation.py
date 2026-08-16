# ============================================================
# ENERGY-EFFICIENT ROUTING IN WIRELESS SENSOR NETWORKS (WSN)
# ============================================================
#
# Optimization-Based Python Simulation
#
# Features:
# - Random sensor deployment
# - Limited battery energy
# - Multi-hop routing
# - Distance-based radio energy model
# - Residual-energy-aware next-hop selection
# - Node failure detection
# - FND / HND / LND metrics
# - Packet generation and delivery tracking
# - Packet Delivery Ratio
# - Network lifetime analysis
# - Residual energy analysis
# - Network topology visualization
#
# ============================================================

import random
import math
import matplotlib.pyplot as plt
import networkx as nx


# ============================================================
# 1. SIMULATION PARAMETERS
# ============================================================

NUM_NODES = 40
AREA_SIZE = 100
MAX_ROUNDS = 500

INITIAL_ENERGY = 3.0          # Joules per sensor
TRANSMISSION_RANGE = 40       # meters

BASE_STATION = (50, 120)

# Radio energy model
E_ELEC = 50e-9                # Energy consumed by electronics (J/bit)
E_AMP = 40e-12                # Amplifier energy coefficient
PACKET_SIZE = 4000            # bits

# Traffic probability
TRAFFIC_PROBABILITY = 0.7

# Distance threshold for radio model
D0 = 30

# Reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)


# ============================================================
# 2. SENSOR NODE CLASS
# ============================================================

class SensorNode:

    def __init__(self, node_id, x, y):

        self.id = node_id
        self.x = x
        self.y = y

        self.energy = INITIAL_ENERGY
        self.alive = True

    def distance(self, x2, y2):

        return math.sqrt(
            (self.x - x2) ** 2 +
            (self.y - y2) ** 2
        )


# ============================================================
# 3. CREATE SENSOR NODES
# ============================================================

nodes = []

for i in range(NUM_NODES):

    x = random.uniform(0, AREA_SIZE)
    y = random.uniform(0, AREA_SIZE)

    nodes.append(
        SensorNode(i, x, y)
    )


# ============================================================
# 4. ENERGY MODEL
# ============================================================

def transmission_energy(distance):
    """
    Calculate the energy required to transmit one packet.

    Short distance:
        E_TX = E_ELEC * k + E_AMP * k * d^2

    Long distance:
        E_TX = E_ELEC * k + E_AMP * k * d^4
    """

    if distance < D0:

        return (
            E_ELEC * PACKET_SIZE
            + E_AMP * PACKET_SIZE * (distance ** 2)
        )

    else:

        return (
            E_ELEC * PACKET_SIZE
            + E_AMP * PACKET_SIZE * (distance ** 4)
        )


def reception_energy():
    """
    Energy required by a sensor node to receive one packet.
    """

    return E_ELEC * PACKET_SIZE


# ============================================================
# 5. FIND VALID NEIGHBORS
# ============================================================

def get_neighbors(node):

    neighbors = []

    for other in nodes:

        if other.id == node.id:
            continue

        if not other.alive:
            continue

        distance = node.distance(
            other.x,
            other.y
        )

        if distance <= TRANSMISSION_RANGE:

            neighbors.append(other)

    return neighbors


# ============================================================
# 6. ENERGY-AWARE NEXT-HOP SELECTION
# ============================================================

def choose_best_next_hop(current_node, visited):
    """
    Select the best next-hop neighbor.

    The score considers:
    1. Energy required for the neighbor to reach
       the base station.
    2. Remaining battery energy of the neighbor.

    Lower score = better candidate.
    """

    neighbors = get_neighbors(current_node)

    # Remove nodes already visited to prevent routing loops
    valid_neighbors = [
        neighbor
        for neighbor in neighbors
        if neighbor.id not in visited
    ]

    if not valid_neighbors:
        return None

    best_neighbor = None
    best_score = float("inf")

    for neighbor in valid_neighbors:

        # Distance from neighbor to base station
        distance_to_sink = neighbor.distance(
            BASE_STATION[0],
            BASE_STATION[1]
        )

        # Estimated transmission energy from
        # neighbor to the base station
        sink_energy = transmission_energy(
            distance_to_sink
        )

        # Energy-aware routing score
        score = (
            sink_energy /
            (neighbor.energy + 0.0001)
        )

        if score < best_score:

            best_score = score
            best_neighbor = neighbor

    return best_neighbor


# ============================================================
# 7. PERFORMANCE METRICS
# ============================================================

alive_nodes_history = []
energy_history = []

packets_generated_history = []
packets_delivered_history = []
packet_delivery_ratio_history = []

# Cumulative counters
total_packets_generated = 0
total_packets_delivered = 0

# Network lifetime metrics
FND = None
HND = None
LND = None


# ============================================================
# 8. MAIN SIMULATION
# ============================================================

for round_num in range(MAX_ROUNDS):

    round_packets_generated = 0
    round_packets_delivered = 0

    # --------------------------------------------------------
    # EACH SENSOR GENERATES DATA
    # --------------------------------------------------------

    for node in nodes:

        if not node.alive:
            continue

        # Random traffic generation
        if random.random() >= TRAFFIC_PROBABILITY:
            continue

        round_packets_generated += 1
        total_packets_generated += 1

        current = node
        visited = set()

        packet_delivered = False

        # ----------------------------------------------------
        # ROUTE PACKET UNTIL IT REACHES THE BASE STATION
        # ----------------------------------------------------

        while True:

            # Prevent routing loops
            if current.id in visited:
                break

            visited.add(current.id)

            # =================================================
            # CHECK DIRECT COMMUNICATION WITH BASE STATION
            # =================================================

            distance_to_sink = current.distance(
                BASE_STATION[0],
                BASE_STATION[1]
            )

            if distance_to_sink <= TRANSMISSION_RANGE:

                energy_needed = transmission_energy(
                    distance_to_sink
                )

                # Energy constraint
                if current.energy >= energy_needed:

                    current.energy -= energy_needed

                    packet_delivered = True

                else:

                    current.energy = 0
                    current.alive = False

                break

            # =================================================
            # MULTI-HOP ROUTING
            # =================================================

            next_hop = choose_best_next_hop(
                current,
                visited
            )

            # No valid route
            if next_hop is None:
                break

            # -------------------------------------------------
            # TRANSMISSION ENERGY
            # -------------------------------------------------

            distance = current.distance(
                next_hop.x,
                next_hop.y
            )

            energy_needed = transmission_energy(
                distance
            )

            # Energy constraint
            if current.energy >= energy_needed:

                current.energy -= energy_needed

            else:

                current.energy = 0
                current.alive = False

                break

            # -------------------------------------------------
            # RECEPTION ENERGY
            # -------------------------------------------------

            receive_energy = reception_energy()

            if next_hop.energy >= receive_energy:

                next_hop.energy -= receive_energy

            else:

                next_hop.energy = 0
                next_hop.alive = False

                break

            # Move packet to next node
            current = next_hop

        # ----------------------------------------------------
        # RECORD SUCCESSFUL DELIVERY
        # ----------------------------------------------------

        if packet_delivered:

            total_packets_delivered += 1
            round_packets_delivered += 1

    # ========================================================
    # NETWORK STATUS
    # ========================================================

    alive_nodes = sum(
        1
        for node in nodes
        if node.alive
    )

    total_energy = sum(
        node.energy
        for node in nodes
    )

    # ========================================================
    # PACKET DELIVERY RATIO
    # ========================================================

    if round_packets_generated > 0:

        round_delivery_ratio = (
            round_packets_delivered /
            round_packets_generated
        ) * 100

    else:

        round_delivery_ratio = 0

    # ========================================================
    # STORE HISTORY
    # ========================================================

    alive_nodes_history.append(
        alive_nodes
    )

    energy_history.append(
        total_energy
    )

    packets_generated_history.append(
        round_packets_generated
    )

    packets_delivered_history.append(
        round_packets_delivered
    )

    packet_delivery_ratio_history.append(
        round_delivery_ratio
    )

    # ========================================================
    # NETWORK LIFETIME METRICS
    # ========================================================

    # First Node Death
    if FND is None and alive_nodes < NUM_NODES:

        FND = round_num

    # Half Node Death
    if HND is None and alive_nodes <= NUM_NODES / 2:

        HND = round_num

    # Last Node Death
    if alive_nodes == 0:

        LND = round_num

        print("\nAll sensor nodes are dead.")

        break

    # ========================================================
    # STATUS OUTPUT
    # ========================================================

    if round_num % 50 == 0:

        print(
            f"Round {round_num:3d} | "
            f"Alive Nodes: {alive_nodes:2d} | "
            f"Total Energy: {total_energy:.2f} J | "
            f"Packets Delivered: {total_packets_delivered}"
        )


# ============================================================
# 9. FINAL RESULTS
# ============================================================

print("\n" + "=" * 50)
print("SIMULATION RESULTS")
print("=" * 50)

print(f"Random Seed: {RANDOM_SEED}")
print(f"Initial Nodes: {NUM_NODES}")
print(f"Simulation Rounds: {len(alive_nodes_history)}")

print("\n--- Network Lifetime ---")

print(
    f"First Node Dead (FND): "
    f"{FND if FND is not None else 'Not reached'}"
)

print(
    f"Half Nodes Dead (HND): "
    f"{HND if HND is not None else 'Not reached'}"
)

print(
    f"Last Node Dead (LND): "
    f"{LND if LND is not None else 'Not reached'}"
)

print("\n--- Packet Statistics ---")

print(
    f"Packets Generated: "
    f"{total_packets_generated}"
)

print(
    f"Packets Delivered: "
    f"{total_packets_delivered}"
)

if total_packets_generated > 0:

    overall_delivery_ratio = (
        total_packets_delivered /
        total_packets_generated
    ) * 100

else:

    overall_delivery_ratio = 0

print(
    f"Packet Delivery Ratio: "
    f"{overall_delivery_ratio:.2f}%"
)

print("\n--- Energy Statistics ---")

print(
    f"Initial Total Energy: "
    f"{NUM_NODES * INITIAL_ENERGY:.2f} J"
)

print(
    f"Final Total Energy: "
    f"{energy_history[-1]:.2f} J"
)

print(
    f"Final Alive Nodes: "
    f"{alive_nodes_history[-1]}"
)

print("=" * 50)


# ============================================================
# 10. NETWORK TOPOLOGY VISUALIZATION
# ============================================================

G = nx.Graph()

# Add nodes
for node in nodes:

    node_color = (
        "green"
        if node.alive
        else "red"
    )

    G.add_node(
        node.id,
        pos=(node.x, node.y),
        color=node_color
    )

# Add communication links between alive nodes
for node in nodes:

    if not node.alive:
        continue

    neighbors = get_neighbors(node)

    for neighbor in neighbors:

        G.add_edge(
            node.id,
            neighbor.id
        )


pos = nx.get_node_attributes(
    G,
    "pos"
)

colors = [
    G.nodes[node_id]["color"]
    for node_id in G.nodes()
]


plt.figure(figsize=(10, 8))

nx.draw(
    G,
    pos,
    with_labels=True,
    node_color=colors,
    node_size=500,
    edge_color="gray",
    alpha=0.7
)

# Base station
plt.scatter(
    BASE_STATION[0],
    BASE_STATION[1],
    color="blue",
    s=500,
    marker="s",
    label="Base Station"
)

plt.title(
    "Wireless Sensor Network Topology"
)

plt.xlabel("X Position")
plt.ylabel("Y Position")

plt.legend()
plt.grid(True)



plt.savefig(
    "network_topology.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ============================================================
# 11. GRAPH 1 — ALIVE NODES VS ROUNDS
# ============================================================

plt.figure(figsize=(10, 5))

plt.plot(
    alive_nodes_history,
    linewidth=2
)

plt.xlabel("Simulation Round")
plt.ylabel("Alive Nodes")

plt.title(
    "Network Lifetime Analysis"
)

plt.grid(True)



plt.savefig(
    "network_lifetime.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ============================================================
# 12. GRAPH 2 — RESIDUAL ENERGY
# ============================================================

plt.figure(figsize=(10, 5))

plt.plot(
    energy_history,
    linewidth=2
)

plt.xlabel("Simulation Round")
plt.ylabel("Residual Energy (J)")

plt.title(
    "Residual Energy Analysis"
)

plt.grid(True)



plt.savefig(
    "residual_energy.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ============================================================
# 13. GRAPH 3 — CUMULATIVE PACKETS DELIVERED
# ============================================================

cumulative_packets = []

running_total = 0

for packets in packets_delivered_history:

    running_total += packets
    cumulative_packets.append(
        running_total
    )


plt.figure(figsize=(10, 5))

plt.plot(
    cumulative_packets,
    linewidth=2
)

plt.xlabel("Simulation Round")
plt.ylabel("Cumulative Packets Delivered")

plt.title(
    "Cumulative Packet Delivery"
)

plt.grid(True)



plt.savefig(
    "cumulative_packets_delivered.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ============================================================
# 14. GRAPH 4 — PACKET DELIVERY RATIO
# ============================================================

plt.figure(figsize=(10, 5))

plt.plot(
    packet_delivery_ratio_history,
    linewidth=2
)

plt.xlabel("Simulation Round")
plt.ylabel("Packet Delivery Ratio (%)")

plt.title(
    "Packet Delivery Ratio"
)

plt.grid(True)


plt.savefig(
    "packet_delivery_ratio.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ============================================================
# END OF SIMULATION
# ============================================================