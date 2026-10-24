from datetime import datetime, timedelta, timezone

from ghostradar.analysis import dedup

TEXT = (
    "Wir suchen einen Backend-Entwickler (m/w/d) mit Erfahrung in Python, Django und PostgreSQL. "
    "Du entwickelst unsere Plattform weiter, arbeitest eng mit Produkt und Design zusammen und "
    "übernimmst Verantwortung für Qualität, Tests und Deployment in der Cloud."
)


def test_signature_similarity_separates_cosmetic_and_new_content():
    a = dedup.signature(TEXT)
    cosmetic = dedup.signature(TEXT.replace("Django", "Flask"))
    other = dedup.signature("Wir suchen eine Pflegefachkraft für unsere Intensivstation im Schichtdienst mit Herz.")
    assert dedup.similarity(a, cosmetic) >= dedup.COSMETIC
    assert dedup.similarity(a, other) < dedup.DIFFERENT


def test_cluster_summary_counts_cosmetic_reposts_and_total_lifetime():
    now = datetime(2026, 10, 24, tzinfo=timezone.utc)
    sig = dedup.signature(TEXT)
    instances = [
        dedup.Instance(1, "a", now - timedelta(days=200), now - timedelta(days=150), sig, None, None),
        dedup.Instance(2, "b", now - timedelta(days=148), now - timedelta(days=100), sig, None, None),
        dedup.Instance(3, "c", now - timedelta(days=97), None, sig, None, None),
    ]
    summary = dedup.summarise_cluster(instances, now)
    assert summary.instances == 3
    assert summary.cosmetic == 2
    assert summary.total_live_days == 200  # short gaps count as continuous presence


def test_parallel_copies_are_not_reposts():
    now = datetime(2026, 10, 24, tzinfo=timezone.utc)
    sig = dedup.signature(TEXT)
    instances = [
        dedup.Instance(1, "a", now - timedelta(days=30), None, sig, None, None),
        dedup.Instance(2, "b", now - timedelta(days=20), None, sig, None, None),
        dedup.Instance(3, "c", now - timedelta(days=1), None, sig, None, None),  # new copy while others are live
    ]
    assert dedup.summarise_cluster(instances, now).cosmetic == 0


def test_replacement_with_short_overlap_counts_as_repost():
    now = datetime(2026, 10, 24, tzinfo=timezone.utc)
    sig = dedup.signature(TEXT)
    instances = [
        dedup.Instance(1, "a", now - timedelta(days=90), now - timedelta(days=40), sig, None, None),
        dedup.Instance(2, "b", now - timedelta(days=45), None, sig, None, None),  # posted 5 days before the old one went
    ]
    assert dedup.summarise_cluster(instances, now).cosmetic == 1


def test_find_cluster_prefers_requisition_and_title():
    sig = dedup.signature(TEXT)
    cands = [
        {"id": 1, "cluster_id": 1, "title_key": "backend entwickler", "requisition_id": "R1", "city": "Berlin", "signature": sig},
        {"id": 2, "cluster_id": 2, "title_key": "pflegefachkraft", "requisition_id": None, "city": "Berlin", "signature": None},
    ]
    row = {"id": 3, "title_key": "backend entwickler", "requisition_id": None, "city": "Berlin", "signature": sig}
    assert dedup.find_cluster(row, cands) == 1
    assert dedup.find_cluster({"id": 4, "title_key": "x", "requisition_id": "R1"}, cands) == 1
    assert dedup.find_cluster({"id": 5, "title_key": "koch", "requisition_id": None, "city": "Berlin"}, cands) is None
