"""Bounded-memory, read-only UnityFS metadata loader for large original bundles.

UnityPy 1.25.4 normally joins every decompressed block into one bytes object
and copies each contained file. A large audio bundle can exhaust hosted-runner
memory before object headers are inventoried. Keep the exact UnityPy parser and
all object records, but expose the original compressed blocks as a seekable
on-demand byte stream; never copy embedded media to RAM or export it.
"""
from bisect import bisect_right
from collections import OrderedDict
from contextlib import contextmanager
from io import RawIOBase
from types import SimpleNamespace

MAX_BLOCK = 32 * 1024 * 1024
MAX_READ = 32 * 1024 * 1024
MAX_CACHE_BYTES = 128 * 1024 * 1024
# A giant Wwise MonoBehaviour payload can expand into many gigabytes of
# Python values even though its serialized byte count is much smaller.
# Above this source-scoped bound, preserve the object as explicitly unparsed.
MAX_WWISE_MONO_OBJECT_BYTES = 8 * 1024 * 1024
# Independently conservative initial city-scene MonoBehaviour allocation cap.
MAX_CITY_MONO_OBJECT_BYTES = 8 * 1024 * 1024


class WwiseMonoObjectBudgetExceeded(ValueError):
    """An original MonoBehaviour was not parsed; numeric evidence incomplete."""


def _parse_bounded_wwise_mono(reader, original, mono_type, *args,
                              budget_bytes=None, scope="WWISE", **kwargs):
    budget = MAX_WWISE_MONO_OBJECT_BYTES if budget_bytes is None else budget_bytes
    if type(budget) is not int or budget < 1:
        raise ValueError("Invalid source-specific MonoBehaviour budget")
    if scope not in ("WWISE", "CITY"):
        raise ValueError("Unknown source-specific inventory scope")
    if reader.type == mono_type:
        raw_size = getattr(reader, "byte_size", None)
        if type(raw_size) is not int or raw_size < 0:
            raise WwiseMonoObjectBudgetExceeded(
                "Missing/invalid original Wwise MonoBehaviour byte count"
            )
        print(f"{scope}_INVENTORY_MONO path_id={reader.path_id} "
              f"byte_size={raw_size} budget={budget}",
              flush=True)
        if raw_size > budget:
            print(f"{scope}_INVENTORY_MONO_UNPARSED_SIZE_BUDGET "
                  f"path_id={reader.path_id} byte_size={raw_size}", flush=True)
            raise WwiseMonoObjectBudgetExceeded(
                f"Wwise MonoBehaviour byte size {raw_size} exceeds "
                f"bounded parse budget {budget}"
            )
    return original(reader, *args, **kwargs)




class BlockStream(RawIOBase):
    """Random-access decompression of verified UnityFS blocks, one block cached."""

    def __init__(self, source, blocks, base_offset, decompress):
        super().__init__()
        self.source = source
        self.blocks = blocks
        self.decompress = decompress
        self.starts = [0]
        self.compressed = []
        self.position = 0
        self.cache = OrderedDict()
        self.cache_bytes = 0
        compressed_pos = base_offset
        for block in blocks:
            raw_size = block.compressedSize
            size = block.uncompressedSize
            if (type(raw_size) is not int or type(size) is not int
                    or not 0 <= raw_size <= MAX_BLOCK or
                    not 0 <= size <= MAX_BLOCK):
                raise ValueError("UnityFS block exceeds bounded-memory budget")
            offset = (base_offset + block.offset
                      if block.offset is not None else compressed_pos)
            if offset < 0 or offset + raw_size > source.Length:
                raise ValueError("UnityFS block lies outside original source bytes")
            self.compressed.append(offset)
            self.starts.append(self.starts[-1] + size)
            compressed_pos += raw_size
        if not self.starts[-1]:
            raise ValueError("UnityFS source has no uncompressed block data")

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        base = (0 if whence == 0 else self.position if whence == 1
                else self.starts[-1] if whence == 2 else None)
        if base is None:
            raise ValueError("Unsupported seek mode")
        position = base + offset
        if not 0 <= position <= self.starts[-1]:
            raise ValueError("Seek beyond verified UnityFS blocks")
        self.position = position
        return position

    def _block(self, index):
        if index in self.cache:
            self.cache.move_to_end(index)
            return self.cache[index]
        block = self.blocks[index]
        self.source.Position = self.compressed[index]
        compressed = self.source.read_bytes(block.compressedSize)
        if len(compressed) != block.compressedSize:
            raise ValueError("Truncated UnityFS source block")
        decoded = self.decompress(
            compressed, block.uncompressedSize, block.flags, index
        )
        if len(decoded) != block.uncompressedSize:
            raise ValueError("Inconsistent UnityFS decompressed block length")
        # The source may alternate between distant serialized-file offsets.
        # Retain recent decompressed blocks under a strict total RAM budget.
        while self.cache and self.cache_bytes + len(decoded) > MAX_CACHE_BYTES:
            _, oldest = self.cache.popitem(last=False)
            self.cache_bytes -= len(oldest)
        self.cache[index] = decoded
        self.cache_bytes += len(decoded)
        return decoded

    def read(self, size=-1):
        remaining = self.starts[-1] - self.position
        if size is None or size < 0:
            size = remaining
        size = min(size, remaining)
        if size > MAX_READ:
            raise ValueError("Unbounded UnityFS materialization refused")
        if not size:
            return b""
        parts = []
        while size:
            index = bisect_right(self.starts, self.position) - 1
            available = self.starts[index + 1] - self.position
            count = min(size, available)
            begin = self.position - self.starts[index]
            parts.append(self._block(index)[begin:begin + count])
            self.position += count
            size -= count
        return b"".join(parts)


class RangeStream(RawIOBase):
    """Bounded read-only view over a contained UnityFS file, without copying it."""

    def __init__(self, source, offset, size):
        super().__init__()
        end = source.seek(0, 2)
        if (type(offset) is not int or type(size) is not int or
                offset < 0 or size < 0 or offset + size > end):
            raise ValueError("Contained UnityFS file outside block address space")
        self.source = source
        self.offset = offset
        self.size = size
        self.position = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        base = 0 if whence == 0 else self.position if whence == 1 else (
            self.size if whence == 2 else None
        )
        if base is None:
            raise ValueError("Unsupported seek mode")
        pos = base + offset
        if not 0 <= pos <= self.size:
            raise ValueError("Seek outside contained UnityFS file")
        self.position = pos
        return pos

    def read(self, size=-1):
        if size is None or size < 0:
            size = self.size - self.position
        size = min(size, self.size - self.position)
        self.source.seek(self.offset + self.position)
        data = self.source.read(size)
        self.position += len(data)
        return data


def _parse_without_unused_container_index(reader, original, assetbundle_type, *args, **kwargs):
    """Keep original AssetBundle objects counted without eagerly indexing media.

    UnityPy's SerializedFile.__init__ invokes parse_as_object() only to build
    its optional container lookup. W1-AH does not inspect that lookup or claim
    its contents were verified. No object headers or MonoBehaviour data are
    removed; all other parse calls retain standard UnityPy behavior.
    """
    if reader.type != assetbundle_type:
        return original(reader, *args, **kwargs)
    print("WWISE_INVENTORY_CONTAINER_INDEX_NOT_REQUESTED "
          f"path_id={reader.path_id}", flush=True)
    return SimpleNamespace(m_Container=[], m_PreloadTable=[])


@contextmanager
def streamed_unityfs(*, mono_budget_bytes=None, scope="WWISE",
                     skip_container_index=True):
    """Temporarily replace eager UnityFS reads and unused container indexing.

    The Wwise inventory counts all original Unity object headers and parses
    manageable MonoBehaviours. Larger original MonoBehaviours are **explicitly
    unparsed** with a recorded reason, not reported as full numeric extraction.
    UnityPy also eagerly builds an optional AssetBundle container index,
    which this metadata-only inventory never uses. Preserve every original
    object in type counts, restore all UnityPy methods on error, and never
    hide unknown numeric fields or claim complete source code reconstruction.
    """
    if scope not in ("WWISE", "CITY"):
        raise ValueError("Unknown source-specific inventory scope")
    if mono_budget_bytes is not None and (
            type(mono_budget_bytes) is not int or mono_budget_bytes < 1):
        raise ValueError("Invalid source-specific MonoBehaviour budget")
    from UnityPy.enums import ArchiveFlags, ArchiveFlagsOld, ClassIDType
    from UnityPy.files import BundleFile, File, ObjectReader, SerializedFile
    from UnityPy.helpers import ArchiveStorageManager, ImportHelper
    from UnityPy.streams import EndianBinaryReader

    old_fs = BundleFile.read_fs
    old_files = File.read_files
    old_parse_object = ObjectReader.parse_as_object
    old_parse_dict = ObjectReader.parse_as_dict

    def parse_as_object(reader, *args, **kwargs):
        if not skip_container_index:
            return old_parse_object(reader, *args, **kwargs)
        return _parse_without_unused_container_index(
            reader, old_parse_object, ClassIDType.AssetBundle, *args, **kwargs
        )

    def parse_as_dict(reader, *args, **kwargs):
        return _parse_bounded_wwise_mono(
            reader, old_parse_dict, ClassIDType.MonoBehaviour, *args,
            budget_bytes=mono_budget_bytes, scope=scope, **kwargs
        )

    def read_fs(self, reader):
        if self.signature != "UnityFS":
            return old_fs(self, reader)
        reader.read_long()  # declared full bundle size
        compressed_size = reader.read_u_int()
        uncompressed_size = reader.read_u_int()
        flags = reader.read_u_int()
        version = self.parse_version()
        if (version < (2020,) or
                (version[0] == 2020 and version < (2020, 3, 34)) or
                (version[0] == 2021 and version < (2021, 3, 2)) or
                (version[0] == 2022 and version < (2022, 1, 1))):
            self.dataflags = ArchiveFlagsOld(flags)
        else:
            self.dataflags = ArchiveFlags(flags)
        if self.dataflags & self.dataflags.UsesAssetBundleEncryption:
            self.decryptor = ArchiveStorageManager.ArchiveStorageDecryptor(reader)
        if self.version >= 7 or (
                version[0] == 2019 and version >= (2019, 4, 15)):
            reader.align_stream(16)
            self._uses_block_alignment = True

        start = reader.Position
        if compressed_size > MAX_BLOCK or uncompressed_size > MAX_BLOCK:
            raise ValueError("UnityFS directory metadata exceeds memory limit")
        if self.dataflags & ArchiveFlags.BlocksInfoAtTheEnd:
            reader.Position = reader.Length - compressed_size
            raw_info = reader.read_bytes(compressed_size)
            reader.Position = start
        else:
            raw_info = reader.read_bytes(compressed_size)
        info_bytes = self.decompress_data(raw_info, uncompressed_size, self.dataflags)
        if len(info_bytes) != uncompressed_size:
            raise ValueError("Inconsistent original UnityFS block directory")
        info = EndianBinaryReader(info_bytes, offset=start)
        info.read_bytes(16)  # directory hash
        block_count = info.read_int()
        if not 0 < block_count <= 2_000_000:
            raise ValueError("Invalid original UnityFS block count")
        blocks = []
        for _ in range(block_count):
            size = info.read_u_int()
            compressed_size = info.read_u_int()
            block_flags = info.read_u_short()
            offset = info.read_u_long() if self.version >= 9 else None
            blocks.append(SimpleNamespace(
                uncompressedSize=size, compressedSize=compressed_size,
                flags=block_flags, offset=offset,
            ))
        node_count = info.read_int()
        if not 0 < node_count <= 1_000_000:
            raise ValueError("Invalid original UnityFS directory count")
        nodes = [SimpleNamespace(
            offset=info.read_long(), size=info.read_long(),
            flags=info.read_u_int(), path=info.read_string_to_null(),
        ) for _ in range(node_count)]
        if not blocks or not nodes:
            raise ValueError("Missing UnityFS blocks or serialized file nodes")
        self._block_info_flags = blocks[0].flags
        if (isinstance(self.dataflags, ArchiveFlags) and
                self.dataflags & ArchiveFlags.BlockInfoNeedPaddingAtStart):
            reader.align_stream(16)
        blocks_reader = BlockStream(reader, blocks, reader.Position, self.decompress_data)
        return nodes, EndianBinaryReader(blocks_reader)

    def read_files(self, reader, nodes):
        if not isinstance(getattr(reader, "stream", None), (BlockStream, RangeStream)):
            return old_files(self, reader, nodes)
        for node in nodes:
            print(f"{scope}_INVENTORY_NODE_BEGIN name={node.path!r} "
                  f"size_bytes={node.size}", flush=True)
            sub_reader = EndianBinaryReader(
                RangeStream(reader.stream, node.offset, node.size)
            )
            parsed = ImportHelper.parse_file(
                sub_reader, self, node.path, is_dependency=self.is_dependency
            )
            kind = "serialized" if isinstance(parsed, SerializedFile) else "resource"
            object_count = len(parsed.objects) if kind == "serialized" else 0
            print(f"{scope}_INVENTORY_NODE_END name={node.path!r} "
                  f"kind={kind} objects={object_count}", flush=True)
            if isinstance(parsed, (EndianBinaryReader, SerializedFile)):
                if self.environment:
                    self.environment.register_cab(node.path, parsed)
            parsed.flags = getattr(node, "flags", 0)
            self.files[node.path] = parsed

    BundleFile.read_fs = read_fs
    File.read_files = read_files
    ObjectReader.parse_as_object = parse_as_object
    ObjectReader.parse_as_dict = parse_as_dict
    try:
        yield
    finally:
        ObjectReader.parse_as_dict = old_parse_dict
        ObjectReader.parse_as_object = old_parse_object
        File.read_files = old_files
        BundleFile.read_fs = old_fs
