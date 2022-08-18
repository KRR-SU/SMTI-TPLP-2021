#!/usr/bin/env python

"""[smp_c.py]
Copyright (c) 2014, Andrew Perrault

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


from __future__ import with_statement

import argparse
import os
import subprocess
from socket import TIPC_ADDR_NAMESEQ
import string
import re
import time

man_dict = {}
woman_dict = {}
couple_dict = {}

NIL_WOMAN_UID = 999999
NIL_WOMAN_SYMBOL = "-1"
TREEMEM_LIM = "12000"


def combinations(iterable, r):
    # combinations('ABCD', 2) --> AB AC AD BC BD CD
    # combinations(range(4), 3) --> 012 013 023 123
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = list(range(r))
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i + 1, r):
            indices[j] = indices[j - 1] + 1
        yield tuple(pool[i] for i in indices)


def product(*args, **kwds):
    # product('ABCD', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy
    # product(range(2), repeat=3) --> 000 001 010 011 100 101 110 111
    pools = map(tuple, args) * kwds.get('repeat', 1)
    result = [[]]
    for pool in pools:
        result = [x + [y] for x in result for y in pool]
    for prod in result:
        yield tuple(prod)


class UIDAllocator():
    def __init__(self, first_uid=None):
        self.last_uid = first_uid - 1

    def allocate_uid(self):
        if self.last_uid is None:
            self.last_uid = 0
        else:
            self.last_uid = self.last_uid + 1
        return self.last_uid

class PreferenceFunction():
    def get_all_weakly_preferred(self, uid):
        raise Exception('must override in subclass')

    def get_rank(self, uid):
        raise Exception('must override in subclass')

    def get_ranks(self, uid):
        raise Exception('must override in subclass')

class ListPreferenceFunction(PreferenceFunction):
    def __init__(self, internal_list):
        self.internal_list = internal_list

    # returns list of agents that are strictly preferred over agent with uid
    def get_all_preferred(self, uid):
        preferred = []
        for rank in self.internal_list:
            if uid in self.internal_list[rank]:
                return preferred
            preferred.extend(self.internal_list[rank])
        raise Exception('uid not in preference list: %r; internal_list; %r'
                        % (uid, self.internal_list))

    # returns tie group that uid belongs to
    def get_tie_group(self, uid):
        rank = self.get_rank(uid)
        return self.internal_list[rank]

    def get_all_weakly_preferred(self, uid):
        return self.get_all_preferred(uid=uid) + self.get_tie_group(uid=uid)

    # added get_acceptable
    def get_acceptable(self):
        acc = []
        for v in self.internal_list.values():
            acc.extend(v)
        return acc

    def get_rank(self, uid):
        for rank in self.internal_list:
            if uid in self.internal_list[rank]:
                return rank

class Agent():
    def __init__(self, uid):
        self.uid = uid
        assert self.uid is not None

    def __hash__(self):
        return self.uid

    def __eq__(self, other):
        return self.uid == other.uid


class SinglePreferrer(Agent):
    def __init__(self, preference_function, uid):
        Agent.__init__(self, uid=uid)
        self.preference_function = preference_function

    def get_all_preferred(self, uid):
        return self.preference_function.get_all_preferred(uid=uid)

    def get_all_weakly_preferred(self, uid):
        return self.preference_function.get_all_weakly_preferred(uid=uid)

    def get_tie_group(self, rank):
        return self.preference_function.internal_list[rank]
    
    def get_tie_group_of(self, uid):
        return self.preference_function.internal_list[self.get_rank(uid)]

    def get_ranked_higher_than(self, rank):
        count = 0
        for r in self.preference_function.internal_list.keys():
            if r < rank:
                count += len(self.preference_function.internal_list[r])
        return count

    def get_acceptable(self):
        return self.preference_function.get_acceptable()

    def get_rank(self, uid):
        return self.preference_function.get_rank(uid=uid)

class Woman(SinglePreferrer):
    def __init__(self, preference_function, uid):
        SinglePreferrer.__init__(self,
                                 preference_function=preference_function,
                                 uid=uid)
        woman_dict[self.uid] = self


class NilWoman(Woman):
    def __init__(self):
        Woman.__init__(self, preference_function=None, uid=NIL_WOMAN_UID)
        self.capacity = 100
        if self.capacity is not None:
            assert isinstance(self.capacity, int)
        woman_dict[self.uid] = self

    def get_all_preferred(self, assignment):
        return []

    def get_all_weakly_preferred(self, assignment):
        return []


class Man(SinglePreferrer):
    def __init__(self, uid, preference_function=None):
        SinglePreferrer.__init__(self, preference_function=preference_function,
                                 uid=uid)
        man_dict[self.uid] = self

class DIMACSConstraint():
    def __init__(self, var_list):
        self.var_list = var_list
        assert len(self.var_list) > 0

    def render(self):
        raise Exception('must override in subclass')


class DIMACSClause(DIMACSConstraint):
    def __init__(self, var_list):
        DIMACSConstraint.__init__(self, var_list=var_list)

    def render(self):
        return ' '.join([str(var) for var in self.var_list]) + ' 0'
    
    def hard_render(self):
        return '{} '.format(maxw + 1) + ' '.join([str(var) for var in self.var_list]) + ' 0'
    
    def soft_max_render(self):
        return '1 ' + ' '.join([str(var) for var in self.var_list]) + ' 0'

    def soft_egal_render(self, weight):
        return '{} '.format(str(2*n-weight)) + ' '.join([str(var) for var in self.var_list]) + ' 0'


class ConstraintsBuffer():
    def __init__(self, filename):
        self.filename = filename
        with open(self.filename, 'w') as f:
            f.write('')
        self.buffer_list = []
        self.soft_buffer_list = []
        self.buffer_size = 100000000

    def append(self, constraint):
        # appending hard constraints
        if len(self.buffer_list) < self.buffer_size:
            self.buffer_list.append(constraint)
        else:
            with open(self.filename, 'a') as f:
                for item in self.buffer_list:
                    f.write(item.render() + '\n')
                f.write(constraint.render() + '\n')
            self.buffer_list = []

    def soft_append_with_weight(self, constraint, weight):
        if len(self.buffer_list) < self.buffer_size:
            self.soft_buffer_list.append((constraint,weight))

    def soft_append(self, constraint):
        if len(self.buffer_list) < self.buffer_size:
            self.soft_buffer_list.append(constraint)


    def flush(self, opt, variable_registry=None):
        with open(self.filename, 'a') as f:
            if opt == 0:
                for item in self.buffer_list:
                    f.write(item.render() + '\n')
                    if variable_registry is not None:
                        print(' '.join([
                            ('-' + variable_registry[abs(var)]
                                if var < 0 else variable_registry[abs(var)])
                            for var in item.var_list]))
            else:
                for item in self.buffer_list:
                    f.write(item.hard_render() + '\n')
                    if variable_registry is not None:
                        print(' '.join([
                            ('-' + variable_registry[abs(var)]
                                if var < 0 else variable_registry[abs(var)])
                            for var in item.var_list]))
                if opt == 1:
                    for item in self.soft_buffer_list:
                        f.write(item.soft_max_render() + '\n')
                        if variable_registry is not None:
                            print(' '.join([
                                ('-' + variable_registry[abs(var)]
                                    if var < 0 else variable_registry[abs(var)])
                                for var in item.var_list]))
                elif opt == 2:
                    for item,w in self.soft_buffer_list:
                        f.write(item.soft_egal_render(w) + '\n')
                        if variable_registry is not None:
                            print(' '.join([
                                ('-' + variable_registry[abs(var)]
                                    if var < 0 else variable_registry[abs(var)])
                                for var in item.var_list]))
        self.buffer_list = []
        self.soft_buffer_list = []


NIL_WOMAN = NilWoman()


def load_matching_from_file(filename):
    matching = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            if line.startswith('#'):
                continue
            split = line.split()
            if split[0] == 'r':
                if split[2] == NIL_WOMAN_SYMBOL:
                    matching[int(split[1])] = NIL_WOMAN_UID
                else:
                    matching[int(split[1])] = int(split[2])
    return matching


class ProblemInstance():
    def __init__(self, men, women):
        self.men = men
        self.women = women
        global n
        n = len(self.men)
        self.matching = {}

    @classmethod
    def from_file(cls, filename):
        # does not check that all referred to programs and residents exist
        # after problem is defined
        # does check for duplicate residents and programs
        man_dict = {}
        woman_dict = {}
        with open(filename, 'r') as f:
            men = []
            women = []
            for line in f:
                if (line.startswith('#') or line.startswith(' ')
                        or line.startswith('\n') or line.startswith('\r')):
                    continue
                items = line.replace('\n', '').split(' ')
                if line.startswith('m'):
                    if int(items[1]) in man_dict:
                        raise Exception('duplicate resident: %d'
                                        % int(items[1]))
                    # rol = []
                    # using dict instead of a list
                    rol = {r:[] for r in range(len(items)-2)}
                    rank = 0

                    for i in range(2, len(items)):
                        res = re.findall('\{(.*)\}', items[i])
                        if len(res) == 0:
                            rol[rank].append(int(items[i]))
                        else:
                            for h in res[0].split(','):
                                rol[rank].append(int(h))
                        rank += 1

                    s = Man(uid=int(items[1]),
                                 preference_function=ListPreferenceFunction(
                                 internal_list=rol))
                    men.append(s)
                elif line.startswith('w'):
                    if int(items[1]) in woman_dict:
                        raise Exception(
                            'duplicate program: %d' % int(items[1]))
                    #  updated similarly to residents' case
                    rol = {r:[] for r in range(len(items)-2)}
                    rank = 0
                    for i in range(2, len(items)):
                        res = re.findall('\{(.*)\}', items[i])
                        if len(res) == 0:
                            rol[rank].append(int(items[i]))
                        else:
                            for h in res[0].split(','):
                                rol[rank].append(int(h))
                        rank += 1

                    w = Woman(uid=int(items[1]),
                                 preference_function=ListPreferenceFunction(
                                 internal_list=rol))
                    women.append(w)
                else:
                    raise Exception('line not readable: %s' % line)
            return cls(men=men, women=women)

    # a matching here is just a dictionary from man_id -> woman_id
    @staticmethod
    def print_matching(matching, filename, times, header=None):
         with open(filename, 'a') as f:
            if header is not None:
                f.write('# %s\n' % header)
            f.write("Modeling time: {}s\n".format(round(times[0],3)))
            f.write("Solving time: {}s\n".format(round(times[1],3)))
            if len(matching) == 0:
                f.write('m 0\n')
                return
            f.write('m 1\n')
            for man_uid in matching.keys():
                if matching[man_uid] == NIL_WOMAN_UID:
                    f.write('%d %s\n' % (man_uid, NIL_WOMAN_SYMBOL))
                else:
                    f.write('%d %d\n' % (man_uid,
                                           matching[man_uid]))

    def solve_sat(self, solver,
                  problem_name='problem',
                  opt=0,
                  verbose=False, run_solver=True,
                  output_filename=None,
                  enumerate_all=False):
        start_time = time.time()
        variable_registry = {}
        problem_name_ = os.path.split(problem_name)[-1]
        constraints_buffer_filename = 'constraints/constraints_buffer-%s' % (problem_name_)
        if output_filename and not run_solver:
            solver_input_filename = output_filename
        else:
            solver_input_filename = 'satfiles/%s.sat' % (problem_name_)
        solver_output_filename = 'output/output-%s' % (problem_name_)
        constraints = ConstraintsBuffer(filename=constraints_buffer_filename)
        num_constraints = 0
        # this will keep track of the DIMACS number of each matching variable
        res_match = {}
        var_uid_allocator = UIDAllocator(first_uid=1)
        
        global maxw
        if opt == 1:
            maxw = n
        elif opt == 2:
            maxw = (2*n)*(n**2)

        for m in self.men:
            assert m not in res_match
            res_match[m] = {}
            # create matching variables res_match
            for w_uid in m.get_acceptable():
                woman = woman_dict[w_uid]
                res_match[m][woman] = \
                    var_uid_allocator.allocate_uid()
                variable_registry[res_match[m][woman]] = \
                    'xr_%d,%d' % (m.uid, woman.uid)
            # add NIL_WOMAN as being single
            res_match[
                m][NIL_WOMAN] = var_uid_allocator.allocate_uid()
            variable_registry[res_match[m][NIL_WOMAN]] = \
                'xr_%d,%d' % (m.uid, NIL_WOMAN_UID)
            constraints.append(DIMACSClause([
                res_match[m][woman_dict[w_uid]]
                for w_uid in m.get_acceptable()]
                + [res_match[m][NIL_WOMAN]]))

        # no man can be matched to two women
        for m in self.men:
            for (w1_uid, w2_uid) in combinations(
                    m.get_acceptable() + [NIL_WOMAN_UID], 2):
                constraints.append(DIMACSClause(
                    [-res_match[m][woman_dict[w1_uid]],
                     -res_match[m][woman_dict[w2_uid]]]))
        # no woman can be matched to two men
        for w in self.women:
            for (m1, m2) in combinations(w.get_acceptable(), 2):
                constraints.append(DIMACSClause(
                        [-res_match[man_dict[m1]][w], -res_match[man_dict[m2]][w]]))

        q = {}
        for w in self.women:
            q[w] = {}
            groups = len(w.preference_function.internal_list.keys())
            for i in range(groups + 1):

                if i == 0:
                    continue

                ranked_at = len(w.get_tie_group(i - 1))
                ranked_better = w.get_ranked_higher_than(i - 1)
                idx = ranked_at + ranked_better

                q[w][i] = var_uid_allocator.allocate_uid()
                variable_registry[q[w][i]] = \
                        'q_%d,%d' % (w.uid, i)
                if i == 1:
                    # q[w][1] is true if woman w is not married to any of the men in her most preferred tie group
                    constraints.append(DIMACSClause(
                        [res_match[man_dict[m]][w] for m in w.get_tie_group(0)] + [-q[w][i]]))
                    for m in w.get_tie_group(0):
                        # if woman w is married to a man m in her most preferred tie group, it implies that q[w][1][1] is true
                        constraints.append(DIMACSClause(
                            [-res_match[man_dict[m]][w], q[w][i]]))
                else:
                    # q[w][i] (i > 1) is true if woman w is not married to any of the men in her ith preferred tie group
                     constraints.append(DIMACSClause(
                           [res_match[man_dict[m]][w] for m in w.get_tie_group(i - 1)] + [q[w][i - 1], -q[w][i]]))
                     for m in w.get_tie_group(i - 1):
                          constraints.append(DIMACSClause([-res_match[man_dict[m]][w], -q[w][i], -q[w][i-1]]))
                     constraints.append(DIMACSClause(
                           [res_match[man_dict[m]][w] for m in w.get_tie_group(i - 1)] + [-q[w][i - 1], q[w][i]]))
                     for m in w.get_tie_group(i - 1):
                          constraints.append(DIMACSClause([-res_match[man_dict[m]][w], q[w][i], q[w][i-1]]))

        def append_q_vars(l, q_vars):
            l_copy = list(l)
            for q_var in q_vars:
                (woman, man, n) = q_var
                if woman.get_rank(man.uid) > 0 and len(woman.get_tie_group_of(man.uid)) == 1:
                     l_copy.append(q[woman][woman.get_rank(man.uid)])
                if len(woman.get_tie_group_of(man.uid)) > 1:
                      l_copy.append(q[woman][woman.get_rank(man.uid) + 1])
            return l_copy

        #stability constraints
        for man in self.men:
             for w_uid in man.get_acceptable():
                 w = woman_dict[w_uid]
                 # man is either married to one of his weakly preferred partners, or 
                 # woman is married to one of her weakly preferred partners
                 # otherwise, they would be a blocking pair
                 constraints.append(DIMACSClause(
                       append_q_vars([res_match[
                          man][woman_dict[uid]]
                            for uid in man.get_all_weakly_preferred(
                               w_uid)], [(w, man, 1)])))
        
        if opt == 1:
            for man in self.men:
                constraints.soft_append(DIMACSClause([-res_match[man][NIL_WOMAN]]))
        
        elif opt == 2:
            for man in self.men:
                for woman in self.women:
                    if man.uid in woman.get_acceptable() and woman.uid in man.get_acceptable():
                        constraints.soft_append_with_weight(DIMACSClause([res_match[man][woman]]), (woman.get_rank(man.uid) + man.get_rank(woman.uid)))
            # for man in self.men:
            #     constraints.soft_append_with_weight(DIMACSClause([res_match[man][NIL_WOMAN]]), 0)

        if verbose:
            constraints.flush(opt,variable_registry=variable_registry)
        else:
            constraints.flush(opt)

        # "lazy" implementation that only works in the one-to-one case
        # only fill out values of true variables
        count = 0
        extra_constraints = []
        num_constraints = 0
        with open(constraints.filename, 'r') as f:
            for line in f:
                if all(c in string.whitespace for c in line):
                    continue
                num_constraints += 1
        num_constraints += len(extra_constraints)
        with open(solver_input_filename, 'w') as problem:
            if opt == 0:
                problem.write('p cnf %s %s\n' % (
                    var_uid_allocator.last_uid, num_constraints))
            else:
                problem.write('p wcnf %s %s %s\n' % (
                    var_uid_allocator.last_uid, num_constraints, maxw))
            with open(constraints.filename, 'r') as f:
                for line in f:
                    if all(c in string.whitespace for c in line):
                        continue
                    problem.write(line)
            for constraint in extra_constraints:
                problem.write(constraint.render() + '\n')
        if not run_solver:
            return
        end_time = time.time()
        modeling_time = end_time - start_time

        start_time = time.time()
        
        if opt == 0:
            with open(solver_output_filename,'w') as f:
                subprocess.run(solver + ' ' + solver_input_filename, stdout=f, shell=True)
        else:
            with open(solver_output_filename,'w') as f:
                subprocess.run([solver + ' ' + solver_input_filename +' -m -cpu-lim=2000 -mem-lim=4000'], stdout=f, shell=True)
        
        end_time = time.time()
        solving_time = end_time - start_time

        if verbose:
            with open(solver_output_filename, 'r') as f:
                for line in f:
                    s = line.split()
                    if len(s) == 1:
                        print(s)
                    else:
                        for var_str in s:
                            if var_str != '0':
                                print('%s: %s' % (
                                    variable_registry[abs(int(var_str))],
                                    '1' if int(var_str) > 0 else '0'))
        matching_found = True
        with open(solver_output_filename, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if "UNSATISFIABLE" in line:
                    matching_found = False
                    break
        if matching_found:
            self.matching = {}
            with open(solver_output_filename, 'r') as f:
                for line in f:
                    if line.startswith('v'):
                        s = line.split()
                        for var_str in s[1:]:
                            if var_str != '0':
                                var_name = variable_registry[
                                    abs(int(var_str))]
                                if var_name.startswith('xr'):
                                    if int(var_str) > 0:
                                        self.matching[
                                            int(var_name[
                                                    3:var_name.find(',')])] \
                                                = int(var_name[
                                                    var_name.find(',')
                                                    + 1:len(var_name)])
                                    elif var_name.startswith('xc'):
                                        if int(var_str) > 0:
                                            self.matching[
                                                int(var_name.split(
                                                    ',')[1])] = int(
                                                        var_name.split(',')[2])
                        for m in self.men:
                            if m.uid not in self.matching:
                                self.matching[
                                    m.uid] = NIL_WOMAN_UID

        assert not matching_found or self.matching
            
        if enumerate_all:
            if not matching_found and count == 0:
                print("Matchings found: 0")
                return("Matchings found: 0")
            if not matching_found:
                print("Matchings found: %d" % count)
                return "Matchings found: %d" % count
            ProblemInstance.print_matching(self.matching, '%s-all%d' % (output_filename, count))
            count += 1
            # at least one matching must change
            constraints.append(DIMACSClause(
                [-res_match[man_dict[m_uid]][woman_dict[self.matching[m_uid]]] for m_uid in self.matching]))
        else:
            keep_searching = False
            return [modeling_time, solving_time]
           

SUFFIX_TABLE = {
    'kpr': '.kpr_out',
    'rp99': '.rp99_out',
    'sat': '.satsolution',
    'mip': '.mipsolution'
}

FORMULATION_TABLE = {
    'sat': '.sat',
    'mip': '.lp'
}


def main():
    output_filename = None
    run_solver = True
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'problem',
        help='the input problem file in the format described in the readme')
    parser.add_argument(
        '-v', '--verbose',
        help='display more detail in problem formulation', action="store_true")
    #currently we only have sat to solve SMTI
    parser.add_argument(
        '--solver',
        help='the solver to be used: mip or sat',
        choices=['sat'], default='sat')
    parser.add_argument(
        '-opt',
        help='the default option is SMTI (opt=0). \
              use -opt=0 for SMTI, use -opt=1 for Max Cardinality SMTI and -opt=2 for Egalitarian SMTI', 
              choices=['0','1','2'], default='0')
    parser.add_argument(
        '--formulate',
        help='formulate, but do not solve, the problem', action="store_true")
    parser.add_argument(
        '--enumerate_all',
        help='enumerate all stable matchings', action="store_true")
    parser.add_argument(
        '-o', '--output', help='output filename')
    args = parser.parse_args()
    if args.output and args.enumerate_all:
        raise Exception("can't enumerate all matchings to single file. to enumerate all matchings, do not specify output.")

    basen = os.path.basename(args.problem)

    if not args.output and not args.formulate:
        output_filename = 'output-matching-t/' + os.path.splitext(basen)[0] + SUFFIX_TABLE[args.solver]
    elif not args.output and args.formulate:
        output_filename = 'output-matching-t/' + os.path.splitext(basen)[0] + FORMULATION_TABLE[args.solver]
    else:
        output_filename = args.output

    if args.formulate:
        run_solver = False
    problem = ProblemInstance.from_file(args.problem)
    if args.solver == 'sat':
        solver_path = os.environ.get('SAT_SOLVER_PATH')
        if solver_path is None and run_solver:
            raise Exception(
                'SAT_SOLVER_PATH must contain the path to a '
                + 'SAT solver that accepts the DIMACS input format')
        optPrefix = ['', 'Max Cardinality', 'Egalitarian']
        with open(output_filename,'w') as f:
            f.write('Solving {} SMTI...\n'.format(optPrefix[int(args.opt)]))
        print('Solving...')
        cputimes = problem.solve_sat(solver=solver_path, verbose=args.verbose,
                                   run_solver=run_solver,
                                   problem_name=args.problem,
                                   opt=int(args.opt),
                                   output_filename=output_filename,
                                   enumerate_all=args.enumerate_all)
    if run_solver:
        ProblemInstance.print_matching(problem.matching,
                                       output_filename, cputimes)
        print('Output is written to', output_filename)

if __name__ == "__main__":
    main()
