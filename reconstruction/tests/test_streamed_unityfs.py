"""Memory-bounded UnityFS block and embedded-file readers.

Pure-Python fixtures deliberately do not fabricate original UnityFS source
evidence; full binary verification still takes place on GitHub Actions.
"""
import io
import unittest
from contextlib import redirect_stdout
from enum import Enum
from types import SimpleNamespace
from unittest.mock import Mock, patch

from reconstruction.tools.streamed_unityfs import (
    BlockStream, RangeStream, MAX_BLOCK, WwiseMonoObjectBudgetExceeded,
    _parse_bounded_wwise_mono, _parse_without_unused_container_index,
)


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

    def test_interleaved_reads_reuse_recent_blocks(self):
        self.assertEqual(self.backing.read(1), b"a")
        self.assertEqual(self.backing.seek(4), 4)
        self.assertEqual(self.backing.read(1), b"E")
        self.backing.seek(0)
        self.assertEqual(self.backing.read(2), b"ab")
        self.assertEqual(self.called, [0, 1])
        self.assertEqual(self.backing.cache_bytes, 6)

    def test_cache_eviction_is_strict_and_reparses_on_demand(self):
        with patch("reconstruction.tools.streamed_unityfs.MAX_CACHE_BYTES", 4):
            self.backing.read(1)
            self.backing.seek(4)
            self.backing.read(1)
            self.assertEqual(self.backing.cache_bytes, 3)
            self.backing.seek(1)
            self.assertEqual(self.backing.read(1), b"b")
            self.assertEqual(self.called, [0, 1, 0])
            self.assertLessEqual(self.backing.cache_bytes, 4)

    def test_wwise_inventory_does_not_eagerly_parse_non_numeric_assetbundle_index(self):
        class Kind(Enum):
            AssetBundle = 1
            MonoBehaviour = 2

        original = Mock(return_value="parsed")
        bundle = SimpleNamespace(type=Kind.AssetBundle, path_id=42)
        with redirect_stdout(io.StringIO()) as output:
            index = _parse_without_unused_container_index(
                bundle, original, Kind.AssetBundle
            )
        self.assertEqual(index.m_Container, [])
        self.assertEqual(index.m_PreloadTable, [])
        self.assertIn("INDEX_NOT_REQUESTED path_id=42", output.getvalue())
        original.assert_not_called()

        monobehaviour = SimpleNamespace(type=Kind.MonoBehaviour, path_id=43)
        self.assertEqual(_parse_without_unused_container_index(
            monobehaviour, original, Kind.AssetBundle, check_read=True
        ), "parsed")
        original.assert_called_once_with(monobehaviour, check_read=True)

    def test_wwise_mono_budget_is_explicitly_unparsed_without_media_allocation(self):
        class Kind(Enum):
            MonoBehaviour = 114
            TextAsset = 49

        original = Mock(return_value={"value": 3})
        small = SimpleNamespace(type=Kind.MonoBehaviour, path_id=1, byte_size=4)
        large = SimpleNamespace(type=Kind.MonoBehaviour, path_id=2, byte_size=5)
        media = SimpleNamespace(type=Kind.TextAsset, path_id=3, byte_size=500)
        with patch("reconstruction.tools.streamed_unityfs."
                   "MAX_WWISE_MONO_OBJECT_BYTES", 4):
            self.assertEqual(_parse_bounded_wwise_mono(
                small, original, Kind.MonoBehaviour
            ), {"value": 3})
            with redirect_stdout(io.StringIO()) as trace:
                with self.assertRaisesRegex(
                    WwiseMonoObjectBudgetExceeded, "budget"
                ):
                    _parse_bounded_wwise_mono(
                        large, original, Kind.MonoBehaviour
                    )
            self.assertIn("UNPARSED_SIZE_BUDGET path_id=2", trace.getvalue())
            self.assertEqual(_parse_bounded_wwise_mono(
                media, original, Kind.MonoBehaviour
            ), {"value": 3})
            missing = SimpleNamespace(type=Kind.MonoBehaviour, path_id=4)
            with self.assertRaises(WwiseMonoObjectBudgetExceeded):
                _parse_bounded_wwise_mono(
                    missing, original, Kind.MonoBehaviour
                )
        self.assertEqual(original.call_count, 2)

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
