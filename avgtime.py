import re
import argparse

suffixes = ['GUROBI', 'LTIU', 'CLINGO', 'CP', 'MIP', 'GA', 'SAT']
opts = ['', 'egalitarian', 'sexequal', 'smti']

def main():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('--solverType', '-sT', help='Specify the solver you want to run(default will run them all)', type=int, default=-1, choices=[1, 2, 3, 4, 5, 6])

    # --solverType = 1 -> Gurobi 
    # --solverType = 2 -> Local Search(LTIU) 
    # --solverType = 3 -> ASP 
    # --solverType = 4 -> OR-Tools CP_SAT 
    # --solverType = 5 -> OR-Tools MIP 
    # --solverType = 6 -> Genetic Algorithm
    # --solverType = 7 -> Cmodels 

    argparser.add_argument('--opt', '-o', help='Specify the optimization variant, 0: Max Cardinality 1: Egalitarian 2: Sex-Equal 3: SMTI', type=int, default=-1, choices=[0, 1, 2, 3])
    argparser.add_argument('--size', '-s', help='Specify the size of benchmarks', type=int, default=-1, choices=[50, 100])
    
    args= argparser.parse_args()

    CPUtime = {}
    timeout = {}

    if args.opt in range(1,3) and (args.solverType != 3 or args.solverType != 4 or args.solverType != 5):
        raise Exception('Selected solver is not implemented to solve this optimization variant!')

    for p1 in [x/10 for x in range(1, 9)]:
        CPUtime[p1] = {}
        timeout[p1] = {}
        for p2 in [x/10 for x in range(1, 10)]:
            c = 0
            s = 0
            for i in range(1, 11):
                if args.opt == 0:
                    fname = 'OUTPUT/output-smti-s-{}--i-{}pc-t-{}pc--{}_{}.txt'.format(args.size, p1, p2, i, suffixes[args.solverType-1])
                else:
                    fname = 'OUTPUT/output-smti-s-{}--i-{}pc-t-{}pc--{}_{}_{}.txt'.format(args.size, p1, p2, i, opts[args.opt], suffixes[args.solverType-1])
                with open(fname, 'r') as f:
                    st = f.read()
                    if args.solverType == 3:
                        pat = re.findall('CPU Time     : ([\d\.]+)', st)
                    elif args.solverType == 6:
                        pat = re.findall('tt ([\d\.]+)', st)
                    elif args.solverType in range(4,7):
                        pat = re.findall('Time: ([\d\.]+)', st)
                    elif args.solverType in range(4,7):
                        pat = re.findall('time: ([\d\.]+)', st)

                    if pat:
                        s += float(pat[0])
                        c += 1

            if c != 0:
                s /= c
            else:
                s = 0

            CPUtime[p1][p2] = round(s, 2)
            timeout[p1][p2] = c

    with open('results.txt', 'w') as f:
        f.write(' '.join([x/10 for x in range(1, 10)]))
        for p1 in CPUtime:
            f.write(str(p1) + ' & ' + ' & '.join([str(CPUtime[k][v]) for v in CPUtime[k]]) + '\\\\' +'\n' )
        print('Results are written to results.txt')


if __name__ == '__main__':
     main()