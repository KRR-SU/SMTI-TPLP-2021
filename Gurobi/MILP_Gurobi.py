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


class PreferenceListNode:
    def __init__(self, rank, partnerID):
        self.rank = rank
        self.partnerID = partnerID  # ID of opposite gender

    def __str__(self):
        return str(self.rank) + "-" + str(self.partnerID)

    __repr__ = __str__


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


def isManInWomanList(manID, womanID, WomanList):
    womanPreferences = WomanList[womanID - 1]
    for i in range(0, len(womanPreferences)):
        preferredManID = womanPreferences[i].partnerID
        if preferredManID == manID:
            return True, i

    return False, -1


def isWomanInManList(womanID, manID, ManList):
    manPreferences = ManList[manID - 1]
    for i in range(0, len(manPreferences)):
        preferredWomanID = manPreferences[i].partnerID
        if preferredWomanID == womanID:
            return True, i

    return False, -1


def generateWomanListWithRank(manID, womanID, ManList):
    # PRECONDITION: womanID should be in the preference list of manID
    # returns the ids of women who has less or equal rank with the womanID in manID's preference list.
    result = []
    manPreferences = ManList[manID - 1]
    rankToCompare = -1
    for i in range(0, len(manPreferences)):
        preferredWomanID = manPreferences[i].partnerID
        if preferredWomanID == womanID:
            rankToCompare = manPreferences[i].rank
            break
    for i in range(0, len(manPreferences)):
        if manPreferences[i].rank <= rankToCompare:
            result.append(manPreferences[i].partnerID)

    return result


def generateManListWithRank(manID, womanID, WomanList):
    # PRECONDITION: manID should be in the preference list of womanID
    # returns the ids of men who has less or equal rank with the manID in womanID's preference list.
    result = []
    womanPreferences = WomanList[womanID - 1]
    rankToCompare = -1
    for i in range(0, len(womanPreferences)):
        preferredManID = womanPreferences[i].partnerID
        if preferredManID == manID:
            rankToCompare = womanPreferences[i].rank
            break
    for i in range(0, len(womanPreferences)):
        if womanPreferences[i].rank <= rankToCompare:
            result.append(womanPreferences[i].partnerID)

    return result


def generateMutuallyUnwantedPairs(ManList, WomanList, numberOfMan, numberOfWoman):
    # this will return a list which will contain man and woman ids if they dont want each other
    result = []
    for i in range(0, numberOfMan):
        for j in range(0, numberOfWoman):
            if isManInWomanList(i + 1, j + 1, WomanList)[0] == False and isWomanInManList(j + 1, i + 1, ManList)[
                0] == False:
                result.append([i + 1, j + 1])

    return result


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--file', '-f', metavar='', help='Input file name', type = str)
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

    for i in range(3, 3 + numberOfMan):
        line = lines[i]  # line = "ID Preferences"
        line = line.replace("\n", "")  # getting rid of \n character at the end of the line
        line = line.rstrip()  # getting rid of whitepace at the end of the line
        line = line.split(" ", 1)  # line = [ID, Preferences]
        id = int(line[0])  # this is the id of man or woman

        rankList = GenerateRankList(line[1])  # line[1] is the rest of the line and it has the form "(x y z)" or "(x) (y) (z)" or "(x y) (z)" ...
        # rankList will have a value ['x y z'] or ['x', 'y', 'z'] or ['x y', 'z']. Each of this ids in indices of this list will be their rank in preference list
        preferenceList = []

        for j in range(0, len(rankList)):
            preferences = rankList[j].split(" ")  # getting each id of the same rank.

            for k in range(0, len(preferences)):
                node = PreferenceListNode(rank=j, partnerID=int(preferences[k]))
                preferenceList.append(node)

        ManList[id - 1] = preferenceList

    for i in range(3 + numberOfMan, 3 + numberOfMan + numberOfWoman):
        line = lines[i]  # line = "ID Preferences"
        line = line.replace("\n", "")  # getting rid of \n character at the end of the line
        line = line.rstrip()  # getting rid of whitepace at the end of the line
        line = line.split(" ", 1)  # line = [ID, Preferences]
        id = int(line[0])  # this is the id of man or woman

        rankList = GenerateRankList(line[1])  # line[1] is the rest of the line and it has the form "(x y z)" or "(x) (y) (z)" or "(x y) (z)" ...
        # rankList will have a value ['x y z'] or ['x', 'y', 'z'] or ['x y', 'z']. Each of this ids in indices of this list will be their rank in preference list
        preferenceList = []

        for j in range(0, len(rankList)):
            preferences = rankList[j].split(" ")  # getting each id of the same rank.

            for k in range(0, len(preferences)):
                node = PreferenceListNode(rank=j, partnerID=int(preferences[k]))
                preferenceList.append(node)

        WomanList[id - 1] = preferenceList

    # print(ManList)
    # print("\n")
    # print(WomanList)
    # print("\n")

    try:
        # CREATE EMPTY MODEL
        m = gp.Model("MAX-SMTI")

        # ADD VARIABLES THAT WILL BE USED IN OPTIMIZING
        matching = m.addMVar((numberOfMan, numberOfWoman), vtype=GRB.BINARY, name="matching")

        # SET OBJECTIVE FUNCTION
        m.setObjective(matching.sum(), GRB.MAXIMIZE)

        # ADD CONSTRAINTS
        # pairs should be acceptable
        # acceptability constraint from man point of view. man wants the woman but woman does not want that man
        for i in range(0, numberOfMan):  # i is man index, i+1 is the man ID
            preferencesOfMan = ManList[i]  # list of nodes.
            for j in range(0, len(preferencesOfMan)):
                womanID = preferencesOfMan[j].partnerID
                if not isManInWomanList(i + 1, womanID, WomanList)[0]:  # gets the bool value, index of that man is not required
                    # print("man " + str(i + 1) + " is not in woman " + str(womanID))
                    m.addConstr(matching[i, womanID - 1] == 0,
                                name="Acceptable pair: man" + str(i + 1) + " with woman " + str(womanID))

        # acceptability constraint from woman point of view. woman wants the man but man does not want that woman
        for i in range(0, numberOfWoman):
            preferencesOfWoman = WomanList[i]
            for j in range(0, len(preferencesOfWoman)):
                manID = preferencesOfWoman[j].partnerID
                if not isWomanInManList(i + 1, manID, ManList)[0]:
                    # print("man " + str(manID) + " does not contain woman " + str(i+1))
                    m.addConstr(matching[manID - 1, i] == 0,
                                name="Acceptable pair: woman " + str(i + 1) + " with man " + str(manID))

        # acceptability constraint. when no one wants each other. i.e, man does not want that woman and that woman does not want that man
        unwantedList = generateMutuallyUnwantedPairs(ManList, WomanList, numberOfMan, numberOfWoman)
        for i in range(0, len(unwantedList)):
            manID = unwantedList[i][0]
            womanID = unwantedList[i][1]
            m.addConstr(matching[manID - 1, womanID - 1] == 0,
                        name="Acceptable pair: woman " + str(womanID) + " with man " + str(manID))

        # man or woman cannot be matched multiple times
        for i in range(numberOfMan):  # or we could use numberOfWoman does not matter since they are equal
            m.addConstr(matching[i, :].sum() <= 1,
                        name="rowMan" + str(i))  # each man can be matched with at most 1 woman
            m.addConstr(matching[:, i].sum() <= 1,
                        name="colWoman" + str(i))  # each woman can be matched with at most 1 man

        # stability constraint
        for i in range(0, numberOfMan):  # for each man
            preferencesOfMan = ManList[i]
            for j in range(0, len(preferencesOfMan)):
                womanID = preferencesOfMan[j].partnerID
                womanList = generateWomanListWithRank(i + 1, womanID,ManList)  # list of woman who has same or smaller(better) rank in i's preference list.

                left = 0
                for q in range(0, len(womanList)):
                    wID = womanList[q]
                    left += matching[i, wID - 1]

                if isManInWomanList(i + 1, womanID, WomanList)[0]:  # if man is not in woman's preference list than that pair cannot block.
                    manList = generateManListWithRank(i + 1, womanID,
                                                      WomanList)  # list of man who has same or smaller(better) rank in j's(womanID's) preference list

                    right = 0
                    for p in range(0, len(manList)):
                        mID = manList[p]
                        right += matching[mID - 1, womanID - 1]

                    m.addConstr(1 - left <= right, name="stability constraint")

        # m.setParam(GRB.Param.PoolSolutions, 10)  # Limit how many solutions to collect. Default value of this is 10.
        # m.setParam(GRB.Param.PoolSearchMode, 2)  # do a systematic search for the k-best solutions

        m.setParam(GRB.Param.OutputFlag, 0) # get rid of the output printed by gurobi
        # m.setParam(GRB.Param.TimeLimit, 5)
        # m.setParam(GRB.Param.LogFile, "asd.txt")  # writes the output generated by gurobi to a file given as parameter

        # OPTIMIZE
        m.optimize()
        print("Run time:", time.time() - START_TIME)
        print("Number of iterations:", m.IterCount) # Number of simplex iterations performed in most recent optimization
        # print("Number of nodes explored:", m.NodeCount) # Number of branch-and-cut nodes explored in most recent optimization
        print("Number of non-zero coefficients in constraint matrix:", m.NumNZs)  # NumConstrs = Number of linear constraints | NumNZs = Number of non-zero coefficients in the constraint matrix


        # print("\nModel Runtime for Optimization: ", m.Runtime, "\n")

        # m.write('output.lp')

        # nSolutions = m.SolCount
        # print("\nNumber of solutions found: " + str(nSolutions) + "\n")
        # # PRINTING ALL SOLUTIONS
        # for a in range(0, nSolutions):
        #     print("--------------")
        #     print("Solution - " + str(a+1))
        #     m.setParam(GRB.Param.SolutionNumber, a)
        #     print("Matching Matrix:")
        #     print(matching.Xn)
        #     print("Max Cardinality: %g" % m.objVal)
        #
        #     print("\nSOLUTION:")
        #     for i in range(0, numberOfMan):
        #         for j in range(0, numberOfWoman):
        #             if matching.Xn[i, j] == 1:
        #                 print("m" + str(i+1) + "-" + "w" + str(j+1))

        # PRINTING SINGLE SOLUTION
        # print("\n\nMatching Matrix:")
        # print(matching.X)
        print('\nMax Cardinality: %g' % m.objVal)

        print("\n\n--------------------------------------------------\nSOLUTION:")
        for i in range(0, numberOfMan):
            for j in range(0, numberOfWoman):
                if matching.X[i, j] == 1:
                    print("m" + str(i + 1) + " - " + "w" + str(j + 1))








    except gp.GurobiError as e:
        print('Error code ' + str(e.errno) + ": " + str(e))

    except AttributeError:
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

