'''
This file contains the implementation of MILP model for MAX-SMTI problem,
based on the paper "Mathematical models for stable matching problems with ties and incomplete lists"
by Delorme, M., Garcia, S., Gondzio, J., Kalcsics J., Manlove D. & Petterson W.


Last Modified: 15.12.2020 - Baturay Yilmaz
'''
import time
from ortools.sat.python import cp_model
import sys



def GenerateRankList(preferencesInLine):
    # it will get preferences in input file and convert it into a ranked list so that we can put the ranks in the preference list
    result = []

    while len(preferencesInLine) != 0:
        element = preferencesInLine[preferencesInLine.find("(") + 1: preferencesInLine.find(")")]

        # typecasting the preference ID to an int
        element = element.split(" ")
        for i in range(len(element)):
            element[i] = int(element[i])


        result.append(element)

        preferencesInLine = preferencesInLine[preferencesInLine.find(")") + 1:]
    return result

def GetRankInPrefList(preferredPartnerID, PreferenceList):
    # PreferenceList is a 2D list. [[x,y], [z]] denotes that id x and y are the first preference and z is the second
    # preferredPartnerID is the ID that we should check if it exists in the PreferenceList
    # This function will return the rank of the preferredPartnerID in the given PreferenceList, if the preferredPartnerID is not in PreferenceList it will return -1
    for rank in range(len(PreferenceList)):
        for ID in PreferenceList[rank]:
            if ID == preferredPartnerID:
                return rank
    return -1


def main():
    START_TIME = time.time()

    # inputFileName = r"TestInputs/optTest2.txt"
    inputFileName = ""
    if len(sys.argv) == 1:  # in this case there is only sys.argv[0] which the is the name of the python file
        print("No file name supplied! Program will exit!")
        exit()
    else:
        inputFileName = sys.argv[1]

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



    ranklessManList = [[partnerID for rankList in ManList[index] for partnerID in rankList] for index in range(len(ManList))] # List of Man with the preferenceLis without rank. It is a 2D version of ManList
    ranklessWomanList = [[partnerID for rankList in WomanList[index] for partnerID in rankList] for index in range(len(WomanList))]

    # print(ManList)
    # print(ranklessManList)
    # print(WomanList)
    # print(ranklessWomanList)
    # print("\n")


    m = cp_model.CpModel()
    matching = [[m.NewBoolVar(name="[m"+str(mIndex)+"-w"+str(wIndex)+"]") for wIndex in range(numberOfWoman)] for mIndex in range(numberOfMan)]
    sumMan = m.NewIntVar(lb=0, ub=(numberOfWoman*numberOfWoman + 1), name="sumMan")
    sumWoman = m.NewIntVar(lb=0, ub=(numberOfMan*numberOfMan + 1), name="sumWoman")


    # Adding constraints
    # Acceptability constraint from man point of view
    for i in range(0, numberOfMan):  # i is man index, i+1 is the man ID
        ranklessPreferencesOfMan = ranklessManList[i]
        nonPreferredWomanIDs = list(set([i for i in range(1, numberOfWoman+1)]) - set(ranklessPreferencesOfMan)) # woman IDs that are not preferred by man with index i (id i +1)
        for womanID in nonPreferredWomanIDs:
            m.Add(matching[i][womanID - 1] == 0)

    # Acceptability constraint from woman point of view
    for i in range(0, numberOfWoman):  # woman with index i (id i +1)
        renklessPreferencesOfWoman = ranklessWomanList[i]
        nonPreferredManIDs = list(set([i for i in range(1, numberOfMan + 1)]) - set(renklessPreferencesOfWoman))  # man IDs that are not preferred by woman with index i (id i +1)
        for manID in nonPreferredManIDs:
            m.Add(matching[manID - 1][i] == 0)

    # Max matching constraint. Each man or woman should be matched with at most 1 partner
    for i in range(numberOfMan):  # or we could use numberOfWoman does not matter since they are equal
        m.Add(sum(matching[i][:]) <= 1)  # each man can be matched with at most 1 woman
        m.Add(sum([row[i] for row in matching]) <= 1)  # each woman can be matched with at most 1 man
        # [row[i] for row in matching] gets the column with index i

    # Stability Constraint
    for i in range(0, numberOfMan):  # for each man
        preferenceListOfMan = ManList[i]

        for rank in range(len(preferenceListOfMan)):
            for j in preferenceListOfMan[rank]:
                # womanID = j
                womanList = [wID for r in range(rank + 1) for wID in preferenceListOfMan[r]] # list of woman who has same or smaller(better) rank in man with index i's preference list.
                left = 0
                for q in range(len(womanList)):
                    wID = womanList[q]
                    left += matching[i][wID - 1]

                rankOfManIn_j = GetRankInPrefList(i+1, WomanList[j-1])
                if rankOfManIn_j != -1: # Checks if the man with id i+1 is in woman with id j's pref list. if man with id i+1 is not in the list of woman with id j, they cannot be a blocking pair.

                    manList = [mID for r in range(rankOfManIn_j+1) for mID in WomanList[j-1][r]] # list of man who has same or smaller(better) rank in j's(womanID's) preference list
                    right = 0
                    for p in range(len(manList)):
                        mID = manList[p]
                        right += matching[mID - 1][j - 1]
                    m.Add(1 - left <= right)

    # Constraints for Objective
    MAN_SUM = 0
    WOMAN_SUM = 0
    for i in range(0, numberOfMan):
        for j in range(0, numberOfWoman):
            MAN_SUM = MAN_SUM + (GetRankInPrefList(j+1, ManList[i]) * matching[i][j])
            WOMAN_SUM = WOMAN_SUM + (GetRankInPrefList(i+1, WomanList[j]) * matching[i][j])

    m.Add(sumMan == MAN_SUM)
    m.Add(sumWoman == WOMAN_SUM)

    # Objective for Egalitarian matching
    m.Minimize(sumMan + sumWoman)

    solver = cp_model.CpSolver()
    status = solver.Solve(m)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("Execution Time:", time.time() - START_TIME)
        print("Number of Branches:", solver.NumBranches())
        print("Number of Booleans:", solver.NumBooleans())
        print("Number of Conflicts:", solver.NumConflicts())
        print("Objective Value(Egalitarian Cost):", solver.ObjectiveValue(), "\n")
        print('Solution:')
        for i in range(numberOfMan):
            for j in range(numberOfWoman):
                if solver.BooleanValue(matching[i][j]):
                    print("m" + str(i + 1) + "-w" + str(j + 1))
    else:
        print("No solution found.")




if __name__ == '__main__':
    main()


