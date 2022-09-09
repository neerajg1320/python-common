import hashlib


def generate_md5_hash_from_str(input_str, max_length=0):
    return generate_md5_hash_from_bytes(input_str.encode('utf-8'), max_length=max_length)


def generate_md5_hash_from_bytes(input_bytes, max_length=0):
    hash_digest = hashlib.md5(input_bytes).hexdigest()

    if max_length > 0:
        hash_digest = hash_digest[0:max_length]

    return hash_digest
