import collections
from itertools import groupby


def reciprocal_rank_fusion_all_with_grouped_scores(*rankings):
    reciprocal_ranks = collections.defaultdict(float)
    for ranking in rankings:
        if not isinstance(ranking, (list, tuple)):
            ranking = [ranking]
        for position, item in enumerate(ranking, start=1):
            reciprocal_ranks[item] += 1 / position

    # Sort by reciprocal rank value, then by item lexicographically for tie-breaking
    fused_ranking_with_scores = sorted(reciprocal_ranks.items(), key=lambda x: (-x[1], x[0]))

    # Group items by their score
    grouped_items_by_score = [(score, [item for item, _ in items]) for score, items in
                              groupby(fused_ranking_with_scores, key=lambda x: x[1])]

    return grouped_items_by_score


# Example usage
rankings = [
    ['a', 'b', 'c'],
    ['b', 'a', 'd'],
    ['e', 'g', 'g', 'h']
]

grouped_fused_ranking_with_scores = reciprocal_rank_fusion_all_with_grouped_scores(*rankings)
for score, items in grouped_fused_ranking_with_scores:
    print(f"Score: {score:.4f}, Items: {items}")
