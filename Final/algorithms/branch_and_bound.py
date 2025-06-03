
"""
branch_and_bound.py — solução exacta VRP pequena (≤ 10‑12 clientes)

Suporta:
  • capacidade do veículo
  • autonomia (bateria) aproximada (kWh = km * consumo)

Não suporta janelas de tempo (poderias acrescentar).

Estratégia:
  Busca em profundidade com poda usando bound = custo acumulado +
  MST dos nós restantes + retorno ao depósito.

Nota: desempenho explode exponencialmente; use apenas para instâncias pequenas.
"""

import json, sys, math, itertools

CONSUMPTION_KWH_PER_KM = 0.2

class Node:
    def __init__(self, d): self.__dict__.update(d)

def dist(a:Node,b:Node)->float:
    return math.hypot(a.x-b.x, a.y-b.y)

def mst_lower_bound(unvisited, mat):
    "Custo de uma MST mínima (Prim) como bound heurístico."
    if not unvisited: return 0.0
    visited = {next(iter(unvisited))}
    cost = 0.0
    while len(visited) < len(unvisited):
        edges = [(mat[i][j], j) for i in visited for j in unvisited if j not in visited]
        w, j = min(edges)
        visited.add(j)
        cost += w
    return cost

def exact_vrp(nodes, vehicle):
    n = len(nodes)
    depot = 0
    mat = [[dist(a,b) for b in nodes] for a in nodes]
    best_cost = math.inf
    best_path = []

    capacity = vehicle["capacity"]
    battery_kwh = vehicle["battery_kwh"]

    demands = [getattr(node, "demand", 0.0) for node in nodes]

    def dfs(path, cost_so_far, load, kwh_used, unvisited):
        nonlocal best_cost, best_path
        bound = cost_so_far + mst_lower_bound(unvisited, mat) + \
                (mat[path[-1]][depot] if path[-1] != depot else 0)
        if bound >= best_cost:
            return
        if not unvisited:
            total = cost_so_far + mat[path[-1]][depot]
            if total < best_cost:
                best_cost = total
                best_path = path + [depot]
            return
        for j in list(unvisited):
            d = mat[path[-1]][j]
            need_kwh = d * CONSUMPTION_KWH_PER_KM
            if load + demands[j] > capacity:
                continue
            if kwh_used + need_kwh > battery_kwh:
                continue
            unvisited.remove(j)
            dfs(path + [j],
                cost_so_far + d,
                load + demands[j],
                kwh_used + need_kwh,
                unvisited)
            unvisited.add(j)

    dfs([depot], 0.0, 0.0, 0.0, set(range(1, n)))
    return best_path, best_cost

def main():
    if len(sys.argv) > 1:
        payload = json.load(open(sys.argv[1], encoding="utf8"))
    else:
        payload = json.loads(sys.stdin.read())
    nodes = [Node(n) for n in payload["nodes"]]
    vehicle = payload["vehicles"][0]
    path, cost = exact_vrp(nodes, vehicle)
    print("Melhor rota:", path, "Distância:", cost)

if __name__ == "__main__":
    main()
