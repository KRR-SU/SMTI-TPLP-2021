m2single(M, F) :- man(M), woman(F), mrank(M, F, X).

w2single(F, M) :- man(M), woman(F), wrank(F, M, X).

acceptable(M,F) :- m2single(M, F), w2single(F, M).

%{marry(M,W) : woman(W),acceptable(M,W)}1 :- man(M).
{marry(M,W)}1 :- acceptable(M,W).

% :- {marry(M, W) : man(M)} > 1, woman(W).

:- 2{marry(M,W):woman(W)},man(M).
:- 2{marry(M,W):man(M)}, woman(W).

msingle(M) :- {marry(M,W):woman(W)}0, man(M).
wsingle(W) :- {marry(M,W):man(M)}0, woman(W).

mprefer(M, DF, CF) :- mrank(M, CF, CUR), mrank(M, DF, DEV), DEV < CUR.
wprefer(F, DM, CM) :- wrank(F, CM, CUR), wrank(F, DM, DEV),  DEV < CUR.

:- man(M1; M2), woman(F1; F2), marry(M1, F1), marry(M2, F2), mprefer(M1, F2, F1), wprefer(F2, M1, M2).
:- man(M), woman(F1; F2), marry(M, F1), wsingle(F2), acceptable(M,F2), mprefer(M, F2, F1).
:- man(M1; M2), woman(F), marry(M1, F), msingle(M2), acceptable(M2,F), wprefer(F, M2, M1).
:- man(M), woman(F), msingle(M), wsingle(F), acceptable(M,F).

