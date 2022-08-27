acceptable(M,W,X,Y) :- mrank(M,W,X), wrank(W,M,Y).

preference(man,M,X)   :- acceptable(M,W,X,Y).
preference(woman,W,Y) :- acceptable(M,W,X,Y).

order(S,P,X,Y)    :- preference(S,P,X), preference(S,P,Y), X < Y,
                     Z <= X : preference(S,P,Z), Z < Y.
order(S,P,X,#sup) :- preference(S,P,X),
                     Z <= X : preference(S,P,Z).

msticky(M)          :- msticky(M,K).
sticky(M,K)         :- msticky(M,K).
sticky(M,0)         :- order(man,M,X,#sup), not msticky(M).
sticky(M,K,J)       :- sticky(M,K), I = (K-1+|K+1|)/2, J = (I-|I|)/2.
sticky(M,X,X,|K|)   :- preference(man,M,X), sticky(M,K).
sticky(M,X,Y,0)     :- sticky(M,X,Y,K), order(man,M,Y,#sup).
sticky(M,X,Y,0)     :- sticky(M,X,Y,Z,K,-1).
sticky(M,X,Z,K)     :- sticky(M,X,Y,Z,K,0).
sticky(M,X,Y,Z,K)   :- sticky(M,X,Y,K), order(man,M,Y,Z), 0 < K, Z < #sup.
sticky(M,X,Y,Z,K,J) :- sticky(M,X,Y,Z,L), K = L+Y-Z,
                       I = (K-1+|K+1|)/2, J = (I-|I|)/2.
sticks(M,A,B)       :- sticky(M,X,Y,0), sticky(M,K,J), X-Y <= K,
                       I = J+1, A = I*X-J*Y, B = I*Y-J*X.

{marry(M,W,X,Y) : acceptable(M,W,X,Y)} 1 :- order(man,M,Z,#sup).
{marry(M,W,X,Y) : acceptable(M,W,X,Y)} 1 :- order(woman,W,Z,#sup).
marry(man,M,X)   :- marry(M,W,X,Y).
marry(woman,W,Y) :- marry(M,W,X,Y).
marry(S,P)       :- marry(S,P,X).

prefer(S,P,X) :- order(S,P,X,Y), marry(S,P,Y).
prefer(S,P,X) :- order(S,P,X,#sup), not marry(S,P).
prefer(S,P,X) :- order(S,P,X,Y), prefer(S,P,Y).
:- acceptable(M,W,X,Y), prefer(woman,W,Y), prefer(man,M,Z) : sticks(M,X,Z).

#show.
#show marry(M,W) : marry(M,W,X,Y).
#show msingle(M) : prefer(man,M,X), order(man,M,X,#sup).
#show wsingle(W) : prefer(woman,W,X), order(woman,W,X,#sup).
