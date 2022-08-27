type(woman) :- 0 #sum{1,M : order(man,M,X,#sup); -1,W : order(woman,W,X,#sup)}.
type(man)   :- not type(woman).

% OPTIMIZATION

:~ prefer(S,P,X), order(S,P,X,#sup), type(S). [1@1,P]
