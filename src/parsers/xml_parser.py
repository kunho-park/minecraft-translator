"""Parser for XML format files."""

from __future__ import annotations

import io
import logging
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

import aiofiles

from .base import BaseParser, DumpError, ParseError

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)

# Type alias for XML values
type XMLValue = str | dict[str, XMLValue] | list[XMLValue]


class XMLParser(BaseParser):
    """Parser for XML format files.

    Flattens XML structure to extract translatable text nodes.
    Preserves attributes and structure when writing back.
    """

    file_extensions = (".xml",)

    async def parse(self) -> Mapping[str, str]:
        """Parse an XML file and extract text content.

        Returns:
            A flattened mapping of paths to text values.

        Raises:
            ParseError: If the file cannot be parsed.
        """
        self._check_extension()
        logger.info("Parsing XML file: %s", self.path)

        try:
            async with aiofiles.open(self.path, encoding="utf-8", errors="replace") as f:
                content = await f.read()
        except OSError as e:
            raise ParseError(self.path, f"Could not read file: {e}") from e

        try:
            data = self._load_xml_content(content)
        except ValueError as e:
            raise ParseError(self.path, str(e)) from e

        result = self._flatten_xml(data)
        logger.debug("Extracted %d text nodes from %s", len(result), self.path)
        return result

    async def dump(self, data: Mapping[str, str]) -> None:
        """Write translated data back to XML format.

        Args:
            data: Flattened mapping of paths to translated values.

        Raises:
            DumpError: If writing fails.
        """
        logger.info("Dumping XML file: %s", self.path)

        # Read original structure
        try:
            async with aiofiles.open(self.path, encoding="utf-8", errors="replace") as f:
                original_content = await f.read()
        except OSError as e:
            raise DumpError(self.path, f"Could not read file: {e}") from e

        try:
            original_data = self._load_xml_content(original_content)
        except ValueError as e:
            raise DumpError(self.path, f"Could not parse original XML: {e}") from e

        # Update with translated values
        updated_data = self._unflatten_xml(original_data, data)

        # Serialize back to XML
        try:
            xml_content = self._save_xml_content(updated_data)
        except ValueError as e:
            raise DumpError(self.path, f"Could not serialize XML: {e}") from e

        try:
            async with aiofiles.open(self.path, "w", encoding="utf-8") as f:
                await f.write(xml_content)
        except OSError as e:
            raise DumpError(self.path, f"Could not write file: {e}") from e

        logger.debug("Successfully wrote XML file: %s", self.path)

    def _load_xml_content(self, content: str) -> dict[str, XMLValue]:
        """Parse XML string to dictionary.

        Args:
            content: Raw XML string.

        Returns:
            Dictionary representation of XML.

        Raises:
            ValueError: If parsing fails.
        """
        try:
            root = ET.fromstring(content)
            result = self._element_to_dict(root)
            return {root.tag: result}
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML: {e}") from e

    def _save_xml_content(self, data: dict[str, XMLValue]) -> str:
        """Convert dictionary back to XML string.

        Args:
            data: Dictionary representation of XML.

        Returns:
            XML string.

        Raises:
            ValueError: If data structure is invalid.
        """
        if len(data) != 1:
            raise ValueError("XML data must have exactly one root element")

        root_tag = next(iter(data))
        root_data = data[root_tag]

        root = self._dict_to_element(root_data, root_tag)

        # Write with XML declaration
        tree = ET.ElementTree(root)
        output = io.BytesIO()
        tree.write(output, encoding="UTF-8", xml_declaration=True)

        return output.getvalue().decode("UTF-8")

    def _element_to_dict(self, element: ET.Element) -> dict[str, XMLValue] | str:
        """Convert XML element to dictionary.

        Args:
            element: XML element to convert.

        Returns:
            Dictionary representation or string if text-only.
        """
        result: dict[str, XMLValue] = {}

        # Handle attributes
        if element.attrib:
            result["@attributes"] = dict(element.attrib)

        # Handle text content
        if element.text and element.text.strip():
            result["#text"] = element.text.strip()

        # Handle children
        children: dict[str, XMLValue] = {}
        for child in element:
            child_dict = self._element_to_dict(child)

            # Handle multiple children with same tag
            if child.tag in children:
                existing = children[child.tag]
                if isinstance(existing, list):
                    existing.append(child_dict)
                else:
                    children[child.tag] = [existing, child_dict]
            else:
                children[child.tag] = child_dict

        if children:
            result.update(children)

        # Simplify text-only elements
        if len(result) == 1 and "#text" in result:
            text_value = result["#text"]
            if isinstance(text_value, str):
                return text_value

        return result

    def _dict_to_element(
        self,
        data: XMLValue,
        tag: str = "root",
    ) -> ET.Element:
        """Convert dictionary to XML element.

        Args:
            data: Dictionary data to convert.
            tag: Element tag name.

        Returns:
            XML element.
        """
        if isinstance(data, str):
            element = ET.Element(tag)
            element.text = data
            return element

        element = ET.Element(tag)

        if not isinstance(data, dict):
            return element

        # Handle attributes
        if "@attributes" in data:
            attrs = data["@attributes"]
            if isinstance(attrs, dict):
                for key, value in attrs.items():
                    if isinstance(value, str):
                        element.set(key, value)

        # Handle text
        if "#text" in data:
            text_value = data["#text"]
            if isinstance(text_value, str):
                element.text = text_value

        # Handle children
        for key, value in data.items():
            if key in ("@attributes", "#text"):
                continue

            if isinstance(value, list):
                for item in value:
                    element.append(self._dict_to_element(item, key))
            else:
                element.append(self._dict_to_element(value, key))

        return element

    def _flatten_xml(
        self,
        data: XMLValue,
        prefix: str = "",
    ) -> dict[str, str]:
        """Flatten XML structure to extract text values.

        Args:
            data: XML data to flatten.
            prefix: Current key prefix.

        Returns:
            Flattened mapping of paths to text values.
        """
        result: dict[str, str] = {}

        if isinstance(data, dict):
            for key, value in data.items():
                if key == "@attributes":
                    continue  # Skip attributes

                new_key = f"{prefix}.{key}" if prefix else key

                if key == "#text" and isinstance(value, str):
                    # Text node - use parent prefix
                    result[prefix if prefix else "text"] = value
                elif isinstance(value, str):
                    result[new_key] = value
                elif isinstance(value, dict | list):
                    result.update(self._flatten_xml(value, new_key))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_key = f"{prefix}[{i}]" if prefix else f"[{i}]"
                if isinstance(item, str):
                    result[new_key] = item
                elif isinstance(item, dict | list):
                    result.update(self._flatten_xml(item, new_key))

        return result

    def _unflatten_xml(
        self,
        original: dict[str, XMLValue],
        flat_data: Mapping[str, str],
    ) -> dict[str, XMLValue]:
        """Restore flattened data to original XML structure.

        Args:
            original: Original XML structure.
            flat_data: Flattened translated data.

        Returns:
            Updated XML structure.
        """
        result = dict(original)

        for flat_key, value in flat_data.items():
            self._set_nested_xml_value(result, flat_key, value)

        return result

    def _set_nested_xml_value(
        self,
        data: dict[str, XMLValue],
        key: str,
        value: str,
    ) -> None:
        """Set a value at a nested path.

        Args:
            data: Dictionary to modify.
            key: Dot-notation path.
            value: Value to set.
        """
        if key == "text":
            data["#text"] = value
            return

        parts = self._parse_key_path(key)
        if not parts:
            return

        current: XMLValue = data
        for i, part in enumerate(parts[:-1]):
            if part.startswith("[") and part.endswith("]"):
                index = int(part[1:-1])
                if isinstance(current, list) and len(current) > index:
                    current = current[index]
                else:
                    return
            elif isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return

        # Set final value
        last_part = parts[-1]
        if last_part.startswith("[") and last_part.endswith("]"):
            index = int(last_part[1:-1])
            if isinstance(current, list) and len(current) > index:
                item = current[index]
                if isinstance(item, dict) and "#text" in item:
                    item["#text"] = value
                else:
                    current[index] = value
        elif isinstance(current, dict):
            if last_part == "#text":
                current["#text"] = value
            elif last_part in current:
                item = current[last_part]
                if isinstance(item, dict) and "#text" in item:
                    item["#text"] = value
                else:
                    current[last_part] = value
            else:
                current[last_part] = value

    @staticmethod
    def _parse_key_path(key: str) -> list[str]:
        """Parse a dot-notation key into parts.

        Args:
            key: Key path string.

        Returns:
            List of path parts.
        """
        parts: list[str] = []
        current_part = ""
        bracket_count = 0

        for char in key:
            if char == "." and bracket_count == 0:
                if current_part:
                    parts.append(current_part)
                    current_part = ""
            elif char == "[":
                if current_part:
                    parts.append(current_part)
                    current_part = "["
                else:
                    current_part += char
                bracket_count += 1
            elif char == "]":
                current_part += char
                bracket_count -= 1
                if bracket_count == 0:
                    parts.append(current_part)
                    current_part = ""
            else:
                current_part += char

        if current_part:
            parts.append(current_part)

        return parts
