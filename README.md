# SMTI
We study a variation of the Stable Marriage problem, where every man and every woman express their preferences as preference lists which may be incomplete and contain ties. This problem is called the Stable Marriage problem with Ties and Incomplete preferences (SMTI).  We consider three optimization variants of SMTI: Max Cardinality, Sex-Equal and Egalitarian. 

We empirically compare the following methods to solve these three hard variants: Answer Set Programming (ASP), Constraint Programming (CP), Integer Linear Programming (ILP). For Max Cardinality, we compare these methods with Local Search methods as well.  We also empirically compare ASP with Propositional Satisfiability, for SMTI instances. 

The experimental setup, evaluation and results are summarized in the following article:

Stable Marriage Problems with Ties and Incomplete Preferences: An Empirical Comparison of ASP, SAT, ILP, CP, and Local Search Methods
Selin Eyupoglu, Muge Fidan, Yavuz Gulesen, Ilayda Begum Izci, Berkan Teber, Baturay Yilmaz, Ahmet Alkan, Esra Erdem 
https://arxiv.org/abs/2108.05165

This repository contains the implementations of ASP, SAT, ILP, CP, and Local Search Methods, and the benchmark instances used in this study.

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
      ```clingo input.lp smti.lp```  
  - For solving optimization variants, specify the logic program of the variant of choice such as: \
     ```clingo input.lp smti.lp maxcardinality.lp```

## Choco

  Under '/Choco' we provide our implementations of the CP model proposed by Gent and Prosser (2002) for Max Card SMTI and the related decision problem.

   * Prerequisites
       - Choco version 4.10.9 must be installed. \
            see: https://github.com/chocoteam/choco-solver/releases
   
   * To run our implementation for decision version, first use the following command\
       ```javac -cp <choco-path> SMTI.java``` where choco-path must be the path to choco jar file.

      then run \
        ```java -cp <choco-path> SMTI input.txt <opt>``` where opt is optional and can be count(counts all models), all(shows all models), if not given finds a model, if one exists, and prints it.
    
   * To run our implementation to solve Max Card SMTI, first use the following command\
      ```javac -cp <choco-path> SMTI_maxcard.java``` where choco-path must be the path to choco jar file.
     then run \
        ```java -cp <choco-path> SMTI_maxcard input.txt```

## Gurobi

Under '/Gurobi' we provide our implementation of the ILP model introduced by Kwanashie and Manlove (2014) to solve Max Card SMTI.  

* Preliminaries <br />
    - gurobipy must be installed.  \
        see: https://www.gurobi.com/documentation/9.1/quickstart_mac/cs_grbpy_the_gurobi_python.html 

* Sample Usage 
    -  For solving Max Cardinality SMTI: \
    ```python3 MILP_Gurobi.py -f input.txt``` 
           

## LTIU

Under '/LTIU' we provide our implementation of the algorithm proposed by Gelain et al. (2013) to solve Max Card SMTI.  

* Sample Usage 
    - For solving Max Cardinality SMTI: \
    ```python3 LTIU.py -f input.txt``` 
           

## GA 

Under '/GA' we provide our implementation of the algorithm proposed by Haas (2020) to solve Max Card SMTI.  

* Sample Usage 
   - To solve Max Cardinality SMTI, run \
    ```python3 matching_ga.py -f input.txt``` 


## OR-Tools 

  Under '/OR-Tools' we provide our implementation of the ILP model proposed by Kwanashie and Manlove (2014) and implementation of our CP model to solve Max Card SMTI.

   * Prerequisites
       - For CP, OR-Tools CP SAT solver must be installed. \
            see: https://developers.google.com/optimization/cp/cp_solver
       - For MIP, pywraplp package must be installed. \
            see: https://google.github.io/or-tools/python/ortools/linear_solver/pywraplp.html 
   
   For both CP and MIP scripts, use -opt to specify optimization variant. 
   -  0(default) : Max Cardinality 
   - 1: Egalitarian
   - 2: Sex-Equal

   * To use CP model, run \
        ```python3 OR-Tools_CP.py -f input.txt -opt <i> ``` where i is the integer specifying the variant.
      
   * To use MIP, run \
        ```python3 OR-Tools_MIP.py -f input.txt -opt <i>``` 

## SAT-E

   We have adapted the SAT formulation introduced by Drummond et al. (2015) to solve SMTI.

   * Prerequisites
      - For SMTI, a SAT solver is required. 
	  - For solving Egalitarian and Sex-Equal SMTI,  a MaxSAT solver is required.

  The environment variable SAT_SOLVER_PATH should be set to the path to the SAT solver.

  * To use SAT-E, run \
      ```python3 smti.py input.txt ``` , 
	   - use --opt=0 for SMTI, --opt=1 for Max Cardinality SMTI and --opt=2 for Egalitarian SMTI
       - Directory name for intermediate files should be specified by -outdir argument.
	   - Output file name should be specified by -o argument. 
           *  First line of the output represents the matching number.
           * 'm 1' reads as 'Matching 1'. 
           * Starting from the second line, each line represents a pair, first id represents the man and second id represents his partner.


## Acknowledgments
 We would like to thank Ian Gent, David Manlove, Andrew Perrault, William Pettersson and Patrick Prosser for useful discussions and suggestions, and sharing their software with us. 
