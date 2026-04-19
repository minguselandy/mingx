from phase1.orderings import build_orderings


def test_build_orderings_is_stable_for_question_and_seed():
    paragraph_ids = [0, 1, 2, 3, 4]

    first = build_orderings("2hop__256778_131879", paragraph_ids, k_lcb=5, seed=20260418)
    second = build_orderings("2hop__256778_131879", paragraph_ids, k_lcb=5, seed=20260418)

    assert first == second
    assert first[0].ordering_id == "canonical_v1"
    assert first[0].paragraph_ids == tuple(paragraph_ids)
    assert len(first) == 5
    assert len({ordering.paragraph_ids for ordering in first}) == 5
