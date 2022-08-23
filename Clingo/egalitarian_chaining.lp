mcost(X,R1) :- marry(X,Y), mrank(X,Y,R1).
mcost(X, R1 - 1) :- mcost(X, R1), R1 > 1.

wcost(Y,R2) :- marry(X,Y), wrank(Y,X,R2).
wcost(Y, R2 - 1) :- wcost(Y,R2), R2 > 1.

:~ mcost(X,C). [1@1, m, X, C]
:~ wcost(Y,C). [1@1, w, Y, C]

