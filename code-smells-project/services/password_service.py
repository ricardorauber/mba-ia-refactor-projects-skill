import hmac

from werkzeug.security import check_password_hash, generate_password_hash

HASH_PREFIXES = ("scrypt:", "pbkdf2:")


def hash_password(raw_password):
    return generate_password_hash(raw_password)


def is_hashed(stored_password):
    return str(stored_password).startswith(HASH_PREFIXES)


def verify_password(stored_password, raw_password):
    """Return (matches, needs_rehash). Legacy plain-text rows are accepted once and flagged for re-hash."""
    if stored_password is None:
        return False, False
    if is_hashed(stored_password):
        return check_password_hash(stored_password, raw_password), False
    matches = hmac.compare_digest(str(stored_password).encode(), raw_password.encode())
    return matches, matches
