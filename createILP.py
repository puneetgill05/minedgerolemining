import datetime
import os
import sys
import time

import gurobipy as gp
from gurobipy import GRB, Var

from readup import readup


def get_nroles(up: dict, users: set, perms: set, nedges: int):
    nroles = int(2 * min(len(users), len(perms)))
    return nroles


def get_variables_by_prefix_and_suffix(variables: dict, var_prefix: str, suffices: set) -> dict:
    ret = dict()
    for suffix in suffices:
        var_name = '{var_prefix}_{suffix}'.format(var_prefix=var_prefix, suffix=suffix)
        if var_name in variables:
            ret[var_name] = variables[var_name]
    return ret


def reduce_to_ilp(up: dict, users: set, perms: set, nroles) -> gp.Model:
    m = gp.Model("minedgesILP")

    variables_dict = dict()
    # add variables
    # user-role variables
    for u in users:
        for r in range(nroles):
            var_c = m.addVar(vtype=GRB.BINARY, name="c_{user}_{role}".format(user=u, role=r))
            variables_dict["c_{user}_{role}".format(user=u, role=r)] = var_c
    # perm-role variables
    for p in perms:
        for r in range(nroles):
            var_d = m.addVar(vtype=GRB.BINARY, name="d_{perm}_{role}".format(perm=p, role=r))
            variables_dict["d_{perm}_{role}".format(perm=p, role=r)] = var_d

    m.update()
    c_d_vars = m.getVars()

    # user-perm and user-perm-role variables
    for u in users:
        for p in perms:
            var_a = m.addVar(vtype=GRB.BINARY, name="a_{user}_{perm}".format(user=u, perm=p))
            variables_dict["a_{user}_{perm}".format(user=u, perm=p)] = var_a

            for r in range(nroles):
                var_b = m.addVar(vtype=GRB.BINARY, name="b_{user}_{perm}_{role}".format(user=u, perm=p, role=r))
                variables_dict["b_{user}_{perm}_{role}".format(user=u, perm=p, role=r)] = var_b

    print('Variables created done')

    m.update()

    # Constraint 1: If user u has permission p
    '''
    Basic constraints:

    for each user and perm in UP
    - (c_{user}_{0} && d_{perm}_{0}) || (c_{user}_{1} && d_{perm}_{1}) || ... || (c_{user}_{nroles-1} && d_{
    perm}_{nroles-1}
    
    Constraints after Tseitein transformation:
    
    - a_{user}_{perm} 
    - a_{user}_{perm} <=> (b_{user}_{perm}_{0} || b_{user}_{perm}_{1} || ... || b_{user}_{perm}_{nroles-1})
    - b_{user}_{perm}_{0} <=> (c_{user}_{0} && d_{perm}_{0})
    - b_{user}_{perm}_{1} <=> (c_{user}_{1} && d_{perm}_{1})
    - ...
    - b_{user}_{perm}_{nroles-1} <=> (c_{user}_{nroles-1} && d_{perm}_{nroles-1})
    '''
    for u in up:
        # c_ur_set = get_variables_by_prefix(m.getVars(), 'c_{user}'.format(user=u))
        c_ur_dict = get_variables_by_prefix_and_suffix(variables_dict, 'c_{user}'.format(user=u), set(range(nroles)))

        for p in up[u]:
            a_up = variables_dict['a_{user}_{perm}'.format(user=u, perm=p)]
            not_a_up = 1 - a_up

            m.addConstr(a_up >= 1, name='user {user} has permission {perm}'.format(user=u, perm=p))

            # b_upr_set = get_variables_by_prefix(m.getVars(), 'b_{user}_{perm}'.format(user=u, perm=p))
            b_upr_dict = get_variables_by_prefix_and_suffix(variables_dict, 'b_{user}_{perm}'.format(user=u, perm=p),
                                                           set(range(nroles)))
            # d_pr_set = get_variables_by_prefix(m.getVars(), 'd_{perm}'.format(perm=p))
            d_pr_dict = get_variables_by_prefix_and_suffix(variables_dict, 'd_{perm}'.format(perm=p),
                                                           set(range(nroles)))

            # a_{user}_{perm} => b_{user}_{perm}
            m.addConstr(not_a_up + gp.quicksum(b_upr_dict.values()) >= 1,
                        name='a_{user}_{perm} => b_{user}_{perm}'
                        .format(user=u, perm=p))


            # b_{user}_{perm} => a_{user}_{perm}
            for b_upr in b_upr_dict.values():
                not_b_upr = 1 - b_upr
                m.addConstr(not_b_upr + a_up >= 1,
                            name='b_{user}_{perm} => a_{user}_{perm}'
                            .format(user=u, perm=p))

            # b_{user}_{perm}_{role} <=> (c_{user}_{role} && d_{perm}_{role})
            # print('Constraint: b_{user}_{perm}_{role} <=> (c_{user}_{role} && d_{perm}_{role}) done')

            for r in range(nroles):
                # b_upr = get_first_variable_by_suffix(list(b_upr_set), str(r))
                b_upr_list = [v for k,v in b_upr_dict.items() if k.endswith('_{role}'.format(role=r))]

                # c_ur = get_first_variable_by_suffix(list(c_ur_set), str(r))
                c_ur_list = [v for k,v in c_ur_dict.items() if k.endswith('_{role}'.format(role=r))]

                # d_pr = get_first_variable_by_suffix(list(d_pr_set), str(r))
                d_pr_list = [v for k,v in d_pr_dict.items() if k.endswith('_{role}'.format(role=r))]

                if len(c_ur_list) > 0 and len(d_pr_list) > 0 and len(b_upr_list) > 0:
                    b_upr = b_upr_list[0]
                    not_b_upr = 1 - b_upr
                    c_ur = c_ur_list[0]
                    not_c_ur = 1 - c_ur
                    d_pr = d_pr_list[0]
                    not_d_pr = 1 - d_pr

                    # b_{user}_{perm}_{role} => c_{user}_{role}
                    m.addConstr(not_b_upr + c_ur >= 1,
                                name='b_{user}_{perm}_{role} => c_{user}_{role}'
                                .format(user=u, perm=p, role=r))

                    # b_{user}_{perm}_{role} => d_{perm}_{role}
                    m.addConstr(not_b_upr + d_pr >= 1,
                                name='b_{user}_{perm}_{role} => d_{perm}_{role}'
                                .format(user=u, perm=p, role=r))

                    # (c_{user}_{role} && d_{perm}_{role}) => b_{user}_{perm}_{role}
                    m.addConstr(not_c_ur + not_d_pr + b_upr >= 1,
                                name='(c_{user}_{role} and d_{perm}_{role}) => b_{user}_{perm}_{role}'
                                .format(user=u, perm=p, role=r))

    m.update()

    print('Constraint 1 done')

    # Constraint 2: If user u does not have permission p
    '''
    Basic Constraints:
    For each role j from 0 to nroles-1
    - ! (c_{user}_{j} && d_{perm}_{j})
    
    After DeMorgan's, constraints are:    
    - ! c_{user}_{0} || ! d_{perm}_{0}
    - ! c_{user}_{1} || ! d_{perm}_{1}
    - ...
    - ! c_{user}_{nroles-1} || ! d_{perm}_{nroles-1}
    '''
    for u in up:
        for p in perms:
            if p not in up[u]:
                m.addConstr(True, 'user {user} does not have permission {perm}'.format(user=u, perm=p))
                for r in range(nroles):
                    c_ur = m.getVarByName("c_{user}_{role}".format(user=u, role=r))
                    not_c_ur = 1 - c_ur
                    d_pr = m.getVarByName("d_{perm}_{role}".format(perm=p, role=r))
                    not_d_pr = 1 - d_pr
                    m.addConstr(not_c_ur + not_d_pr >= 1,
                                name='!(c_{user}_{role} &&  d_{perm}_{role})'.format(user=u, perm=p, role=r))

    print('Constraint 2 done')

    m.update()

    # set objective
    obj = gp.quicksum(c_d_vars)

    m.setObjective(obj, GRB.MINIMIZE)
    m.update()
    print('Objective done')

    return m


def run_model(m, filepath, filename):
    m.update()
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
    # print('# roles to begin with:', nedges)
    nroles = get_nroles(up, users, perms, nedges)
    print('# roles:', nroles)

    m = reduce_to_ilp(up, users, perms, nroles)
    time2 = time.time()
    print('Time taken to reduce to ILP:', time2 - time1)
    sys.stdout.flush()
    run_model(m, filepath, filename)
    time3 = time.time()
    print('Time taken to run model:', time3 - time2)
    sys.stdout.flush()


if __name__ == '__main__':
    main()
