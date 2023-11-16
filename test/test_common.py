import pandas as pd
from io import StringIO

data1 = """
Entity1,Entity2,Value1
A,X,10
B,Y,20
C,Z,30
D,W,40
"""

data2 = """
Entity1,Entity2,Value2
E,V,300
F,U,400
A,X,100
B,Y,200
"""

df1 = pd.read_csv(StringIO(data1))
df2 = pd.read_csv(StringIO(data2))

# Find common values
# common_values = df1[df1['Entity1'].isin(df2['Entity1']) & df1['Entity2'].isin(df2['Entity2'])]
common_values = pd.merge(df1, df2, on=['Entity1', 'Entity2'])

print(common_values)
