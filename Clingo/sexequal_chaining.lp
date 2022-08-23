mcost(X,R1) :- marry(X,Y), mrank(X,Y,R1).
mcost(X, R1 - 1) :- mcost(X, R1), R1 > 1.

wcost(Y,R2) :- marry(X,Y), wrank(Y,X,R2).
wcost(Y, R2 - 1) :- wcost(Y,R2), R2 > 1.

mcost(T) :- T = #count{1,C,M: mcost(M,C)}.
wcost(T) :- T = #count{1,C,W: wcost(W,C)}.
cost(|T1-T2|) :- mcost(T1), wcost(T2).
cost(T-1) :- cost(T), T > 1.
:~ cost(T), T != 0. [1@1,T]  
