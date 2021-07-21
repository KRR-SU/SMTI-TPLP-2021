import os
import subprocess
import multiprocessing
import json
import argparse

TIMEOUT_VALUE = 2000 # in seconds

solvers = ['GUROBI', 'LTIU', 'CLINGO', 'CP', 'MIP', 'GA']


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


def solve(root, inputFile, outputFilesPath, dictKey, solverType):
    if solverType == 1:
        cmd = "python3 Gurobi/MILP_Gurobi.py -f {}".format(os.path.join(root, inputFile))
    elif solverType == 2:
        cmd = "python3 LTIU/LTIU.py " + os.path.join(root, inputFile)
    elif solverType == 3:
        cmd = "clingo -V Clingo/smti.lp Clingo/maxcardinality.lp input_ASP.lp --stats"
        ASP_inputConverter(inputFile)
    elif solverType == 4:
        cmd =  "python OR-Tools/OR-Tools_CP-SAT.py " + os.path.join(root, inputFile)
    elif solverType == 5:
        cmd =  "python OR-Tools/OR-Tools_MIP.py " + os.path.join(root, inputFile)
    elif solverType == 6:
        cmd = "python GA/matching_ga.py " + os.path.join(root, inputFile)

    subPro = timeout(func=run_SMTI_Solver, command=cmd, timeoutValue=TIMEOUT_VALUE)

    if subPro is False:  # then the process of gurobi solver is terminated because timeout is being reached
        # print("A process is terminated due to timeout.")
        # Writing the output to the file
        outputFileName = inputFile.replace("input", "output")[:-4] + "_{}.txt".format(solvers[solverType - 1])
        outputFile = open(os.path.join(outputFilesPath, outputFileName), "w")
        outputFile.write("Solver reached to a timeout limit.")
        outputFile.close()

        STATS[solverType][dictKey]["NUMBER_OF_TIMEOUTS_REACHED"] += 1

    else:  # Process is finished. subPro has a value (which has the stdout of the solver)
        # So gurobiSolver will print to console(stdout) ... TotalTime: 112s \n NumberOfExpandedNode: 10 \n ...
        processOutput = subPro.stdout.decode('utf-8')
        # the stdout of gurobi will contain license information in the first 2 lines runtime in 3rd, iteration number in 4th and explored nodes in 5th
        processOutput = processOutput.split("\n", 2)[2]  # Getting rid of Gurobi information in the begining of the output.
        
        # Writing the output to the file
        outputFileName = inputFile.split('/')[1].replace("input", "output")[:-4] + "_{}.txt".format(solvers[solverType - 1])
        outputFile = open(os.path.join(outputFilesPath, outputFileName), "w")
        outputFile.write(processOutput)
        outputFile.close()

def main():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('--solverType', '-sT', metavar='', help='Specify the solver you want to run(default will run them all)', type=int, default=-1, choices=[1, 2, 3, 4, 5, 6])
    # --solverType = 1 -> Gurobi will run
    # --solverType = 2 -> Local Search(LTIU) will run
    # --solverType = 3 -> ASP will run
    # --solverType = 4 -> OR-Tools CP_SAT will run
    # --solverType = 5 -> OR-Tools MIP will run
    # --solverType = 6 -> Genetic Algorithm will run
    # --solverType = -1 -> All of the solvers will run

    argparser.add_argument('--size', '-s', metavar='', help='Specify the size of the benchmark instances', type=int, default=-1, choices=[50,100])
    args = argparser.parse_args()
    selectedSolver = args.solverType
    size = args.size

    PATH_TO_INPUT_FILES = r"benchmark-instances-{}".format(size) # assume that this directory contains only input samples as .txt files
    PATH_TO_OUTPUT_FILES = r"OUTPUT"

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
            
            inputFile = '{}/{}'.format(PATH_TO_INPUT_FILES, inputFile)

            if selectedSolver == -1:
                solve(root, inputFile, PATH_TO_OUTPUT_FILES, Dictionary_Key, 1)
                solve(root, inputFile, PATH_TO_OUTPUT_FILES, Dictionary_Key, 2)
                solve(root, inputFile, PATH_TO_OUTPUT_FILES, Dictionary_Key, 3)
                solve(root, inputFile, PATH_TO_OUTPUT_FILES, Dictionary_Key, 4)
                solve(root, inputFile, PATH_TO_OUTPUT_FILES, Dictionary_Key, 5)
                solve(root, inputFile, PATH_TO_OUTPUT_FILES, Dictionary_Key, 6)
            elif selectedSolver != 6:
                solve(root, inputFile, PATH_TO_OUTPUT_FILES, Dictionary_Key, selectedSolver)
            else:
                try:
                    solve(root, inputFile, PATH_TO_OUTPUT_FILES, Dictionary_Key, 6)
                except:
                    print("A problem occured in file:", inputFile)



if __name__ == '__main__':
    main()

