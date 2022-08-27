ranked(S,P,0,X) :- preference(S,P,X), order(S,P,Y,#sup), not prefer(S,P,Y),
                   X <= Z : preference(S,P,Z).
ranked(S,P,X,Y) :- order(S,P,X,Y), ranked(S,P,0,Z), prefer(S,P,X), Y < #sup.

% OPTIMIZATION

:~ ranked(S,P,X,Y). [Y-X@1,S,P,Y]
