import numpy as np

# Example text embeddings and graph embeddings
text_embeddings = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])  # Text embeddings for two nodes
graph_embeddings = np.array([[0.7, 0.8, 0.9], [1.0, 1.1, 1.2]])  # Graph embeddings for two nodes

# Combine text and graph embeddings via concatenation
combined_embeddings = np.concatenate((text_embeddings, graph_embeddings), axis=1)

# Now, you can use combined_embeddings for downstream tasks (e.g., classification)
print("Combined Embeddings:")
print(combined_embeddings)