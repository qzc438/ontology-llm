import pandas as pd


df = pd.read_csv('../result-conference-0.90.csv')

df = df[df['Alignment'].str.endswith('/')]

print(df)

average_precision = df['Precision'].mean()
average_recall = df['Recall'].mean()
average_f1 = df['F1'].mean()
print(f"{average_precision:.2f}", f"{average_recall:.2f}", f"{average_f1:.2f}")