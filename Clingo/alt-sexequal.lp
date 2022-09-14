different(man,M,woman,W,X,Y,M,W,X,Y) :- acceptable(M,W,X,Y), X != Y.
different(woman,W,man,M,Y,X,M,W,X,Y) :- different(man,M,woman,W,X,Y,M,W,X,Y).

difference(S,P,F,D,M,W,X,Y) :- different(S,P,T,Q,U,V,M,W,X,Y),
                               D = |U-V|, F = (U-V)/D.
difference(S,P,F,D)         :- difference(S,P,F,D,M,W,X,Y).
difference(S,P,F,D)         :- difference(S,P,F,D+1), 0 < D.

divergence(S,I,J,N,M) :- S = (man;woman),
                         I = #count{P,D : difference(S,P, 1,D)},
                         J = #count{P,D : difference(S,P,-1,D)},
                         N = I+J, M = (N+|I-J|)/2.

diff(man)   :- divergence(man,I1,J1,N1,M1), divergence(woman,I2,J2,N2,M2),
               (N1,M1) < (N2,M2).
diff(woman) :- not diff(man).

apply(P,F,D) :- difference(S,P,F,D,M,W,X,Y), diff(S), marry(M,W,X,Y).
apply(P,F,D) :- apply(P,F,D+1), 0 < D.
:- apply(P,1,1), apply(P,-1,1).

apply(K) :- divergence(S,I,J,N,M), diff(S), K = 1..I,
            K #sum{1,P,D : apply(P,1,D); -1,P,D : apply(P,-1,D)}.
apply(K) :- divergence(S,I,J,N,M), diff(S), K = 1..J,
            K #sum{1,P,D : apply(P,-1,D); -1,P,D : apply(P,1,D)}.
:- apply(K), 1 < K, not apply(K-1).

% OPTIMIZATION

:~ apply(K). [1@1,K]
