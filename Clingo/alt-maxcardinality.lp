type(woman) :- 0 #sum{1,M : limit(man,M,X); -1,W : limit(woman,W,X)}.
type(man)   :- not type(woman).

% OPTIMIZATION

:~ prefer(S,P,X), limit(S,P,X), type(S). [1@1,P]
