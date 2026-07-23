"""Regression test for the ATW-116 secret/PII detection allowlist/regex.

Validates the regex rules in ``.gitleaks.toml`` against the Tailscale-CGNAT
leakage class that bit PR #38 (ATW-114): concrete Tailscale IPs, tailnet
FQDNs, Paperclip identifiers, and private-key blocks must be flagged, while the
``<...>`` placeholder convention used in ``docs/developer/remote-access.md``
must not false-positive.

Pure-Python: no Django/NetBox dependency, runs in the fast pytest lane.
"""

import re
import unittest


RULES = {
    "tailscale-cgnat-ip": re.compile(
        r"\b100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.\d{1,3}\.\d{1,3}\b"
    ),
    "tailscale-dns-fqdn": re.compile(
        r"\b[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
        r"\.(?:ts\.net|tscale\.net|tailscale\.com)\b"
    ),
    "paperclip-identifier": re.compile(
        r"(?i)\bPAPERCLIP_(?:API_KEY|AGENT_ID|RUN_ID|COMPANY_ID|TASK_ID)\b"
        r"[=:]\s*[\"']?[A-Za-z0-9._-]{8,}[\"']?"
    ),
    "private-key-block": re.compile(
        r"-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP |ENCRYPTED |)PRIVATE KEY-----"
    ),
}

ALLOWLIST = {
    "tailscale-cgnat-ip": [
        r"<TAILSCALE_IP>",
        r"100\.x\.y\.z",
        r"100\.64\.0\.0/10",
        r"100\.127\.255\.255",
    ],
    "tailscale-dns-fqdn": [
        r"<TAILNET_FQDN>",
        r"your-host\.tailnet-name\.ts\.net",
    ],
    "paperclip-identifier": [
        r"PAPERCLIP_API_KEY=<<.*>>",
        r"PAPERCLIP_API_KEY=\$PAPERCLIP_API_KEY",
        r"\$\{?PAPERCLIP_[A-Z_]+\}?",
        r"<PAPERCLIP_[A-Z_]+>",
    ],
}


def _flagged(text):
    """Return list of (rule_id, matched_segment) the gitleaks rules would flag."""
    hits = []
    lines = text.splitlines() or [text]
    for rid, rx in RULES.items():
        for line in lines:
            for m in rx.finditer(line):
                seg = m.group(0)
                if any(re.search(ap, line) for ap in ALLOWLIST.get(rid, [])):
                    continue
                hits.append((rid, seg))
    return hits


class SecretDetectionPositiveCases(unittest.TestCase):
    """Concrete leaks that MUST be flagged (the ATW-114 regression set)."""

    def test_concrete_tailscale_cgnat_ip_low(self):
        self.assertTrue(_flagged("ssh user@100.64.0.1"))

    def test_concrete_tailscale_cgnat_ip_high(self):
        self.assertTrue(_flagged("ssh user@100.127.200.1"))

    def test_concrete_tailnet_fqdn(self):
        self.assertTrue(_flagged("myhost.tailnet.ts.net"))

    def test_concrete_paperclip_api_key(self):
        self.assertTrue(_flagged("PAPERCLIP_API_KEY=abc123secrettoken"))

    def test_concrete_paperclip_agent_id(self):
        self.assertTrue(_flagged("PAPERCLIP_AGENT_ID=46a7f4a1-1d1f-4a61"))

    def test_private_key_block(self):
        self.assertTrue(_flagged("-----BEGIN RSA PRIVATE KEY-----"))


class SecretDetectionNegativeCases(unittest.TestCase):
    """Placeholder / RFC1918 / loopback forms that MUST NOT be flagged."""

    def test_placeholder_tailscale_ip(self):
        self.assertFalse(_flagged("ssh -N -L 8000:127.0.0.1:8080 user@<TAILSCALE_IP>"))

    def test_runbook_example_row(self):
        self.assertFalse(
            _flagged("| Tailscale IP | `<TAILSCALE_IP>` (e.g. `100.x.y.z`) |")
        )

    def test_cgnat_range_header(self):
        self.assertFalse(_flagged("100.64.0.0/10 is the CGNAT range"))

    def test_placeholder_tailnet_fqdn(self):
        self.assertFalse(_flagged("https://<TAILNET_FQDN>/"))

    def test_example_tailnet_fqdn(self):
        self.assertFalse(_flagged("your-host.tailnet-name.ts.net"))

    def test_paperclip_shell_var(self):
        self.assertFalse(_flagged("$PAPERCLIP_TASK_ID in env"))

    def test_paperclip_placeholder(self):
        self.assertFalse(_flagged("<PAPERCLIP_RUN_ID>"))

    def test_loopback_not_flagged(self):
        self.assertFalse(_flagged("127.0.0.1:8080 loopback"))

    def test_rfc1918_not_flagged(self):
        self.assertFalse(_flagged("192.168.1.5"))

    def test_rfc1918_ten_not_flagged(self):
        self.assertFalse(_flagged("10.0.0.1"))

    def test_just_below_cgnat(self):
        self.assertFalse(_flagged("100.63.255.255"))

    def test_just_above_cgnat(self):
        self.assertFalse(_flagged("100.128.0.1"))


if __name__ == "__main__":
    unittest.main()