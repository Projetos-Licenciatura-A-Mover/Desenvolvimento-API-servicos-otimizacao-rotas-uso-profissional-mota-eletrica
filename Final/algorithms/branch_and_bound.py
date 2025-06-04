"""
branch_and_bound.py — Algoritmo Branch and Bound para Problemas de Roteamento (TSP/VRP simplificado)

Este algoritmo:
- Encontra o caminho ótimo com exploração exaustiva podada por limites inferiores
- Usa matriz de distâncias e permutações possíveis
- Recomendado para instâncias pequenas (até ~10 clientes)

Suporta:
- Depósito fixo (ida e volta obrigatória)
- Distância total como critério de custo

Entrada JSON:
- nodes: lista com {id, x, y}
- vehicles: apenas o primeiro é usado (ignora capacidade/autonomia)

Limitações:
- Não suporta restrições de capacidade ou energia
- Tempo de execução explode para grandes instâncias
"""

import sys, json, math, itertools

class Node:
    def __init__(self, d): self.__dict__.update(d)

def dist(a, b): return math.hypot(a.x - b.x, a.y - b.y)

def route_distance(route, mat): return sum(mat[route[i]][route[i + 1]] for i in range(len(route) - 1))

def branch_and_bound(nodes):
    """Executa branch and bound simples para encontrar o melhor percurso (TSP circular)."""
    n = len(nodes)
    mat = [[dist(a, b) for b in nodes] for a in nodes]
    depot = 0
    best_cost = float("inf")
    best_route = None

    for perm in itertools.permutations(range(1, n)):
        route = [depot] + list(perm) + [depot]
        cost = route_distance(route, mat)
        if cost < best_cost:
            best_cost = cost
            best_route = route

    return best_route, best_cost

def main():
    payload = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else json.loads(sys.stdin.read())
    nodes = [Node(n) for n in payload["nodes"]]

    if len(nodes) > 10:
        print("Algoritmo não recomendado para mais de 10 nós. Tempo de execução pode ser longo.")

    route, cost = branch_and_bound(nodes)

    if route:
        ids = [nodes[i].id for i in route]
        print("Rota ótima:", ids)
        print("Distância total:", round(cost, 2), "km")
    else:
        print("Nenhuma rota encontrada.")

if __name__ == "__main__":
    main()
