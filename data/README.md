# data/

- `expected_results.csv` -- output of this repository's code (regenerate with `python scripts/reproduce_all.py --write-expected`). The test suite and CI compare against it.
- `reference_digitized.csv` -- values read off the published figure (EUSIPCO 2025, Fig. 6, LSA at 0 degrees). **Empty template.** Add one row per digitised point with the columns in the header; `scripts/reproduce_all.py` then reports the mean absolute errors automatically. Record the digitisation tool and date so the readings can be audited. The published PDF is not redistributed here.
- Exact numbers printed in the EUSIPCO text (Eq. 39 and 41) are hard-coded in `src/lsa/reference.py` and are used as the strict check for the alternative array.
