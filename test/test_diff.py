# import pandas as pd
# from io import StringIO
#
# # Simulating CSV file contents
# csv1 = StringIO("""Entity1,Entity2
# A,B
# C,D
# E,F""")
#
# csv2 = StringIO("""Entity1,Entity2
# A,B
# X,Y
# E,F""")
#
# # Reading the CSV data into Pandas DataFrames
# df1 = pd.read_csv(csv1)
# df2 = pd.read_csv(csv2)
#
# # Identifying rows that are different
# diff_df1 = df1[~df1.apply(tuple, 1).isin(df2.apply(tuple, 1))]
# diff_df2 = df2[~df2.apply(tuple, 1).isin(df1.apply(tuple, 1))]
#
# # Combining the different rows
# diff_df = pd.concat([diff_df1, diff_df2])
#
# # Writing the different rows to a new CSV file
# diff_df.to_csv('different_rows.csv', index=False)

import pandas as pd
from io import StringIO

# Simulating CSV file contents
csv1 = StringIO("""Entity1,Entity2
A,B
C,D
E,F""")

csv2 = StringIO("""Entity1,Entity2
A,B
X,Y
E,F""")

# Reading the CSV data into Pandas DataFrames
df1 = pd.read_csv(csv1)
df2 = pd.read_csv(csv2)

# Finding rows in df1 that are not in df2
diff_df = df1[~df1.apply(tuple, 1).isin(df2.apply(tuple, 1))]

# Writing the different rows to a new CSV file
diff_csv_path = 'different_rows.csv'
diff_df.to_csv(diff_csv_path, index=False)

# Output the path for reference
print(f"Different rows saved to: {diff_csv_path}")