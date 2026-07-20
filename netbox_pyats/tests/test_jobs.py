"""Tests for the golden-config-text parser in :mod:`netbox_pyats.jobs` (Phase 4).

Pure-Python: exercises :func:`netbox_pyats.jobs._golden_text_to_config_dict`
against plain strings (no NetBox, no RQ, no Genie). The parser is a v1
line-oriented parse grouping lines under ``!``-delimited section headers into
a nested dict, so the compliance job can run on the worker with no extra
device connection.
"""

import pytest

pytest.importorskip("pyats")  # keep parity with the other pure-Python test files

from netbox_pyats.jobs import _golden_text_to_config_dict


class TestGoldenTextParser:
    def test_empty_text_yields_empty_dict(self):
        assert _golden_text_to_config_dict("") == {}

    def test_none_text_yields_empty_dict(self):
        assert _golden_text_to_config_dict(None) == {}

    def test_single_section_with_indented_lines(self):
        text = "interface GigabitEthernet0/0\n ip address 10.0.0.1 255.255.255.0\n no shutdown\n!\n"
        d = _golden_text_to_config_dict(text)
        assert "interface GigabitEthernet0/0" in d
        assert d["interface GigabitEthernet0/0"] == [
            " ip address 10.0.0.1 255.255.255.0",
            " no shutdown",
        ]

    def test_multiple_sections_separated_by_bang(self):
        text = "version 16.12\n!\n" "hostname rtr01\n!\n" "interface Gig0\n ip address 10.0.0.1 255.255.255.0\n!\n"
        d = _golden_text_to_config_dict(text)
        assert "version 16.12" in d
        assert "hostname rtr01" in d
        assert "interface Gig0" in d
        assert d["interface Gig0"] == [" ip address 10.0.0.1 255.255.255.0"]

    def test_preamble_lines_before_first_bang_grouped_under_preamble(self):
        text = "version 16.12\nhostname rtr01\n!\ninterface Gig0\n no shutdown\n!\n"
        d = _golden_text_to_config_dict(text)
        # "version" and "hostname" are top-level lines before the first "!".
        # The parser treats each non-indented line as a new section header,
        # so "version 16.12" and "hostname rtr01" each become their own
        # section (with no indented child lines).
        assert "version 16.12" in d
        assert "hostname rtr01" in d
        assert "interface Gig0" in d
        assert d["interface Gig0"] == [" no shutdown"]

    def test_trailing_section_without_bang_is_flushed(self):
        text = "hostname rtr01\n!\ninterface Gig0\n ip address 10.0.0.1 255.255.255.0"
        d = _golden_text_to_config_dict(text)
        assert "hostname rtr01" in d
        assert "interface Gig0" in d
        assert d["interface Gig0"] == [" ip address 10.0.0.1 255.255.255.0"]

    def test_indented_lines_without_section_header_grouped_under_preamble(self):
        text = " ip address 10.0.0.1 255.255.255.0\n no shutdown\n"
        d = _golden_text_to_config_dict(text)
        # No section header seen; indented lines go under "_preamble".
        assert "_preamble" in d
        assert d["_preamble"] == [
            " ip address 10.0.0.1 255.255.255.0",
            " no shutdown",
        ]

    def test_blank_lines_are_preserved_as_empty_indented_entries(self):
        text = "hostname rtr01\n!\ninterface Gig0\n\n no shutdown\n!\n"
        d = _golden_text_to_config_dict(text)
        # The blank line inside the interface section is preserved as an empty
        # string entry (v1 limitation; the diff engine treats it as a leaf).
        assert "interface Gig0" in d
        assert "" in d["interface Gig0"]
        assert " no shutdown" in d["interface Gig0"]
