
"""
savings.py — Heurística Clarke & Wright (paralela) com capacidade e autonomia.

Suporta:
    • vários veículos
    • limite de capacidade
    • autonomia por km*consumo (simplificado)

Não trata janelas de tempo (TW) nem recarga; pode ser estendido.

Algoritmo:
    1) Inicializa rota individual para cada cliente.
    2) Calcula 'saving' S(i,j) = d(i,0)+d(0,j)-d(i,j).
    3) Ordena decrescente; tenta fundir rotas se não violar capacidade/autonomia.
"""

import sys, json, math, itertools
from typing import List, Dict, Tuple

CONSUMPTION = 0.2  # kWh/km

class Node:
    def __init__(self,d): self.__dict__.update(d)

def dist(a,b): return math.hypot(a.x-b.x,a.y-b.y)

def clarke_wright(nodes:List[Node], vehicles:List[Dict]):
    n=len(nodes)
    depot=next(i for i,nod in enumerate(nodes) if getattr(nod,"is_depot",False))
    mat=[[dist(a,b) for b in nodes] for a in nodes]
    clients=[i for i in range(n) if i!=depot]
    # rota inicial {cliente}: [depot, cliente, depot]
    routes={i:[depot,i,depot] for i in clients}
    loads={i:getattr(nodes[i],"demand",0.0) for i in clients}
    # savings list
    savings=[(mat[i][depot]+mat[depot][j]-mat[i][j],i,j)
             for i,j in itertools.combinations(clients,2)]
    savings.sort(reverse=True)

    capacity=vehicles[0]["capacity"]
    battery=vehicles[0]["battery_kwh"]

    def route_distance(r): return sum(mat[r[k]][r[k+1]] for k in range(len(r)-1))
    def route_energy(r): return route_distance(r)*CONSUMPTION

    for s,i,j in savings:
        ri=next(r for r in routes.values() if r[1]==i or r[-2]==i)
        rj=next(r for r in routes.values() if r[1]==j or r[-2]==j)
        if ri is rj: continue
        # combina?)
        if ri[-2]==i and rj[1]==j:
            new_r=ri[:-1]+rj[1:]
            new_load=loads[ri[1]]+loads[rj[1]]
            if new_load>capacity: continue
            if route_energy(new_r)>battery: continue
            # merge
            routes[ri[1]]=new_r
            loads[ri[1]]=new_load
            routes.pop(rj[1]); loads.pop(rj[1])

    final=list(routes.values())
    return final, mat

def main():
    payload=json.load(open(sys.argv[1])) if len(sys.argv)>1 else json.loads(sys.stdin.read())
    nodes=[Node(n) for n in payload["nodes"]]
    routes,mat=clarke_wright(nodes,payload["vehicles"])
    for r in routes:
        d=sum(mat[r[k]][r[k+1]] for k in range(len(r)-1))
        print([nodes[i].id for i in r],f"{d:.1f} km")

if __name__=="__main__":
    main()
