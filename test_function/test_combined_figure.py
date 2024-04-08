import pandas as pd
import matplotlib.pyplot as plt

# Initial datasets
data1 = {
    'Name': ['Model A', 'Model B', 'Model C'],
    'Precision': [0.9, 0.85, 0.95],
    'Recall': [0.8, 0.9, 0.85],
    'F1': [0.85, 0.875, 0.9]
}

data2 = {
    'Name': ['Model B', 'Model C', 'Model D'],
    'Precision': [0.8, 0.75, 0.85],
    'Recall': [0.7, 0.8, 0.75],
    'F1': [0.75, 0.775, 0.8]
}

df1 = pd.DataFrame(data1)
df2 = pd.DataFrame(data2)

# Dynamically combining unique model names from both datasets
combined_names = pd.concat([df1['Name'], df2['Name']]).unique().tolist()

# Creating the plot
fig, axs = plt.subplots(1, 2, figsize=(12, 6), sharey=True)

# Creating a color map based on the dynamically combined list of names
color_map = {name: f'C{i}' for i, name in enumerate(combined_names)}

# Plotting the first dataset
for i, row in df1.iterrows():
    axs[0].plot(['Precision', 'Recall', 'F1'], row[['Precision', 'Recall', 'F1']], marker='o', label=row['Name'], color=color_map.get(row['Name'], 'grey'))

# Plotting the second dataset
for i, row in df2.iterrows():
    axs[1].plot(['Precision', 'Recall', 'F1'], row[['Precision', 'Recall', 'F1']], marker='o', label=row['Name'], color=color_map.get(row['Name'], 'grey'))

# Adding titles, labels, and setting up the grid
axs[0].set_title('Dataset 1')
axs[1].set_title('Dataset 2')
axs[0].set_ylim(0, 1)  # Assuming scores range from 0 to 1
axs[0].set_ylabel('Scores')
for ax in axs:
    ax.set_xlabel('Metrics')
    ax.grid(True)

# Creating custom handles for the dynamically determined legend
handles = [plt.Line2D([0], [0], color=color_map[name], marker='o', linestyle='-', label=name) for name in combined_names]

# Adding the dynamically determined legend
fig.legend(handles, combined_names, loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=len(combined_names))

plt.tight_layout()
plt.show()