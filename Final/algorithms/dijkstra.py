"""
dijkstra.py — Caminho mais curto com restrições de energia para veículos elétricos (EV)

Funcionalidades:
- Considera autonomia (kWh)
- Considera consumo por km (configurável)
- Suporta estações de carregamento com potência
- Suporte opcional a matriz OSRM se definida via variável de ambiente

Entrada JSON:
- nodes: lista com {id, x, y, is_charging_station (bool), charger_power_kw (opcional)}
- vehicles: usa o primeiro veículo com 'battery_kwh'
- start_id e end_id (opcionais): IDs de início e fim da rota

Limitações:
- Não suporta janelas de tempo
- Apenas um caminho origem → destino
"""

import os, sys, json, math, heapq
from typing import List, Dict, Optional

try:
    import requests
except ImportError:
    requests = None

CONSUMPTION = 0.2  # kWh/km

class Node:
    def __init__(self, d):
        self.id = d["id"]
        self.x = d["x"]
        self.y = d["y"]
        self.is_cs = d.get("is_charging_station", False)
        self.charger_kw = d.get("charger_power_kw")

def euclidean(a: Node, b: Node) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)

def osrm_matrix(nodes: List[Node]) -> Optional[List[List[float]]]:
    url = os.getenv("OSRM_URL")
    if not url or not requests: return None
    coords = ";".join(f"{n.x},{n.y}" for n in nodes)
    try:
        r = requests.get(f"{url}/table/v1/driving/{coords}?annotations=distance", timeout=10)
        if r.status_code == 200:
            return r.json()["distances"]
    except Exception as e:
        print("OSRM error:", e)
    return None

def build_matrix(nodes: List[Node]) -> List[List[float]]:
    return [[euclidean(a, b) for b in nodes] for a in nodes]

def shortest_path(nodes: List[Node], start: int, end: int,
                  battery_kwh: float, cons_km: float = CONSUMPTION):
    n = len(nodes)
    dist = osrm_matrix(nodes) or build_matrix(nodes)
    graph = [[(j, dist[i][j]) for j in range(n) if j != i] for i in range(n)]

    # (custo acumulado, nó atual, energia restante)
    pq = [(0, start, battery_kwh)]
    best = {}
    parent = {}

    while pq:
        cost, u, soc = heapq.heappop(pq)
        key = (u, round(soc, 1))
        if key in best and best[key] <= cost:
            continue
        best[key] = cost

        if u == end:
            path = []
            while (u, soc) in parent:
                path.append(u)
                u, soc = parent[(u, soc)]
            path.append(start)
            return list(reversed(path)), cost

        for v, w in graph[u]:
            need = w * cons_km
            if need <= soc:  # pode avançar
                heapq.heappush(pq, (cost + w, v, soc - need))

            if nodes[u].is_cs and nodes[u].charger_kw:
                new_soc = battery_kwh
                if need <= new_soc:
                    heapq.heappush(pq, (cost + w, v, new_soc - need))

    return None, float("inf")

def main():
    if len(sys.argv) > 1:
        payload = json.load(open(sys.argv[1]))
    else:
        print("Ficheiro JSON não fornecido.")
        return

    nodes = [Node(n) for n in payload["nodes"]]
    vehicle = payload["vehicles"][0]
    start_id = payload.get("start_id", nodes[0].id)
    end_id = payload.get("end_id", nodes[-1].id)

    id_to_idx = {n.id: i for i, n in enumerate(nodes)}

    if start_id not in id_to_idx or end_id not in id_to_idx:
        print("ID de início ou fim inválido.")
        return

    path, cost = shortest_path(nodes, id_to_idx[start_id], id_to_idx[end_id], vehicle["battery_kwh"])

    if path:
        print("Caminho encontrado:", [nodes[i].id for i in path])
        print("Distância total:", round(cost, 2), "km")
        print("Energia estimada:", round(cost * CONSUMPTION, 2), "kWh")
    else:
        print("Rota inviável. Verifica autonomia, estações de recarga e conectividade.")

if __name__ == "__main__":
    main()

