
"""
tabu_search.py — heurística Tabu Search multi‑rota.

Características:
    • inicializa com Nearest Neighbor por veículo
    • movimentos de relocalização (transferir cliente entre rotas)
    • lista tabu com tenure configurável
    • critério de parada: tempo máximo (s) ou iterações

Dependências: só stdlib.
"""

import sys, json, math, time, random, itertools, argparse
CONSUMPTION=0.2

class Node:
    def __init__(self,d): self.__dict__.update(d)

def dist(a,b): return math.hypot(a.x-b.x,a.y-b.y)

def route_distance(route,mat):
    return sum(mat[route[i]][route[i+1]] for i in range(len(route)-1))

def initial_solution(nodes,vehicles,mat):
    dep=0
    clients=list(range(1,len(nodes)))
    random.shuffle(clients)
    k=len(vehicles)
    routes=[ [dep]+clients[i::k]+[dep] for i in range(k) ]
    return routes

def tabu_search(nodes,vehicles,mat,tenure=15,max_iter=500,time_limit=60):
    best_routes=initial_solution(nodes,vehicles,mat)
    best_cost=sum(route_distance(r,mat) for r in best_routes)
    tabu_list={}
    cur_routes=[r[:] for r in best_routes]
    start=time.time()
    it=0
    while it<max_iter and time.time()-start<time_limit:
        it+=1
        neighborhood=[]
        # generate relocate moves
        for ri,r in enumerate(cur_routes):
            for idx in range(1,len(r)-1):
                client=r[idx]
                for rj,rr in enumerate(cur_routes):
                    if ri==rj: continue
                    for pos in range(1,len(rr)):
                        neighborhood.append((ri,idx,rj,pos))
        best_move=None; best_move_cost=math.inf
        for mv in neighborhood:
            ri,idx,rj,pos=mv
            new=[r[:] for r in cur_routes]
            client=new[ri].pop(idx)
            new[rj].insert(pos,client)
            cost=sum(route_distance(r,mat) for r in new)
            if cost<best_move_cost and tabu_list.get((client,rj),0)<=it:
                best_move_cost=cost; best_move=mv
        if not best_move: break
        ri,idx,rj,pos=best_move
        client=cur_routes[ri].pop(idx)
        cur_routes[rj].insert(pos,client)
        tabu_list[(client,ri)]=it+tenure
        cur_cost=sum(route_distance(r,mat) for r in cur_routes)
        if cur_cost<best_cost:
            best_cost=cur_cost
            best_routes=[r[:] for r in cur_routes]
    return best_routes,best_cost

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("file",nargs="?",help="payload")
    parser.add_argument("--time",type=int,default=30)
    parser.add_argument("--iter",type=int,default=1000)
    parser.add_argument("--tenure",type=int,default=10)
    args=parser.parse_args()
    payload=json.load(open(args.file)) if args.file else json.loads(sys.stdin.read())
    nodes=[Node(n) for n in payload["nodes"]]
    mat=[[dist(a,b) for b in nodes] for a in nodes]
    routes,cost=tabu_search(nodes,payload["vehicles"],mat,args.tenure,args.iter,args.time)
    ids=[[nodes[i].id for i in r] for r in routes]
    print("Roteamento:",ids,"Custo:",cost)

if __name__=="__main__":
    main()
