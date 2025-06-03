
"""
dijkstra.py  —  Caminho mais curto para veículos eléctricos (EV) com possível recarga

Entrada obrigatória
-------------------
nodes : list[dict] com pelo menos {id,x,y}
vehicles : list[dict] – o primeiro veículo fornece autonomia ‘battery_kwh’
start_id, end_id : int  (opcional – usa primeiro depósito se ausentes)

Opcional
--------
is_charging_station, charger_power_kw
energy_matrix : matriz kWh i→j
travel_time_matrix : matriz s i→j
OSRM_URL : var de ambiente para distâncias reais

Bibliotecas externas usadas
---------------------------
networkx : cálculo de paths
requests : chamadas OSRM (opcionais)

Se faltar networkx o script cai para implementação própria de Dijkstra.
"""

import os, sys, json, math, itertools, heapq
from typing import List, Dict, Any, Tuple, Optional

try:
    import networkx as nx
except ImportError:
    nx = None
try:
    import requests
except ImportError:
    requests = None


###############################################################################
# Estruturas
###############################################################################
class Node:
    def __init__(self, d):
        self.id=d["id"]; self.x=d["x"]; self.y=d["y"]
        self.is_cs=d.get("is_charging_station",False)
        self.charger_kw=d.get("charger_power_kw")

def euclid(a:Node,b:Node)->float:
    return math.hypot(a.x-b.x,a.y-b.y)

def osrm_dist(nodes:List[Node], metric="distance")->Optional[List[List[float]]]:
    url=os.getenv("OSRM_URL")
    if not url or not requests: return None
    coords=";".join(f"{n.x},{n.y}" for n in nodes)
    q=f"{url}/table/v1/driving/{coords}?annotations={metric}"
    try:
        r=requests.get(q,timeout=10)
        if r.status_code==200:
            return r.json()[metric+"s"]
    except Exception as e:
        print("OSRM error",e)
    return None

def build_matrix(nodes):
    return [[euclid(a,b) for b in nodes] for a in nodes]

###############################################################################
# Dijkstra com bateria
###############################################################################
def shortest_path(nodes:List[Node], start:int, end:int,
                  battery_kwh:float, cons_km:float=0.2):
    n=len(nodes)
    dist=osrm_dist(nodes) or build_matrix(nodes)
    graph=[[(j,dist[i][j]) for j in range(n) if j!=i] for i in range(n)]

    # estado = (custo, idx, soc)
    pq=[(0,start,battery_kwh)]
    best={}
    parent={}
    while pq:
        cost,u,soc=heapq.heappop(pq)
        key=(u,round(soc,1))
        if key in best and best[key]<=cost: continue
        best[key]=cost
        if u==end:  # chegou
            path=[]
            while (u,soc) in parent:
                path.append(u)
                u,soc=parent[(u,soc)]
            path.append(start)
            return list(reversed(path)),cost
        for v,w in graph[u]:
            need=w*cons_km
            if need<=soc:  # segue sem carregar
                heapq.heappush(pq,(cost+w,v,soc-need))
            if nodes[u].is_cs and nodes[u].charger_kw:  # carrega full e parte
                new_soc=battery_kwh
                if need<=new_soc:
                    charge_time=0  # ignorado
                    heapq.heappush(pq,(cost+w+charge_time,v,new_soc-need))
    return None, math.inf

###############################################################################
def main():
    if len(sys.argv)>1:
        payload=json.load(open(sys.argv[1],"r",encoding="utf8"))
    else:
        print("Give JSON file with nodes & vehicles")
        return
    nodes=[Node(n) for n in payload["nodes"]]
    veh=payload["vehicles"][0]
    start=payload.get("start_id",nodes[0].id)
    end=payload.get("end_id",nodes[-1].id)
    id_to_idx={n.id:i for i,n in enumerate(nodes)}
    path,cost=shortest_path(nodes,id_to_idx[start],id_to_idx[end],
                            veh["battery_kwh"])
    if path:
        print("Path:",[nodes[i].id for i in path],"dist:",cost)
    else:
        print("Infeasible")

if __name__=="__main__":
    main()
