from datetime import datetime, timedelta, timezone

import pytest

from ghostradar.analysis import baselines


@pytest.mark.parametrize(
    "title,kldb,level",
    [
        ("Softwareentwickler Java (m/w/d)", "434", "4"),
        ("Pflegefachkraft (w/m/d)", "813x+821", "2"),
        ("Pflegehelfer (m/w/d)", "813x+821", "1"),
        ("Lagerhelfer (m/w/d)", "513", "1"),
        ("Fachkraft für Lagerlogistik", "513", "2"),
        ("Staplerfahrer (m/w/d)", "525", "1"),
        ("Berufskraftfahrer CE", "521", "2"),
        ("Mechanical Engineer", "251", None),
        ("Sales Engineer", "611", "3"),
        ("Personalentwickler (m/w/d)", "715", "3"),
        ("Steuerfachangestellte (m/w/d)", "723", "3"),
        ("Senior Data Scientist", "431", "4"),
        ("Erzieher (m/w/d)", "831", "2"),
    ],
)
def test_title_classification(title, kldb, level):
    got_kldb, got_level, _ = baselines.classify(title)
    assert got_kldb == kldb
    if level:
        assert got_level == level


def test_baseline_uses_ba_table():
    base = baselines.baseline_for("Softwareentwickler (m/w/d)")
    table = baselines.load_table()
    assert table.national, "run scripts/update_baselines.py to create data/ba_engpass.csv"
    assert base.vakanzzeit_days == table.national[("434", "4")].days
    assert base.expected_days == max(baselines.MIN_EXPECTED_DAYS, base.vakanzzeit_days + baselines.LEAD_DAYS)
    assert base.shortage


def test_regional_baseline_when_available():
    table = baselines.load_table()
    key = next(k for k in table.regional if k[0] == "Bayern")
    title = {"434": "Softwareentwickler", "813x+821": "Pflegefachkraft"}.get(key[1])
    if title is None:
        pytest.skip("no mapped title for the first Bavarian row")
    base = baselines.baseline_for(title, "", "Bayern")
    assert base.region in {"Bayern", "Deutschland - Berufsgruppen"}


def test_unknown_title_falls_back_to_national_median():
    base = baselines.baseline_for("Zauberer am Hofe")
    assert base.kldb is None
    assert base.vakanzzeit_days == baselines.load_table().overall_median


def test_empirical_tail_needs_enough_data():
    now = datetime(2026, 10, 24, tzinfo=timezone.utc)
    few = [((now - timedelta(days=50)).isoformat(), None, "active")] * 10
    assert baselines.empirical_tail(100, few, now) is None
    many = [((now - timedelta(days=d)).isoformat(), now.isoformat(), "removed") for d in range(1, 101)]
    assert baselines.empirical_tail(95, many, now) == pytest.approx(0.06, abs=0.01)


def test_machine_and_device_testing_is_not_software_testing():
    assert baselines.classify("Mechanical Test Engineer (w/m/d) Applicators", "")[0] == "271"
    assert baselines.classify("Prüfingenieur Fahrzeugtechnik (m/w/d)", "")[0] == "271"
    assert baselines.classify("Software Test Engineer (m/w/d)", "")[0] == "434"
