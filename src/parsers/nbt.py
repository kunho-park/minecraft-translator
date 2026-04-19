"""Parser for binary NBT (Named Binary Tag) format files."""

from __future__ import annotations

import gzip
import logging
import struct
from typing import TYPE_CHECKING

import aiofiles

from .base import BaseParser, DumpError, ParseError

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)

# Type alias for NBT values
type NBTValue = (
    str | int | float | list[NBTValue] | dict[str, NBTValue] | list[int] | None
)

# NBT Tag type constants
TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12


class NBTParser(BaseParser):
    """Parser for binary NBT format files.

    Handles both compressed (gzip) and uncompressed NBT files.
    Extracts string values for translation.
    """

    file_extensions = (".nbt", ".dat")

    async def parse(self) -> Mapping[str, str]:
        """Parse an NBT file and extract string values.

        Returns:
            A flattened mapping of paths to string values.

        Raises:
            ParseError: If the file cannot be parsed.
        """
        self._check_extension()
        logger.info("Parsing NBT file: %s", self.path)

        try:
            async with aiofiles.open(self.path, "rb") as f:
                content = await f.read()
        except OSError as e:
            raise ParseError(self.path, f"Could not read file: {e}") from e

        # Try to decompress, fall back to raw if not gzip
        try:
            decompressed = gzip.decompress(content)
            data = self._parse_nbt(decompressed)
            self._was_compressed = True
        except (gzip.BadGzipFile, OSError):
            data = self._parse_nbt(content)
            self._was_compressed = False

        if not data:
            logger.warning("No data extracted from NBT file: %s", self.path)
            return {}

        result = self._flatten_nbt(data)
        logger.debug("Extracted %d strings from %s", len(result), self.path)
        return result

    async def dump(self, data: Mapping[str, str]) -> None:
        """Write translated data back to NBT format.

        Args:
            data: Flattened mapping of paths to translated values.

        Raises:
            DumpError: If writing fails.
        """
        logger.info("Dumping NBT file: %s", self.path)

        # Read original structure
        source_path = self.original_path if self.original_path else self.path
        try:
            async with aiofiles.open(source_path, "rb") as f:
                original_content = await f.read()
        except OSError as e:
            raise DumpError(self.path, f"Could not read original file: {e}") from e

        # Parse original
        try:
            decompressed = gzip.decompress(original_content)
            original_data = self._parse_nbt(decompressed)
            was_compressed = True
        except (gzip.BadGzipFile, OSError):
            original_data = self._parse_nbt(original_content)
            was_compressed = False

        if not original_data:
            raise DumpError(self.path, "Could not parse original NBT structure")

        # Update with translated values
        updated_data = self._unflatten_nbt(original_data, data)

        # Serialize back to NBT
        nbt_content = self._serialize_nbt(updated_data)

        # Compress if original was compressed
        if was_compressed:
            nbt_content = gzip.compress(nbt_content)

        try:
            async with aiofiles.open(self.path, "wb") as f:
                await f.write(nbt_content)
        except OSError as e:
            raise DumpError(self.path, f"Could not write file: {e}") from e

        logger.debug("Successfully wrote NBT file: %s", self.path)

    def _parse_nbt(self, data: bytes) -> dict[str, NBTValue]:
        """Parse NBT binary data.

        Args:
            data: Raw NBT bytes.

        Returns:
            Parsed NBT as a dictionary.
        """
        if not data:
            return {}

        try:
            offset = 0
            tag_type = data[offset]
            offset += 1

            if tag_type != TAG_COMPOUND:
                logger.warning("NBT does not start with TAG_Compound")
                return {}

            # Read root tag name
            name_length = struct.unpack(">H", data[offset : offset + 2])[0]
            offset += 2
            root_name = data[offset : offset + name_length].decode(
                "utf-8", errors="replace"
            )
            offset += name_length

            # Parse compound data
            compound_data, _ = self._parse_compound(data, offset)
            return {root_name: compound_data}

        except (struct.error, IndexError) as e:
            logger.error("Failed to parse NBT: %s", e)
            return {}

    def _parse_compound(
        self,
        data: bytes,
        offset: int,
    ) -> tuple[dict[str, NBTValue], int]:
        """Parse TAG_Compound.

        Args:
            data: Raw bytes.
            offset: Current position.

        Returns:
            Tuple of (parsed dict, new offset).
        """
        result: dict[str, NBTValue] = {}

        while offset < len(data):
            tag_type = data[offset]
            offset += 1

            if tag_type == TAG_END:
                break

            # Read tag name
            name_length = struct.unpack(">H", data[offset : offset + 2])[0]
            offset += 2
            tag_name = data[offset : offset + name_length].decode(
                "utf-8", errors="replace"
            )
            offset += name_length

            # Parse tag value
            value, offset = self._parse_tag(data, offset, tag_type)
            result[tag_name] = value

        return result, offset

    def _parse_tag(
        self,
        data: bytes,
        offset: int,
        tag_type: int,
    ) -> tuple[NBTValue, int]:
        """Parse a tag value based on its type.

        Args:
            data: Raw bytes.
            offset: Current position.
            tag_type: NBT tag type.

        Returns:
            Tuple of (parsed value, new offset).
        """
        if tag_type == TAG_BYTE:
            return struct.unpack(">b", data[offset : offset + 1])[0], offset + 1
        if tag_type == TAG_SHORT:
            return struct.unpack(">h", data[offset : offset + 2])[0], offset + 2
        if tag_type == TAG_INT:
            return struct.unpack(">i", data[offset : offset + 4])[0], offset + 4
        if tag_type == TAG_LONG:
            return struct.unpack(">q", data[offset : offset + 8])[0], offset + 8
        if tag_type == TAG_FLOAT:
            return struct.unpack(">f", data[offset : offset + 4])[0], offset + 4
        if tag_type == TAG_DOUBLE:
            return struct.unpack(">d", data[offset : offset + 8])[0], offset + 8
        if tag_type == TAG_BYTE_ARRAY:
            length = struct.unpack(">i", data[offset : offset + 4])[0]
            offset += 4
            return list(data[offset : offset + length]), offset + length
        if tag_type == TAG_STRING:
            length = struct.unpack(">H", data[offset : offset + 2])[0]
            offset += 2
            return data[offset : offset + length].decode(
                "utf-8", errors="replace"
            ), offset + length
        if tag_type == TAG_LIST:
            list_type = data[offset]
            offset += 1
            length = struct.unpack(">i", data[offset : offset + 4])[0]
            offset += 4
            result: list[NBTValue] = []
            for _ in range(length):
                value, offset = self._parse_tag(data, offset, list_type)
                result.append(value)
            return result, offset
        if tag_type == TAG_COMPOUND:
            return self._parse_compound(data, offset)
        if tag_type == TAG_INT_ARRAY:
            length = struct.unpack(">i", data[offset : offset + 4])[0]
            offset += 4
            result_ints: list[int] = []
            for _ in range(length):
                value_int = struct.unpack(">i", data[offset : offset + 4])[0]
                result_ints.append(value_int)
                offset += 4
            return result_ints, offset
        if tag_type == TAG_LONG_ARRAY:
            length = struct.unpack(">i", data[offset : offset + 4])[0]
            offset += 4
            result_longs: list[int] = []
            for _ in range(length):
                value_long = struct.unpack(">q", data[offset : offset + 8])[0]
                result_longs.append(value_long)
                offset += 8
            return result_longs, offset

        # Unknown tag type
        logger.warning("Unknown NBT tag type: %d", tag_type)
        return None, offset

    def _flatten_nbt(self, data: NBTValue, prefix: str = "") -> dict[str, str]:
        """Flatten NBT structure to extract string values.

        Args:
            data: NBT data to flatten.
            prefix: Current key prefix.

        Returns:
            Flattened mapping of paths to string values.
        """
        result: dict[str, str] = {}

        if isinstance(data, dict):
            for key, value in data.items():
                new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, str):
                    result[new_key] = value
                elif isinstance(value, dict | list):
                    result.update(self._flatten_nbt(value, new_key))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_key = f"{prefix}[{i}]" if prefix else f"[{i}]"
                if isinstance(item, str):
                    result[new_key] = item
                elif isinstance(item, dict | list):
                    result.update(self._flatten_nbt(item, new_key))

        return result

    def _unflatten_nbt(
        self,
        original: NBTValue,
        flat_data: Mapping[str, str],
    ) -> NBTValue:
        """Restore flattened data to original NBT structure.

        Args:
            original: Original NBT structure.
            flat_data: Flattened translated data.

        Returns:
            Updated NBT structure.
        """
        return self._update_structure_recursive(original, flat_data, "")

    def _update_structure_recursive(
        self,
        obj: NBTValue,
        flat_data: Mapping[str, str],
        prefix: str,
    ) -> NBTValue:
        """Recursively update structure with translated values.

        Args:
            obj: Object to update.
            flat_data: Flattened translated data.
            prefix: Current key prefix.

        Returns:
            Updated object.
        """
        if isinstance(obj, dict):
            result: dict[str, NBTValue] = {}
            for key, value in obj.items():
                new_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, str) and new_key in flat_data:
                    result[key] = flat_data[new_key]
                elif isinstance(value, dict | list):
                    result[key] = self._update_structure_recursive(
                        value, flat_data, new_key
                    )
                else:
                    result[key] = value
            return result

        if isinstance(obj, list):
            result_list: list[NBTValue] = []
            for i, item in enumerate(obj):
                new_key = f"{prefix}[{i}]" if prefix else f"[{i}]"
                if isinstance(item, str) and new_key in flat_data:
                    result_list.append(flat_data[new_key])
                elif isinstance(item, dict | list):
                    result_list.append(
                        self._update_structure_recursive(item, flat_data, new_key)
                    )
                else:
                    result_list.append(item)
            return result_list

        if isinstance(obj, str) and prefix in flat_data:
            return flat_data[prefix]

        return obj

    def _serialize_nbt(self, data: dict[str, NBTValue]) -> bytes:
        """Serialize NBT data to binary.

        Args:
            data: NBT data to serialize.

        Returns:
            Binary NBT data.
        """
        result = b""

        # Root tag is TAG_Compound
        for root_name, root_data in data.items():
            result += struct.pack("B", TAG_COMPOUND)
            encoded_name = root_name.encode("utf-8")
            result += struct.pack(">H", len(encoded_name))
            result += encoded_name
            if isinstance(root_data, dict):
                result += self._serialize_compound(root_data)
            break  # Only process first root

        return result

    def _serialize_compound(self, data: dict[str, NBTValue]) -> bytes:
        """Serialize TAG_Compound.

        Args:
            data: Dictionary to serialize.

        Returns:
            Binary data.
        """
        result = b""

        for key, value in data.items():
            tag_type = self._get_tag_type(value)
            result += struct.pack("B", tag_type)
            encoded_key = key.encode("utf-8")
            result += struct.pack(">H", len(encoded_key))
            result += encoded_key
            result += self._serialize_value(value, tag_type)

        result += struct.pack("B", TAG_END)
        return result

    def _get_tag_type(self, value: NBTValue) -> int:
        """Determine NBT tag type for a value.

        Args:
            value: Value to check.

        Returns:
            NBT tag type constant.
        """
        if isinstance(value, bool):
            return TAG_BYTE
        if isinstance(value, int):
            if -128 <= value <= 127:
                return TAG_BYTE
            if -32768 <= value <= 32767:
                return TAG_SHORT
            if -2147483648 <= value <= 2147483647:
                return TAG_INT
            return TAG_LONG
        if isinstance(value, float):
            return TAG_DOUBLE
        if isinstance(value, str):
            return TAG_STRING
        if isinstance(value, list):
            return TAG_LIST
        if isinstance(value, dict):
            return TAG_COMPOUND
        return TAG_STRING  # Default to string

    def _serialize_value(self, value: NBTValue, tag_type: int) -> bytes:
        """Serialize a value to NBT binary.

        Args:
            value: Value to serialize.
            tag_type: NBT tag type.

        Returns:
            Binary data.
        """
        if tag_type == TAG_BYTE:
            byte_value = (
                int(value)
                if isinstance(value, bool)
                else (value if isinstance(value, int) else 0)
            )
            byte_value = max(-128, min(127, byte_value))
            return struct.pack(">b", byte_value)
        if tag_type == TAG_SHORT:
            return struct.pack(">h", value if isinstance(value, int) else 0)
        if tag_type == TAG_INT:
            return struct.pack(">i", value if isinstance(value, int) else 0)
        if tag_type == TAG_LONG:
            return struct.pack(">q", value if isinstance(value, int) else 0)
        if tag_type == TAG_FLOAT:
            return struct.pack(">f", value if isinstance(value, float | int) else 0.0)
        if tag_type == TAG_DOUBLE:
            return struct.pack(">d", value if isinstance(value, float | int) else 0.0)
        if tag_type == TAG_STRING:
            encoded = str(value).encode("utf-8")
            return struct.pack(">H", len(encoded)) + encoded
        if tag_type == TAG_LIST:
            if not isinstance(value, list) or not value:
                return struct.pack("B", 0) + struct.pack(">i", 0)
            list_type = self._get_tag_type(value[0])
            result = struct.pack("B", list_type)
            result += struct.pack(">i", len(value))
            for item in value:
                result += self._serialize_value(item, list_type)
            return result
        if tag_type == TAG_COMPOUND:
            if isinstance(value, dict):
                return self._serialize_compound(value)
            return struct.pack("B", TAG_END)

        # Default to string
        encoded = str(value).encode("utf-8")
        return struct.pack(">H", len(encoded)) + encoded
