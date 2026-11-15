"""Memory-bounded UnityFS block and embedded-file readers.

Pure-Python fixtures deliberately do not fabricate original UnityFS source
evidence; full binary verification still takes place on GitHub Actions.
"""
import io
import unittest
from types import SimpleNamespace

from reconstruction.tools.streamed_unityfs import BlockStream, RangeStream, MAX_BLOCK


class Reader:
    def __init__(self, data):
        self.stream = io.BytesIO(data)
        self.Length = len(data)

    @property
    def Position(self):
        return self.stream.tell()

    @Position.setter
    def Position(self, value):
        self.stream.seek(value)

    def read_bytes(self, size):
        return self.stream.read(size)


class StreamedUnityfsTests(unittest.TestCase):
    def setUp(self):
        self.blocks = [
            SimpleNamespace(compressedSize=3, uncompressedSize=3,
                            flags=0, offset=None),
            SimpleNamespace(compressedSize=3, uncompressedSize=3,
                            flags=0, offset=None),
        ]
        self.called = []
        def decompress(payload, size, flags, index):
            self.called.append(index)
            return payload
        self.backing = BlockStream(Reader(b"abcDEF"), self.blocks, 0, decompress)

    def test_read_boundary_and_random_access_caches_one_block(self):
        self.assertEqual(self.backing.read(4), b"abcD")
        self.assertEqual(self.backing.read(2), b"EF")
        self.assertEqual(self.backing.seek(1), 1)
        self.assertEqual(self.backing.read(2), b"bc")
        self.assertEqual(self.backing.read(1), b"D")
        self.assertEqual(self.backing.read(2), b"EF")
        self.assertEqual(self.backing.read(1), b"")
        self.assertEqual(self.backing.seek(-3, 2), 3)
        self.assertEqual(self.backing.read(3), b"DEF")
        self.assertGreaterEqual(self.called.count(0), 1)

    def test_embedded_file_reads_only_selected_range(self):
        segment = RangeStream(self.backing, 2, 3)
        self.assertEqual(segment.read(2), b"cD")
        self.assertEqual(segment.read(9), b"E")
        self.assertEqual(segment.read(), b"")
        self.assertEqual(segment.seek(0), 0)
        self.assertEqual(segment.read(3), b"cDE")
        with self.assertRaisesRegex(ValueError, "outside"):
            segment.seek(4)

    def test_rejects_invalid_blocks_and_ranges(self):
        huge = [SimpleNamespace(compressedSize=3, uncompressedSize=MAX_BLOCK + 1,
                                flags=0, offset=None)]
        with self.assertRaisesRegex(ValueError, "budget"):
            BlockStream(Reader(b"abc"), huge, 0, lambda *_: b"")
        with self.assertRaisesRegex(ValueError, "outside"):
            RangeStream(self.backing, 0, 7)
        invalid = [SimpleNamespace(compressedSize=4, uncompressedSize=4,
                                   flags=0, offset=None)]
        with self.assertRaisesRegex(ValueError, "outside"):
            BlockStream(Reader(b"abc"), invalid, 0, lambda *_: b"")
        with self.assertRaisesRegex(ValueError, "Seek beyond"):
            self.backing.seek(7)

    def test_fails_closed_on_incomplete_decompression(self):
        backing = BlockStream(Reader(b"abc"), self.blocks[:1], 0,
                              lambda *_: b"ab")
        with self.assertRaisesRegex(ValueError, "length"):
            backing.read(2)
