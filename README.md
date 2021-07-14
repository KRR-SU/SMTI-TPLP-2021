# SMTI
We provide implementations of ILP, CP, ASP and Local Search approaches to solve Stable Marriage with ties and incomplete lists(SMTI), and its optimization variants, and benchmark instances with n=50 and n=100.

## Input format

To use Gurobi, LTIU, GA and OR-Tools for solving an SMTI instance, the input file should be of the following form.
  - First line is reserved for the beginning of file which should be 0.
  - Second line is reserved for number of men.
  - Third line is reserved for number of women. 
  - Starting from the 4th line, men's preferences are specified at each line:
      * First element in the line is reserved for the id of the men whose preferences are given.
      * Followed by a single space, the preference list is given in the corresponding order.
      * Elements of the preference list are specified as a tie group of women(or a woman) between brackets.

      e.g. 1 (2 3) (1) represents that man 1 is indifferent between woman 2 and 3 and prefers them over woman 1.

  - After men's preferences, women's preferences should be specified.

Example: \
  0                    
  2         -> two men  
  2         -> two women  
  1 (1) (2) -> man 1 prefers woman 1 over 2   \
  2 (2 1)   -> man 2 is indifferent between woman 1 and 2  \
  1 (1) (2) -> woman 1 prefers woman 1 over 2   \
  2 (2) (1) -> woman 2 prefers woman 2 over 1    

  For Clingo the input file should be a .lp file which contains atoms that represents the instance.
 
  Given an SMTI instance,
  *  For each man with identifier x, 'man(x).'
  *  For each woman with identifier y, 'woman(y).'
  *  For each man x, if he ranks the woman y as his rth partner , 'mrank(x,y,r).'
  *  For each woman y, if she ranks the man x as his rth partner , 'wrank(y,x,r).'

 Referring to the previous example, the corresponding .lp file would contain:

 man(1).man(2). \
 woman(1).woman(2). \
 mrank(1,1,1).mrank(1,2,2). \
 mrank(2,1,1).mrank(2,2,1). \
 wrank(1,1,1).wrank(1,2,2). \
 wrank(2,2,1).wrank(2,1,2).


## Clingo

Under '/Clingo' directory we provide logic programs that solve SMTI (smti.lp) and its optimization variants (maxcardinality.lp, sexequal.lp, egalitarian.lp).

* Preliminaries <br />
     - clingo must be installed. Experiments were done with version 5.2.2. \
    see: https://github.com/potassco/clingo 

* Sample Usage 
    - For solving an SMTI problem: \
      ``` clingo input.lp smti.lp ```  
  - For solving optimization variants, specify the logic program of the variant of choice such as: \
     ``` clingo input.lp smti.lp maxcardinality.lp``` 

## Gurobi

Under '/Gurobi' we provide our ILP implementation to solve Max Card SMTI.  

* Preliminaries <br />
    - gurobipy must be installed.  \
        see:https://www.gurobi.com/documentation/9.1/quickstart_mac/cs_grbpy_the_gurobi_python.html 

* Sample Usage 
    -  For solving Max Cardinality SMTI: \
    ``` python3 MILP_Gurobi.py -f input.txt ``` 
           

## LTIU

Under '/LTIU' we provide our ILP implementation to solve Max Card SMTI.  

* Sample Usage 
    - For solving Max Cardinality SMTI: \
    ``` python3 LTIU.py -f input.txt ``` 
           

## GA 

Under '/GA' we provide our ILP implementation to solve Max Card SMTI.  

* Sample Usage 
   - For solving Max Cardinality SMTI:  
    ``` python3 matching_ga.py -f input.txt ``` 
           
## OR-Tools 
   * Prerequisites
       - For CP, OR-Tools CP SAT solver must be installed. \
            see: https://developers.google.com/optimization/cp/cp_solver
       - For MIP, pywraplp package must be installed. \
            see: https://google.github.io/or-tools/python/ortools/linear_solver/pywraplp.html 
   
   For both CP and MIP scripts, use -opt to specify optimization variant. 
   -  0(default) : Max Cardinality 
   - 1: Egalitarian
   - 2: Sex-Equal

   * To use CP model,  \
        ``` python3 OR-Tools_CP.py -f input.txt -opt <i> ``` where i is the integer specifying the variant.
      
   * To use MIP, \
      ``` python3 OR-Tools_MIP.py -f input.txt -opt <i>``` 