import hashlib


def get_md5_hash(input_str, max_length=0):
    hash_digest = hashlib.md5(input_str.encode('utf-8')).hexdigest()

    if max_length > 0:
        hash_digest = hash_digest[0:max_length]

    return hash_digest
