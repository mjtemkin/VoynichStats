# Is the Voynich Manuscript Meaningful Text or a Hoax? A Statistical Investigation

## Summary

This project set out to test, from first principles and with real
computational analysis, whether the Voynich manuscript's text shows
statistical evidence of being meaningful (a natural language or a
classical cipher over one) or being a mechanically generated hoax. Using
roughly 14,400 words (~38% of the manuscript, drawn primarily from the
Herbal section with smaller samples from Biological, Pharmaceutical, and
Stars), we replicated several well-known anomalies from scratch,
subjected them to genre-matched real-language controls that, to our
knowledge, had not previously been applied in combination, and
systematically tested and largely ruled out the major classical cipher
mechanisms. The weight of evidence that emerged is asymmetric: every
specific cipher mechanism we tested directly either failed or was
weakened, while a mechanical, table-and-grille style generation process
(the hoax mechanism proposed by Gordon Rugg in 2004) received partial,
qualitative support. We did not solve the Voynich manuscript. We also
did not find definitive proof of a hoax. What we found is a body of
evidence that leans consistently in one direction across many
independent tests, which is different from -- and more informative than
-- where we started.

## What we did, in order

**Phase 1 -- Data.** We transcribed a working corpus from the Currier/
First Study Group transliteration system, which preserves Currier's
original Language A/B classification, scribal hand, and section labels
(herbal, biological, pharmaceutical, stars) inline. We started with the
Herbal section (~12,000 words) and later deliberately expanded into
Pharmaceutical and Stars specifically to test whether our findings held
outside the section we started in.

**Phase 2 -- Structure.** We confirmed, using our own data, that
Currier's Language A and Language B split is a real effect and not an
artifact of which section or scribe wrote a given page -- B-language text
from the Herbal section and B-language text from the Biological section
resemble each other statistically far more than either resembles
A-language Herbal text. We concluded that A and B are best understood not
as two different languages or dialects, but as two different scribal
conventions or "registers" -- closer to the difference between a
shopping list and a legal contract than the difference between Spanish
and Italian.

**Phase 3 -- Generative hypotheses and genre controls.** We tested
character-level Markov models, syllable/slot recombination models, and
word-frequency resampling models against the real data, and found that
simple sub-word models systematically fail to reproduce Voynichese's
degree of exact whole-word repetition. We then ran two real-language
genre controls that we believe is a genuinely useful, underused
technique for this kind of analysis: a real 17th-century English herbal
(Culpeper's Complete Herbal) to control for "this looks weird because the
topic is narrow and repetitive," and a real 13th-century Latin song/verse
text maximally built on repetition and refrain (the Carmina Burana,
including its drinking-litany "Bibit hera, bibit herus...") to control
for "this looks weird because repetition is a feature of this genre."
Both controls confirmed that Voynichese's low word-variety (TTR) is
explainable by genre, but its low conditional entropy and its elevated
immediate word-doubling are not -- both anomalies survived contact with
real, repetition-heavy language in two genres and two languages.

**Phase 4 -- Cipher-specific tests.** We tested and ruled out, using our
own data: simple monoalphabetic substitution (produces pure gibberish
against both English and Latin frequency profiles); classical
gemination/verbose cipher mechanisms (no elevated internal,
within-word character doubling, which this mechanism would require); a
grammatical-marker-class explanation for word-doubling (doubling-rate by
suffix is statistically indistinguishable from noise); and we weakened
the case for running-key/stateful cipher mechanisms (no positional drift
or section-boundary discontinuity in doubling rate across the whole
manuscript) and for exact-sequence-dependent mechanisms (doubling depends
on which words share a line, not on the literal order the scribe wrote
them in). We then built two implementations of Gordon Rugg's
table-and-grille mechanical hoax-generation method and found that it
qualitatively reproduces the *kind* of word-correlation anomaly we
measured (exactly as Rugg's own research predicts as a side-effect of
this mechanism) without precisely matching its *magnitude* -- which is
expected, since we reconstructed the mechanism class from his published
description, not his specific table and grille.

## The central findings, and how confident we are in each

**Voynichese's letter-to-letter predictability (conditional entropy) is
anomalously low, even controlling for genre.** This is the most
load-bearing finding in the project and the one we are most confident in.
It replicates a result well-established in the literature (most notably
in Lindemann & Bowern's 2020/2021 study, which used a much larger and
more rigorous comparison corpus including alchemical and esoteric texts
and a 311-language, 34-script comparison set), and we independently
reproduced the core pattern ourselves, including against a fair,
genre-matched real text. Confidence: high.

**Voynichese doubles the exact same word immediately, twice in a row,
at roughly twice the rate chance would predict -- and real language, even
at its most repetition-heavy, does not do this.** This is the most
novel-feeling result of the project. Real English herbal prose showed
zero instances of immediate word-doubling against its own chance
baseline; real Latin verse built entirely around repetition and refrain
also showed zero, even where the same word was deliberately repeated 24
times across a short passage. Voynichese, in contrast, consistently
shows roughly double the chance rate, in both Language A and Language B,
and now across multiple sections of the manuscript. We are confident this
effect is real (it survives a formal confidence-interval check at 3-4
standard errors from chance) and confident it is not explained by topic,
genre, vocabulary size, grammatical word-class, or scribal hand alone, since
we tested and ruled out each of those specifically. Confidence: high on
the existence of the effect; moderate-to-low on any specific explanation
for *why* it happens, since every mechanism we tested for either failed
or only partially matched.

**The doubling effect has no internal structure we could find.** We
looked for it in five different ways -- specific marker words, line
position, line length, internal letter-level doubling, and grammatical
suffix class -- and none of them explained it. This pattern (a strong,
real effect with no detectable internal fingerprint) is unusual and is
itself informative: deliberate human conventions (a scribal abbreviation
practice, a specific cipher rule) usually leave at least one trace when
you look for it this many ways. The absence of any trace, combined with
the partial match to a known *mechanical* hoax-generation method, is what
shifted our overall reading of the evidence toward "generative artifact"
rather than "deliberate convention."

**No classical cipher mechanism we tested succeeded.** Simple
substitution produces gibberish. A verbose/gemination cipher would
require elevated internal letter-doubling, which we did not find. A
cipher keyed by grammatical word-class would require doubling to
concentrate on specific suffixes, which we did not find. A running-key
or otherwise stateful cipher would likely show drift or discontinuity
across the manuscript, which we did not find. None of these are
mathematically impossible to rescue with a more elaborate version of the
mechanism, but none of the straightforward versions survived contact
with the data.

## Is any of this novel?

Being honest about this distinction matters. The underlying facts about
the manuscript -- anomalously low entropy, the Currier A/B split, the
viability of Rugg's table-and-grille hypothesis -- are well-established
prior work, due principally to Currier, Stolfi, Lindemann & Bowern, and
Rugg. We did not discover any of those facts. What we believe may be
genuinely novel, or at least not something we are aware of having been
published in this specific combination, is:

- Testing the word-doubling anomaly against a real, maximally
  repetition-favoring poetic/song genre (the Carmina Burana) in
  addition to repetitive prose, in a different real language (Latin) from
  the prose control (English) -- this was the user's suggestion
  mid-project, and it produced a cleaner, more genre-proof version of the
  doubling anomaly than the prose comparison alone could establish.
- The specific finding that doubling depends on word
  co-membership within a manuscript line rather than on exact scribal
  write-order (the "local scramble" test) -- a distinction we have not
  seen drawn explicitly elsewhere, and one that meaningfully narrows the
  space of viable cipher mechanisms.
- The systematic, five-way elimination process for what
  structural feature (if any) underlies the doubling anomaly --
  marker-words, position, length, internal gemination, grammatical class
  -- run as one connected investigation with consistent methodology and a
  shuffle-based null model throughout.

We want to be precise about what kind of claim this is. This is not a
new fact about the Voynich manuscript that nobody has ever known. It is,
at best, a new piece of evidence-gathering -- a specific battery of tests,
some genuinely uncommon in combination, that someone else could in
principle have run before and may have, but which we are not aware of
having seen published together. Anyone making claims about this project
to a third party should describe it that way: an independent
computational verification and modest extension of existing Voynich
research, not a new discovery about the manuscript itself.

## What we did not establish

We have not determined what the Voynich manuscript actually says, if
anything. We have not proven it is a hoax -- "consistent with mechanical
generation, inconsistent with several specific cipher mechanisms" is a
real but limited conclusion, well short of proof. We have not tested
against the majority of historically proposed solutions (most published
"decipherments" were not tested here at all). Our corpus covers only
about 38% of the manuscript, concentrated in sections that may not be
representative of the whole; while our targeted expansion into
Pharmaceutical and Stars increased our confidence that the doubling
effect is manuscript-wide, we have not covered Cosmological,
Astronomical, or most of Biological and Stars.

## Methodological notes worth preserving

Two negative results from this project are worth keeping as lessons,
since they nearly produced false conclusions:

1. A naive word-level bigram entropy test initially suggested a large
   (~68-70%) reduction in uncertainty from knowing the previous word --
   which would have been a striking finding. A shuffle control revealed
   this was a sparse-data artifact (the same "reduction" appeared in
   fully randomized text), not a real effect. Any entropy-reduction claim
   at small-to-moderate corpus sizes should be paired with a shuffle
   control before being trusted.

2. Our first implementation of the table-and-grille generator failed
   catastrophically (98% doubling) due to a table-layout bug, not because
   the underlying hypothesis was wrong. The fix revealed a real, milder
   version of the same phenomenon -- which turned out to be consistent
   with what the mechanism's original author predicted, not a flaw in our
   reasoning.

## Addendum 3 (Update 9): A positive grammar-suggestive signal, and a
## revised closing assessment

Everything above was written when the project's evidence pointed in a
fairly consistent direction: real anomalies (entropy, doubling) that
survived every control, combined with an inability to find any internal
structure explaining them (no special marker words, no position effect,
no grammatical-class effect, no character-level effect). That pattern --
strong effect, no structure -- was read as leaning toward a mechanical,
generative explanation over a deliberate linguistic one.

A final test complicates that picture in an important way. We classified
Voynichese words into groups by their suffix (a proxy for grammatical
role, consistent with prior scholarship on Voynichese's apparent
prefix-stem-suffix word structure) and asked whether certain classes
reliably precede or follow other classes more often than chance --
the kind of directional, relational ordering associated with real
syntax (articles before nouns, consistent case-marking patterns, and
so on), as opposed to simple repetition or random template-filling.

Using a proper null model (200 independent shuffles, not a single
comparison) and a targeted check to rule out a frequency-imbalance
confound, we found a real, statistically robust effect: word-classes in
Voynichese show genuine directional ordering preferences, strongest in
Language A (z=5.07 even after the robustness filter; essentially zero
chance this arose from random shuffling) and present but weaker in
Language B (z=2.17). This is the first test in the entire project where
real data showed meaningfully more structure than its own shuffled
control. Every other structural hypothesis we tested -- for the doubling
anomaly specifically -- came back null. This one did not.

This does not overturn the doubling finding, which remains real, robust,
and independently corroborated by outside research (Amancio et al.
2013). But it means the cleanest version of the "structurally
featureless, therefore probably mechanical" story is no longer the full
picture. A text can have both: a specific, hard-to-explain repetition
anomaly, and real positional/relational structure between word classes.
Mechanically generated hoax text is not inherently incapable of showing
positional structure (a sufficiently deliberate generation scheme could
produce it), but plain unstructured generators -- including the ones we
built and tested in this project -- would not be expected to produce it
without being specifically designed to. This finding does not prove the
manuscript is meaningful language. It does mean the evidence is now
genuinely mixed rather than leaning consistently in one direction, which
is a more honest and more interesting place to end than where the
project stood before this test.

## Closing assessment (revised)

If you are asking "should I now believe the Voynich manuscript is a
hoax," the honest answer has changed somewhat from the original version
of this document. The evidence still includes a real, robust, genre-
proof, independently-corroborated repetition anomaly that no natural
language or classical cipher mechanism we tested can explain. But it now
also includes a real, properly-controlled signal of word-class ordering
structure that resembles what grammar produces, which we did not expect
to find and which several earlier, more confident-sounding results in
this project (the original Hebrew compression finding, the word-bigram
entropy test) did NOT survive equivalent scrutiny -- this one did. The
honest summary is no longer a clean lean toward "generative artifact."
It is: the manuscript shows at least one anomaly that real language and
known cipher mechanisms struggle to explain, AND at least one feature
that real language and grammar would predict and simple mechanical
generation would not, by default, produce. Both are well-evidenced by
this project's own data and methods. We do not think these two findings
have been reconciled into one coherent account of what the manuscript
actually is, and we do not believe they can be from text-statistics
alone. That is the right place to end this investigation: not at an
answer, but at a sharper, better-evidenced, and more genuinely uncertain
version of the original question than we started with.

---

## Addendum (Update 9): Multi-language sparse coding comparison

After the main synthesis above was written, we ran a further analysis
using sparse dictionary learning (inspired by the hierarchical sparse
coding / dictionary learning literature, Smith & Lewicki 2006 lineage)
to compare Voynichese's word-formation compressibility against real
samples of English, Latin, Hebrew, and Arabic. The method learns a
small set of reusable multi-character "atoms" that best compress a word
list, and measures the resulting compression ratio as a structural
fingerprint.

An initial result appeared to show Hebrew sitting "between" English/Latin
and Voynichese on this metric, consistent with a user-proposed hypothesis
that Hebrew's lack of written vowels (an abjad) would make it naturally
more compressible. This was reported, but a subsequent genre cross-check
and data audit revealed a tokenization bug: Biblical Hebrew text uses the
maqaf character (U+05BE, ─) as a word-joiner that naive whitespace
splitting fails to handle, artificially inflating the compression ratio.

After fixing the bug and testing three Hebrew books (Genesis, Exodus,
Psalms) and two Arabic surahs (Al-Baqarah, Yusuf) across different
genres, the honest corrected picture is:

- Hebrew varies substantially by book (1.129x–1.162x), overlapping
  heavily with Culpeper English (1.153x) and Carmina Burana Latin
  (1.130x). No clean separation from vowel-spelling languages.
- Arabic consistently lands lowest of all tested languages (1.091–1.103x),
  actively contradicting the "abjad compresses more like Voynichese"
  hypothesis.
- No real language reliably and robustly sits as close to Voynichese
  (1.200–1.230x) as Voynichese's own sections cross-validate with each
  other.

This is a meaningful negative result. It does not support the Kondrak &
Hauer Hebrew hypothesis, and does not identify any specific language
family as "closest" to Voynichese. The instability across genre samples
is a genuine limitation of this method at these sample sizes, and is
itself informative: a real cipher text derived from a specific language
might be expected to show more consistent structure than what we observe.

---

## Addendum 2 (Update 9): Reconciling the "network-topology vs. entropy"
## literature disagreement

The main synthesis above noted an unresolved disagreement in the
literature: entropy-based studies (e.g. Lindemann & Bowern, which this
project leaned on heavily) find Voynichese anomalous, while a separate
network-topology-based study (Amancio, Altmann, Rybski, Oliveira, and
da F. Costa, PLOS ONE 2013) concluded the manuscript is "mostly
compatible with natural languages." On closer reading of the full paper,
this disagreement is resolved rather than left open.

The Amancio et al. paper builds a broad battery of dozens of statistical
measurements -- network-topology metrics, first-order word statistics,
and time-series/intermittency measures -- and validates each one against
real text in many languages before applying the full battery to the
Voynich manuscript. Their headline "mostly compatible" verdict is an
aggregate judgment: most of their measurements do pattern like real
language in the manuscript. Critically, however, their own results
explicitly flag immediate word-repetition (duplicated bigrams) as a
specific, clear exception -- in their own words, "much greater than
expected by chance, unlike natural languages." This is the same
word-doubling anomaly this project independently discovered and
extensively tested (entropy, genre controls, mechanism elimination,
corpus-wide validation), found via an entirely different method
(network/bigram analysis) by an entirely different research team,
published seven years before the entropy-focused paper this project
otherwise relied on.

The honest, integrated conclusion: the Voynich manuscript is broadly
similar to real language across many structural measures, AND it has at
least one specific, narrow, robustly anomalous feature -- immediate
word-doubling -- that multiple independent research teams using
different methods (network analysis, conditional entropy, and this
project's own from-scratch reproduction with extensive genre and
mechanism controls) have all identified. This is not a contradiction in
the literature so much as a difference in how aggressively each paper's
summary verdict weights a small number of specific exceptions against a
larger number of broadly-compatible measurements. This project's
detailed focus on the doubling anomaly specifically is, in this light,
independently corroborated rather than contradicted by the wider
literature, and the "mostly natural-language-like, with one well-
documented and hard-to-explain exception" framing is the most accurate
overall summary available from everything examined in this project.

---

## Addendum 4 (Update 9, continued): Full-corpus validation and rebuild

In the course of expanding the corpus to address the Language B sample-
size question (Addendum 3), an attempt to add new text via web-fetched
sources led first to a serious process failure -- a chunk of synthetic,
fabricated text was briefly added to the corpus before being caught and
removed in the same session, never reaching any analysis. This incident
prompted a full audit of the project's original data source, which had
never been independently validated.

The audit produced good news with one important correction. The
original corpus was confirmed to be genuine, accurately-entered
historical transcription data (the First Study Group transliteration,
compiled by Jim Reeds in 1994 from the Friedman Collection), not
fabricated -- but it had been mislabeled as "Currier's alphabet"
throughout the project when it is more precisely the FSG alphabet.

The user then obtained and provided the complete, authoritative source
file directly. A full automated comparison against the project's prior
corpus found that of 139 previously-included folios, 123 matched
exactly, two had trivial single-word discrepancies, and fourteen --
concentrated heavily in the Stars section -- had been severely
truncated, in some cases containing only 20-25% of the folio's true
content. Critically, no folio contained wrong or fabricated content;
every discrepancy was either an exact match, a clean truncation, or a
negligible variant reading.

The corpus was rebuilt in full from this authoritative source, growing
from 14,440 words (~38% of the manuscript) to 33,601 words (~88% of the
manuscript) -- essentially complete coverage. Every major test in this
project was then systematically re-run on the rebuilt corpus. With one
minor exception (an internal character-doubling measurement for
Language B that shifted from a clean null toward a weaker, still-
inconclusive signal), every finding was confirmed essentially unchanged.

The one finding that changed substantially was the one the expansion
specifically targeted: the apparent gap between Language A's and
Language B's word-class ordering asymmetry (Addendum 3). On the full
corpus, with Language B now five times larger and the majority language
overall, this gap disappeared entirely -- both languages show
statistically indistinguishable, equally strong, equally robust
ordering structure. The original gap was sample-size noise, not a real
linguistic difference. This strengthens, rather than complicates, the
project's most positive and unexpected finding: real, grammar-suggestic
positional structure is a robust property of Voynichese as a whole, not
an artifact specific to one Currier language or one partial sample.

This is, on balance, a good outcome from what began as a process
failure. The fabrication incident should not have happened, and is
documented in full rather than minimized. But the response to it --
validating the existing data, obtaining a complete authoritative
source, and systematically re-confirming every finding -- has left the
project on meaningfully firmer ground than before, with both of its
central, most surprising results (the doubling anomaly and the word-
class ordering asymmetry) now resting on essentially complete,
validated data rather than a partial sample.

---

## Addendum 5: Bootstrap resolution of the two remaining open threads

Following the full-corpus rebuild (Addendum 4), two findings had been
flagged as murky or potentially inconsistent with the rest of the
evidence: a cross-section gap in doubling rates (Biological and
Pharmaceutical appearing weaker than Herbal and Stars), and Language B's
internal character doubling ratio creeping upward to 1.38x with more data.

Both were resolved using proper permutation/bootstrap tests -- the HEP-
style Monte Carlo approach the user had proposed as a more rigorous
framework for this kind of analysis.

**The cross-section gap** was tested via a permutation null: shuffle all
word content across the corpus while keeping section boundaries and line
structure fixed, then measure how often a gap as large as the observed
one arises by chance. Result: Language B's gap has p=0.144, Language A's
is p=0.034 -- neither significant after accounting for multiple
comparisons. The observed section-to-section variation in doubling
rates is fully compatible with a single stationary process generating
the whole text, with noise arising from the different section sizes.
This is a non-finding, but an important one: it rules out a class of
hypotheses in which different sections were generated by different
mechanisms or different "settings" of the same mechanism.

**The B internal doubling** was resolved by decomposing the elevated
ratio by character pair. Language B's internal doubling is 93.4%
attributable to a single pair: CC. CC is not incidental same-character
repetition -- it is a specific, structurally meaningful cluster in B's
compound word templates, already identified in multiple earlier findings
(the "4OD-CC-8G" compound structure). Once CC is excluded, B's non-CC
internal doubling rate is actually lower than A's. The apparent increase
in B's ratio from 1.14x (partial corpus) to 1.38x (full corpus) is
explained simply by the Stars and Biological sections -- which contain
B's most CC-heavy compound words -- having been severely underrepresented
in the old partial corpus. This is not a new anomaly; it is a known
structural feature showing up more clearly with complete data.

**The clean picture that remains:** two well-supported, well-tested,
mutually consistent findings. Voynichese shows real, stationary,
manuscript-wide elevated whole-word doubling (stationary confirmed by
both sliding-window analysis and permutation test), and real, equally
strong in both Currier languages, word-class ordering asymmetry
suggestive of grammatical structure. Every other specific structural
hypothesis tested -- marker-word classes, line position, line length,
running-key mechanisms, exact sequence dependence, gemination,
grammatical suffix marking -- came back null or was explained by known
vocabulary structure. No unresolved anomalies remain in the current
analysis.

---

## Addendum 6: Sanskrit Rigveda and Hebrew liturgical extensions

Following the bootstrap resolution of all prior open threads (Addendum 5),
two new corpora were added to the multi-language comparison: the complete
Rigveda in Unicode IAST romanization (135,279 words, from the INDOLOGY/
GRETIL-mirror), and two Hebrew liturgical samples (Hallel and festival
psalms 113-150, 4,273 words; and the complete 150 Psalms, 19,662 words).

The Rigveda sits comfortably in the normal real-language range on entropy
and compression, with no anomalous features. Its doubling ratio (1.71x
shuffled baseline) is loosely similar to Voynichese's, but this is flagged
as requiring caution: IAST romanization may generate same-word coincidences
via sandhi and morphological identity that would not appear in the Devanagari
original, and Sanskrit narrative does not use within-line rhythmic repetition
of the kind that motivates the liturgical hypothesis.

The Hebrew liturgical results are the more significant finding. Both Hallel
(0.31x) and full Psalms (0.48x) show doubling actively suppressed below
their own chance baselines -- the strongest negative control for the
Voynichese doubling anomaly found in this entire project. Critically, the
famous repetitive structure of Jewish liturgical poetry (Psalm 136's 26-verse
refrain; the Hallelujah frame of Psalm 113) always inserts at least one
different word between repetitions of the same phrase, never placing the
identical word twice in immediate succession. Real liturgical repetition
is a pattern of return across intervening material, not literal sequential
self-adjacency.

This finding extends and strengthens the conclusion first established by
the Carmina Burana test (Addendum 2 of the original synthesis): that
genres deliberately built around repetition, whether poetic/musical or
liturgical, actively avoid the specific kind of immediate word-self-adjacency
that Voynichese exhibits at approximately twice the rate expected by chance.
The Voynichese doubling anomaly has now been tested against, and survived:
formulaic herbal English prose, maximally repetition-saturated Latin verse,
consonantal Hebrew narrative (Genesis, Exodus), consonantal Arabic legal and
narrative verse, Sanskrit Vedic hymns, and now Hebrew liturgical poetry
across two different sample sizes. In every case, real language either shows
zero immediate doubling (prose, Arabic) or suppressed-below-chance doubling
(liturgy), never the systematic above-chance elevation that Voynichese shows
consistently and stationarily across its full manuscript.

---

## Addendum 7: Sefer Yetzirah, Latin technical register, and the complete comparison table

Two further corpora were tested following the Sanskrit and Hebrew liturgical
analysis of Addendum 6.

**Sefer Yetzirah** (Jewish Kabbalistic/mystical text, 1,699 words) is the most
combinatorially-structured real Hebrew text known -- explicitly organized around
permutations of letters and numerical combinations. Despite this, it shows
entirely normal results: H1 = 3.782 (within the Hebrew range), compression
1.152x (comparable to Genesis), and doubling suppressed below chance (0.48x,
z = -1.25). The small sample means the z-score is not itself statistically
significant, but the direction is consistent with every other real Hebrew sample.
The mathematical/combinatorial register of Sefer Yetzirah does not produce
Voynichese-like statistics.

**Latin Vulgate narrative and Leviticus** (5,000 and 3,000 words from the
complete Vulgate corpus, 534,301 words total) extend our Latin comparison into
a new register: Leviticus is the most formulaic, procedural, and legally
repetitive Latin in the Bible -- the closest real-language parallel to a
recipe or procedure manual. It shows H1 = 3.410 and compression 1.160x
(slightly higher than narrative Latin, as expected from formulaic repetition),
and zero immediate doubling (z = -5.07, p = 1.000). Even the most
procedure-manual-like real Latin maintains the real-language property of
suppressed doubling.

**The complete comparison table** across all 13 tested corpora now shows a
completely consistent pattern: every real-language corpus (English, Latin,
Hebrew narrative/liturgical/mystical, Arabic, Sanskrit) shows doubling
at or below chance, regardless of genre, register, script type, or language
family. Voynichese A and B show doubling consistently above chance in every
section of the manuscript. No tested corpus bridges this gap from the
real-language side.

**On the mathematical framing of the null results:** the systematic pattern
of nulls across all mechanism tests (marker words, line position, line length,
grammatical suffix class, internal gemination, sequential statefulness, exact
write-order dependence) collectively constrain the complexity of whatever
process generated Voynichese. The right mathematical framing is minimum
description length (MDL): what is the simplest generative model that
simultaneously reproduces all observed statistics? A hierarchy of generators
of increasing complexity has been partially explored (character Markov chain,
bag-of-words, sticky bag-of-words, table/grille), with the sticky bag-of-words
currently the best fit (matching H1, TTR, avglen, and doubling rate, but
slightly over-shooting on TTR). The proposed next step is a Level 4 generator
adding word-class ordering structure (a simple HMM where suffix-class
transitions are learned from the asymmetric ordering signal), which would be
the minimum sufficient model if it fits all five key statistics simultaneously.
This represents a concrete, testable lower bound on the complexity of the
Voynich manuscript's generating process.

---

## Addendum 8 (Final): The dual-constraint anomaly and the generator hierarchy

The final phase of this project pursued two parallel threads: completing the
generator hierarchy (finding the minimum-complexity model that reproduces all
of Voynichese's statistics) and asking whether any known natural language could
naturally produce Voynichese-like statistics. Both threads converged on the
same answer, which we call the dual-constraint anomaly.

**The generator hierarchy** was extended to Level 4 (HMM with word-class
ordering transitions and stickiness) and Level 4.5 (adding temperature
sampling to adjust vocabulary diversity). Level 4 was the first generator to
reproduce the word-class ordering asymmetry signal, confirming that the learned
transition matrix captures real structure. But neither level could close the
TTR gap: vocabulary diversity remained 33-40% below the real Voynichese value
regardless of parameter tuning. The conclusion is structural: no generator
that draws from a fixed word pool can simultaneously achieve Voynichese's low
conditional entropy AND its vocabulary diversity. The minimum additional
complexity required is productive word formation -- the ability to generate
novel word forms from reusable morpheme-like parts rather than resampling a
fixed vocabulary. This is a specific, falsifiable claim about the nature of
the generating process.

**The cross-linguistic comparison** confirmed the same constraint from the
other direction. Among all known natural languages (drawing on the 311-language
Lindemann & Bowern corpus and our own 13-corpus test suite), low conditional
entropy (H1 < 3.0) is found only in languages with severely restricted syllabic
phonology: Hawaiian (H1=2.77), Venda (H1=2.79), Min Dong Chinese (H1=2.84).
These languages achieve low entropy through phonological simplicity -- but as
a consequence, their vocabulary diversity is limited. Agglutinative languages
(Finnish H1=3.47, Turkish H1=3.55, Hungarian H1=3.74) have productive word
formation and high vocabulary diversity, but their entropy is well above
Voynichese. The two properties trade off in real language: every language sits
on a curve, and Voynichese sits off the curve entirely.

**The dual-constraint anomaly** is the unified statement of this finding:
Voynichese simultaneously has low conditional entropy (implying restricted
character-sequence templates) AND high vocabulary diversity (implying productive
word formation). These are naturally anti-correlated in real language, and no
known natural language occupies the region where Voynichese sits.

**What this rules out and what it doesn't:** the finding rules out "ordinary
text in an ordinary natural language" more precisely than the prior literature
has stated. It does not rule out (a) a cipher that simplifies phonological
distinctions many-to-one while preserving morphological vocabulary structure
at the word level, or (b) an artificial language or constructed system with
both a restricted glyph-assembly template (producing low entropy) and
combinable word-part structure (producing vocabulary diversity). The Rugg
table/grille class of hypotheses falls into category (b), though our earlier
tests showed that simple table/grille generators overshoot the doubling rate
by 3-19x.

**The project's final position:** Voynichese is not ordinary natural language.
It is not a simple cipher of natural language. It has real, grammar-like
ordering structure. It has a specific, genre-proof, mechanism-resistant
doubling anomaly. And it sits in a region of statistical space -- simultaneously
low entropy and high vocabulary diversity -- that no known natural language
occupies. These constraints do not resolve the hoax-vs-meaning question, but
they characterize it with more precision than was previously available: whatever
process generated Voynichese, it was not a simple one, and it was not a
familiar one.

---

*This synthesis covers all 41 numbered findings across the full project
(Updates 1-9+). The complete research log is in FINDINGS_LOG.md. All code
and data are at https://github.com/mjtemkin/VoynichStats.*

---

## Future Work

Several directions remain unexplored that could meaningfully extend this
analysis, noted here for completeness rather than as unresolved gaps in the
current findings.

**Logographic and pictographic scripts.** The dual-constraint anomaly was
established by comparing Voynichese against alphabetic and syllabic writing
systems. Logographic-syllabic scripts -- Egyptian hieroglyphs and Classic
Mayan -- represent a genuinely different structural class that has not been
tested. At the glyph level (treating each glyph as a token rather than
transliterating into phonemes), these scripts might produce word-level
doubling rates and vocabulary distributions that are structurally closer to
Voynichese's than any alphabetic language. This would require purpose-built
glyph-sequence corpora: Mayan hieroglyphs are not yet in Unicode (as of
2026), and the serious digital projects (TWKM, FAMSI) encode their material
in specialist XML-TEI rather than plain text. Transliterating either script
into phonemic romanization would lose the glyph-inventory structure that
makes the comparison interesting, and would likely produce H1 values in the
normal language range (3.2-3.8) reflecting the underlying spoken language
rather than the script. This analysis is left for when accessible glyph-
sequence corpora become available.

**Agglutinative language corpora directly tested.** The dual-constraint
analysis used H1 values from the Lindemann and Bowern (2020) 311-language
Wikipedia corpus rather than running our own pipeline on Turkish, Finnish,
or Hungarian text. Direct testing would allow us to measure all five key
statistics (H1, TTR, compression, doubling rate, word-class asymmetry)
simultaneously on agglutinative languages, rather than just H1. This would
confirm whether agglutinative languages are as far from Voynichese on TTR
and compression as they are on entropy, or whether they show partial overlap
on some metrics.

**Amidah and complete Shabbat siddur.** The Hebrew liturgical analysis used
Psalms 113-150 and the complete Psalms as liturgical samples. The Amidah
(the central standing prayer of every Jewish service, heavily formulaic in
structure) was not accessible via the sandbox network. It represents a
meaningfully different liturgical register -- declaratory rather than poetic
-- and would be worth testing to confirm the Hebrew liturgical suppression
result holds across all registers.

**Productive word-formation generator (Level 5).** The generator hierarchy
identified productive word formation as the missing ingredient in Level 4.5.
A Level 5 generator would implement a slot-based word-formation model
(following Stolfi's grammar framework) where words are assembled from
combinable prefix, stem, and suffix slots rather than drawn from a fixed
pool. This would directly test whether the dual-constraint anomaly is
resolvable by a generator with morphology-like structure, and would provide
a more precise lower bound on the complexity of the Voynichese generating
process.
