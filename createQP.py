import datetime
import os
import sys
import time

import gurobipy as gp
from gurobipy import GRB

from readup import readup


def remove_roles_if_duplicate(up: dict, users: set, perms: set, nroles: int) -> int:
    indices_removed = set()
    users_list = list(users)
    for i in range(len(users_list)):
        ui = users_list[i]
        perms_ui = up[ui]
        j = i + 1
        while j < len(users_list):
            if i in indices_removed or j in indices_removed:
                j += 1
                continue

            uj = users_list[j]
            if ui != uj:
                perms_uj = up[uj]
                if perms_ui == perms_uj:
                    nroles -= len(perms_uj)
                    indices_removed.add(j)
            j += 1
        return nroles


def remove_intersecting_roles(up: dict, users: set, perms: set, nroles: int) -> int:
    users_list = list(users)
    for i in range(len(users_list)):
        ui = users_list[i]
        max_num_intersecting_perms_ui = set()

        j = i + 1
        while j < len(users_list):
            uj = users_list[j]
            if ui != uj:
                tmp = up[ui].intersection(up[uj])
                if len(tmp) > len(max_num_intersecting_perms_ui):
                    max_num_intersecting_perms_ui = tmp
            j += 1
        k = len(max_num_intersecting_perms_ui)
        if k > 2:
            nroles -= k
    return nroles


def get_nroles(up: dict, users: set, perms: set, nedges: int):
    nroles = nedges
    nroles = remove_roles_if_duplicate(up, users, perms, nroles)
    print('# roles remaining after removing                                                                                                                                                                                                                                                                                                                                                                                                             duplicates:', nroles)

    # nroles = remove_intersecting_roles(up, users, perms, nroles)
    # print('# roles remaining after removing intersecting roles:', nroles)

    nroles = int(2 * min(len(users), len(perms)))
    return nroles


def reduce_to_qp(up: dict, users: set, perms: set, nroles) -> gp.Model:
    m = gp.Model("minedgesQP")

    # add variables
    for u in users:
        for r in range(nroles):
            m.addVar(vtype=GRB.BINARY, name="c_{user}_{role}".format(user=u, role=r))

    for p in perms:
        for r in range(nroles):
            m.addVar(vtype=GRB.BINARY, name="d_{perm}_{role}".format(perm=p, role=r))
    m.update()

    # Constraint 1: If user u has permission p
    for u in up:
        for p in up[u]:
            constr1_list = []
            for r in range(nroles):
                c_ur = m.getVarByName("c_{user}_{role}".format(user=u, role=r))
                d_pr = m.getVarByName("d_{perm}_{role}".format(perm=p, role=r))
                constr1_list.append(c_ur * d_pr)

            constr1 = gp.quicksum(constr1_list) >= 1
            m.addConstr(constr1, name='user_{user}_has_permission_{perm}'.format(user=u, perm=p))
    m.update()

    # Constraint 2: If user u does not have permission p
    for u in up:
        for p in perms:
            if p not in up[u]:
                # constr2_list = []
                for r in range(nroles):
                    c_ur = m.getVarByName("c_{user}_{role}".format(user=u, role=r))
                    d_pr = m.getVarByName("d_{perm}_{role}".format(perm=p, role=r))

                    not_c_ur = 1 - c_ur
                    not_d_pr = 1 - d_pr
                    m.addConstr(not_c_ur + not_d_pr >= 1, name='user_{user}_does_not_have_permission_{perm}'.format(
                        user=u, perm=p))

                    # constr2_list.append(c_ur * d_pr)

                # constr2 = gp.quicksum(constr2_list) == 0
                # m.addConstr(constr2, name='user_{user}_does_not_have_permission_{perm}'.format(user=u, perm=p))
    m.update()

    # set objective
    obj = gp.quicksum(m.getVars())

    m.setObjective(obj, GRB.MINIMIZE)
    m.update()
    return m


def run_model(m, filepath, filename):
    m.update()
    filename = filename.replace('.txt', '')
    m.write(os.path.join(filepath, filename + '.lp'))

    m.optimize()
    m.write(os.path.join(filepath, filename + '.sol'))


def rindex(input_str, target_str):
    if input_str[::-1].find(target_str) > -1:
        return len(input_str) - input_str[::-1].find(target_str)
    else:
        return 0


def main():
    print('Start time:', datetime.datetime.now())
    sys.stdout.flush()

    if len(sys.argv) != 2:
        print('Usage: ', end='')
        print(sys.argv[0], end=' ')
        print('<input-file>')
        return

    last_sep_index = rindex(sys.argv[1], '/')
    filepath = sys.argv[1][:last_sep_index]
    filename = sys.argv[1][last_sep_index:]

    up = readup(sys.argv[1])
    if not up:
        return

    nedges = 0
    users = set()
    perms = set()
    for u in up:
        users.add(u)
        perms = perms.union(up[u])
        nedges += len(up[u])

    print('Total # users:', len(users))
    print('Total # perms:', len(perms))
    print('Total # edges:', nedges)
    sys.stdout.flush()

    time1 = time.time()
    print('# roles to begin with:', nedges)
    nroles = get_nroles(up, users, perms, nedges)
    print('# roles remaining:', nroles)

    m = reduce_to_qp(up, users, perms, nroles)
    time2 = time.time()
    print('Time taken to reduce to ILP:', time2-time1)
    sys.stdout.flush()
    run_model(m, filepath, filename)
    time3 = time.time()
    print('Time taken to run model:', time3-time2)
    sys.stdout.flush()


if __name__ == '__main__':
    main()
