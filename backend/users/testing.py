"""Вспомогательные классы для тестов приложений."""
import fakeredis

from users import redis_store


class RedisTestCaseMixin:
    """Подменяет Redis на fakeredis на время тестового класса.

    Использует setUpClass/tearDownClass, чтобы работать и в классах,
    которые определяют собственный setUp.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.redis = fakeredis.FakeRedis(decode_responses=True)
        redis_store.set_redis_client(cls.redis)

    @classmethod
    def tearDownClass(cls):
        try:
            if hasattr(cls, 'redis'):
                cls.redis.flushall()
                cls.redis.close()
        finally:
            redis_store.set_redis_client(None)
        super().tearDownClass()
