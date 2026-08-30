from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import povo_worker


class RunOnceTests(unittest.TestCase):
    def test_not_due_refreshes_without_redeeming(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(
            povo_worker, "DATA_DIR", Path(temporary)
        ), patch.object(povo_worker, "recover_interrupted_submission"), patch.object(
            povo_worker, "append_history"
        ), patch.object(
            povo_worker, "refresh_session", return_value=True
        ) as refresh, patch.object(
            povo_worker, "load_state", return_value={"paused": False}
        ), patch.object(
            povo_worker, "due_now", return_value=False
        ), patch.object(
            povo_worker, "redeem_once"
        ) as redeem:
            self.assertEqual(povo_worker.run_once(), 0)
            refresh.assert_called_once_with(force=True)
            redeem.assert_not_called()

    def test_due_calls_redeem_exactly_once(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(
            povo_worker, "DATA_DIR", Path(temporary)
        ), patch.object(povo_worker, "recover_interrupted_submission"), patch.object(
            povo_worker, "append_history"
        ), patch.object(
            povo_worker, "refresh_session", return_value=True
        ), patch.object(
            povo_worker, "load_state", return_value={"paused": False}
        ), patch.object(
            povo_worker, "due_now", return_value=True
        ), patch.object(
            povo_worker, "redeem_once", return_value=3
        ) as redeem:
            self.assertEqual(povo_worker.run_once(), 3)
            redeem.assert_called_once_with()

    def test_refresh_failure_never_redeems(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(
            povo_worker, "DATA_DIR", Path(temporary)
        ), patch.object(povo_worker, "recover_interrupted_submission"), patch.object(
            povo_worker, "append_history"
        ), patch.object(
            povo_worker, "refresh_session", return_value=False
        ), patch.object(
            povo_worker, "redeem_once"
        ) as redeem:
            self.assertEqual(povo_worker.run_once(), 2)
            redeem.assert_not_called()


if __name__ == "__main__":
    unittest.main()
