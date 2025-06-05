"""
nearest_neighbor.py — Heurística do Vizinho Mais Próximo com 2‑opt opcional.

Funcionalidades:
- Capacidade do veículo (verificação da carga total)
- Autonomia com consumo energético (kWh/km)
- Otimização 2‑opt opcional com argumento --two_opt
- Simples, eficiente, útil para gerar rota inicial ou comparação

Entrada JSON:
- nodes: lista com {id, x, y, demand (opcional)}
- vehicles: usa o primeiro com {capacity, battery_kwh}

Parâmetros CLI:
--two_opt  → aplica melhoria 2‑opt à rota gerada
"""

import sys, json, math, argparse
CONSUMPTION = 0.2  # kWh por km

class Node:
    def __init__(self, d): self.__dict__.update(d)

def dist(a, b): return math.hypot(a.x - b.x, a.y - b.y)

def nearest_neighbor(nodes, vehicle):
    """Gera uma rota inicial por aproximação gananciosa considerando capacidade e bateria."""
    n = len(nodes)
    depot = 0
    mat = [[dist(a, b) for b in nodes] for a in nodes]
    unvisited = set(range(1, n))
    cap = vehicle["capacity"]
    battery = vehicle["battery_kwh"]
    route = [depot]
    load = 0
    energy = 0
    cur = depot

    while unvisited:
        nxt = min(unvisited, key=lambda j: mat[cur][j])
        next_demand = getattr(nodes[nxt], "demand", 0)
        next_energy = mat[cur][nxt] * CONSUMPTION

        if load + next_demand > cap:
            print(f"Capacidade excedida ao tentar visitar {nodes[nxt].id}.")
            break
        if energy + next_energy > battery:
            print(f"Autonomia excedida ao tentar visitar {nodes[nxt].id}.")
            break

        route.append(nxt)
        load += next_demand
        energy += next_energy
        cur = nxt
        unvisited.remove(nxt)

    route.append(depot)
    return route, mat

def two_opt(route, mat):
    """Aplica 2‑opt para melhorar rota localmente."""
    improved = True
    while improved:
        improved = False
        for i in range(1, len(route) - 2):
            for j in range(i + 1, len(route) - 1):
                if j - i == 1:
                    continue
                delta = (mat[route[i - 1]][route[j]] +
                         mat[route[i]][route[j + 1]] -
                         mat[route[i - 1]][route[i]] -
                         mat[route[j]][route[j + 1]])
                if delta < -1e-6:
                    route[i:j + 1] = reversed(route[i:j + 1])
                    improved = True
    return route

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", help="Ficheiro JSON com dados")
    parser.add_argument("--two_opt", action="store_true", help="Ativa 2‑opt para melhorar a rota")
    args = parser.parse_args()

    payload = json.load(open(args.file)) if args.file else json.loads(sys.stdin.read())
    nodes = [Node(n) for n in payload["nodes"]]
    vehicle = payload["vehicles"][0]
    route, mat = nearest_neighbor(nodes, vehicle)

    if args.two_opt:
        route = two_opt(route, mat)

    dist_total = sum(mat[route[k]][route[k + 1]] for k in range(len(route) - 1))
    energia = dist_total * CONSUMPTION
    print("Rota:", [nodes[i].id for i in route])
    print("Distância:", round(dist_total, 2), "km")
    print("Energia estimada:", round(energia, 2), "kWh")

if __name__ == "__main__":
    main()
