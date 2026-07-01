import re, math
from collections import Counter, defaultdict

def parse_fsg_with_lines(path):
    """Like parse_fsg but preserves LINE structure (word position within line)."""
    records = []  # each: {folio, lang, section, lines: [[words...], [words...], ...]}
    cur_lang = None; cur_section = None; cur_folio = None
    cur_lines = []  # list of word-lists
    cur_line_words = []

    def flush_line():
        nonlocal cur_line_words
        if cur_line_words:
            cur_lines.append(cur_line_words)
            cur_line_words = []

    def flush_folio():
        flush_line()
        if cur_lines and cur_folio:
            records.append({'folio': cur_folio, 'lang': cur_lang, 'section': cur_section, 'lines': [l[:] for l in cur_lines]})
        cur_lines.clear()

    with open(path, encoding='utf-8', errors='replace') as f:
        raw_lines = f.readlines()

    for raw in raw_lines:
        line = raw.rstrip('\n')
        stripped = line.strip()
        if stripped.startswith('#'):
            comment = stripped.lstrip('#').strip()
            low = comment.lower()
            if low.startswith('folio'):
                flush_folio()
                cur_folio = comment.split(None,1)[1].strip() if len(comment.split(None,1))>1 else comment
            if 'language a' in low: cur_lang='A'
            elif 'language b' in low: cur_lang='B'
            if 'herbal' in low: cur_section='herbal'
            elif 'biological' in low: cur_section='biological'
            elif 'pharma' in low or 'phamaceutical' in low: cur_section='pharmaceutical'
            elif 'star' in low: cur_section='stars'
            elif 'cosmological' in low: cur_section='cosmological'
            elif 'astronom' in low: cur_section='astronomical'
            continue
        if not stripped:
            continue
        # each raw line in the file corresponds to ONE manuscript line (ends with - or =)
        text = re.sub(r'\{[^}]*\}', '', stripped)
        is_para_end = text.rstrip().endswith('=')
        text = text.rstrip('-=')
        text = re.sub(r'\(([^|)]*)\|[^)]*\)', r'\1', text)
        words_here = [w.strip() for w in text.split(',') if w.strip()]
        if words_here:
            cur_line_words.extend(words_here)
        # flush this manuscript line as a "line" unit
        flush_line()

    flush_folio()
    return records

recs = parse_fsg_with_lines('raw_fsg.txt')
print(f"Parsed {len(recs)} folio records")

# Separate by language
lines_A = []  # list of word-lists, each a manuscript line
lines_B = []
for r in recs:
    if r['lang'] == 'A':
        lines_A.extend(r['lines'])
    elif r['lang'] == 'B':
        lines_B.extend(r['lines'])

print(f"Language A: {len(lines_A)} lines, {sum(len(l) for l in lines_A)} words")
print(f"Language B: {len(lines_B)} lines, {sum(len(l) for l in lines_B)} words")

# ===== TEST 1: word-level bigram conditional entropy (does word order matter?) =====
def word_bigram_entropy(lines):
    """Compute H(next_word | prev_word) at the WORD level, using line-internal sequences only."""
    word_counts = Counter()
    bigram_counts = Counter()
    for line in lines:
        for w in line:
            word_counts[w] += 1
        for i in range(len(line)-1):
            bigram_counts[(line[i], line[i+1])] += 1
    total_words = sum(word_counts.values())
    total_bigrams = sum(bigram_counts.values())
    # H0 at word level (unigram entropy)
    H0_word = -sum((c/total_words)*math.log2(c/total_words) for c in word_counts.values())
    # H1 at word level (conditional on previous word)
    ctx_counts = Counter()
    for (a,b), cnt in bigram_counts.items():
        ctx_counts[a] += cnt
    H1_word = 0.0
    for (a,b), cnt in bigram_counts.items():
        p_ab = cnt/total_bigrams
        p_b_given_a = cnt/ctx_counts[a]
        H1_word -= p_ab * math.log2(p_b_given_a)
    return H0_word, H1_word, total_words, len(word_counts)

print("\n=== WORD-LEVEL BIGRAM ENTROPY (does knowing the PREVIOUS WORD reduce uncertainty?) ===")
for label, lines in [('A', lines_A), ('B', lines_B)]:
    H0w, H1w, n, vocab = word_bigram_entropy(lines)
    reduction = 100*(H0w - H1w)/H0w if H0w > 0 else 0
    print(f"Language {label}: H0(word)={H0w:.3f} bits  H1(word|prev)={H1w:.3f} bits  "
          f"reduction={reduction:.1f}%  (vocab={vocab}, n={n})")

print("\nFor comparison, what would a RANDOM SHUFFLE of the same words give us?")
import random
def shuffled_lines(lines, seed=42):
    rng = random.Random(seed)
    flat = [w for line in lines for w in line]
    rng.shuffle(flat)
    out = []
    idx = 0
    for line in lines:
        out.append(flat[idx:idx+len(line)])
        idx += len(line)
    return out

for label, lines in [('A', lines_A), ('B', lines_B)]:
    shuf = shuffled_lines(lines)
    H0w, H1w, n, vocab = word_bigram_entropy(shuf)
    reduction = 100*(H0w - H1w)/H0w if H0w > 0 else 0
    print(f"Language {label} (SHUFFLED): H0(word)={H0w:.3f} bits  H1(word|prev)={H1w:.3f} bits  reduction={reduction:.1f}%")
