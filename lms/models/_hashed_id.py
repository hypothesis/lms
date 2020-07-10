import hashlib


def hashed_id(*parts):
    """
    Create a hashed id from multiple stringifying parts.

    It is crucial that if any one of the parts changes meaningfully that it's
    stringification changes too.

    :param parts: An objects which can be converted to strings
    :return: A string which can be used as an id.
    """
    hash_object = hashlib.sha1()
    for part in parts:
        hash_object.update(str(part).encode())

    return hash_object.hexdigest()
