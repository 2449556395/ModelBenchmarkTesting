HUMAN_REVIEW_DIMENSIONS = [
    'readability', 'minimal_change', 'design', 'test_quality', 'security', 'project_style'
]


def empty_review():
    return {k: None for k in HUMAN_REVIEW_DIMENSIONS}
