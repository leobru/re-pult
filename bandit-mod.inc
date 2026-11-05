* MOD: GET data path with reversed copying and block writes.
MODBEG сч key
        по MNOKEY
        мод base
        уиа (М16)
MFIND  сч (М16)
        по notfnd
        нтж key
        по MFOUND
        мода MFIND
        цикл (М16)
MFOUND сч 1(М16)
        зп curdsc
        мода MFIRST
        уиа (М5)
        пб rdelt
MNOKEY call getelt,(М5)
MFIRST сч mylen
        по MSKIP
        мод adata
        сч
        и E15T1
        вчоб mylen
        пе toolng
MSKIP  сч adata
        слц E1
        зп adata
        сч itmlen
        вч E1
        зп itmlen
MNEXT  уи М16
        счи М16
        по MWRITE
MCOPY  мод myloc
        сч -1(М16)
        мод adata
        зп -1(М16)
        слиа -1(М16)
        пино MCOPY,(М16)
MWRITE сч curbuf
        сда 64-20
        или curzon
        слц nuzzzz
        зп ИСЭ70
        Э70 ИСЭ70
        сч myloc
        слц itmlen
        зп myloc
        сч chain
        и E40T21
        по rtexit
        сда 64+20
        мода MNEXT
        уиа (М5)
        пб rdelt
MODEND пам 385-MODEND+MODBEG
