import subprocess
import os
import subprocessmethodrun
import argparse


def ASP_inputConverter(inputFile):
    # takes the inputFile(as path) and converts it into the input format for ASP solver.
    # the converted input will be written in a file called input_ASP_Version.lp
    # So, for each input file we will change this file only for ASP instead of creating new files for each input.

    f = open(inputFile)
    output_str = ''
    lines = f.read().split('\n')
    f.close()
    m_size = int(lines[1])
    w_size = int(lines[2])

    output_str += 'man(1..{}).\n'.format(m_size)
    output_str += 'woman(1..{}).\n'.format(w_size)

    for line in lines[3:m_size + 3]:
        m = line.split(' ')[0]
        cnt = 1
        for group in line.split(' (')[1:]:
            gr = group.replace(')', '')
            if gr != '':
                for el in gr.split(' '):
                    if el != '':
                        output_str += 'mrank({},{},{}).\n'.format(m, el, cnt)
                cnt += 1

    for line in lines[m_size + 3:m_size + w_size + 3]:
        w = line.split(' ')[0]
        cnt = 1
        for group in line.split(' (')[1:]:
            gr = group.replace(')', '')
            if gr != '':
                for el in gr.split(' '):
                    if el != '':
                        output_str += 'wrank({},{},{}).\n'.format(w, el, cnt)
                cnt += 1

    f = open('input_ASP.lp', 'w')
    f.write(output_str)
    f.close()


def run_cmodels(input_path):
    for f in os.listdir(input_path):
        ASP_inputConverter(os.path.join(input_path, f))
        rsname = 'OUTPUT/{}'.format(f.replace('input', 'output').replace('.txt', '_SMTI_SAT.txt'))
        command = "gringo ASP/smti_lparse.lp input_ASP.lp | timeout -t 2000 -m 2000000 cmodels -zc -statistics"
        retcode, stdout, stderr = subprocessmethodrun.run(command, shell=True, stdout=subprocess.PIPE)
        output = stdout.decode('utf-8')
        with open(rsname, "w") as out:
            out.write(output)


def run_clingo(input_path):
    for f in os.listdir(input_path):
        ASP_inputConverter(os.path.join(input_path, f))
        rsname = 'OUTPUT/{}'.format(f.replace('input', 'output').replace('.txt','_SMTI_CLINGO.txt'))
        command = "clingo --stats input_ASP.lp Clingo/smti.lp  --time-limit=2000"
        retcode, stdout, stderr = subprocessmethodrun.run(command, shell=True, stdout=subprocess.PIPE)
        output = stdout.decode('utf-8')
        with open(rsname, "w") as out:
            print(rsname)
            out.write(output)


def main():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('--solverType', '-sT', metavar='', help='Specify the solver, 0: Clingo, 1: Cmodels ', type=int, default=0, choices=[0, 1])
    argparser.add_argument('--size', '-s', metavar='', help='Specify the size of the benchmark instances', type=int, default=50, choices=[50,100])
    args = argparser.parse_args()
    size = args.size

    input_path = r"benchmark-instances-{}".format(size) # assume that this directory contains only input samples as .txt files

    if args.solverType == 0:
        run_clingo(input_path)
    else:
        run_cmodels(input_path)


if __name__ == '__main__':
    main()