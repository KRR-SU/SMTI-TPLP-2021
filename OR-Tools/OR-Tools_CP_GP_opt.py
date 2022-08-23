import time
from ortools.sat.python import cp_model
import argparse
import os
import numpy as np

def flatten(preflis):
    '''
    flatten the prefence list by breaking ties (preserving the order of the input)
    '''
    li = []
    for el in preflis:
        li.extend([int(x) for x in el.split(' ')])
    return li

class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self, x, y):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.x = x
        self.y = y
        self.__solution_count = 0

    def on_solution_callback(self):
        self.__solution_count += 1

    def solution_count(self):
        return self.__solution_count


class Instance:
    def __init__(self, manList, womanList):
        self.manList = manList
        self.womanList = WomanList
        
        self.numberOfMan = len(manList.keys())
        self.numberOfWoman = len(womanList.keys())

        self.mrank = {}
        self.wrank = {}

        for mIndex in range(1,len(self.manList)+1):
            self.mrank[mIndex] = {}
            for wIndex in range(1, len(self.womanList)+1):
                wmi, wi = self.isWomanInManList(mIndex, wIndex)
                if wmi:
                    self.mrank[mIndex][wIndex] = wi
                else:
                    self.mrank[mIndex][wIndex] = False

        for wIndex in range(1,len(self.womanList)+1):
            self.wrank[wIndex] = {}
            for mIndex in range(1, len(self.manList)+1):
                mwi, mi = self.isManInWomanList(mIndex, wIndex)
                if mwi:
                    self.wrank[wIndex][mIndex] = mi
                else:
                    self.wrank[wIndex][mIndex] = False

    def getAcceptableMenSet(self, womanID):
        ''' checks the acceptable set of woman with wIndex '''
        d = set()
        for el in self.womanList[womanID]:
            for x in el.split(' '):
                d.add(int(x))
        # includes the dummy person that represents being single
        d.add(self.numberOfMan+1)
        return list(d)

    def getAcceptableWomenSet(self, manID):
        ''' checks the acceptable set of man with mIndex '''
        d = set()
        for el in self.manList[manID]:
            for x in el.split(' '):
                d.add(int(x))
        # includes the dummy person that represents being single
        d.add(self.numberOfWoman+1)
        return list(d)

    def nextMan(self, manID, womanID):
        ''' get the next man to manID in the preference list of womanID '''
        plis = self.manList[manID]
        for idx, x in enumerate(plis):
            d = [int(z) for z in x.split(' ')]
            if womanID in d and idx + 1 != len(plis):
                return plis[idx + 1]
        return -1

    def nextWoman(self, manID, womanID):
        ''' get the next woman to womanID in the preference list of manID '''
        plis = self.womanList[womanID]
        for idx, x in enumerate(plis):
            d = [int(z) for z in x.split(' ')]
            if manID in d and idx + 1 != len(plis):
                return plis[idx + 1]
        return -1

    def findNext(self, manID, womanID):
        ''' 
        find next tie group of manID's list to womanID
        find for womanID and return them as a tuple
         '''
        next = self.nextMan(manID, womanID)
        if next == -1:
            b1 = next
        elif len(next.split(' ')) == 1:
            b1 = flatten(self.manList[manID]).index(int(next))
        elif len(next.split(' ')) > 1:
            b1 = flatten(self.manList[manID]).index(int(next.split(' ')[0]))

        next = self.nextWoman(manID, womanID)
        if next == -1:
            b2 = next
        elif len(next.split(' ')) == 1:
            b2 = flatten(self.womanList[womanID]).index(int(next))
        elif len(next.split(' ')) > 1:
            b2 = flatten(self.womanList[womanID]).index(int(next.split(' ')[0]))

        return b1, b2

    def isManInWomanList(self, manID, womanID):
        ''' checks if man with manID is in womanID's list, returns the rank '''
        if manID in self.getAcceptableMenSet(womanID):
            for idx, el in enumerate(self.womanList[womanID]):
                d = [int(x) for x in el.split(' ')]
                if manID in d:
                    return True, idx
        else:
            return False, -1

    def isWomanInManList(self, manID, womanID):
        ''' checks if woman with womanID is in manID's list, returns the rank '''
        if womanID in self.getAcceptableWomenSet(manID):
            for idx, el in enumerate(self.manList[manID]):
                d = [int(x) for x in el.split(' ')]
                if womanID in d:
                    return True, idx
        else:
            return False, -1

    def createModel(self, opt):
        m = cp_model.CpModel()
        x = {}
        y = {}
        # creating variables
        for mIndex in range(1, self.numberOfMan+1):
            x[mIndex] = m.NewIntVarFromDomain(cp_model.Domain.FromValues(self.getAcceptableWomenSet(mIndex)), name='m{}'.format(mIndex))
        for wIndex in range(1, self.numberOfWoman+1):
            y[wIndex] = m.NewIntVarFromDomain(cp_model.Domain.FromValues(self.getAcceptableMenSet(wIndex)), name='w{}'.format(wIndex))

        for mIndex in range(1, self.numberOfMan+1):
            for wIndex in range(1, self.numberOfWoman+1):
                if self.mrank[mIndex][wIndex] is not False and self.wrank[wIndex][mIndex] is not False:
                    # eliminate illegal marriages
                    # vertical
                    mpref = flatten(self.manList[mIndex]) + [self.numberOfWoman+1]
                    wpref = flatten(self.womanList[wIndex]) + [self.numberOfMan+1]
                    updatedi = mpref.index(wIndex)
                    updatedj = wpref.index(mIndex)
                    for k in range(len(mpref)):
                        if k != updatedi:
                            m.AddForbiddenAssignments([x[mIndex], y[wIndex]], [(mpref[k], mIndex)])

                    # horizontal
                    for l in range(len(wpref)):
                        if l != updatedj:
                            m.AddForbiddenAssignments([y[wIndex], x[mIndex]], [(wpref[l], wIndex)])

                    # eliminate blocking pairs
                    # find next elements in the pref lists of i and j
                    b1, b2 = self.findNext(mIndex, wIndex)
                    if b1 == -1:
                        # if there is no next man, take the dummy person
                        b1 = len(mpref) - 1
                    if b2 == -1:
                         # if there is no next woman, take the dummy person
                        b2 = len(wpref) - 1
                    for k in range(b1, len(mpref)):
                        for l in range(b2, len(wpref)):
                            m.AddForbiddenAssignments([y[wIndex], x[mIndex]], [(wpref[l], mpref[k])])
        return m, x, y


def generateRankList(preferencesInLine):
    ''' 
    it will get preferences in input file 
    and convert it into a ranked list so that 
    we can put the ranks in the preference list
    '''
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
    argparser.add_argument('--opt', '-o', metavar='', help='Specify the optimization variant. 0: Max Cardinality, 1: Egalitarian, 2: Sex-Equal', type = int, default=0, choices=[0, 1, 2])
    argparser.add_argument('--output', '-out', metavar='', help='Name of the output file', type = str)
    args = argparser.parse_args()

    start = time.time()

    if not args.file:  # in this case there is only sys.argv[0] which the is the name of the python file
        print("No file name supplied! Program will exit!")
        exit()
    else:
        inputFileName = args.file
    
    if not args.output: 
        print("No output file name supplied!")
        exit()
    else:
        outputFileName = args.output

    f = open(inputFileName, "r")  # Read the input file
    lines = f.readlines()
    f.close()

    numberOfMan = int(lines[1])
    numberOfWoman = int(lines[2])

    ManList = {} # np.empty(numberOfMan, dtype=object)
    WomanList = {} # np.empty(numberOfWoman, dtype=object)

    for i in range(3, 3 + numberOfMan):
        line = lines[i]  # line = "ID Preferences"
        line = line.replace("\n", "")  # getting rid of \n character at the end of the line
        line = line.rstrip()  # getting rid of whitepace at the end of the line
        line = line.split(" ", 1)  # line = [ID, Preferences]
        id = int(line[0])  # this is the id of man or woman

        preferenceList = generateRankList(line[1])  

        # preferenceList will have a value ['x y z'] or ['x', 'y', 'z'] or ['x y', 'z']. 
        ManList[id] = preferenceList

    for i in range(3 + numberOfMan, 3 + numberOfMan + numberOfWoman):
        line = lines[i]  # line = "ID Preferences"
        line = line.replace("\n", "")  # getting rid of \n character at the end of the line
        line = line.rstrip()  # getting rid of whitepace at the end of the line
        line = line.split(" ", 1)  # line = [ID, Preferences]
        id = int(line[0])  # this is the id of man or woman

        preferenceList = generateRankList(line[1])  # line[1] is the rest of the line and it has the form "(x y z)" or "(x) (y) (z)" or "(x y) (z)" ...
        
        # preferenceList will have a value ['x y z'] or ['x', 'y', 'z'] or ['x y', 'z']. Each of this ids in indices of this list will be their rank in preference list
        WomanList[id] = preferenceList

    inst = Instance(ManList, WomanList)
    model, x, y = inst.createModel(args.opt)

    opt = ['maxcard','egalitarian','sexequal']
    if args.opt == 0:
        #max card
        mm_vars = [model.NewBoolVar('mm{}'.format(mIndex)) for mIndex in range(1,numberOfMan+1)]
        for i, mvar in enumerate(mm_vars):
            # ensure mvar for man x_i is true iff x_i is not single
            model.Add(x[i+1] <= numberOfWoman).OnlyEnforceIf(mvar) 
            model.Add(x[i+1] > numberOfWoman).OnlyEnforceIf(mvar.Not())
        model.Maximize(sum(mm_vars))
    elif args.opt == 1:
        #egalitarian
        costs = []
        for mIndex in range(1, inst.numberOfMan + 1):
            for wIndex in range(1, inst.numberOfWoman + 1):
                if inst.mrank[mIndex][wIndex] is not False and inst.wrank[wIndex][mIndex] is not False:
                    b = model.NewBoolVar(str(mIndex) + '-' + str(wIndex))
                    cost = model.NewIntVar(0, 2*inst.numberOfMan + 1, 'cost' + str(mIndex) + '-' + str(wIndex))
                    # ensure b_ij is true if and only if x_i and y_j are married 
                    model.Add(x[mIndex] == wIndex).OnlyEnforceIf(b) 
                    model.Add(x[mIndex] != wIndex).OnlyEnforceIf(b.Not())
                    # cost for x_i and y_j is 0 if they are not married, else it is equal to the sum of ranks 
                    # that they give to each other
                    model.Add(cost == 0).OnlyEnforceIf(b.Not())
                    model.Add(cost == (inst.mrank[mIndex][wIndex] + inst.wrank[wIndex][mIndex])).OnlyEnforceIf(b)
                    costs.append(cost)
        # minimize total cost
        model.Minimize(sum(costs))
    elif args.opt == 2:
        #sex-equal
        mcosts = []
        wcosts = []
        z = model.NewIntVar(0, 500, 'z')
        for mIndex in range(1, inst.numberOfMan + 1):
            for wIndex in range(1, inst.numberOfWoman + 1):
                if inst.mrank[mIndex][wIndex] is not False and inst.wrank[wIndex][mIndex] is not False:
                    b = model.NewBoolVar(str(mIndex) + '-' + str(wIndex))
                    mcost = model.NewIntVar(0,inst.numberOfWoman, 'mcost' + str(mIndex))
                    wcost = model.NewIntVar(0,inst.numberOfMan, 'wcost' + str(wIndex))
                    # ensure b_ij is true if and only if x_i and y_j are married
                    model.Add(x[mIndex] == wIndex).OnlyEnforceIf(b) 
                    model.Add(x[mIndex] != wIndex).OnlyEnforceIf(b.Not())
                    # ensure mcost for the pair (x_i,y_j) equals to the mrank(x_i, y_j)
                    model.Add(mcost == 0).OnlyEnforceIf(b.Not())
                    model.Add(mcost == (inst.mrank[mIndex][wIndex])).OnlyEnforceIf(b)
                    # ensure wcost for the pair (x_i,y_j) equals to the wrank(y_j, x_i)
                    model.Add(wcost == 0).OnlyEnforceIf(b.Not())
                    model.Add(wcost == (inst.wrank[wIndex][mIndex])).OnlyEnforceIf(b)
                    mcosts.append(mcost)
                    wcosts.append(wcost)
        # ensure z equals to |sum of mcosts - sum of wcosts|
        model.Add(z >= (sum(mcosts) - sum(wcosts)))
        model.Add(z >= -(sum(mcosts) - sum(wcosts)))
        # finally minimize the abs value
        model.Minimize(z)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    c = SolutionPrinter(x, y)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        with open(outputFileName, 'w') as f:
            f.write("Execution Time: {}\n".format(time.time() - start))
            f.write("Number of Branches: {}\n".format(solver.NumBranches()))
            f.write("Number of Booleans: {}\n".format(solver.NumBooleans()))
            f.write("Number of Conflicts: {}\n".format(solver.NumConflicts()))
            if args.opt == 0: 
                f.write("Objective Value(Max Card): {}\n".format(solver.ObjectiveValue()))
            elif args.opt == 1:
                f.write("Objective Value(Egalitarian): {}\n".format(solver.ObjectiveValue()))
            else:
                f.write("Objective Value(Sex Equal): {}\n".format(solver.ObjectiveValue()))
            f.write('Solution:\n')
            f.write('\n'.join(["m-{}: w-{}".format(i, str(solver.Value(x[i]))) for i in range(1, numberOfMan+1)]))
    else:
        with open(outputFileName, 'w') as f:
            f.write("No solution found.")


if __name__ == '__main__':
    main()
