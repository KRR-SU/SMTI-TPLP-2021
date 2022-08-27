ranked(S,P,0,X) :- preference(S,P,X), order(S,P,Y,#sup), not prefer(S,P,Y),
                   X <= Z : preference(S,P,Z).
ranked(S,P,X,Y) :- order(S,P,X,Y), ranked(S,P,0,Z), prefer(S,P,X), Y < #sup.

factor(woman, 1) :- 0 #sum{X-Y,M,Y : ranked(man,M,X,Y);
                           Y-X,W,Y : ranked(woman,W,X,Y)}.
factor(woman,-1) :- not factor(woman,1).
factor(man,-F)   :- factor(woman,F).
:- not 0 #sum{F*(Y-X),P,Y : ranked(S,P,X,Y), factor(S,F)}.

% OPTIMIZATION

:~ ranked(S,P,X,Y), factor(S,F). [F*(Y-X)@1,P,Y]
