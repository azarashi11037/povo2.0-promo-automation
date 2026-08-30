from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from tools.update_workflow_schedule import managed_block, update_workflow


class WorkflowScheduleTests(unittest.TestCase):
    def test_due_time_generates_early_and_fallback_crons_in_utc(self):
        due = datetime.fromisoformat("2026-09-07T00:42+09:00")
        block = managed_block(due)
        self.assertIn('- cron: "32 15 6 9 *"', block)
        self.assertIn('- cron: "47 15 6 9 *"', block)
        self.assertIn('- cron: "57 15 6 9 *"', block)
        self.assertIn('- cron: "12 16 6 9 *"', block)
        self.assertIn('- cron: "43 2 * * *"', block)

    def test_rewrite_is_idempotent_and_preserves_the_rest(self):
        due = datetime.fromisoformat("2026-09-07T00:42+09:00")
        with tempfile.TemporaryDirectory() as temporary:
            workflow = Path(temporary) / "povo.yml"
            workflow.write_text(
                "before\n"
                "    # BEGIN MANAGED PRECISE SCHEDULE\n"
                '    - cron: "17 1 * * *"\n'
                "    # END MANAGED PRECISE SCHEDULE\n"
                "after\n",
                encoding="utf-8",
            )
            self.assertTrue(update_workflow(workflow, due))
            first = workflow.read_text(encoding="utf-8")
            self.assertFalse(update_workflow(workflow, due))
            self.assertEqual(workflow.read_text(encoding="utf-8"), first)
            self.assertTrue(first.startswith("before\n"))
            self.assertTrue(first.endswith("\nafter\n"))


if __name__ == "__main__":
    unittest.main()
