"""Hardening invariant guard for :data:`netbox_pyats.capture.STATE_COMMANDS` (ATW-436).

``STATE_COMMANDS`` is the OS-agnostic command list the ``kind=state`` /
``kind=full`` capture iterates over (``capture.py`` §``capture_snapshot``). It
expanded 4 -> 8 commands in ATW-248 with **no test** asserting the structural
invariants of the tuple itself:

- **non-empty** — an empty ``STATE_COMMANDS`` silently degrades ``kind=state``
  captures to a no-op with an empty ``state`` dict; the operator sees a green
  snapshot with zero state. A regression that empties the tuple (e.g. a bad
  refactor or a stray ``return`` above the assignment) would slip past the
  existing capture tests, which hard-code fixtures against the *current* set.
- **all strings** — ``capture_snapshot`` calls ``device.parse(command)`` per
  entry; a non-string element (a ``None`` leaked from a config loader, a
  ``bytes`` from a mis-typed source) raises ``TypeError`` deep in the pyATS
  parser instead of the clean ``ParserNotFound`` skip path, surfacing as a
  500 in the job rather than a recorded warning.
- **unique** — a duplicate command double-runs the parser and writes the
  second parse over the first in the ``state`` dict, masking the earlier
  result. The dict shape hides the duplicate at the data level; the invariant
  must be asserted at the source tuple.

Pure-Python: imports ``netbox_pyats.capture.STATE_COMMANDS`` only (no Genie,
no NetBox). Runs in the fast pytest lane alongside ``test_capture.py``.
"""

from netbox_pyats.capture import STATE_COMMANDS


class TestStateCommandsInvariant:
    """Structural invariants for :data:`STATE_COMMANDS` (ATW-436)."""

    def test_state_commands_is_non_empty(self):
        # An empty tuple silently makes kind=state captures no-ops with an
        # empty state dict; the operator sees a green snapshot with no state.
        assert len(STATE_COMMANDS) > 0, "STATE_COMMANDS must not be empty"

    def test_state_commands_is_a_tuple(self):
        # The capture loop, docs, and downstream parsers all assume an
        # immutable ordered sequence. A list (mutable) would let a stray
        # append corrupt the snapshot shape at runtime.
        assert isinstance(
            STATE_COMMANDS, tuple
        ), f"STATE_COMMANDS must be a tuple (immutable), got {type(STATE_COMMANDS).__name__}"

    def test_every_entry_is_a_non_empty_string(self):
        # device.parse(command) requires a str. A None or bytes entry raises
        # TypeError inside the pyATS parser instead of the clean
        # ParserNotFound skip path, surfacing as a job 500.
        for i, command in enumerate(STATE_COMMANDS):
            assert isinstance(
                command, str
            ), f"STATE_COMMANDS[{i}] is {type(command).__name__}, expected str: {command!r}"
            assert command.strip() != "", f"STATE_COMMANDS[{i}] is empty/whitespace: {command!r}"

    def test_entries_are_unique(self):
        # A duplicate double-runs the parser and the second parse overwrites
        # the first in the state dict, masking the earlier result. The dict
        # shape hides this at the data level; assert it at the source.
        seen: dict[str, list[int]] = {}
        for i, command in enumerate(STATE_COMMANDS):
            seen.setdefault(command, []).append(i)
        dupes = {cmd: idxs for cmd, idxs in seen.items() if len(idxs) > 1}
        assert dupes == {}, (
            f"duplicate entries in STATE_COMMANDS (would double-run + mask the " f"first parse): {dupes}"
        )

    def test_entries_are_lower_case_show_commands(self):
        # STATE_COMMANDS is OS-agnostic and Genie parser lookups are
        # case-sensitive against the parser registry (lower-case). An
        # upper/mixed-case entry silently misses every parser and is recorded
        # as None state with a warning across the whole OS matrix — a
        # silent-unsupported regression for a command that DOES have a parser.
        for i, command in enumerate(STATE_COMMANDS):
            assert command == command.lower(), (
                f"STATE_COMMANDS[{i}] is not lower-case (Genie parser lookup is " f"case-sensitive): {command!r}"
            )
            assert command.startswith("show "), (
                f"STATE_COMMANDS[{i}] is not a 'show ...' command (the v1 "
                f"state set is read-only show commands; a non-show entry "
                f"would be a scope creep regression): {command!r}"
            )

    def test_known_v1_command_set_present(self):
        # Pin the v1 expansion (ATW-248: 4 -> 8) so a silent rollback that
        # drops the expansion commands is caught. The four original commands
        # (version, inventory, ip interface brief, interfaces) plus the four
        # expansion commands (ip route, cdp neighbors, lldp neighbors, arp)
        # must all be present. This guards both the original and the expanded
        # shape.
        expected = {
            "show version",
            "show inventory",
            "show ip interface brief",
            "show interfaces",
            "show ip route",
            "show cdp neighbors",
            "show lldp neighbors",
            "show arp",
        }
        actual = set(STATE_COMMANDS)
        missing = expected - actual
        assert missing == set(), (
            f"STATE_COMMANDS is missing v1 command(s) (the ATW-248 expansion or "
            f"the original 4 must not be silently dropped): missing={sorted(missing)}"
        )
        # No undocumented extra commands either — adding one is a commitment
        # that Genie has a parser for every os in PLATFORM_SLUG_TO_PYATS_OS,
        # and should be a deliberate change reflected in this guard.
        extra = actual - expected
        assert extra == set(), (
            f"STATE_COMMANDS has undocumented command(s) not in the v1 set; "
            f"adding a command requires Genie coverage across the OS matrix "
            f"and updating this guard: extra={sorted(extra)}"
        )
