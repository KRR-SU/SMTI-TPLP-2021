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
        self.womanList = womanList
        self.pc_sum = 0
        self.log_sum = 0
        self.numberOfMan = len(manList.keys())
        self.numberOfWoman = len(womanList.keys())

    def getAcceptableMenSet(self, womanID):
        ''' checks the acceptable set of woman with wIndex '''
        d = set()
        for el in self.womanList[womanID]:
            for x in el.split(' '):
                d.add(int(x))
        return list(d)

    def getAcceptableWomenSet(self, manID):
        ''' checks the acceptable set of man with mIndex '''
        d = set()
        for el in self.manList[manID]:
            for x in el.split(' '):
                d.add(int(x))
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

    def createModel(self):
        m = cp_model.CpModel()
        x = {}
        y = {}
        # creating variables
        for mIndex in range(1, self.numberOfMan+1):
            x[mIndex] = m.NewIntVarFromDomain(cp_model.Domain.FromValues(self.getAcceptableWomenSet(mIndex)), name='m{}'.format(mIndex))
            self.log_sum += round(np.log2(len(self.getAcceptableWomenSet(mIndex))),5)
        for wIndex in range(1, self.numberOfWoman+1):
            y[wIndex] = m.NewIntVarFromDomain(cp_model.Domain.FromValues(self.getAcceptableMenSet(wIndex)), name='w{}'.format(wIndex))
            self.log_sum += round(np.log2(len(self.getAcceptableMenSet(wIndex))),5)
        for mIndex in range(1, self.numberOfMan+1):
            for wIndex in range(1, self.numberOfWoman+1):
                mwi, i = self.isWomanInManList(mIndex, wIndex)
                wmi, j = self.isManInWomanList(mIndex, wIndex)
                if mwi and wmi:
                    # eliminate illegal marriages
                    # vertical
                    mpref = flatten(self.manList[mIndex])
                    wpref = flatten(self.womanList[wIndex])
                    updatedi = mpref.index(wIndex)
                    updatedj = wpref.index(mIndex)
                    # constrainedness value for pair (x_i,y_j)
                    pc = round(np.log2(1 - 1 / (len(mpref) * len(wpref))),5)
                    for k in range(len(mpref)):
                        if k != updatedi:
                            self.pc_sum += pc
                            m.AddForbiddenAssignments([x[mIndex], y[wIndex]], [(mpref[k], mIndex)])

                    # horizontal
                    for l in range(len(wpref)):
                        if l != updatedj:
                            self.pc_sum += pc
                            m.AddForbiddenAssignments([y[wIndex], x[mIndex]], [(wpref[l], wIndex)])

                    # eliminate blocking pairs
                    # find next elements in the pref lists of i and j
                    b1, b2 = self.findNext(mIndex, wIndex)
                    if b1 != -1 and b2 != -1:
                        for k in range(b1, len(mpref)):
                            for l in range(b2, len(wpref)):
                                self.pc_sum += pc
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
    argparser.add_argument('--output', '-out', metavar='', help='Name of the output file', type = str)
    args = argparser.parse_args()

    start = time.time()

    if not args.file:
        print("No input file name supplied!")
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

    i = Instance(ManList, WomanList)
    model, x, y = i.createModel()
    kappa = -1 * (i.pc_sum)/(i.log_sum)
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    c = SolutionPrinter(x, y)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        with open(outputFileName, 'w') as f:
            f.write('Constrainedness: {}\n'.format(round(kappa,3)))
            f.write("Execution Time: {}\n".format(time.time() - start))
            f.write("Number of Branches: {}\n".format(solver.NumBranches()))
            f.write("Number of Conflicts: {}\n".format(solver.NumConflicts()))
            f.write("Number of Booleans: {}\n".format(solver.NumBooleans()))
            f.write('Solution:\n')
            f.write('\n'.join(["m-{}: w-{}".format(i, str(solver.Value(x[i]))) for i in range(1, numberOfMan+1)]))
    else:
        with open(outputFileName, 'w') as f:
            f.write('Constrainedness: {}\n'.format(round(kappa,3)))
            f.write("Execution Time: {}\n".format(time.time() - start))
            f.write("Number of Branches: {}\n".format(solver.NumBranches()))
            f.write("Number of Conflicts: {}\n".format(solver.NumConflicts()))
            f.write("No solution found.")


if __name__ == '__main__':
    main()
