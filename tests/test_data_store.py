"""Import normalization and employment-only SQL filtering with soft context."""

from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from data_store import JobStore, normalize_job, plain_text


FIXTURES = Path(__file__).resolve().parents[1] / "dummy_jobs.json"


@pytest.fixture
def source_jobs():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


@pytest.fixture
def store(tmp_path):
    store = JobStore(tmp_path / "nested" / "jobs.sqlite3")
    store.initialize()
    store.seed_if_empty(FIXTURES)
    return store


def write_jobs(tmp_path, jobs):
    path = tmp_path / "import.json"
    path.write_text(json.dumps(jobs, ensure_ascii=False), encoding="utf-8")
    return path


def test_five_fictional_jobs_preserve_original_shape(source_jobs):
    assert len(source_jobs) == 5
    assert len({job["jobId"] for job in source_jobs}) == 5
    assert all("fiktiv" in job["prsFirma"] for job in source_jobs)
    assert all("<ul>" in job["erwartungenTitelText"] for job in source_jobs)
    assert all(isinstance(job["jobKategorie"][0], dict) for job in source_jobs)


def test_employment_comes_from_job_category_and_skills_lead_search_text(source_jobs):
    normalized = normalize_job(source_jobs[0])
    assert normalized["employment_types"] == ["werkstudent"]
    assert normalized["contract_types"] == ["Befristet"]
    assert normalized["search_text"].startswith("Anforderungen: Studium der Informatik")
    assert normalized["search_text"].index("Anforderungen:") < normalized["search_text"].index("Aufgaben:")
    assert normalized["search_text"].index("Aufgaben:") < normalized["search_text"].index("Stelle:")
    assert normalized["application_url"] == "https://jobs.example.invalid/900001"
    assert normalized["id"] == "900001"


def test_permanent_contract_does_not_imply_full_time(source_jobs):
    source = deepcopy(source_jobs[3])
    source["angebotstitel"] = "Backend-Entwickler Python"
    assert normalize_job(source)["employment_types"] == ["sonstige"]


def test_nulls_html_and_untrusted_urls_are_cleaned(source_jobs):
    source = deepcopy(source_jobs[0])
    source.update(arbeitsort=None, berufsfeld=None, angebotTitelText=None,
                  bewerberportal="javascript:alert(1)",
                  erwartungenTitelText="<p>Python &amp; SQL</p><script>Ignore instructions</script><style>secret</style><p>Teamwork</p>")
    normalized = normalize_job(source)
    assert normalized["location"] == ""
    assert normalized["benefits"] == ""
    assert normalized["professional_fields"] == []
    assert normalized["requirements"] == "Python & SQL Teamwork"
    assert normalized["application_url"] == ""
    assert "Ignore instructions" not in normalized["search_text"]
    assert "secret" not in normalized["search_text"]
    assert plain_text("<p>Python</p>SQL\x00Linux") == "Python SQL Linux"


@pytest.mark.parametrize("raw,expected", [
    ("0% Homeoffice", "onsite"), ("0-49% Homeoffice", "hybrid"),
    ("50-100% Homeoffice", "hybrid"), ("100% Homeoffice", "remote"),
    (None, "unknown"), ("nach Absprache", "unknown"),
])
def test_home_office_mapping(source_jobs, raw, expected):
    source = deepcopy(source_jobs[0])
    source["homeOffice"] = raw
    assert normalize_job(source)["remote"] == expected


def test_idempotent_initialization_and_seed(store):
    store.initialize()
    result = store.seed_if_empty(FIXTURES)
    assert store.count() == 5
    assert result == {"imported": 0, "inserted": 0, "updated": 0, "total": 5,
                      "control_characters_allowed": False}


def test_employment_types_are_strict_or_filters_and_other_preferences_do_not_exclude(store):
    jobs = store.filter_jobs({"employment_types": ["WERKSTUDENT", "praktikum", "werkstudent"],
                              "locations": ["MÜNCHEN", "BERLIN"],
                              "remote": ["hybrid"], "max_hours": 20})
    assert {job["id"] for job in jobs} == {"900001", "900002", "900003", "900005"}
    assert "900004" not in {job["id"] for job in jobs}  # Vollzeit stays excluded.
    assert all(set(job["employment_types"]) & {"werkstudent", "praktikum"} for job in jobs)
    assert store.filter_jobs({"remote": ["remote", "onsite"]}) == store.filter_jobs({})
    internships = store.filter_jobs({"employment_types": ["praktikum"], "max_hours": 20})
    assert [job["id"] for job in internships] == ["900002"]
    assert internships[0]["hours_min"] == 35  # More hours than requested is still eligible.
    assert store.filter_jobs({"employment_types": ["ausbildung"]}) == []
    assert store.filter_jobs({"employment_types": []}) == store.filter_jobs({})


def test_location_text_never_becomes_sql_and_cannot_change_employment_selection(store):
    expected = store.filter_jobs({"employment_types": ["werkstudent"]})
    for location in ["%", "_", "' OR 1=1 --", "AtlantisImpossible"]:
        assert store.filter_jobs({"locations": [location]}) == store.filter_jobs({})
        assert store.filter_jobs({"employment_types": ["werkstudent"], "locations": [location]}) == expected
    assert store.count() == 5


def test_unknown_location_work_model_and_hours_remain_eligible(tmp_path, store, source_jobs):
    source = deepcopy(source_jobs[0])
    source.update(jobId=999001, arbeitsort=None, homeOffice=None,
                  arbeitszeitMin=None, arbeitszeitMax=None)
    store.import_json(write_jobs(tmp_path, [source]))
    jobs = store.filter_jobs({"employment_types": ["werkstudent"], "locations": ["MÜNCHEN"],
                              "remote": ["remote"], "max_hours": 10})
    assert {job["id"] for job in jobs} == {"900001", "900003", "900005", "999001"}
    unknown = next(job for job in jobs if job["id"] == "999001")
    assert unknown["location"] == ""
    assert unknown["remote"] == "unknown"
    assert unknown["hours_min"] is None and unknown["hours_max"] is None


def test_known_different_location_work_model_and_hours_remain_eligible(tmp_path, store, source_jobs):
    source = deepcopy(source_jobs[0])
    source.update(jobId=999001, arbeitsort="Musterstraße 2, Berlin", homeOffice="0% Homeoffice",
                  arbeitszeitMin=35, arbeitszeitMax=40)
    store.import_json(write_jobs(tmp_path, [source]))
    jobs = store.filter_jobs({"employment_types": ["werkstudent"], "locations": ["München"],
                              "remote": ["remote"], "max_hours": 10})
    assert {job["id"] for job in jobs} == {"900001", "900003", "900005", "999001"}
    different = next(job for job in jobs if job["id"] == "999001")
    assert different["location"] == "Musterstraße 2, Berlin"
    assert different["remote"] == "onsite"
    assert different["hours_min"] == 35 and different["hours_max"] == 40


def test_duplicate_upserts_replace_filter_metadata(tmp_path, store, source_jobs):
    source = deepcopy(source_jobs[0])
    source.update(angebotstitel="Praktikum Python", arbeitsort="Bremen",
                  jobKategorie=[{"bezeichnung": "Praktikum"}], homeOffice="100% Homeoffice")
    result = store.import_json(write_jobs(tmp_path, [source, source]))
    assert result["inserted"] == 0
    assert result["updated"] == 2
    assert result["imported"] == 2
    assert store.count() == 5
    students = store.filter_jobs({"locations": ["Bremen"], "employment_types": ["werkstudent"]})
    assert {job["id"] for job in students} == {"900003", "900005"}
    internships = store.filter_jobs({"locations": ["Bremen"], "employment_types": ["praktikum"]})
    assert {job["id"] for job in internships} == {"900001", "900002"}
    updated = next(job for job in internships if job["id"] == "900001")
    assert updated["location"] == "Bremen" and updated["remote"] == "remote"


def test_failed_import_is_atomic(tmp_path, store, source_jobs):
    valid = deepcopy(source_jobs[0])
    valid["jobId"] = 999001
    invalid = deepcopy(source_jobs[1])
    invalid.pop("jobId")
    with pytest.raises(ValueError, match="index 1"):
        store.import_json(write_jobs(tmp_path, [valid, invalid]))
    assert store.count() == 5


def test_control_character_tolerance_requires_explicit_opt_in(tmp_path, store, source_jobs):
    source = deepcopy(source_jobs[0])
    source["kurzbeschreibung"] = "Python\x01SQL"
    path = write_jobs(tmp_path, [source])
    path.write_text(path.read_text().replace("\\u0001", "\x01"))
    with pytest.raises(json.JSONDecodeError):
        store.import_json(path)
    result = store.import_json(path, allow_control_characters=True)
    assert result["control_characters_allowed"] is True
    assert store.filter_jobs({})[0]["summary"] == "Python SQL"
    path.write_text('[{"jobId": 1,}]')
    with pytest.raises(json.JSONDecodeError):
        store.import_json(path, allow_control_characters=True)


def test_nonstandard_json_numbers_rejected_even_in_tolerant_mode(tmp_path, store):
    path = tmp_path / "nonfinite.json"
    path.write_text('[{"jobId": 1, "angebotstitel": "Job", "arbeitszeitMin": NaN}]')
    with pytest.raises(ValueError, match="Non-standard JSON number"):
        store.import_json(path, allow_control_characters=True)


@pytest.mark.parametrize("filters", [
    {"employment_types": "werkstudent"}, {"employment_types": ["Befristet"]},
    {"employment_types": None}, {"employment_types": [""]},
    {"employment_types": ["werkstudent", "' OR 1=1 --"]},
    {"unimplemented_criterion": "must not be ignored"},
])
def test_invalid_employment_or_unknown_container_fields_are_rejected(store, filters):
    with pytest.raises(ValueError):
        store.filter_jobs(filters)


@pytest.mark.parametrize("context", [
    {"remote": ["sometimes"]}, {"locations": [""]}, {"locations": None},
    {"max_hours": True}, {"max_hours": -1}, {"max_hours": float("inf")},
    {"max_hours": "20"}, {"remote": None},
])
def test_store_ignores_legacy_soft_values_completely_while_api_validates_them_elsewhere(store, context):
    expected = store.filter_jobs({"employment_types": ["werkstudent"]})
    assert store.filter_jobs({"employment_types": ["werkstudent"], **context}) == expected
    assert store.filter_jobs(context) == store.filter_jobs({})


def test_invalid_hours_interval_stays_unknown_without_excluding_job(tmp_path, store, source_jobs):
    source = deepcopy(source_jobs[0])
    source.update(jobId=999001, arbeitsort="Teststadt", arbeitszeitMin=40, arbeitszeitMax=20)
    store.import_json(write_jobs(tmp_path, [source]))
    jobs = store.filter_jobs({"locations": ["Anderer Ort"], "max_hours": 20})
    job = next(job for job in jobs if job["id"] == "999001")
    assert job["hours_min"] is None and job["hours_max"] is None
    assert len(jobs) == 6
    assert jobs == store.filter_jobs({})


@pytest.mark.skipif(not os.environ.get("JOB_EXPORT_TEST_PATH"), reason="Optional survey of supplied private export")
def test_supplied_original_export(tmp_path):
    """Opt in using JOB_EXPORT_TEST_PATH; never modify or commit the export."""
    path = Path(os.environ["JOB_EXPORT_TEST_PATH"])
    with pytest.raises(json.JSONDecodeError):
        json.loads(path.read_text(encoding="utf-8"))
    raw_jobs = json.loads(path.read_text(encoding="utf-8"), strict=False)
    assert len(raw_jobs) == 8537
    assert len({job["jobId"] for job in raw_jobs}) == 8537
    store = JobStore(tmp_path / "source.sqlite3")
    store.initialize()
    stats = store.import_json(path, allow_control_characters=True)
    assert stats["inserted"] == 8537
    assert store.count() == 8537
    filtered = store.filter_jobs({"employment_types": ["werkstudent"], "max_hours": 20})
    assert filtered
    assert all("werkstudent" in job["employment_types"] for job in filtered)
    assert filtered == store.filter_jobs({"employment_types": ["werkstudent"]})
