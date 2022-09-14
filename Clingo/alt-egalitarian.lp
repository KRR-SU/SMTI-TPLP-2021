ranked(S,P,X) :- marry(S,P,X).
ranked(S,P,X) :- range(S,P,X), ranked(S,P,X+1).

% OPTIMIZATION

:~ ranked(S,P,X). [1@1,S,P,X]
