mancost(M, R1) :- marry(M, W), mrank(M, W, R1).
womancost(M, R2) :- marry(M, W), wrank(W, M, R2).
:~ mancost(M, R1). [R1@1, m, M]
:~ womancost(W, R2). [R2@1, w, W]
