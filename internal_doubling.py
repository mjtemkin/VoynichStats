import re, math, random
from collections import Counter

def parse_fsg(path):
    records = []
    cur_lang = None; cur_section = None; cur_folio = None; cur_words = []
    def flush():
        if cur_words and cur_folio:
            records.append({'folio': cur_folio, 'lang': cur_lang, 'section': cur_section, 'words': list(cur_words)})
    with open(path, encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    for raw in lines:
        line = raw.rstrip('\n'); stripped = line.strip()
        if stripped.startswith('#'):
            comment = stripped.lstrip('#').strip(); low = comment.lower()
            if low.startswith('folio'):
                flush(); cur_words = []
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
        if not stripped: continue
        text = re.sub(r'\{[^}]*\}', '', stripped)
        text = text.rstrip('-=')
        text = re.sub(r'\(([^|)]*)\|[^)]*\)', r'\1', text)
        for w in text.split(','):
            w = w.strip()
            if w: cur_words.append(w)
    flush()
    return records

recs = parse_fsg('raw_fsg.txt')
words_A, words_B = [], []
for r in recs:
    if r['lang'] == 'A': words_A.extend(r['words'])
    elif r['lang'] == 'B': words_B.extend(r['words'])

def internal_doubling_rate(words):
    """Rate of word[i]==word[i+1] WITHIN a word (character-level), e.g. 'OO', 'EE'."""
    total_adjacent = 0
    doubles = 0
    double_chars = Counter()
    for w in words:
        for i in range(len(w)-1):
            total_adjacent += 1
            if w[i] == w[i+1]:
                doubles += 1
                double_chars[w[i]] += 1
    return doubles, total_adjacent, (doubles/total_adjacent if total_adjacent else 0), double_chars

def expected_internal_rate(words):
    """Chance baseline from character frequency (sum p_i^2)."""
    corpus = ''.join(words)
    counts = Counter(corpus); n = len(corpus)
    return sum((c/n)**2 for c in counts.values())

def shuffled_internal_rate(words, seed=42, n_trials=20):
    """Shuffle CHARACTERS within each word (preserving word length) and recompute."""
    rng = random.Random(seed)
    rates = []
    for _ in range(n_trials):
        doubles = 0; total = 0
        for w in words:
            chars = list(w)
            rng.shuffle(chars)
            for i in range(len(chars)-1):
                total += 1
                if chars[i] == chars[i+1]:
                    doubles += 1
        rates.append(doubles/total if total else 0)
    return sum(rates)/len(rates)

print("=== INTERNAL (WITHIN-WORD) CHARACTER DOUBLING ===")
for label, words in [('A', words_A), ('B', words_B)]:
    doubles, total, rate, double_chars = internal_doubling_rate(words)
    expected = expected_internal_rate(words)
    shuf = shuffled_internal_rate(words)
    print(f"\nLanguage {label}:")
    print(f"  Real internal-doubling rate: {rate*100:.3f}% ({doubles}/{total} adjacent char pairs)")
    print(f"  Chance baseline (char freq^2): {expected*100:.3f}%")
    print(f"  Shuffled-within-word baseline: {shuf*100:.3f}%")
    print(f"  Real/Shuffled ratio: {rate/shuf:.2f}x" if shuf > 0 else "  n/a")
    print(f"  Most common doubled characters: {double_chars.most_common(8)}")

# Compare to Culpeper and Carmina Burana for the same internal-doubling statistic
print("\n=== SAME TEST ON REAL-LANGUAGE CONTROLS ===")
for label, path in [('Culpeper', '../compare/culpeper_full.txt'), ('Carmina Burana', '../compare/carmina_burana.txt')]:
    with open(path) as f:
        text = f.read()
    real_words = re.findall(r"[a-z]+", text.lower())
    doubles, total, rate, double_chars = internal_doubling_rate(real_words)
    expected = expected_internal_rate(real_words)
    shuf = shuffled_internal_rate(real_words)
    print(f"\n{label}:")
    print(f"  Real internal-doubling rate: {rate*100:.3f}% ({doubles}/{total})")
    print(f"  Chance baseline: {expected*100:.3f}%")
    print(f"  Shuffled baseline: {shuf*100:.3f}%")
    print(f"  Real/Shuffled ratio: {rate/shuf:.2f}x" if shuf > 0 else "  n/a")
    print(f"  Most common doubled characters: {double_chars.most_common(8)}")
