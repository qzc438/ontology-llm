import pandas as pd

df = pd.read_csv('result.csv')

average_precision = df['Precision'].mean()
average_recall = df['Recall'].mean()

print(average_precision, average_recall)