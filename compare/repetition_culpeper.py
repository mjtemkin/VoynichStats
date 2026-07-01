import re, random
from collections import Counter

with open('compare/culpeper_full.txt') as f:
    text = f.read()

# Split into sentences/lines roughly the way the original prose is lineated --
# but since this is prose, not manuscript lines, we'll treat each SENTENCE as
# a "line" unit for the adjacency test (most comparable to how Voynich lines
# are bounded units of word-sequence).
sentences = re.split(r'[.!?]+', text)
lines = []
for s in sentences:
    words = re.findall(r"[a-z']+", s.lower())
    words = [w.strip("'") for w in words if w.strip("'")]
    if words:
        lines.append(words)

print(f"Culpeper: {len(lines)} sentences, {sum(len(l) for l in lines)} words")

def immediate_repeat_stats(lines):
    total_adjacent_pairs = 0
    exact_repeats = 0
    repeat_examples = []
    for line in lines:
        for i in range(len(line)-1):
            total_adjacent_pairs += 1
            if line[i] == line[i+1]:
                exact_repeats += 1
                repeat_examples.append(line[i])
    rate = exact_repeats/total_adjacent_pairs if total_adjacent_pairs else 0
    return exact_repeats, total_adjacent_pairs, rate, repeat_examples

def expected_repeat_rate(lines):
    flat = [w for line in lines for w in line]
    counts = Counter(flat)
    n = len(flat)
    return sum((c/n)**2 for c in counts.values())

def shuffled_repeat_rate(lines, seed=42, n_trials=20):
    rng = random.Random(seed)
    flat = [w for line in lines for w in line]
    line_lens = [len(l) for l in lines]
    rates = []
    for trial in range(n_trials):
        shuf = flat[:]
        rng.shuffle(shuf)
        idx = 0; reps = 0; pairs = 0
        for ln in line_lens:
            seg = shuf[idx:idx+ln]
            idx += ln
            for i in range(len(seg)-1):
                pairs += 1
                if seg[i] == seg[i+1]:
                    reps += 1
        rates.append(reps/pairs if pairs else 0)
    return sum(rates)/len(rates)

reps, pairs, rate, examples = immediate_repeat_stats(lines)
expected_chance = expected_repeat_rate(lines)
shuf_rate = shuffled_repeat_rate(lines)

print(f"\n=== CULPEPER (real English, herbal genre) ===")
print(f"REAL adjacent-repeat rate:      {rate*100:.3f}%  ({reps} repeats / {pairs} adjacent pairs)")
print(f"Expected from word frequencies: {expected_chance*100:.3f}%")
print(f"SHUFFLED rate:                  {shuf_rate*100:.3f}%")
if shuf_rate > 0:
    print(f"Real / Shuffled ratio: {rate/shuf_rate:.2f}x")
else:
    print("Real / Shuffled ratio: n/a (zero real repeats)")
print(f"Repeated word examples: {examples}")

print("\n=== COMPARISON TABLE ===")
print(f"{'Corpus':<20}{'Real rate':>12}{'Shuffled rate':>15}{'Ratio':>8}")
print(f"{'Culpeper (real)':<20}{rate*100:>11.3f}%{shuf_rate*100:>14.3f}%{(rate/shuf_rate if shuf_rate else float('nan')):>7.2f}x")
print(f"{'Voynichese A':<20}{1.155:>11.3f}%{0.587:>14.3f}%{1.97:>7.2f}x")
print(f"{'Voynichese B':<20}{1.010:>11.3f}%{0.502:>14.3f}%{2.01:>7.2f}x")
