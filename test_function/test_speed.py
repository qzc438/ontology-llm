import os
import time
import statistics as stats
import dotenv
from openai import OpenAI

# --- Setup ---
dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
model = "gpt-3.5-turbo"  # use your target model
N = 10                   # how many runs per config

SYSTEM_MSG = {"role": "system", "content": "You are a deterministic AI assistant."}
USER_MSG   = {"role": "user",   "content": "20-paragraph article about apples"}

def run_benchmark(name, **gen_kwargs):
    times = []
    prompt_toks = []
    completion_toks = []
    total_toks = []
    print(f"\n--- Running: {name} ---")
    for i in range(N):
        t0 = time.perf_counter()
        resp = client.chat.completions.create(
            model=model,
            messages=[SYSTEM_MSG, USER_MSG],
            **gen_kwargs
        )
        dt = time.perf_counter() - t0
        times.append(dt)

        usage = resp.usage  # has prompt_tokens, completion_tokens, total_tokens
        if usage:
            prompt_toks.append(usage.prompt_tokens or 0)
            completion_toks.append(usage.completion_tokens or 0)
            total_toks.append(usage.total_tokens or 0)

        # print a short preview so the loop feels alive
        preview = resp.choices[0].message.content[:60].replace("\n", " ")
        print(f"Run {i+1:02d}: {dt:.2f}s | “{preview}..”")

    # summarize
    total_time = sum(times)
    avg_time = stats.mean(times)
    std_time = stats.pstdev(times) if len(times) > 1 else 0.0

    tok_info = ""
    if total_toks:
        tok_sum = sum(total_toks)
        tok_per_sec = tok_sum / total_time if total_time > 0 else float('inf')
        tok_info = (
            f"\nTokens — prompt/comp/total (avg): "
            f"{(sum(prompt_toks)/N):.1f}/"
            f"{(sum(completion_toks)/N):.1f}/"
            f"{(sum(total_toks)/N):.1f}"
            f"\nThroughput: {tok_per_sec:.1f} tokens/sec"
        )

    print(
        f"\n{name} results:"
        f"\n  Calls: {N}"
        f"\n  Total time: {total_time:.2f}s"
        f"\n  Avg time per call: {avg_time:.2f}s (σ={std_time:.2f}s)"
        f"{tok_info}"
    )

# --- Configs to test ---

# 1) Temperature-only
temp_only = dict(
    temperature=0.0,
    # NOTE: we intentionally leave out top_p, presence_penalty, frequency_penalty
)

# 2) All parameters
all_params = dict(
    temperature=0.0,
    top_p=1.0,
    presence_penalty=0.0,
    frequency_penalty=0.0,
)

# --- Run benchmarks ---
run_benchmark("Temperature-only", **temp_only)
run_benchmark("All-parameters", **all_params)