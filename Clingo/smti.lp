% DEFINE

% man M prefers W to being single
maccept(M, W) :- man(M), woman(W), mrank(M, W, R).

% woman W prefers man M to being single
waccept(W, M) :- man(M), woman(W), wrank(W, M, R).

% acceptability
acceptable(M, W) :- maccept(M, W), waccept(W, M).

% GENERATE 

% generate matching
{marry(M, W) : woman(W), acceptable(M, W)}1 :- man(M).
:- {marry(M, W) : man(M)} > 1, woman(W).

% singles
msingle(M) :- man(M), {marry(M, W) : woman(W)}0.
wsingle(W) :- woman(W), {marry(M, W) : man(M)}0.

% man M prefers woman W1 to woman W2.
mprefer(M, W1, W2) :- mrank(M, W1, R1), mrank(M, W2, R2), R1 < R2.

% woman W prefers man M1 to man M2.
wprefer(W, M1, M2) :- wrank(W, M1, R1), wrank(W, M2, R2), R1 < R2.

% TEST

% M1 and W2 form a blocking pair.
:- man(M1; M2), woman(W1; W2), marry(M1, W1), marry(M2, W2),
                    mprefer(M1, W2, W1), wprefer(W2, M1, M2).

% M and W2 form a blocking pair.
:- man(M), woman(W1; W2), marry(M, W1), wsingle(W2), 
                          acceptable(M, W2), mprefer(M, W2, W1).

% M1 and W2 form a blocking pair.
:- man(M1; M2), woman(W), marry(M1, W), msingle(M2), 
                          acceptable(M2, W), wprefer(W, M2, M1).

% M and W form a blocking pair.
:- man(M), woman(W), msingle(M), wsingle(W), acceptable(M, W).

% SHOW

#show marry/2.
#show msingle/1.
#show wsingle/1.