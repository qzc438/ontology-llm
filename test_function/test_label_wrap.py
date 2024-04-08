import matplotlib.pyplot as plt

# Create a plot with multiple legend labels
x = [1, 2, 3]
y = [4, 5, 6]

labels = [
    "This is a very long legend label that needs to be wrapped",
    "Label 2",
    "Another long legend label that should wrap",
    "Label 4",
]

# Wrap the legend labels at spaces
wrapped_labels = [label.replace(" ", "\n") for label in labels]

# Create the plot
plt.plot(x, y)
plt.plot(x, y)

# Create the legend with wrapped labels
plt.legend(wrapped_labels, loc='upper left', title="Legend Label")

# Display the plot
plt.show()