import redis


def cache_connect(host='localhost'):
    try:
        cache = redis.StrictRedis(host=host, decode_responses=True)
    except Exception as e:
        print(e)
    return cache