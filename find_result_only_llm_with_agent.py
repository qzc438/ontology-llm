import pandas as pd

# load csv
df = pd.read_csv("result.csv")
# filter alignment ends with "llm_with_agent"
filtered = df[df["Alignment"].astype(str).str.endswith("llm_with_agent")]
# save to new csv
filtered.to_csv("result_llm_with_agent.csv", index=False)
print("Saved to result_llm_with_agent.csv")