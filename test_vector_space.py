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