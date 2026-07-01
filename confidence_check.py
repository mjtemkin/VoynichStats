import re, math
from collections import Counter

def parse_fsg_with_lines(path):
    records = []
    cur_lang = None; cur_section = None; cur_folio = None
    cur_lines = []; cur_line_words = []
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
        line = raw.rstrip('\n'); stripped = line.strip()
        if stripped.startswith('#'):
            comment = stripped.lstrip('#').strip(); low = comment.lower()
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
        if not stripped: continue
        text = re.sub(r'\{[^}]*\}', '', stripped)
        text = text.rstrip('-=')
        text = re.sub(r'\(([^|)]*)\|[^)]*\)', r'\1', text)
        words_here = [w.strip() for w in text.split(',') if w.strip()]
        if words_here:
            cur_line_words.extend(words_here)
        flush_line()
    flush_folio()
    return records

recs = parse_fsg_with_lines('raw_fsg.txt')
lines_A, lines_B = [], []
for r in recs:
    if r['lang'] == 'A': lines_A.extend(r['lines'])
    elif r['lang'] == 'B': lines_B.extend(r['lines'])

def doubling_ci(lines, label):
    """Compute a Wilson/normal confidence interval on the doubling rate,
    treating each adjacent word-pair as a Bernoulli trial."""
    pairs = 0; reps = 0
    for line in lines:
        for i in range(len(line)-1):
            pairs += 1
            if line[i] == line[i+1]:
                reps += 1
    p_hat = reps / pairs
    se = math.sqrt(p_hat * (1 - p_hat) / pairs)
    ci_low = p_hat - 1.96 * se
    ci_high = p_hat + 1.96 * se
    print(f"\nLanguage {label}:")
    print(f"  n (adjacent pairs) = {pairs}")
    print(f"  observed doublings = {reps}")
    print(f"  rate = {p_hat*100:.3f}%")
    print(f"  standard error = {se*100:.4f} percentage points")
    print(f"  95% CI: [{ci_low*100:.3f}%, {ci_high*100:.3f}%]")
    return p_hat, se, ci_low, ci_high

print("=== CONFIDENCE INTERVALS ON DOUBLING RATE (current sample) ===")
pA, seA, loA, hiA = doubling_ci(lines_A, 'A')
pB, seB, loB, hiB = doubling_ci(lines_B, 'B')

print("\n=== IS THE CHANCE BASELINE OUTSIDE THE CI? ===")
chance_A = 0.587/100  # from shuffle test
chance_B = 0.502/100
print(f"Language A: chance baseline {chance_A*100:.3f}% vs 95% CI [{loA*100:.3f}%, {hiA*100:.3f}%]")
print(f"  --> chance baseline is {'OUTSIDE (significant)' if chance_A < loA else 'INSIDE (not significant)'} the CI")
print(f"Language B: chance baseline {chance_B*100:.3f}% vs 95% CI [{loB*100:.3f}%, {hiB*100:.3f}%]")
print(f"  --> chance baseline is {'OUTSIDE (significant)' if chance_B < loB else 'INSIDE (not significant)'} the CI")

print("\n=== HOW MUCH WOULD MORE DATA SHRINK THE CI? ===")
print("Standard error shrinks as 1/sqrt(n). To halve the CI width, we'd need 4x the data.")
print(f"Current A: n={len(lines_A)} lines / {sum(len(l) for l in lines_A)} words -- SE={seA*100:.4f}pp")
print(f"If we had the FULL manuscript (~3x our current word count): SE would shrink by ~sqrt(3)={math.sqrt(3):.2f}x")
print(f"  --> estimated SE at full size: ~{seA*100/math.sqrt(3):.4f}pp (vs current {seA*100:.4f}pp)")

print("\n=== EFFECT SIZE CONTEXT ===")
print(f"Language A: effect is {(pA-chance_A)/seA:.1f} standard errors away from chance baseline (a 'z-score' of sorts)")
print(f"Language B: effect is {(pB-chance_B)/seB:.1f} standard errors away from chance baseline")
print("For reference: z > 3 is generally considered very strong evidence; z > 5 is overwhelming.")
