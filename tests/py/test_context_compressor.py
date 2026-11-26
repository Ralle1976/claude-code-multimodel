"""Offline-Tests fuer den Context Compressor (keine ML-Modelle, kein Netzwerk)."""

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_DIR = REPO_ROOT / "plugins" / "context-compressor"
sys.path.insert(0, str(PLUGIN_DIR))

from ccompressor import cli, compress, storage  # noqa: E402


class TempMemoryTest(unittest.TestCase):
    """Basisklasse: leitet den Session-Memory in ein temporaeres Verzeichnis um."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ccm-py-"))
        self.memory = self.tmp / "memory"
        self._env_backup = {
            key: os.environ.get(key)
            for key in ("CLAUDE_MEMORY_DIR", "CLAUDE_DISABLE_LLMLINGUA", "HOME")
        }
        os.environ["CLAUDE_MEMORY_DIR"] = str(self.memory)
        os.environ["CLAUDE_DISABLE_LLMLINGUA"] = "1"

    def tearDown(self):
        for key, value in self._env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        shutil.rmtree(self.tmp, ignore_errors=True)


class SimpleCompressTest(unittest.TestCase):
    def test_removes_filler_words(self):
        text = "Also eigentlich ist das basically eine einfache Sache."
        result = compress.simple_compress(text, 1.0)
        self.assertNotIn("eigentlich", result)
        self.assertNotIn("basically", result)
        self.assertIn("einfache Sache", result)

    def test_collapses_whitespace(self):
        self.assertEqual(compress.simple_compress("a   b \n\n c", 1.0), "a b c")

    def test_truncates_long_text_and_keeps_edges(self):
        words = [f"wort{i}" for i in range(400)]
        result = compress.simple_compress(" ".join(words), 0.5)
        self.assertIn("[...]", result)
        self.assertIn("wort0", result)
        self.assertIn("wort399", result)

    def test_short_text_is_untouched(self):
        self.assertEqual(compress.simple_compress("kurz", 0.5), "kurz")


class CompressTextTest(TempMemoryTest):
    def test_short_input_is_skipped(self):
        result = compress.compress_text("zu kurz", use_llmlingua=False)
        self.assertTrue(result["success"])
        self.assertTrue(result["skipped"])
        self.assertEqual(result["compression_ratio"], 1.0)

    def test_empty_input_is_skipped(self):
        result = compress.compress_text("", use_llmlingua=False)
        self.assertTrue(result["success"])
        self.assertEqual(result["original_tokens"], 0)

    def test_simple_fallback_is_used_without_llmlingua(self):
        text = " ".join(f"satz{i}" for i in range(300))
        result = compress.compress_text(text, target_ratio=0.5)
        self.assertTrue(result["success"])
        self.assertEqual(result["method"], "simple")
        self.assertLess(result["compressed_tokens"], result["original_tokens"])

    def test_invalid_ratio_is_rejected(self):
        text = "x " * 200
        for ratio in (0, -0.5, 1.5):
            result = compress.compress_text(text, target_ratio=ratio)
            self.assertFalse(result["success"])
            self.assertEqual(result["error"], "invalid_ratio")

    def test_stats_are_written(self):
        text = " ".join(f"wort{i}" for i in range(300))
        compress.compress_text(text, target_ratio=0.5)
        stats = json.loads(storage.stats_file().read_text(encoding="utf-8"))
        self.assertEqual(stats["compressions"], 1)
        self.assertGreater(stats["total_original"], 0)


class StorageTest(TempMemoryTest):
    def test_memory_dir_honours_env_override(self):
        self.assertEqual(storage.memory_dir(), self.memory)
        self.assertEqual(storage.session_file(), self.memory / "session_summary.md")

    def test_session_roundtrip_preserves_unicode(self):
        summary = "Emoji 🚀, CJK 日本語, Umlaute äöüß"
        saved = storage.save_session_summary(summary)
        self.assertTrue(saved["success"])

        loaded = storage.load_session_summary()
        self.assertTrue(loaded["exists"])
        self.assertIn(summary, loaded["content"])

    def test_load_without_session(self):
        loaded = storage.load_session_summary()
        self.assertTrue(loaded["success"])
        self.assertFalse(loaded["exists"])

    def test_history_gets_one_line_per_save(self):
        storage.save_session_summary("eins")
        storage.save_session_summary("zwei")
        lines = storage.history_file().read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[1])["summary_length"], 4)

    def test_metadata_is_stored(self):
        storage.save_session_summary("text", {"projekt": "demo"})
        content = storage.load_session_summary()["content"]
        self.assertIn("**projekt**: demo", content)

    def test_non_serialisable_metadata_does_not_crash(self):
        result = storage.save_session_summary("text", {"obj": object()})
        self.assertTrue(result["success"])


class StatsRobustnessTest(TempMemoryTest):
    def _write_stats(self, content: str):
        storage.ensure_memory_dir()
        storage.stats_file().write_text(content, encoding="utf-8")

    def test_corrupt_json_falls_back_to_empty_stats(self):
        self._write_stats("{kaputt")
        stats = storage.get_compression_stats()
        self.assertTrue(stats["success"])
        self.assertEqual(stats["stats"]["compressions"], 0)

    def test_json_array_falls_back_to_empty_stats(self):
        self._write_stats("[1, 2, 3]")
        stats = storage.get_compression_stats()
        self.assertEqual(stats["stats"]["compressions"], 0)

    def test_wrong_types_are_ignored(self):
        self._write_stats(json.dumps({"total_original": "viel", "compressions": True}))
        stats = storage.get_compression_stats()
        self.assertEqual(stats["stats"]["compressions"], 0)
        self.assertEqual(stats["stats"]["total_original"], 0)

    def test_valid_stats_are_used(self):
        self._write_stats(json.dumps({"total_original": 100, "total_compressed": 25, "compressions": 2}))
        stats = storage.get_compression_stats()["stats"]
        self.assertEqual(stats["total_saved"], 75)
        self.assertEqual(stats["average_ratio"], 0.25)

    def test_saving_a_stat_on_corrupt_file_does_not_crash(self):
        self._write_stats("{kaputt")
        storage.save_compression_stat(10, 5)
        stats = json.loads(storage.stats_file().read_text(encoding="utf-8"))
        self.assertEqual(stats["compressions"], 1)


class CliTest(TempMemoryTest):
    def _capture(self, argv, stdin_bytes=b""):
        stdout = io.StringIO()
        original_stdout, original_stdin = sys.stdout, sys.stdin

        class _Stdin:
            def __init__(self, data):
                self.buffer = io.BytesIO(data)

            def read(self, *_args):
                return self.buffer.read().decode("utf-8", errors="replace")

        sys.stdout = stdout
        sys.stdin = _Stdin(stdin_bytes)
        try:
            code = cli.main(argv)
        finally:
            sys.stdout, sys.stdin = original_stdout, original_stdin
        return code, stdout.getvalue()

    def test_no_arguments_prints_help(self):
        code, out = self._capture(["prog"])
        self.assertEqual(code, 0)
        self.assertIn("Context Compressor", out)

    def test_unknown_action_returns_error_code(self):
        code, out = self._capture(["prog", "gibtsnicht"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["error"], "invalid_action")

    def test_save_session_reads_stdin(self):
        code, out = self._capture(["prog", "save-session"], "Zeile eins\nZeile zwei".encode())
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["success"])
        self.assertIn("Zeile eins", storage.load_session_summary()["content"])

    def test_save_session_reads_arguments(self):
        code, _ = self._capture(["prog", "save-session", "aus", "argumenten"])
        self.assertEqual(code, 0)
        self.assertIn("aus argumenten", storage.load_session_summary()["content"])

    def test_compress_accepts_ratio_flag(self):
        text = " ".join(f"wort{i}" for i in range(300))
        code, out = self._capture(["prog", "compress", "--ratio", "0.4"], text.encode())
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["success"])

    def test_compress_rejects_invalid_ratio(self):
        text = " ".join(f"wort{i}" for i in range(300))
        code, out = self._capture(["prog", "compress", "--ratio", "0"], text.encode())
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["error"], "invalid_ratio")

    def test_status_reports_memory_dir(self):
        code, out = self._capture(["prog", "status"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["memory_dir"], str(self.memory))

    def test_load_session_when_missing(self):
        code, out = self._capture(["prog", "load-session"])
        self.assertEqual(code, 0)
        self.assertFalse(json.loads(out)["exists"])


class ParseRatioTest(unittest.TestCase):
    def test_default_without_flag(self):
        ratio, rest = cli.parse_ratio(["hallo", "welt"])
        self.assertEqual(ratio, compress.DEFAULT_COMPRESSION_RATE)
        self.assertEqual(rest, ["hallo", "welt"])

    def test_ratio_separate_argument(self):
        ratio, rest = cli.parse_ratio(["--ratio", "0.7", "text"])
        self.assertEqual(ratio, 0.7)
        self.assertEqual(rest, ["text"])

    def test_ratio_equals_form(self):
        ratio, rest = cli.parse_ratio(["--ratio=0.2"])
        self.assertEqual(ratio, 0.2)
        self.assertEqual(rest, [])

    def test_invalid_ratio_keeps_default_and_text(self):
        ratio, rest = cli.parse_ratio(["--ratio", "abc"])
        self.assertEqual(ratio, compress.DEFAULT_COMPRESSION_RATE)
        self.assertEqual(rest, ["--ratio", "abc"])


if __name__ == "__main__":
    unittest.main()
