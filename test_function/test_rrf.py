from collections import defaultdict

def reciprocal_rank_fusion(*rankings):
    # Create a dictionary to store the reciprocal ranks for each item
    reciprocal_ranks = defaultdict(float)

    # Compute the reciprocal ranks for each item in each ranking
    for i, ranking in enumerate(rankings):
        for j, item in enumerate(ranking):
            reciprocal_rank = 1 / (j + 1)  # Reciprocal rank for the item
            reciprocal_ranks[item] += reciprocal_rank

    # Sort the items based on their summed reciprocal ranks in descending order
    fused_ranking = sorted(reciprocal_ranks.keys(), key=lambda item: reciprocal_ranks[item], reverse=True)

    return fused_ranking

# Define your rankings
ranking1 = ["0", "1", "2", "3", "4", "5"]
ranking2 = ["3", "2", "1", "0", "4", "6"]
ranking3 = ["2", "1", "0", "3", "4", "7"]

# Use the reciprocal_rank_fusion function to generate the fused ranking
fused_ranking = reciprocal_rank_fusion(ranking1, ranking2, ranking3)

# Print the fused ranking
print(fused_ranking)
