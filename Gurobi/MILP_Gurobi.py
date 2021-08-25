'''
This file contains the implementation of MILP model for MAX-SMTI problem,
based on the paper "Mathematical models for stable matching problems with ties and incomplete lists"
by Delorme, M., Garcia, S., Gondzio, J., Kalcsics J., Manlove D. & Petterson W.


Last Modified: 5.11.2020 - Baturay Yilmaz
'''
import numpy as np
import gurobipy as gp
from gurobipy import GRB
import time
import sys
import argparse


class Instance:
    def __init__(self, manList, womanList):
        self.manList = [None] * len(manList)
        
        for idx, m in enumerate(manList):
            rank = 1
            lw = {}
            for key in m:
                lw[rank] = [int(el) for el in key.split(' ')]
                rank += 1
            self.manList[idx] = lw
        
        self.womanList = [None] * len(womanList)

        for idx, m in enumerate(womanList):
            rank = 1
            lw = {}
            for key in m:
                lw[rank] = [int(el) for el in key.split(' ')]
                rank += 1
            self.womanList[idx] = lw

        self.numberOfMan = len(manList)
        self.numberOfWoman = len(womanList)

    def isManInWomanList(self, manID, womanID):
        womanPreferences = self.womanList[womanID - 1]
        for key in womanPreferences:
            if manID in womanPreferences[key]:
                return True, key

        return False, 0

    def isWomanInManList(self, manID, womanID):
        manPreferences = self.manList[manID - 1]
        for key in manPreferences:
            if womanID in manPreferences[key]:
                return True, key

        return False, 0
        

    def createModel(self, opt):
        # CREATE EMPTY MODEL
        m = gp.Model("MAX-SMTI")

        # ADD VARIABLES THAT WILL BE USED IN OPTIMIZING
        #matching = m.addMVar((self.numberOfMan, self.numberOfWoman), vtype=GRB.BINARY, name="matching")
        matching = [[m.addVar(vtype=GRB.BINARY, name="[m" + str(mIndex) + "-w" + str(wIndex) + "]") for wIndex in range(self.numberOfWoman)] for mIndex in range(self.numberOfMan)]
        

        # ADD CONSTRAINTS
        for i in range(self.numberOfMan):
            for k in range(self.numberOfWoman):
                mlis = [item for sl in list(self.manList[i].values()) for item in sl]
                wlis = [item for sl in list(self.womanList[k].values()) for item in sl]
                if (k+1 not in mlis) or (i+1 not in wlis):
                    m.addConstr(matching[i][k] == 0)

        # # man or woman cannot be matched multiple times
        for i in range(self.numberOfMan):  # or we could use numberOfWoman does not matter since they are equal
             m.addConstr(sum(matching[i][:]) <= 1,
                         name="rowMan" + str(i))  # each man can be matched with at most 1 woman
             m.addConstr(sum([row[i] for row in matching]) <= 1,
                         name="colWoman" + str(i))  # each woman can be matched with at most 1 man

        # # stability constraint
        for i in range(self.numberOfMan):  # for each man
            preferencesOfMan = self.manList[i]
            for j in preferencesOfMan:
                for k in preferencesOfMan[j]:
                    womanList = [preferencesOfMan[m] for m in preferencesOfMan if m <= j]  # list of woman who has same or smaller(better) rank in i's preference list.
                    flat_woman_list = [item for sl in womanList for item in sl]
                    left = sum([matching[i][wID - 1] for wID in flat_woman_list])
                    if self.isManInWomanList(i + 1, k)[0]:  # if man is not in woman's preference list than that pair cannot block.
                        manList = [self.womanList[k-1][m] for m in self.womanList[k-1] if m <= self.isManInWomanList(i + 1, k)[1]]  # list of woman who has same or smaller(better) rank in i's preference list.
                        flat_man_list = [item for sl in manList for item in sl]
                        right = sum([matching[mID - 1][k - 1] for mID in flat_man_list])
                        #print(self.isManInWomanList(i + 1, k)[1])
                        m.addConstr(1 - left <= right, name="stability constraint")
        
        if opt == 0:
           # Max Cardinality
            m.setObjective(sum([item for ls in matching for item in ls]), GRB.MAXIMIZE)
           #solver.Maximize(sum(matching[i][j] for i in range(numberOfMan) for j in range(numberOfWoman)))
        elif opt == 1:
            # Egalitarian
            m.setObjective(sum(matching[i][j] * (self.isWomanInManList(i+1, j+1)[1] + self.isManInWomanList(i+1, j+1)[1]) for i in range(self.numberOfMan) for j in range(self.numberOfWoman)), GRB.MINIMIZE)
        elif opt == 2:
            # Sex Equal
            z = m.addVar(0, 500, name='z')
            m.addConstr(z >= sum(matching[i][j] * self.isWomanInManList(i+1, j+1)[1] for i in range(self.numberOfMan) for j in range(self.numberOfWoman)) - sum(matching[i][j] * self.isManInWomanList(i+1, j+1)[1] for i in range(self.numberOfMan) for j in range(self.numberOfWoman)))
            m.addConstr(z >= -(sum(matching[i][j] * self.isWomanInManList(i+1,j+1)[1] for i in range(self.numberOfMan) for j in range(self.numberOfWoman)) - sum(matching[i][j] * self.isManInWomanList(i+1, j+1)[1] for i in range(self.numberOfMan) for j in range(self.numberOfWoman))))
            m.setObjective(z, GRB.MINIMIZE)

        # m.setParam(GRB.Param.PoolSolutions, 10)  # Limit how many solutions to collect. Default value of this is 10.
        # m.setParam(GRB.Param.PoolSearchMode, 2)  # do a systematic search for the k-best solutions

        m.setParam(GRB.Param.OutputFlag, 0) # get rid of the output printed by gurobi
        # m.setParam(GRB.Param.TimeLimit, 5)
        # m.setParam(GRB.Param.LogFile, "asd.txt")  # writes the output generated by gurobi to a file given as parameter
        return m, matching

def GenerateRankList(preferencesInLine):
    # it will get preferences in input file and convert it into a ranked list so that we can put the ranks in the preference list
    result = []

    while len(preferencesInLine) != 0:
        leftPar = "("
        rightPar = ")"

        element = preferencesInLine[preferencesInLine.find(leftPar) + 1: preferencesInLine.find(rightPar)]
        result.append(element)

        preferencesInLine = preferencesInLine[preferencesInLine.find(rightPar) + 1:]
    return result

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--file', '-f', metavar='', help='Input file name', type = str)
    argparser.add_argument('--opt', '-o', metavar='', help='Optimization variant', type = int)
    args = argparser.parse_args()

    START_TIME = time.time()

    # inputFileName = r"TestInputs/input14.txt"
    inputFileName = ""
    if not args.file:  # in this case there is only sys.argv[0] which the is the name of the python file
        print("No file name supplied! Program will exit!")
        exit()
    else:
        inputFileName = args.file

    f = open(inputFileName, "r")  # Read the input file
    lines = f.readlines()
    f.close()

    numberOfMan = int(lines[1])
    numberOfWoman = int(lines[2])

    ManList = [None] * numberOfMan  # np.empty(numberOfMan, dtype=object)
    WomanList = [None] * numberOfWoman  # np.empty(numberOfWoman, dtype=object)
    start = time.time()
    for i in range(3, 3 + numberOfMan):
        line = lines[i]  # line = "ID Preferences"
        line = line.replace("\n", "")  # getting rid of \n character at the end of the line
        line = line.rstrip()  # getting rid of whitepace at the end of the line
        line = line.split(" ", 1)  # line = [ID, Preferences]
        id = int(line[0])  # this is the id of man or woman

        preferenceList = GenerateRankList(line[1])  # line[1] is the rest of the line and it has the form "(x y z)" or "(x) (y) (z)" or "(x y) (z)" ...
        # rankList will have a value ['x y z'] or ['x', 'y', 'z'] or ['x y', 'z']. Each of this ids in indices of this list will be their rank in preference list

        ManList[id - 1] = preferenceList

    for i in range(3 + numberOfMan, 3 + numberOfMan + numberOfWoman):
        line = lines[i]  # line = "ID Preferences"
        line = line.replace("\n", "")  # getting rid of \n character at the end of the line
        line = line.rstrip()  # getting rid of whitepace at the end of the line
        line = line.split(" ", 1)  # line = [ID, Preferences]
        id = int(line[0])  # this is the id of man or woman

        preferenceList = GenerateRankList(line[1])  # line[1] is the rest of the line and it has the form "(x y z)" or "(x) (y) (z)" or "(x y) (z)" ...
        # rankList will have a value ['x y z'] or ['x', 'y', 'z'] or ['x y', 'z']. Each of this ids in indices of this list will be their rank in preference list

        WomanList[id - 1] = preferenceList

    try:
        i = Instance(ManList, WomanList)
        m,matching = i.createModel(args.opt)
        m.optimize()
        end = time.time()
        print('Run time:' + str(end-start))

        # PRINTING SINGLE SOLUTION
        print("\n\nMatching Matrix:")
        # print(matching.X)
        print('\nOpt value: %g' % m.objVal)
        print("\n\n--------------------------------------------------\nSOLUTION:")
        for i in range(0, numberOfMan):
             for j in range(0, numberOfWoman):
                 if matching[i][j].x == 1:
                     print("m" + str(i + 1) + " - " + "w" + str(j + 1))






    except gp.GurobiError as e:
        print('Error code ' + str(e.errno) + ": " + str(e))

    except AttributeError as e:
        print(e)
        print('Encountered an attribute error')



if __name__ == '__main__':
    main()

    # import cProfile
    # import pstats
    #
    # cProfile.run('main()', "output.dat")
    #
    # with open("output_time.txt", "w") as f:
    #     p = pstats.Stats("output.dat", stream=f)
    #     p.sort_stats("cumtime").print_stats()

