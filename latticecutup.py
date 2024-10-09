#! /usr/bin/python3

import sys
import time
import os
import datetime
import networkx as nx

from removedominatorsbp import readem
from removedominatorsbp import dmfromem
from greedythenlattice import latticeshrink

def mergeem(emone, emtwo):
    # Merge everything from emtwo into emone
    for e in emtwo:
        if e in emone:
            continue
        emone[e] = emtwo[e]

def main():
    print('Start time:', datetime.datetime.now())
    sys.stdout.flush()

    if len(sys.argv) < 2:
        print('Usage: ', end = '')
        print(sys.argv[0], end = ' ')
        print('<em-file-1> <em-file-2> ...')
        return

    print('Reading and merging ems...', end='')
    sys.stdout.flush()

    em = dict()
    for fnum in range(1,len(sys.argv)):
        fname = sys.argv[fnum]
        if not os.path.exists(fname):
            print(fname, 'does not exist! Exiting...')
            sys.stdout.flush()
            sys.exit(0)

        thisem = readem(fname)
        mergeem(em, thisem)
    
    print('done!')
    sys.stdout.flush()

    print('Creating rolesasperms...', end='')
    sys.stdout.flush()

    # Create roles as permissions
    rolesasperms = list()
    dm = dmfromem(em)
    G = nx.Graph()
    for e in dm:
        if e == tuple((-1,-1)):
            for f in dm[e]:
                G.add_node(f)
        else:
            for f in dm[e]:
                G.add_edge(e, f)

    #One role per connected component in G
    for c in nx.connected_components(G):
        r = set() # our role as a set of permissions
        for t in c:
            r.add(t[1])
        rolesasperms.append(r)

    print('done! len(rolesasperms):', len(rolesasperms))
    sys.stdout.flush()

    latticeshrink(rolesasperms)

    print('After lattice-shrink, len(rolesasperms):', len(rolesasperms))
    sys.stdout.flush()

    print('End time:', datetime.datetime.now())

if __name__ == '__main__':
    main()
