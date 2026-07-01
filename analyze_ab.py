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
            if "language a" in low:
                cur_lang = 'A'
            elif "language b" in low:
                cur_lang = 'B'
            if 'herbal' in low: cur_section = 'herbal'
            elif 'biological' in low: cur_section = 'biological'
            elif 'pharma' in low or 'phamaceutical' in low: cur_section = 'pharmaceutical'
            elif 'star' in low: cur_section = 'stars'
            elif 'cosmological' in low: cur_section = 'cosmological'
            elif 'astronom' in low: cur_section = 'astronomical'
            continue
        if not stripped:
            continue
        text = re.sub(r'\{[^}]*\}', '', stripped)
        text = text.rstrip('-=')
        text = re.sub(r'\(([^|)]*)\|[^)]*\)', r'\1', text)
        for w in text.split(','):
            w = w.strip()
            if w:
                cur_words.append(w)
    flush()
    return records

recs = parse_fsg('raw_fsg.txt')

words_A = []
words_B = []
for r in recs:
    if r['lang'] == 'A':
        words_A.extend(r['words'])
    elif r['lang'] == 'B':
        words_B.extend(r['words'])

print(f"Language A: {len(words_A)} words, {len(set(words_A))} unique types")
print(f"Language B: {len(words_B)} words, {len(set(words_B))} unique types")

def char_entropy(words):
    corpus = ''.join(words)
    counts = Counter(corpus)
    total = sum(counts.values())
    H0 = -sum((c/total)*math.log2(c/total) for c in counts.values())
    # order-1 conditional entropy
    bigrams = Counter()
    unigram_ctx = Counter()
    for i in range(len(corpus)-1):
        a,b = corpus[i], corpus[i+1]
        bigrams[(a,b)] += 1
        unigram_ctx[a] += 1
    H1 = 0.0
    for (a,b),cnt in bigrams.items():
        p_ab = cnt/total
        p_b_given_a = cnt/unigram_ctx[a]
        H1 -= p_ab * math.log2(p_b_given_a)
    return H0, H1, total, len(counts)

print("\n=== CHARACTER ENTROPY ===")
for label, words in [('A', words_A), ('B', words_B)]:
    H0, H1, total_chars, alphabet = char_entropy(words)
    print(f"Language {label}: order-0 H={H0:.3f} bits/char, order-1 H={H1:.3f} bits/char, "
          f"alphabet size={alphabet}, total chars={total_chars}")

def avg_word_len(words):
    return sum(len(w) for w in words)/len(words)

print("\n=== WORD LENGTH ===")
for label, words in [('A', words_A), ('B', words_B)]:
    print(f"Language {label}: avg word length = {avg_word_len(words):.2f} chars")

def type_token_ratio(words):
    return len(set(words))/len(words)

print("\n=== TYPE-TOKEN RATIO ===")
for label, words in [('A', words_A), ('B', words_B)]:
    print(f"Language {label}: TTR = {type_token_ratio(words):.3f}")

def top_words(words, n=10):
    return Counter(words).most_common(n)

print("\n=== TOP 10 WORDS ===")
for label, words in [('A', words_A), ('B', words_B)]:
    print(f"Language {label}:", top_words(words))

def initial_final_dist(words, n_top=8):
    first = Counter(w[0] for w in words if w)
    last = Counter(w[-1] for w in words if w)
    total = len(words)
    print(f"  Top initial chars: {[(c, f'{100*ct/total:.1f}%') for c,ct in first.most_common(n_top)]}")
    print(f"  Top final chars:   {[(c, f'{100*ct/total:.1f}%') for c,ct in last.most_common(n_top)]}")

print("\n=== WORD-INITIAL / WORD-FINAL CHAR DISTRIBUTION ===")
for label, words in [('A', words_A), ('B', words_B)]:
    print(f"Language {label}:")
    initial_final_dist(words)
