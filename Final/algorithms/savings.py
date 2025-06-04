"""
savings.py — Heurística Clarke & Wright com capacidade, autonomia e múltiplos depósitos.

Suporta:
- vários veículos
- vários depósitos
- limite de capacidade e autonomia
- agrupamento automático de clientes por depósito mais próximo

Entrada JSON:
- nodes: lista com {id, x, y, demand (opcional), is_depot (bool)}
- vehicles: lista com {id, capacity, battery_kwh, start_node (opcional)}

Limitado a problemas sem janelas de tempo.
"""

import sys, json, math, itertools
from typing import List, Dict

CONSUMPTION = 0.2  # kWh/km

class Node:
    def __init__(self,d): self.__dict__.update(d)

def dist(a, b): return math.hypot(a.x - b.x, a.y - b.y)

def clarke_wright(nodes: List[Node], vehicles: List[Dict], depot_index: int):
    """Executa o algoritmo Clarke-Wright clássico para um único depósito e conjunto de clientes."""
    mat = [[dist(a,b) for b in nodes] for a in nodes]
    clients = [i for i in range(len(nodes)) if i != depot_index and not getattr(nodes[i], "is_depot", False)]

    routes = {i: [depot_index, i, depot_index] for i in clients}
    loads = {i: getattr(nodes[i], "demand", 0.0) for i in clients}

    savings = [(mat[i][depot_index] + mat[depot_index][j] - mat[i][j], i, j)
               for i, j in itertools.combinations(clients, 2)]
    savings.sort(reverse=True)

    capacity = vehicles[0]["capacity"]
    battery = vehicles[0]["battery_kwh"]

    def route_distance(r): return sum(mat[r[k]][r[k+1]] for k in range(len(r) - 1))
    def route_energy(r): return route_distance(r) * CONSUMPTION

    for _, i, j in savings:
        try:
            ri = next(r for r in routes.values() if r[1] == i or r[-2] == i)
            rj = next(r for r in routes.values() if r[1] == j or r[-2] == j)
        except StopIteration:
            continue
        if ri is rj: continue
        if ri[-2] == i and rj[1] == j:
            new_r = ri[:-1] + rj[1:]
            new_load = loads[ri[1]] + loads[rj[1]]
            if new_load > capacity or route_energy(new_r) > battery:
                continue
            routes[ri[1]] = new_r
            loads[ri[1]] = new_load
            routes.pop(rj[1])
            loads.pop(rj[1])

    return list(routes.values()), mat

def main():
    payload = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else json.loads(sys.stdin.read())
    nodes = [Node(n) for n in payload["nodes"]]
    vehicles = payload["vehicles"]

    depots = [i for i, n in enumerate(nodes) if getattr(n, "is_depot", False)]
    if not depots:
        print("Nenhum depósito encontrado.")
        return

    depot_vehicles: Dict[int, List[Dict]] = {d: [] for d in depots}
    for v in vehicles:
        d = v.get("start_node", depots[0])
        depot_vehicles[d].append(v)

    client_assignments: Dict[int, List[int]] = {d: [] for d in depots}
    for i, n in enumerate(nodes):
        if getattr(n, "is_depot", False) or "demand" not in n.__dict__:
            continue
        closest = min(depots, key=lambda d: dist(nodes[d], n))
        client_assignments[closest].append(i)

    found_any = False
    for depot_index in depots:
        local_nodes_idx = [depot_index] + client_assignments[depot_index]
        local_nodes = [nodes[i] for i in local_nodes_idx]
        idx_map = {i: k for k, i in enumerate(local_nodes_idx)}
        remap_nodes = [Node({**nodes[i].__dict__, "id": idx_map[i]}) for i in local_nodes_idx]
        remap_vehicles = depot_vehicles.get(depot_index, [])

        if not remap_vehicles or len(remap_nodes) <= 1:
            continue

        routes, mat = clarke_wright(remap_nodes, remap_vehicles, depot_index=0)
        for r in routes:
            route_ids = [local_nodes[i].id for i in r]
            d = sum(mat[r[k]][r[k+1]] for k in range(len(r)-1))
            print("Caminho encontrado:", route_ids)
            print("Distância total:", round(d, 2), "km")
            found_any = True

    if not found_any:
        print("Nenhuma rota viável encontrada para os depósitos ou veículos fornecidos.")

if __name__ == "__main__":
    main()
