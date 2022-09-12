import os
import re
import subprocess
import multiprocessing
import json
import argparse

TIMEOUT_VALUE = 2000 # in seconds

solvers = ['GUROBI', 'CLINGO', 'SAT', 'OR-CP-GP', 'OR-CP-KM', 'OR-MIP-KM']
optimization=['egalitarian', 'sexequal']

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

def SAT_inputConverter(inputFile, size):
    output_str=''
    with open(inputFile) as f:
        lines = f.readlines()[3:]
        for line in lines[:size]:
           output_str += 'm ' + line.split()[0] + ' '
           ff = re.findall('\(([\d ]+)\)', line)
           prefs = []
           for f in ff:
               if ' ' in f:
                   prefs.append('{' + f.replace(' ',',') + '}')
               else:
                   prefs.append(f)
           output_str += ' '.join(prefs)
           output_str += '\n'
        for line in lines[size:]:
           output_str += 'w ' + line.split()[0] + ' '
           ff = re.findall('\(([\d ]+)\)', line)
           prefs = []
           for f in ff:
               if ' ' in f:
                   prefs.append('{' + f.replace(' ',',') + '}')
               else:
                   prefs.append(f)
           output_str += ' '.join(prefs)
           output_str += '\n'
    
    f = open('input_SAT.txt', 'w')
    f.write(output_str)
    f.close()


def timeout(func, command, timeoutValue):
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    process = multiprocessing.Process(target=func, args=[command, return_dict])
    process.start()
    process.join(timeout=timeoutValue)

    if process.is_alive(): # TIMEOUT VALUE IS REACHED AND PROCESS IS STILL WORKING
        process.terminate()
        return False
    else: # PROCESS IS FINISHED
        return return_dict.values()[0]


def run_SMTI_Solver(command, return_dict):
    # subPro = subprocess.run(command, shell=True, capture_output=True, text=True)
    subPro = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # return subPro
    return_dict[0] = subPro


def solve(root, inputFile, outputFilesPath, dictKey, size, opt, solverType):
    if solverType == 1:
        cmd = "python3 Gurobi/MILP_Gurobi.py -f {}".format(os.path.join(root, inputFile)) + " --opt={}".format(opt)
    elif solverType == 2:
        if opt == 1:
            # using the best weak constraint
            cmd = "clingo Clingo/smti.lp Clingo/egalitarian_chaining.lp input_ASP.lp --stats"
            ASP_inputConverter(os.path.join(root, inputFile))
        else:
             # using the best weak constraint
            cmd = "clingo Clingo/smti.lp Clingo/sexequal_chaining.lp input_ASP.lp --stats"
            ASP_inputConverter(os.path.join(root, inputFile))
    elif solverType == 3:
        if opt == 1:
            cmd =  "python3 SAT-E/smti.py input_SAT.txt -opt=2 --outdir={}".format(outputFilesPath)
            SAT_inputConverter(os.path.join(root, inputFile), size)
        else:
            print('No SAT formulation to solve Sex Equal SMTI!')
    elif solverType == 4:
        cmd =  "python3 OR-Tools/OR-Tools_CP_GP_opt.py --file " + os.path.join(root, inputFile) + " --opt={}".format(opt)
    elif solverType == 5:
        cmd =  "python3 OR-Tools/OR-Tools_CP.py --file " + os.path.join(root, inputFile) + " --opt={}".format(opt)
    elif solverType == 6:
        cmd =  "python3 OR-Tools/OR-Tools_MIP.py --file " + os.path.join(root, inputFile) + " --opt={}".format(opt)

    subPro = timeout(func=run_SMTI_Solver, command=cmd, timeoutValue=TIMEOUT_VALUE)

    if subPro is False:  # then the process of gurobi solver is terminated because timeout is being reached
        # print("A process is terminated due to timeout.")
        # Writing the output to the file
        outputFileName = inputFile.replace("input", "output")[:-4] + "_{}_{}.txt".format(solvers[solverType - 1], optimization[opt-1])
        outputFile = open(os.path.join(outputFilesPath, outputFileName), "w")
        outputFile.write("Solver reached to a timeout limit.")
        outputFile.close()

    else:  # Process is finished. subPro has a value (which has the stdout of the solver)
        # So gurobiSolver will print to console(stdout) ... TotalTime: 112s \n NumberOfExpandedNode: 10 \n ...
        processOutput = subPro.stdout.decode('utf-8')
        # the stdout of gurobi will contain license information in the first 2 lines runtime in 3rd, iteration number in 4th and explored nodes in 5th
        processOutput = processOutput.split("\n", 2)[2]  # Getting rid of Gurobi information in the begining of the output.
        
        # Writing the output to the file
        outputFileName = inputFile.replace("input", "output")[:-4] + "_{}_{}.txt".format(solvers[solverType - 1], optimization[opt-1])
        outputFile = open(os.path.join(outputFilesPath, outputFileName), "w")
        outputFile.write(processOutput)
        print(outputFileName)
        outputFile.close()

def main():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('--solverType', '-sT', metavar='', help='Specify the solver you want to run(default will run them all)', type=int, default=-1, choices=range(1,9))
    # --solverType = 1 -> Gurobi will run
    # --solverType = 2 -> Clingo will run
    # --solverType = 3 -> SAT will run
    # --solverType = 4 -> OR-Tools CP_SAT (GP) will run
    # --solverType = 5 -> OR-Tools CP_SAT (KM) will run
    # --solverType = 6 -> OR-Tools MIP (KM) will run
    # --solverType = -1 -> All of the solvers will run

    argparser.add_argument('--size', '-s', metavar='', help='Specify the size of the benchmark instances', type=int, default=-1, choices=[50,100])
    argparser.add_argument('--opt', '-o', metavar='', help='Specify the opt. variant to solve: 1 for Egalitarian, 2 for Sex-Equal', type=int, default=1, choices=[1,2])
    
    args = argparser.parse_args()
    selectedSolver = args.solverType
    size = args.size

    PATH_TO_INPUT_FILES = r"benchmark-instances-{}".format(size) # assume that this directory contains only input samples as .txt files
    PATH_TO_OUTPUT_FILES = r"OUTPUT-OPT"

    for root, dirs, files in os.walk(PATH_TO_INPUT_FILES):
        # root is the path of where the search takes place
        # dirs is the list of subdirectories inside the root.
        # files is the list of files inside the root
        # So, (for our case) a directory which contains only .txt files
        #   -> root = PATH_TO_INPUT_FILES
        #   -> dirs = []
        #   -> files = [input1.txt, input2.txt, ....]
        for inputFile in files:
            # # parse the input file to get "instance size", "p1" and "p2" combination in order to obtain the dict key
            instance_size = inputFile[inputFile.find("s-") + 2:inputFile.find("--i")]
            p1 = inputFile[inputFile.find("--i-") + 4:inputFile.find("pc-t")]
            p2 = inputFile[inputFile.find("-t-") + 3:inputFile.find("pc--")]

            Dictionary_Key = instance_size + "_" + p1 + "_" + p2
            if selectedSolver == -1:
                for i in range(1,len(solvers)+1):
                    solve(root, inputFile, PATH_TO_OUTPUT_FILES, Dictionary_Key, int(instance_size), args.opt, i)
            else:
                solve(root, inputFile, PATH_TO_OUTPUT_FILES, Dictionary_Key, int(instance_size),  args.opt, selectedSolver)

if __name__ == '__main__':
    main()

