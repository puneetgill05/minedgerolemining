#! /usr/bin/python3

import time
import datetime
import sys

from readup import readup
from readup import uptopu
from removedominatorsbp import removedominators
from removedominatorsbp import hasbeenremoved
from removedominatorsbp import neighbours

def getedgeset(em, up):
    # set of all edges
    edgeset = set()
    for u in up:
        for p in up[u]:
            e = tuple((u, p))
            if hasbeenremoved(e, em):
                continue
            edgeset.add(e)

    return edgeset

def find_bicliquesbp(em, up, pu, nodes):
    #Adapted from networkx.find_cliques
    #Presumably dominators and zero-neighbour vertices have been
    #removed. But that's not a necessary condition

    if len(up) == 0:
        return

    edgeset = getedgeset(em, up)

    adj = {u: {v for v in neighbours(u, em, up, pu) if v != u} for u in edgeset}

    # Initialize Q with the given nodes and subg, cand with their nbrs
    Q = nodes[:] if nodes is not None else []
    cand = edgeset
    for node in Q:
        if node not in cand:
            raise ValueError(f"The given `nodes` {nodes} do not form a clique")
        cand &= adj[node]

    if not cand:
        yield Q[:]
        return

    subg = cand.copy()
    stack = []
    Q.append(None)

    u = max(subg, key=lambda u: len(cand & adj[u]))
    ext_u = cand - adj[u]

    try:
        while True:
            if ext_u:
                q = ext_u.pop()
                cand.remove(q)
                Q[-1] = q
                adj_q = adj[q]
                subg_q = subg & adj_q
                if not subg_q:
                    yield Q[:]
                else:
                    cand_q = cand & adj_q
                    if cand_q:
                        stack.append((subg, cand, ext_u))
                        Q.append(None)
                        subg = subg_q
                        cand = cand_q
                        u = max(subg, key=lambda u: len(cand & adj[u]))
                        ext_u = cand - adj[u]
            else:
                Q.pop()
                subg, cand, ext_u = stack.pop()
    except IndexError:
        pass

def main():
    print('Start time:', datetime.datetime.now())
    sys.stdout.flush()

    if len(sys.argv) != 2:
        print('Usage: ', end = '')
        print(sys.argv[0], end = ' ')
        print('<input-file>')
        return

    up = readup(sys.argv[1])
    if not up:
        return

    pu = uptopu(up)

    print('Removing doms...', end='')
    sys.stdout.flush()

    timeone = time.time()
    em = dict()
    seq = removedominators(em, up)
    timetwo = time.time()

    print('done! Time taken:', timetwo - timeone)
    sys.stdout.flush()

    nedges = 0
    for u in up:
        nedges += len(up[u])

    print("Original # edges:", nedges)
    print('# dominators removed:', seq)
    #print('edge-marks:')
    #for e in em:
    #    print('\t'+str(e)+': '+str(em[e]))

    nzerodeg = 0
    for u in up:
        for p in up[u]:
            e = tuple((u,p))

            if hasbeenremoved(e, em):
                continue
            
            if not neighbours(e, em, up, pu):
                nzerodeg += 1

    print('# edges with no neighbours:', nzerodeg)

    # Enumerate 'cliques'
    print('Enumerating cliques:')
    for c in find_bicliquesbp(em, up, pu, list()):
        print('\t'+str(c))
        sys.stdout.flush()

    print('End time:', datetime.datetime.now())

if __name__ == '__main__':
    main()
