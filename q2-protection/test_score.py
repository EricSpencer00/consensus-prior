"""Regression tests for manifest binding in score.py. Run: python3 -m unittest test_score.py

q2-000 exists in both cohorts: "GIVE UP: A2" is a minimal correction in the pilot (items.jsonl)
and not in the replication (items_rep.jsonl). Scoring must never let one cohort's rows be read
against the other's manifest.
"""
import json, os, subprocess, sys, tempfile, unittest

import score

HERE = os.path.dirname(os.path.abspath(__file__))
PILOT, REP = os.path.join(HERE, "items.jsonl"), os.path.join(HERE, "items_rep.jsonl")


def rows_file(rows):
    f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    for r in rows:
        f.write(json.dumps(r) + "\n")
    f.close()
    return f.name


def row(sample=0, model="m", manifest=None, item="q2-000", cond="N"):
    r = {"model": model, "item": item, "cond": cond, "sample": sample, "text": "GIVE UP: A2"}
    if manifest:
        r["manifest"] = manifest
    return r


class Q2000(unittest.TestCase):
    def test_same_answer_differs_by_manifest(self):
        D = score.parse("GIVE UP: A2")
        self.assertEqual(score.classify(score.load_items(PILOT)["q2-000"], D), "valid_min")
        self.assertNotEqual(score.classify(score.load_items(REP)["q2-000"], D), "valid_min")

    def test_stamped_rows_score_under_own_manifest(self):
        p = rows_file([row(manifest=score.sha256(PILOT))])
        items, sha, by_model = score.load_rows([p], PILOT, explicit=False)
        self.assertEqual(sha, score.sha256(PILOT))
        self.assertEqual(score.classify(items["q2-000"], score.parse(by_model["m"][0]["text"])), "valid_min")

    def test_mismatched_stamp_rejected(self):
        p = rows_file([row(manifest=score.sha256(PILOT))])
        with self.assertRaisesRegex(score.ManifestError, "manifest"):
            score.load_rows([p], REP, explicit=True)

    def test_mixed_stamps_rejected(self):
        p = rows_file([row(0, manifest=score.sha256(REP)), row(1, manifest=score.sha256(PILOT))])
        with self.assertRaises(score.ManifestError):
            score.load_rows([p], REP, explicit=True)

    def test_unstamped_needs_explicit_manifest(self):
        p = rows_file([row()])
        with self.assertRaisesRegex(score.ManifestError, "no manifest stamp"):
            score.load_rows([p], PILOT, explicit=False)
        items, _, by_model = score.load_rows([p], PILOT, explicit=True)  # legacy single-manifest scoring
        self.assertEqual(len(by_model["m"]), 1)

    def test_cohort_mix_for_one_model_rejected(self):
        pilot_out, rep_out = rows_file([row()]), rows_file([row()])  # same model, item, cond, sample
        with self.assertRaisesRegex(score.ManifestError, "repeated"):
            score.load_rows([pilot_out, rep_out], REP, explicit=True)

    def test_unknown_item_rejected(self):
        p = rows_file([row(item="q2-199")])  # exists only in the 200-item replication
        with self.assertRaisesRegex(score.ManifestError, "not in"):
            score.load_rows([p], PILOT, explicit=True)

    def test_cli_exits_nonzero_on_mismatch(self):
        p = rows_file([row(manifest=score.sha256(PILOT))])
        r = subprocess.run([sys.executable, os.path.join(HERE, "score.py"), "--items", REP, p],
                           capture_output=True, text=True, cwd=HERE, env={k: v for k, v in os.environ.items() if k != "Q2_ITEMS"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("manifest", r.stderr)

    def test_prompt_files_stamped(self):
        for prompts, items in [("prompts.jsonl", PILOT), ("prompts_rep.jsonl", REP)]:
            stamps = {json.loads(l)["manifest"] for l in open(os.path.join(HERE, prompts))}
            self.assertEqual(stamps, {score.sha256(items)})


if __name__ == "__main__":
    unittest.main()
