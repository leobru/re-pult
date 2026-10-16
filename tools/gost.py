# GOST 10859 -> Unicode (Cyrillic variant), from dispak/encoding.c.
G = ('0123456789+-/,. ' '⏨↑()×=;[]*‘’≠<>:'
     'АБВГДЕЖЗИЙКЛМНОП' 'РСТУФХЦЧШЩЫЬЭЮЯD'
     'FGIJLNQRSUVWZ‾⩽⩾' '∨∧⊃¬÷≡%◇|―_!"Ъ°′')

def text(b):
    """Decode GOST bytes; unknown codes as \\ooo."""
    return ''.join(G[c] if c < len(G) else '\\%03o' % c for c in b)
