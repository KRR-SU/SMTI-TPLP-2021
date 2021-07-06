% GENERATE

% M prefers F to single
m2single(M, F) :- man(M), woman(F), mrank(M, F, X).

% F prefers M to single
w2single(F, M) :- man(M), woman(F), wrank(F, M, X).

% acceptability
acceptable(M,F) :- m2single(M, F), w2single(F, M).

msingle(M) :- man(M), {marry(M, W) : woman(W)}0.
wsingle(W) :- woman(W), {marry(M, W) : man(M)}0.

{marry(M,F) : woman(F), acceptable(M,F)}1 :- man(M).
:- {marry(M, F) : man(M)} > 1, woman(F).

% DEFINE

% M prefers DF to CF.
mprefer(M, DF, CF) :- mrank(M, CF, CUR), mrank(M, DF, DEV), DEV < CUR.

% F prefers DM to CM.
wprefer(F, DM, CM) :- wrank(F, CM, CUR), wrank(F, DM, DEV),  DEV < CUR.

% TEST

% it is assumed that marriage to an acceptable partner is preferred over being single

% m1-f1, m2-f2 -- m1 and f2 block
:- man(M1; M2), woman(F1; F2), marry(M1, F1), marry(M2, F2), mprefer(M1, F2, F1), wprefer(F2, M1, M2).

% m-f1, f2 single -- m and f2 block
:- man(M), woman(F1; F2), marry(M, F1), wsingle(F2), acceptable(M,F2), mprefer(M, F2, F1).

% m1-f, m2 single -- m2 and f block
:- man(M1; M2), woman(F), marry(M1, F), msingle(M2), acceptable(M2,F), wprefer(F, M2, M1).

% m, f single -- m and f block
:- man(M), woman(F), msingle(M), wsingle(F), acceptable(M,F).

% SHOW

#show marry/2.
#show msingle/1.
#show wsingle/1.
