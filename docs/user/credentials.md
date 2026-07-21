# Credential encryption

The plugin stores per-device credentials (password + optional enable secret) so the pyats worker can connect to devices during snapshot captures. Secrets are encrypted at rest with [Fernet](https://cryptography.io/en/latest/fernet/) (symmetric, authenticated). This guide explains the key model, the dev fallback, rotation, and what is never exposed.

## The key

Set `PLUGINS_CONFIG['netbox_pyats']['credential_key']` to a dedicated Fernet key. Generate one with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

```python
PLUGINS_CONFIG = {
    "netbox_pyats": {
        "credential_key": "<paste the generated key here>",
    },
}
```

## Dev fallback (do not use in production)

If `credential_key` is unset, the plugin derives a stable key from a slice of NetBox's `SECRET_KEY` and emits a `RuntimeWarning`. This is acceptable for dev but **must not ship to production** — anyone with the NetBox `SECRET_KEY` can decrypt every stored credential.

## Rotation

Changing `credential_key` means existing ciphertext can no longer be decrypted (Fernet is symmetric + authenticated). Re-key credentials after rotating:

1. Generate a new key (above).
2. Update `PLUGINS_CONFIG['netbox_pyats']['credential_key']` and restart NetBox.
3. Re-enter each `PyatsCredential`'s password / enable secret at **Plugins → PyATS →** the credential's edit page. Old ciphertext is unreadable; the re-entered plaintext is encrypted with the new key.

v1 ships a management note for this; an automated re-key command is planned for a later release.

## What is never exposed

- Secrets are **never** returned by the REST API, GraphQL, or the detail view template. Only the ciphertext is persisted.
- Only the in-memory pyATS `Testbed` object (built on the worker) ever holds plaintext, for the lifetime of the connection.
- The `PyatsCredential` detail view shows metadata (device, username, timestamps) but never the password or enable secret fields.

## Where the key lives

The key is read from `PLUGINS_CONFIG` at plugin load time. Treat it like any other NetBox secret: source it from your secrets manager (Vault, sops, environment injection) rather than committing it to `configuration.py` in plaintext. NetBox's own [configuration plugin pattern](https://netboxlabs.com/docs/netbox/en/stable/configuration/) supports environment-variable interpolation in `configuration.py` — use it.

## Related

- [Installation](installation.md) — the install + NetBox config steps.
- [Usage guide](usage.md) — adding a credential and capturing a snapshot.
- [Troubleshooting](troubleshooting.md) — what to check when captures fail with `connection failed`.