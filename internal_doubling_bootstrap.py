import re, math, random
from collections import Counter

def parse_fsg(path):
    records = []
    cur_lang = None; cur_section = None; cur_folio = None; cur_words = []
    def flush():
        if cur_words and cur_folio:
            records.append({'folio': cur_folio, 'lang': cur_lang,
                          'section': cur_section, 'words': list(cur_words)})
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
words_A = [w for r in recs if r['lang']=='A' for w in r['words']]
words_B = [w for r in recs if r['lang']=='B' for w in r['words']]

def internal_doubling_by_pair(words):
    """Measure internal doubling broken down by WHICH character pair doubles."""
    pair_counts = Counter()   # (char, char) -> count of adjacent same-char occurrences
    total_adjacent = 0
    doubles = 0
    for w in words:
        for i in range(len(w)-1):
            total_adjacent += 1
            if w[i] == w[i+1]:
                doubles += 1
                pair_counts[(w[i], w[i+1])] += 1
    return doubles, total_adjacent, pair_counts

def shuffle_within_words(words, seed=42):
    """Shuffle characters WITHIN each word independently -- preserves each word's
    exact character multiset but destroys internal character order."""
    rng = random.Random(seed)
    out = []
    for w in words:
        chars = list(w)
        rng.shuffle(chars)
        out.append(''.join(chars))
    return out

# ===== PART 1: Which character pairs drive B's excess internal doubling? =====
print("=== INTERNAL DOUBLING BY CHARACTER PAIR ===")
for label, words in [('A', words_A), ('B', words_B)]:
    real_doubles, total_adj, pair_counts = internal_doubling_by_pair(words)
    real_rate = real_doubles/total_adj
    # compute null rate (shuffled within words)
    shuf_doubles = 0
    shuf_adj = 0
    for trial in range(30):
        sw = shuffle_within_words(words, seed=trial)
        d, a, _ = internal_doubling_by_pair(sw)
        shuf_doubles += d; shuf_adj += a
    shuf_rate = shuf_doubles/shuf_adj
    ratio = real_rate/shuf_rate if shuf_rate > 0 else float('nan')

    print(f"\nLanguage {label}: real={real_rate*100:.3f}% shuf={shuf_rate*100:.3f}% ratio={ratio:.3f}x")
    print(f"  Top doubling pairs (real data):")
    total = sum(pair_counts.values())
    for (a,b), cnt in pair_counts.most_common(8):
        pct = 100*cnt/total
        print(f"    {a}{b}: {cnt} ({pct:.1f}% of all doublings)")

    # What's the ratio EXCLUDING CC doublings?
    cc_count = pair_counts.get(('C','C'), 0)
    non_cc_doubles = real_doubles - cc_count
    # total adjacent pairs minus pairs involving CC positions
    # (approximate: remove pairs where both chars are C)
    cc_positions = sum(1 for w in words for i in range(len(w)-1)
                      if w[i]=='C' and w[i+1]=='C')
    non_cc_adj = total_adj - cc_positions
    non_cc_shuf_d = shuf_doubles - sum(
        sum(1 for w in shuffle_within_words(words, seed=t)
            for i in range(len(w)-1) if w[i]=='C' and w[i+1]=='C')
        for t in range(30))
    non_cc_shuf_adj = shuf_adj - sum(
        sum(1 for w in shuffle_within_words(words, seed=t)
            for i in range(len(w)-1))
        for t in range(30))

    if non_cc_adj > 0 and shuf_adj > 0:
        non_cc_real_rate = non_cc_doubles/non_cc_adj
        # rough null: shuf rate on non-CC positions
        # (simpler: shuf rate overall minus CC contribution)
        cc_shuf = pair_counts.get(('C','C'), 0)  # placeholder
        print(f"\n  Ratio EXCLUDING CC doublings:")
        print(f"    Non-CC real doublings: {non_cc_doubles} / {non_cc_adj} = {non_cc_real_rate*100:.3f}%")

# ===== PART 2: Proper bootstrap -- is B's excess internal doubling
#  statistically significant AFTER controlling for known character-bigram structure? =====
print("\n=== BOOTSTRAP TEST: Is B's excess internal doubling significant? ===")
print("Null model: reshuffle characters within each word (preserving per-word")
print("char-frequency distribution exactly), repeat 500 times, build null distribution")
print("of the overall real/shuffled ratio.")

n_trials = 500
for label, words in [('A', words_A), ('B', words_B)]:
    real_d, real_a, _ = internal_doubling_by_pair(words)
    real_rate = real_d/real_a

    shuf_rates = []
    for t in range(n_trials):
        sw = shuffle_within_words(words, seed=t)
        d, a, _ = internal_doubling_by_pair(sw)
        shuf_rates.append(d/a if a else 0)

    shuf_mean = sum(shuf_rates)/len(shuf_rates)
    shuf_sd = math.sqrt(sum((x-shuf_mean)**2 for x in shuf_rates)/len(shuf_rates))
    z = (real_rate - shuf_mean)/shuf_sd if shuf_sd > 0 else float('inf')
    p = sum(1 for x in shuf_rates if x >= real_rate)/len(shuf_rates)

    print(f"\nLanguage {label}:")
    print(f"  Real internal-doubling rate: {real_rate*100:.4f}%")
    print(f"  Null (shuffled-within-word): mean={shuf_mean*100:.4f}%, sd={shuf_sd*100:.5f}%")
    print(f"  Z-score: {z:.2f}   p-value: {p:.4f}")
    if p < 0.01:
        print(f"  --> SIGNIFICANT: excess internal doubling is REAL, not explained by")
        print(f"      per-word character frequencies alone")
    else:
        print(f"  --> NOT SIGNIFICANT: consistent with per-word character frequencies")
