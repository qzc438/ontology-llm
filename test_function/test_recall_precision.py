import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.cm as cm
from matplotlib.font_manager import FontProperties

# plt.style.use('tableau-colorblind10')
# colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']

def get_cmap_colors(cmap_name, num_colors):
    cmap = plt.get_cmap(cmap_name)
    colors = cmap(np.linspace(0, 1, num_colors))
    return colors


# Choose a colormap and the number of colors to sample
cmap_name = 'tab20'
num_colors = 20
# Get a list of colors from the colormap
colors_list = get_cmap_colors(cmap_name, num_colors)
# Convert colors to a list of hex color codes
colors_hex_list = ['#' + ''.join(f'{int(c * 255):02X}' for c in color[:3]) for color in colors_list]
colors_hex_list.remove('#D62728')
# Print the hex color codes
# for color_hex in colors_hex_list:
#     print(color_hex)

new_matcher = "Agent-OM*"

# Read the csv file
df = pd.read_csv('../benchmark_2022/conference/conference_benchmark.csv')
df = df.sort_values(by='Name', key=lambda col: col.apply(lambda x: (x, '') if x == new_matcher else ('', x)))
precision = df['Precision'].values
recall = df['Recall'].values
names = df['Name'].values

# Create a scatter plot
plt.figure(figsize=(4.5, 4.5))

# plot precision and recall
for i, (rec, prec, name) in enumerate(zip(recall, precision, names)):
    if name == new_matcher:
        plt.scatter(rec, prec, s=100, marker='o', label=f'{name}', color='#D62728')
    else:
        plt.scatter(rec, prec, s=100, marker='^', label=f'{name}', color=colors_hex_list[i])
    # plt.text(rec-0.01, prec-0.05, f'{name}', fontsize=12)

# Calculate and plot the iso-F1 curves
f1_levels = np.linspace(0.1, 0.9, num=9)
for f1 in f1_levels:
    x = np.linspace(0.001, 1, 1000)
    y = f1 * x / (2 * x - f1)
    valid_idx = np.where(y >= 0)  # valid indices where y is non-negative
    plt.plot(x[valid_idx], y[valid_idx], color='black', alpha=0.3, linestyle='--')
    plt.annotate('F1={0:0.1f}'.format(f1), xy=(x[-10], y[-10]), textcoords="offset points", xytext=(-20, -10),
                 ha='center')

plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.0])
plt.xlabel('Recall')
plt.ylabel('Precision')
# plt.title('Precision-Recall Scatter Plot with iso-F1 Curves')
plt.legend(loc='upper right', bbox_to_anchor=(1.45, 1), frameon=False)
# title_font = FontProperties(weight='bold')
# plt.legend(title="System Name", title_fontproperties=title_font, loc='upper right', bbox_to_anchor=(1.4, 1), frameon=False)
# plt.subplots_adjust(left=0)

# save the plot
plt.savefig('test_function.png', bbox_inches='tight', pad_inches=0.1)
# Show the plot
plt.show()
