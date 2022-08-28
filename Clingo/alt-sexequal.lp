rankeq(S,P,X) :- range(S,P,X), marry(S,P,X+1).
rankeq(S,P,X) :- range(S,P,X), rankeq(S,P,X+1).

bound(S,Y) :- S = (man;woman), Y = #sum+{X,P : limit(S,P,X+1)}.
total(S,Z) :- bound(S,Y), Z = 1..Y, Z #count{P,X : rankeq(S,P,X)}.

% OPTIMIZATION

:~ total(man,Z), not total(woman,Z). [1@1,Z]
:~ total(woman,Z), not total(man,Z). [1@1,Z]
