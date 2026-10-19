# legacy/

`THE_LSA.py` is the original PyTorch script used to produce the figures in the paper, kept unmodified (md5 8428151712e6caa3e930b59f27f495be).

Notes for anyone running or comparing against it:
- It sets `pm = [1,0,1,0,1,0,1]` -- the **alternative** 4 omni / 3 bidirectional array -- even though its comment says "3 omni + 4 bidirectional".
- It uses `c0 = 340`, a 72 x 36 DF grid, and `torch.linalg.pinv(D, rcond=1e-12)`.
- It does not need PyTorch for anything it computes; `src/lsa/` is the NumPy equivalent and matches it (see `tests/`).

Superseded by `src/lsa/` and `scripts/`.
