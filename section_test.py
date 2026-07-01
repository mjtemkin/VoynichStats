import re, math
from collections import Counter, defaultdict

def parse_fsg(path):
    records = []
    cur_lang = None
    cur_section = None
    cur_folio = None
    cur_words = []
    def flush():
        if cur_words and cur_folio:
            records.append({'folio': cur_folio, 'lang': cur_lang, 'section': cur_section, 'words': list(cur_words)})
    with open(path, encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    for raw in lines:
        line = raw.rstrip('\n')
        stripped = line.strip()
        if stripped.startswith('#'):
            comment = stripped.lstrip('#').strip()
            low = comment.lower()
            if low.startswith('folio'):
                flush()
                cur_words = []
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

groups = defaultdict(list)
for r in recs:
    if r['lang'] and r['section']:
        groups[(r['lang'], r['section'])].extend(r['words'])

def char_entropy(words):
    corpus = ''.join(words)
    counts = Counter(corpus)
    total = sum(counts.values())
    H0 = -sum((c/total)*math.log2(c/total) for c in counts.values())
    bigrams = Counter(); ctx = Counter()
    for i in range(len(corpus)-1):
        a,b = corpus[i], corpus[i+1]
        bigrams[(a,b)] += 1
        ctx[a] += 1
    H1 = 0.0
    for (a,b),cnt in bigrams.items():
        p_ab = cnt/total
        p_b_given_a = cnt/ctx[a]
        H1 -= p_ab * math.log2(p_b_given_a)
    return H0, H1

def stats(words):
    H0, H1 = char_entropy(words)
    ttr = len(set(words))/len(words)
    avglen = sum(len(w) for w in words)/len(words)
    first = Counter(w[0] for w in words if w)
    last = Counter(w[-1] for w in words if w)
    n = len(words)
    top_final_G = 100*last.get('G',0)/n
    top_initial_T = 100*first.get('T',0)/n
    return dict(n=n, H0=H0, H1=H1, ttr=ttr, avglen=avglen, pct_final_G=top_final_G, pct_initial_T=top_initial_T)

print(f"{'Group':<20} {'N':>6} {'H0':>6} {'H1':>6} {'TTR':>6} {'AvgLen':>7} {'%final-G':>9} {'%init-T':>8}")
for key in [('B','herbal'), ('B','biological'), ('A','herbal')]:
    words = groups[key]
    s = stats(words)
    label = f"{key[0]}/{key[1]}"
    print(f"{label:<20} {s['n']:>6} {s['H0']:>6.3f} {s['H1']:>6.3f} {s['ttr']:>6.3f} {s['avglen']:>7.2f} {s['pct_final_G']:>8.1f}% {s['pct_initial_T']:>7.1f}%")

print()
print("=== KEY COMPARISON ===")
print("If B/herbal and B/biological look SIMILAR to each other but DIFFERENT from A/herbal:")
print("  -> supports a real LANGUAGE A vs B effect, independent of section")
print("If B/herbal and B/biological look very DIFFERENT from each other:")
print("  -> the earlier A vs B differences may have been partly a SECTION artifact")

# top words per group for qualitative check
print("\n=== TOP 8 WORDS PER GROUP ===")
for key in [('B','herbal'), ('B','biological'), ('A','herbal')]:
    words = groups[key]
    print(f"{key}: {Counter(words).most_common(8)}")
