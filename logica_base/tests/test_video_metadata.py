import os
import re
import unittest

ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
SOURCE = os.path.join(ROOT, "logica_base", "video_metadata.py")
PLUGIN_COPY = os.path.join(
    ROOT, "autopsy_plugin", "GeoEvidenceDataSource", "video_metadata.py"
)

FORBIDDEN = (
    "subprocess",
    "FileNotFoundError",
    "JSONDecodeError",
    "capture_output",
    "pathlib",
    "dataclass",
)


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


class TestVideoMetadataIsJythonSafe(unittest.TestCase):
    """video_metadata.py is copied in the plugin: it must run in Jython."""

    def test_no_python3_only_constructs(self):
        text = read_bytes(SOURCE).decode("utf-8")

        for word in FORBIDDEN:
            self.assertNotIn(word, text)

        self.assertIsNone(re.search(r'\bf["\']', text))

    def test_source_is_ascii(self):
        read_bytes(SOURCE).decode("ascii")

    def test_plugin_copy_is_identical(self):
        source = read_bytes(SOURCE).replace(b"\r\n", b"\n")
        copy = read_bytes(PLUGIN_COPY).replace(b"\r\n", b"\n")
        self.assertEqual(source, copy)


if __name__ == "__main__":
    unittest.main()