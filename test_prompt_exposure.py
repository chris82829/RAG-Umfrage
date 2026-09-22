"""Offline checks for immutable per-participant system-prompt exposure."""
import csv
import io
import json
import secrets
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import create_app
from persona_mlds import advisor_to_mlds
from privacy import token_hash
from system_prompt_store import DEFAULT_SYSTEM_PROMPTS, SystemPromptStore


class FakeRetriever:
    def search(self, jobs, query, top_k=20):
        return [
            {
                "job": job,
                "rrf_score": 0.1,
                "bm25_rank": index + 1,
                "semantic_rank": index + 1,
                "bm25_score": 1,
                "semantic_score": 0.8,
            }
            for index, job in enumerate(jobs[:top_k])
        ]


class CapturingModel:
    def __init__(self):
        self.prompts = []

    def rerank(self, persona, profile, candidates, **kwargs):
        self.prompts.append(kwargs.get("system_prompt"))
        return {
            "rankings": [
                {
                    "job_id": item["job"]["id"],
                    "score": 80,
                    "reason": "Python passt.",
                    "matched_skills": ["Python"],
                    "missing_skills": [],
                }
                for item in candidates
            ],
            "assistant_message": "Python passt. Welche Tätigkeit ist dir wichtiger?",
        }


class ParticipantPromptSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "prompt.sqlite3"
        self.store = SystemPromptStore(self.db_path)

    def test_snapshot_stays_bound_while_new_participant_gets_new_revision(self):
        first_digest = "a" * 64
        second_digest = "b" * 64
        first = self.store.participant_snapshot(
            first_digest, "diana-abc-v4", "career_fixed"
        )
        prompts = dict(DEFAULT_SYSTEM_PROMPTS)
        prompts["career_fixed"] += "\nBleibe bei jeder Antwort besonders konkret."
        self.store.update(self.store.get()["revision"], prompts)

        retained = self.store.participant_snapshot(
            first_digest, "diana-abc-v4", "career_fixed"
        )
        newer = self.store.participant_snapshot(
            second_digest, "diana-abc-v4", "career_fixed"
        )
        self.assertEqual(retained, first)
        self.assertEqual(retained["revision"], 1)
        self.assertEqual(newer["revision"], 2)
        self.assertNotEqual(retained["sha256"], newer["sha256"])
        self.assertNotEqual(retained["text"], newer["text"])

    def test_empty_a_is_recorded_as_versioned_empty_prompt_without_system_message(self):
        snapshot = self.store.participant_snapshot(
            "c" * 64, "diana-abc-v4", "unprompted"
        )
        self.assertEqual(snapshot["policy"], "unprompted")
        self.assertEqual(snapshot["revision"], 1)
        self.assertEqual(snapshot["text"], "")
        self.assertEqual(len(snapshot["sha256"]), 64)
        with sqlite3.connect(self.db_path) as db:
            row = db.execute(
                """SELECT text, revision, sha256
                   FROM system_prompt_participant_snapshots"""
            ).fetchone()
        self.assertEqual(row, ("", 1, snapshot["sha256"]))

    def test_a_participant_keeps_empty_revision_while_new_participant_gets_configured_a(self):
        first = self.store.participant_snapshot(
            "e" * 64, "diana-abc-v4", "unprompted"
        )
        prompts = {
            key: value["text"] for key, value in self.store.get()["prompts"].items()
        }
        prompts["unprompted"] = "Du bist ein allgemeiner KI-Assistent."
        self.store.update(self.store.get()["revision"], prompts)
        retained = self.store.participant_snapshot(
            "e" * 64, "diana-abc-v4", "unprompted"
        )
        newer = self.store.participant_snapshot(
            "f" * 64, "diana-abc-v4", "unprompted"
        )
        self.assertEqual(retained, first)
        self.assertEqual(retained["text"], "")
        self.assertEqual(newer["text"], "Du bist ein allgemeiner KI-Assistent.")
        self.assertEqual(newer["revision"], first["revision"] + 1)
        self.assertNotEqual(newer["sha256"], first["sha256"])


class PromptExposureAppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.db_path = root / "app.sqlite3"
        notice = root / "privacy.json"
        notice.write_text(
            json.dumps(
                {
                    "approved": True,
                    "controller": "Test",
                    "retention": "Test",
                    "openai_processing": "Test",
                    "technical_processing": "Test",
                }
            ),
            encoding="utf-8",
        )
        self.app = create_app(
            {
                "TESTING": True,
                "PRIVACY_REQUIRED": True,
                "DATABASE_PATH": self.db_path,
                "PRIVACY_SETTINGS_PATH": notice,
                "SEED_DUMMY_DATA": False,
            }
        )
        self.client = self.app.test_client()

    def consent(self):
        token = secrets.token_hex(32)
        headers = {"X-Diana-Consent": token}
        notice = self.client.get("/api/privacy", headers=headers).get_json()["notice"]
        accepted = self.client.post(
            "/api/privacy/consent",
            headers=headers,
            json={
                "token": token,
                "version": notice["version"],
                "purpose": "study",
                "accepted": True,
            },
        )
        self.assertEqual(accepted.status_code, 200)
        return token, headers

    def test_assignment_endpoint_binds_once_and_admin_export_has_only_metadata(self):
        token, headers = self.consent()
        with patch("study_assignment.secrets.choice", return_value="B"):
            assigned = self.client.post("/api/study-assignment", headers=headers)
        self.assertEqual(assigned.status_code, 200)
        digest = token_hash(token)
        prompt_store = self.app.extensions["system_prompt_store"]
        with sqlite3.connect(self.db_path) as db:
            first = db.execute(
                """SELECT policy, revision, sha256, text
                   FROM system_prompt_participant_snapshots WHERE token_hash=?""",
                (digest,),
            ).fetchone()
        self.assertEqual(first[0], "career_fixed")
        self.assertEqual(first[1], 1)
        self.assertEqual(len(first[2]), 64)

        prompts = {
            key: value["text"] for key, value in prompt_store.get()["prompts"].items()
        }
        prompts["career_fixed"] += "\nNutze ab jetzt eine neue Verwaltungsrevision."
        prompt_store.update(prompt_store.get()["revision"], prompts)
        self.assertEqual(
            self.client.post("/api/study-assignment", headers=headers).status_code, 200
        )
        with sqlite3.connect(self.db_path) as db:
            retained = db.execute(
                """SELECT policy, revision, sha256, text
                   FROM system_prompt_participant_snapshots WHERE token_hash=?""",
                (digest,),
            ).fetchone()
        self.assertEqual(retained, first)

        submission_id = "survey-prompt-exposure"
        historical_digest = "d" * 64
        prompt_store.participant_snapshot(
            historical_digest, "diana-abc-v3", "career_fixed"
        )
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                "INSERT INTO survey_responses VALUES (?, ?, ?)",
                (submission_id, "2026-09-21T12:00:00+00:00", json.dumps({"version": "diana-v13", "study_arm": "B"})),
            )
            db.execute(
                "INSERT INTO privacy_links VALUES ('survey', ?, ?)",
                (submission_id, digest),
            )
            db.execute(
                """INSERT INTO privacy_consents
                   (token_hash, version, notice_json, accepted_at, withdrawn_at,
                    participation_id, purpose) VALUES (?, 'old', '{}', ?, NULL, ?, 'study')""",
                (historical_digest, "2026-09-20T12:00:00+00:00", "DIANA-HISTORICAL"),
            )
            db.execute(
                "INSERT INTO study_assignments VALUES (?, 'diana-abc-v3', 'B', ?, 0)",
                (historical_digest, "2026-09-20T12:00:00+00:00"),
            )
            db.execute(
                "INSERT INTO survey_responses VALUES ('survey-historical', ?, ?)",
                ("2026-09-20T12:00:00+00:00", json.dumps({"version": "diana-v10", "study_arm": "B"})),
            )
            db.execute(
                "INSERT INTO privacy_links VALUES ('survey', 'survey-historical', ?)",
                (historical_digest,),
            )

        admin = self.app.extensions["admin_data"]
        records = admin.records()
        row = next(item for item in records if item["id"] == submission_id)
        historical = next(item for item in records if item["id"] == "survey-historical")
        self.assertEqual(row["system_prompt_policy"], "career_fixed")
        self.assertEqual(row["system_prompt_revision"], 1)
        self.assertEqual(row["system_prompt_base_sha256"], first[2])
        self.assertNotIn("system_prompt_text", row)
        self.assertEqual(historical["system_prompt_policy"], "")
        self.assertEqual(historical["system_prompt_revision"], "")
        self.assertEqual(historical["system_prompt_base_sha256"], "")

        exported = admin.csv_data([row], columns="technical").decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(exported), delimiter=";"))
        self.assertEqual(rows[0]["system_prompt_policy"], "career_fixed")
        self.assertEqual(rows[0]["system_prompt_revision"], "1")
        self.assertEqual(rows[0]["system_prompt_base_sha256"], first[2])
        self.assertNotIn(first[3], exported)
        codebook = {item["technical_variable"]: item for item in admin.codebook()}
        self.assertEqual(codebook["system_prompt_policy"]["versions"], ["diana-v13"])
        self.assertIn("kein Systemprompt", codebook["system_prompt_policy"]["codes"]["unprompted"])

        participation_id = row["participation_id"]
        self.app.extensions["privacy_store"].delete_participant(participation_id)
        with sqlite3.connect(self.db_path) as db:
            remaining = db.execute(
                "SELECT COUNT(*) FROM system_prompt_participant_snapshots WHERE token_hash=?",
                (digest,),
            ).fetchone()[0]
        self.assertEqual(remaining, 0)

    def test_configured_a_is_frozen_and_exported_by_revision_without_prompt_text(self):
        prompt_store = self.app.extensions["system_prompt_store"]
        current = prompt_store.get()
        prompts = {
            key: value["text"] for key, value in current["prompts"].items()
        }
        a_prompt = "Du bist ein allgemeiner KI-Assistent."
        prompts["unprompted"] = a_prompt
        prompt_store.update(current["revision"], prompts)

        token, headers = self.consent()
        with patch("study_assignment.secrets.choice", return_value="A"):
            response = self.client.post("/api/study-assignment", headers=headers)
        self.assertEqual(response.status_code, 200)
        submission_id = "survey-configured-a"
        digest = token_hash(token)
        with sqlite3.connect(self.db_path) as db:
            snapshot = db.execute(
                """SELECT policy, revision, sha256, text
                   FROM system_prompt_participant_snapshots WHERE token_hash=?""",
                (digest,),
            ).fetchone()
            db.execute(
                "INSERT INTO survey_responses VALUES (?, ?, ?)",
                (
                    submission_id,
                    "2026-09-21T12:30:00+00:00",
                    json.dumps({"version": "diana-v13", "study_arm": "A"}),
                ),
            )
            db.execute(
                "INSERT INTO privacy_links VALUES ('survey', ?, ?)",
                (submission_id, digest),
            )
        self.assertEqual(snapshot[0], "unprompted")
        self.assertGreater(snapshot[1], 1)
        self.assertEqual(len(snapshot[2]), 64)
        self.assertEqual(snapshot[3], a_prompt)

        admin = self.app.extensions["admin_data"]
        row = next(item for item in admin.records() if item["id"] == submission_id)
        self.assertEqual(row["system_prompt_policy"], "unprompted")
        self.assertEqual(row["system_prompt_revision"], snapshot[1])
        self.assertEqual(row["system_prompt_base_sha256"], snapshot[2])
        exported = admin.csv_data([row], columns="technical").decode("utf-8-sig")
        self.assertIn(snapshot[2], exported)
        self.assertNotIn(a_prompt, exported)

    def test_assignment_rolls_back_if_prompt_cannot_be_frozen(self):
        token, headers = self.consent()
        prompt_store = self.app.extensions["system_prompt_store"]
        with patch.object(
            prompt_store, "participant_snapshot", side_effect=RuntimeError("test")
        ):
            response = self.client.post("/api/study-assignment", headers=headers)
        self.assertEqual(response.status_code, 500)
        with sqlite3.connect(self.db_path) as db:
            assignment_count = db.execute(
                "SELECT COUNT(*) FROM study_assignments WHERE token_hash=?",
                (token_hash(token),),
            ).fetchone()[0]
        self.assertEqual(assignment_count, 0)

    def test_standalone_test_url_uses_current_prompt_for_each_new_session(self):
        model = CapturingModel()
        test_app = create_app(
            {
                **dict(self.app.config),
                "SEED_DUMMY_DATA": True,
                "REQUIRE_COMPLETE_INDEX": False,
            },
            retriever=FakeRetriever(),
            llm=model,
        )
        client = test_app.test_client()
        token = secrets.token_hex(32)
        headers = {"X-Diana-Consent": token, "X-Diana-Test": "B"}
        notice = client.get("/api/privacy", headers=headers).get_json()["notice"]
        self.assertEqual(
            client.post(
                "/api/privacy/consent",
                headers=headers,
                json={
                    "token": token,
                    "version": notice["version"],
                    "purpose": "test_b",
                    "accepted": True,
                },
            ).status_code,
            200,
        )
        profile = {
            "profile": {
                "query": "Python Datenanalyse",
                "skills": ["Python"],
                "filters": {},
            }
        }
        self.assertEqual(client.post("/api/onboard", headers=headers, json=profile).status_code, 201)
        first = model.prompts[-1]
        prompts = {
            key: value["text"]
            for key, value in test_app.extensions["system_prompt_store"].get()["prompts"].items()
        }
        prompts["career_fixed"] += "\nNeue Testrevision für nachfolgende Sitzungen."
        prompt_store = test_app.extensions["system_prompt_store"]
        prompt_store.update(prompt_store.get()["revision"], prompts)
        self.assertEqual(client.post("/api/onboard", headers=headers, json=profile).status_code, 201)
        second = model.prompts[-1]
        self.assertEqual(first["revision"] + 1, second["revision"])
        self.assertNotEqual(first["sha256"], second["sha256"])

    def test_standalone_a_uses_empty_then_edited_prompt_for_new_sessions(self):
        model = CapturingModel()
        test_app = create_app(
            {
                **dict(self.app.config),
                "SEED_DUMMY_DATA": True,
                "REQUIRE_COMPLETE_INDEX": False,
            },
            retriever=FakeRetriever(),
            llm=model,
        )
        client = test_app.test_client()
        token = secrets.token_hex(32)
        headers = {"X-Diana-Consent": token, "X-Diana-Test": "A"}
        notice = client.get("/api/privacy", headers=headers).get_json()["notice"]
        self.assertEqual(
            client.post(
                "/api/privacy/consent",
                headers=headers,
                json={
                    "token": token,
                    "version": notice["version"],
                    "purpose": "test_a",
                    "accepted": True,
                },
            ).status_code,
            200,
        )
        profile = {
            "profile": {
                "query": "Python Datenanalyse",
                "skills": ["Python"],
                "filters": {},
            }
        }
        self.assertEqual(client.post("/api/onboard", headers=headers, json=profile).status_code, 201)
        first = model.prompts[-1]
        self.assertEqual(first["policy"], "unprompted")
        self.assertEqual(first["text"], "")

        prompt_store = test_app.extensions["system_prompt_store"]
        current = prompt_store.get()
        prompts = {key: value["text"] for key, value in current["prompts"].items()}
        prompts["unprompted"] = "Du bist ein allgemeiner KI-Assistent."
        prompt_store.update(current["revision"], prompts)
        self.assertEqual(client.post("/api/onboard", headers=headers, json=profile).status_code, 201)
        second = model.prompts[-1]
        self.assertEqual(second["policy"], "unprompted")
        self.assertEqual(second["text"], prompts["unprompted"])
        self.assertEqual(second["revision"], first["revision"] + 1)
        self.assertNotEqual(first["sha256"], second["sha256"])

    def test_c_endpoint_normalizes_removed_preset_to_custom_career_start(self):
        model = CapturingModel()
        test_app = create_app(
            {
                **dict(self.app.config),
                "SEED_DUMMY_DATA": True,
                "REQUIRE_COMPLETE_INDEX": False,
            },
            retriever=FakeRetriever(),
            llm=model,
        )
        client = test_app.test_client()
        token = secrets.token_hex(32)
        headers = {"X-Diana-Consent": token, "X-Diana-Test": "C"}
        notice = client.get("/api/privacy", headers=headers).get_json()["notice"]
        self.assertEqual(
            client.post(
                "/api/privacy/consent",
                headers=headers,
                json={
                    "token": token,
                    "version": notice["version"],
                    "purpose": "test_c",
                    "accepted": True,
                },
            ).status_code,
            200,
        )
        payload = {
            "profile": {
                "query": "Python Datenanalyse",
                "skills": ["Python"],
                "filters": {},
            },
            "advisor": {
                "mode": "preset",
                "preset": "steve",
                "name": "Steve-Jobs-KI",
                "description": "",
                "traits": ["kreativ", "direkt"],
                "focus": "innovation",
            },
            "advisor_selection": {"source": "custom", "template_id": None},
        }
        response = client.post("/api/onboard", headers=headers, json=payload)
        self.assertEqual(response.status_code, 201, response.get_json())
        advisor = response.get_json()["advisor"]
        self.assertEqual(advisor["mode"], "custom")
        self.assertEqual(advisor["preset"], "diana")
        self.assertEqual(advisor["name"], "Top-Berufsberater")
        self.assertEqual(advisor["focus"], "ausgewogen")
        self.assertEqual(response.get_json()["advisor_selection"], {
            "source": "custom", "template_id": None,
        })

    def test_c_rejects_cached_rankings_with_a_former_or_invalid_focus(self):
        _, headers = self.consent()
        with patch("study_assignment.secrets.choice", return_value="C"):
            self.assertEqual(
                self.client.post("/api/study-assignment", headers=headers).status_code, 200,
            )
        response = self.client.post("/api/onboard", headers=headers, json={
            "profile": {"query": "Python", "skills": ["Python"], "filters": {}},
        })
        self.assertEqual(response.status_code, 201, response.get_json())
        session_id = response.get_json()["session_id"]
        sessions = self.app.extensions["chat_store"]
        balanced_state, _ = sessions.get(session_id)
        self.assertEqual(
            self.client.get(f"/api/sessions/{session_id}", headers=headers).status_code, 200,
        )
        for key in ("advisor", "advisor_mlds"):
            for focus in ("lernpotenzial", "innovation", "fachliche_tiefe", "obsolete"):
                with self.subTest(key=key, focus=focus):
                    stale_advisor = {**balanced_state["advisor"], "focus": focus}
                    cached = (stale_advisor if key == "advisor" else {
                        **advisor_to_mlds(balanced_state["advisor"]),
                        "personality": stale_advisor,
                    })
                    _, version = sessions.get(session_id)
                    sessions.update(session_id, {**balanced_state, key: cached}, version)
                    restored = self.client.get(f"/api/sessions/{session_id}", headers=headers)
                    self.assertEqual(restored.status_code, 404, restored.get_json())
                    self.assertIn("Suche neu", restored.get_json()["error"]["message"])
                    continued = self.client.post("/api/chat", headers=headers, json={
                        "session_id": session_id, "message": "Was bedeutet die Bewertung?",
                    })
                    self.assertEqual(continued.status_code, 404, continued.get_json())

    def test_b_and_historical_c_can_restore_their_original_focus(self):
        for arm, experiment in (("B", "diana-abc-v4"), ("C", "diana-abc-v3")):
            with self.subTest(arm=arm, experiment=experiment):
                token, headers = self.consent()
                with patch("study_assignment.secrets.choice", return_value=arm):
                    self.assertEqual(
                        self.client.post("/api/study-assignment", headers=headers).status_code, 200,
                    )
                if experiment != "diana-abc-v4":
                    with sqlite3.connect(self.db_path) as db:
                        db.execute("UPDATE study_assignments SET experiment_id=? WHERE token_hash=?",
                                   (experiment, token_hash(token)))
                response = self.client.post("/api/onboard", headers=headers, json={
                    "profile": {"query": "Python", "skills": ["Python"], "filters": {}},
                    **({"advisor": {"mode": "custom", "focus": "lernpotenzial"}}
                       if arm == "C" else {}),
                })
                self.assertEqual(response.status_code, 201, response.get_json())
                self.assertEqual(response.get_json()["advisor"]["focus"], "lernpotenzial")
                session_id = response.get_json()["session_id"]
                restored = self.client.get(f"/api/sessions/{session_id}", headers=headers)
                self.assertEqual(restored.status_code, 200, restored.get_json())
                self.assertEqual(restored.get_json()["advisor"]["focus"], "lernpotenzial")


if __name__ == "__main__":
    unittest.main()
