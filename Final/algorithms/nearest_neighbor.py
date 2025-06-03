
"""
nearest_neighbor.py — heurística NN com 2‑opt opcional.

Suporta:
    • capacidade (verificação simples)
    • autonomia
    • opção --two_opt para melhorar rota única
"""

import sys, json, math, random, itertools, argparse
CONSUMPTION=0.2

class Node:
    def __init__(self,d): self.__dict__.update(d)

def dist(a,b): return math.hypot(a.x-b.x,a.y-b.y)

def nearest_neighbor(nodes, vehicle):
    n=len(nodes); depot=0
    mat=[[dist(a,b) for b in nodes] for a in nodes]
    unvisited=set(range(1,n))
    cap=vehicle["capacity"]
    battery=vehicle["battery_kwh"]
    route=[depot]; load=0; energy=0
    cur=depot
    while unvisited:
        nxt=min(unvisited,key=lambda j:mat[cur][j])
        if load+getattr(nodes[nxt],"demand",0)>cap: break
        need=mat[cur][nxt]*CONSUMPTION
        if energy+need>battery: break
        route.append(nxt); load+=getattr(nodes[nxt],"demand",0); energy+=need
        cur=nxt; unvisited.remove(nxt)
    route.append(depot)
    return route, mat

def two_opt(route,mat):
    improved=True
    while improved:
        improved=False
        for i in range(1,len(route)-2):
            for j in range(i+1,len(route)-1):
                if j-i==1: continue
                delta = (mat[route[i-1]][route[j]]+
                         mat[route[i]][route[j+1]]-
                         mat[route[i-1]][route[i]]-
                         mat[route[j]][route[j+1]])
                if delta< -1e-6:
                    route[i:j+1]=reversed(route[i:j+1])
                    improved=True
    return route

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("file",nargs="?",help="payload json")
    parser.add_argument("--two_opt",action="store_true")
    args=parser.parse_args()
    payload=json.load(open(args.file)) if args.file else json.loads(sys.stdin.read())
    nodes=[Node(n) for n in payload["nodes"]]
    route,mat=nearest_neighbor(nodes,payload["vehicles"][0])
    if args.two_opt: route=two_opt(route,mat)
    d=sum(mat[route[k]][route[k+1]] for k in range(len(route)-1))
    print([nodes[i].id for i in route],f"{d:.2f} km")

if __name__=="__main__":
    main()
