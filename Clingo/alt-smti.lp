acceptable(M,W,X,Y) :- mrank(M,W,X), wrank(W,M,Y).

preference(man,M,X)   :- acceptable(M,W,X,Y).
preference(woman,W,Y) :- acceptable(M,W,X,Y).

range(S,P,X) :- preference(S,P,X).
range(S,P,X) :- range(S,P,X+1), 0 < X.
limit(S,P,X) :- range(S,P,X), not range(S,P,X+1).

msticky(M)    :- msticky(M,K).
sticky(M,K)   :- msticky(M,K).
sticky(M,0)   :- limit(man,M,X), not msticky(M).
sticky(M,X,Z) :- preference(man,M,X), limit(man,M,Y), sticky(M,K),
                 L = K+X, Z = (L+Y-|L-Y|)/2, 0 < Z.

{marry(M,W,X,Y) : acceptable(M,W,X,Y)} 1 :- limit(man,M,Z).
{marry(M,W,X,Y) : acceptable(M,W,X,Y)} 1 :- limit(woman,W,Z).
marry(man,M,X)   :- marry(M,W,X,Y).
marry(woman,W,Y) :- marry(M,W,X,Y).
marry(S,P)       :- marry(S,P,X).

prefer(S,P,X) :- range(S,P,X), marry(S,P,X+1).
prefer(S,P,X) :- limit(S,P,X), not marry(S,P).
prefer(S,P,X) :- range(S,P,X), prefer(S,P,X+1).
:- acceptable(M,W,X,Y), prefer(woman,W,Y), prefer(man,M,Z) : sticky(M,X,Z).

#show.
#show marry(M,W) : marry(M,W,X,Y).
#show msingle(M) : prefer(man,M,X), limit(man,M,X).
#show wsingle(W) : prefer(woman,W,X), limit(woman,W,X).
