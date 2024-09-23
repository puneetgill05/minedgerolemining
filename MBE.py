# https://bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-15-110
# variable names are as in paper

import bisect

from matplotlib import pyplot as plt

import viz_bicliques


def biclique_find(G):
    """
    Returns generator object, enumerating all maximal bicliques of G

    This function is preparation for recursion

    :param G: list of tuples, denoting bipartite graph edges
    :return: generator object
    """

    # initializing lists
    R = []
    L, P = zip(*G)
    L = list(set(L))
    P = list(set(P))
    NHS = [neighborhood_size(G, v) for v in P]

    P, NHS = zip(*[(p, nhs) for nhs, p in sorted(zip(NHS, P))])
    P = list(P)
    NHS = list(NHS)

    Q = []

    return biclique_find_core(G, L, R, P, NHS, Q)


def neighborhood_size(G, v):
    """
    This was called "common neighborhood size" in paper

    Didn't understand, what is "common", so just used neighborhood size
    :param G:
    :param v:
    :return:
    """
    return len([u for u, v1 in G if v1 == v])


def biclique_find_core(G, L, R, P, NHS, Q):
    """
    Used lists everywhere, not sets

    Appsarently, elemnt uniqueness is guaranteed by algorithm (not sure)

    Additional NHS list holds neighborhood sizes for P

    :param G:
    :param L:
    :param R:
    :param P:
    :param Q:
    :return:
    """

    pass
    while len(P) > 0:

        x = P.pop(0)
        NHS.pop(0)

        R1 = R + [x]
        L1 = [u for u in L if (u, x) in G]
        L1_bar = [u for u in L if u not in L1]

        C = [x]
        dI = []
        P1 = []
        NHS1 = []
        Q1 = []
        is_maximal = True

        for v in Q:
            N_v = [u for u in L1 if (u, v) in G]

            if len(N_v) == len(L1):
                is_maximal = False
                break
            elif len(N_v) > 0:
                Q1 = Q1 + [v]

        if is_maximal:

            for i, (v, nhs) in enumerate(zip(P, NHS)):
                N_v = [u for u in L1 if (u, v) in G]

                if len(N_v) == len(L1):

                    R1 = R1 + [v]

                    S = [u for u in L1_bar if (u, v) in G]

                    if len(S) == 0:
                        C = C + [v]
                        dI = dI + [i]

                elif len(N_v) > 0:

                    j = bisect.bisect_right(NHS1, nhs)
                    NHS1 = NHS1[:j] + [nhs] + NHS1[j:]
                    P1 = P1[:j] + [v] + P1[j:]

            yield L1, R1

            if len(P1) > 0:

                # recursion is "unwrapped" to return pairs
                for (L2, R2) in biclique_find_core(G, L1, R1, P1, NHS1, Q1):
                    yield L2, R2

        Q = Q + C
        P = [v for v in P if v not in C]
        NHS = [nhs for i, nhs in enumerate(NHS) if i not in dI]


def test_article_example():
    G = [
        ('u1', 'p1'),
        ('u1', 'p2'),

        ('u2', 'p2'),
        ('u2', 'p3'),

        ('u3', 'p1'),
        ('u3', 'p3'),

        ('u4', 'p1'),
        ('u4', 'p2'),
        ('u4', 'p3'),

        ('u5', 'p1'),
        ('u5', 'p2'),
        ('u5', 'p3'),

        # ('u6', 'p1'),
        # ('u6', 'p2'),
        # ('u6', 'p3'),

    ]

    plt.figure()
    viz_bicliques.plot_biclique(G)
    plt.show(block=False)
    # pass

    for i, (U, V) in enumerate(biclique_find(G)):
        plt.figure()
        viz_bicliques.plot_biclique(G, (U, V))
        plt.show(block=False)

        print('\nLargest biclique #%d:' % i)
        print('U: %s' % str(U))
        print('V: %s' % str(V))


test_article_example()