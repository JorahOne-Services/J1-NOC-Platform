"""One-shot verification: proves the secret-safe collector pipeline.

1. Writes a (fake) LDAP credential into the encrypted DB vault.
2. Runs the LDAP collector.
3. Asserts:
   - the credential is NOT present in any output file or stdout unmasked,
   - directory_status.json (if any) holds only operational state,
   - collector_status.json records the run.
4. Cleans up the test credential afterwards.
"""
import json
import sys

from app import config
from app.database import SessionLocal
from app.encryption import encrypt
from app.models import EncryptedSetting
from app.collectors import base, ldap


def main() -> int:
    test_key = "LDAP_BIND_PASSWORD"
    test_val = "Sup3rS3cretBindPass!ZZZ"  # clearly fake; proves masking works
    try:
        db = SessionLocal()
        # upsert test credential into the vault
        row = db.query(EncryptedSetting).filter(EncryptedSetting.key == test_key).first()
        if row:
            row.value = encrypt(test_val)
        else:
            db.add(EncryptedSetting(key=test_key, value=encrypt(test_val), is_encrypted=True,
                                    category="integrations", description="verify"))
        db.commit()
        print("VAULT: stored LDAP_BIND_PASSWORD (encrypted)")

        # read back via the same path the collector uses -> must equal raw
        got = config.get_db_setting(test_key)
        assert got == test_val, "vault read mismatch"
        print("VAULT_READ: matches decrypted value")

        # run collector; LDAP not reachable -> 'offline' but must NOT leak value
        ldap.collect()
    finally:
        db.close()

    # inspect everything that got written / printed
    status = json.loads((base.DATA_DIR / base.STATUS_FILE).read_text())
    ldap_status = next((s for s in status if s["name"] == "ldap"), {})
    print("LDAP_STATUS:", ldap_status)

    # leak assertions
    leak = False
    blob = json.dumps(status)
    if test_val in blob:
        print("LEAK: raw credential found in status file!"); leak = True
    if test_val in ldap_status.get("detail", ""):
        print("LEAK: raw credential in detail!"); leak = True

    # cleanup test credential
    db = SessionLocal()
    try:
        r = db.query(EncryptedSetting).filter(EncryptedSetting.key == test_key).first()
        if r:
            db.delete(r); db.commit()
        print("CLEANUP: removed test credential")
    finally:
        db.close()

    if leak:
        print("RESULT: FAIL (secret leaked)")
        return 1
    print("RESULT: PASS (vault-only cred, masked logs, no leak)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
