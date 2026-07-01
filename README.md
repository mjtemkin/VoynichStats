# Voynich Manuscript Statistical Analysis

Computational analysis of the Voynich manuscript using the First Study Group
(FSG) transliteration corpus (~33,600 words, ~88% of the manuscript).

## Authors
Michael Temkin and Claude Sonnet 4.6 (Anthropic)

Note: this project was conducted as a human-AI collaboration. Michael Temkin
directed the analysis and all research decisions; Claude implemented the
statistical tests, generated code, and drafted the write-ups. All methodology
was reviewed and approved by the human author.

## Paper
[voynich_statistical_analysis.pdf](voynich_statistical_analysis.pdf) — typeset
academic-style writeup of all findings, with figures and references.

Also see `SYNTHESIS.md` for the full research narrative.

## Data
`raw_fsg.txt` -- the First Study Group transliteration by Jim Reeds (1994),
from the William F. Friedman Collection, Marshall Library. Retrieved from
voynich.nu. Public domain.

The alphabet used is the FSG alphabet (not identical to Currier's original
alphabet despite historical references to both in the comments).

## How to reproduce

No external dependencies are required for the analysis scripts (Python 3.8+
only). Clone the repo and run from the project root:

```bash
git clone https://github.com/yourname/voynich-analysis
cd voynich-analysis

# Main findings
python3 repetition_test.py             # immediate word-doubling (~2x chance)
python3 word_class_asymmetry.py        # grammar-suggestive ordering structure

# Significance tests (each takes 1-2 minutes)
python3 confidence_check_v2_robust.py  # bootstrap for ordering asymmetry
python3 section_gap_bootstrap.py       # permutation test for section gap

# Cross-language comparison
cd compare && python3 run_stats.py     # entropy/TTR/compression table
```

For the figure and PDF generation (requires matplotlib and reportlab):

```bash
pip install matplotlib reportlab
python3 ../make_figures.py
python3 ../make_paper.py
```

## Scripts (run from the project root directory)
- `parse_fsg.py` -- core parser; all other scripts import from this
- `analyze_ab.py` -- basic Language A vs B descriptive statistics
- `section_test.py` -- section/scribe confound control
- `repetition_test.py` -- immediate word-doubling rate (main finding)
- `expanded_doubling_check.py` -- doubling by section cross-check
- `doubling_mechanism.py` -- positional/lexical breakdown of doubling
- `section_gap_bootstrap.py` -- permutation test for cross-section gap
- `internal_doubling_bootstrap.py` -- bootstrap decomposition of B internal doubling
- `sequential_drift_test.py` -- sliding-window drift analysis
- `local_scramble_test.py` -- line co-membership vs write-order test
- `word_class_asymmetry.py` -- grammatical-style ordering asymmetry test
- `confidence_check_v2_robust.py` -- frequency-matched bootstrap for asymmetry
- `sparse_coding_v3.py` -- sparse dictionary learning on Voynichese
- `substitution_test.py` -- formal simple substitution cipher test
- `compare/` -- comparison corpora (Culpeper English, Carmina Burana Latin,
  Hebrew Genesis/Exodus/Psalms, Arabic Al-Baqarah/Yusuf) and matching scripts

## Key findings (see SYNTHESIS.md for full detail)
1. Immediate word-doubling at ~2x chance in both Currier languages, stationary
   across the manuscript, surviving all genre and mechanism controls.
2. Word-class ordering asymmetry (grammar-suggestive positional structure),
   z > 4.7 in both languages, p < 0.0001, robust to frequency-matching control.

## Cite as

Temkin, M. and Claude Sonnet 4.6 (Anthropic). (2025). Statistical Properties
of the Voynich Manuscript: An Independent Computational Analysis.
GitHub: github.com/yourname/voynich-analysis
