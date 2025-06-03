
"""
grasp.py — GRASP genérico p/ VRP

Fases:
 1) Construção — lista restrita de candidatos (RCL) controlada por α.
 2) Busca local — 2‑opt sobre cada rota.
 3) Repete até limite de iterações ou tempo, guarda melhor.

Parâmetros:
  --alpha  controle de aleatoriedade (0 = greedy, 1 = rand)
"""

import sys, json, math, random, time, argparse, itertools
CONSUMPTION=0.2

class Node:
    def __init__(self,d): self.__dict__.update(d)

def dist(a,b): return math.hypot(a.x-b.x,a.y-b.y)

def two_opt(route,mat):
    improved=True
    while improved:
        improved=False
        for i in range(1,len(route)-2):
            for j in range(i+1,len(route)-1):
                if j-i==1: continue
                delta=(mat[route[i-1]][route[j]]+mat[route[i]][route[j+1]]-
                       mat[route[i-1]][route[i]]-mat[route[j]][route[j+1]])
                if delta<-1e-6:
                    route[i:j+1]=reversed(route[i:j+1])
                    improved=True
    return route

def build_solution(nodes,vehicle,mat,alpha):
    depot=0
    unvisited=set(range(1,len(nodes)))
    route=[depot]
    while unvisited:
        dists=[(mat[route[-1]][j],j) for j in unvisited]
        dists.sort()
        if not dists: break
        max_idx=max(1,int(alpha*len(dists)))
        _,chosen=random.choice(dists[:max_idx])
        route.append(chosen)
        unvisited.remove(chosen)
    route.append(depot)
    return route

def grasp(nodes,vehicle,mat,alpha,iters,time_limit):
    best=None; best_cost=math.inf; start=time.time()
    for _ in range(iters):
        if time.time()-start>time_limit: break
        r=build_solution(nodes,vehicle,mat,alpha)
        r=two_opt(r,mat)
        c=sum(mat[r[k]][r[k+1]] for k in range(len(r)-1))
        if c<best_cost:
            best_cost=c; best=r
    return best,best_cost

def main():
    p=argparse.ArgumentParser()
    p.add_argument("file",nargs="?",help="payload")
    p.add_argument("--alpha",type=float,default=0.3)
    p.add_argument("--iter",type=int,default=500)
    p.add_argument("--time",type=int,default=60)
    args=p.parse_args()
    payload=json.load(open(args.file)) if args.file else json.loads(sys.stdin.read())
    nodes=[Node(n) for n in payload["nodes"]]
    mat=[[dist(a,b) for b in nodes] for a in nodes]
    r,c=grasp(nodes,payload["vehicles"][0],mat,args.alpha,args.iter,args.time)
    print("Rota:",[nodes[i].id for i in r],"Custo:",c)

if __name__=="__main__":
    main()
