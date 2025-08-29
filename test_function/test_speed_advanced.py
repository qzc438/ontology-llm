import os, time, random, statistics as stats
from math import inf
import dotenv
from openai import OpenAI

# -------------------- Setup --------------------
dotenv.load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

model = "gpt-3.5-turbo"  # change if needed
SYSTEM_MSG = {"role": "system", "content": "You are a deterministic AI assistant."}
USER_MSG   = {"role": "user",   "content": "20-paragraph article about apples"}

# Benchmark controls
N_PER_CONFIG = 30      # runs per configuration (≥30 recommended)
BOOTSTRAPS   = 5000    # for CI on mean difference
PERM_TEST_IT = 10000   # for two-sided p-value via permutation test
RANDOM_SEED  = 1337

random.seed(RANDOM_SEED)

# Two configurations
configs = {
    "Temperature-only": dict(temperature=0.0),
    "All-parameters":   dict(temperature=0.0, top_p=1.0, presence_penalty=0.0, frequency_penalty=0.0),
}

# -------------------- Runner --------------------
def one_call(**gen_kwargs):
    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=model,
        messages=[SYSTEM_MSG, USER_MSG],
        **gen_kwargs
    )
    dt = time.perf_counter() - t0
    usage = getattr(resp, "usage", None)
    pt = getattr(usage, "prompt_tokens", 0) if usage else 0
    ct = getattr(usage, "completion_tokens", 0) if usage else 0
    tt = getattr(usage, "total_tokens", 0) if usage else 0
    return dt, (pt, ct, tt)

def run_config(name, kwargs, n):
    times, tokens = [], []
    for i in range(n):
        dt, tok = one_call(**kwargs)
        times.append(dt)
        tokens.append(tok)
        print(f"{name:<18} run {i+1:02d}: {dt:.2f}s")
    return times, tokens

def summarize_times(times):
    return {
        "n": len(times),
        "mean": stats.mean(times),
        "median": stats.median(times),
        "stdev": stats.pstdev(times) if len(times) > 1 else 0.0,
        "min": min(times),
        "max": max(times),
    }

def cliff_delta(a, b):
    # Effect size: P(a>b) - P(a<b)
    greater = equal = less = 0
    for x in a:
        for y in b:
            if x > y: greater += 1
            elif x < y: less += 1
            else: equal += 1
    n = len(a) * len(b)
    return (greater - less) / n if n else 0.0

def bootstrap_mean_diff(a, b, B=1000):
    # 95% CI for mean(a)-mean(b)
    diffs = []
    n1, n2 = len(a), len(b)
    for _ in range(B):
        sa = [a[random.randrange(n1)] for _ in range(n1)]
        sb = [b[random.randrange(n2)] for _ in range(n2)]
        diffs.append(stats.mean(sa) - stats.mean(sb))
    diffs.sort()
    lo = diffs[int(0.025 * B)]
    hi = diffs[int(0.975 * B)]
    return (lo, hi)

def permutation_test(a, b, iters=10000, seed=None):
    # Two-sided p-value for mean difference via random label shuffles
    if seed is not None:
        rnd = random.Random(seed)
    else:
        rnd = random
    obs = abs(stats.mean(a) - stats.mean(b))
    pool = a + b
    n1 = len(a)
    hits = 0
    for _ in range(iters):
        rnd.shuffle(pool)
        s1 = pool[:n1]
        s2 = pool[n1:]
        diff = abs(stats.mean(s1) - stats.mean(s2))
        if diff >= obs:
            hits += 1
    return hits / iters

# -------------------- Balanced random order --------------------
plan = []
for name in configs:
    plan += [(name, configs[name])] * N_PER_CONFIG
random.shuffle(plan)

# Execute plan
buckets = {name: {"times": [], "tokens": []} for name in configs}
for name, kwargs in plan:
    dt, tok = one_call(**kwargs)
    buckets[name]["times"].append(dt)
    buckets[name]["tokens"].append(tok)
    print(f"{name:<18} (shuffle) -> {dt:.2f}s")

# -------------------- Reporting --------------------
print("\n=== Summary ===")
for name in configs:
    s = summarize_times(buckets[name]["times"])
    toks = buckets[name]["tokens"]
    if toks:
        pt = stats.mean([t[0] for t in toks])
        ct = stats.mean([t[1] for t in toks])
        tt = stats.mean([t[2] for t in toks])
    else:
        pt = ct = tt = 0
    print(
        f"\n{name}\n"
        f"  n={s['n']}, mean={s['mean']:.3f}s, median={s['median']:.3f}s, σ={s['stdev']:.3f}s\n"
        f"  min={s['min']:.3f}s, max={s['max']:.3f}s\n"
        f"  avg tokens  prompt/comp/total: {pt:.1f}/{ct:.1f}/{tt:.1f}"
    )

a = buckets["All-parameters"]["times"]
t = buckets["Temperature-only"]["times"]

mean_diff = stats.mean(a) - stats.mean(t)  # >0 means All-params slower
ci_lo, ci_hi = bootstrap_mean_diff(a, t, B=BOOTSTRAPS)
pval = permutation_test(a, t, iters=PERM_TEST_IT, seed=RANDOM_SEED)
delta = cliff_delta(a, t)

print("\n=== Comparison (All-parameters minus Temperature-only) ===")
print(f"Mean difference: {mean_diff:.4f} s  (95% CI: {ci_lo:.4f}, {ci_hi:.4f})")
print(f"Permutation test p-value (two-sided): {pval:.4f}")
print(f"Cliff's delta: {delta:.3f}  (|delta|≈0.147 small, 0.33 medium, 0.474 large)")
print("\nInterpretation:")
print("• If the CI straddles 0 and p≈>0.05, differences are indistinguishable from noise.")
print("• Positive mean_diff means the 'All-parameters' config is slower; negative means faster.")