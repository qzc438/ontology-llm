import numpy as np

# Example vectors and classifications
vector_a = np.array([2.5, 1.0])
vector_b = np.array([0.8, 3.0])
class_a_indicator = np.array([1, 0])  # Class A indicator
class_b_indicator = np.array([0, 1])  # Class B indicator

# Combine vectors with classification indicators
combined_vector_a = np.concatenate([vector_a, class_a_indicator])
combined_vector_b = np.concatenate([vector_b, class_b_indicator])

print("Combined vector for a (Class A):", combined_vector_a)
print("Combined vector for b (Class B):", combined_vector_b)

# Example text embeddings and graph embeddings
text_embeddings = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])  # Text embeddings for two nodes
graph_embeddings = np.array([[0.7, 0.8, 0.9], [1.0, 1.1, 1.2]])  # Graph embeddings for two nodes

# Combine text and graph embeddings via concatenation
combined_embeddings = np.concatenate((text_embeddings, graph_embeddings), axis=1)

# Now, you can use combined_embeddings for downstream tasks (e.g., classification)
print("Combined Embeddings:")
print(combined_embeddings)