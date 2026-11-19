"""Вспомогательные классы для тестов приложений."""
import fakeredis

from users import redis_store


class RedisTestCaseMixin:
    """Подменяет Redis на fakeredis на время тестового класса.

    Redis очищается перед каждым тестом (`_pre_setup`), поэтому счётчики
    лимитов и сессии не перетекают между тестами.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.redis = fakeredis.FakeRedis(decode_responses=True)
        redis_store.set_redis_client(cls.redis)

    def _pre_setup(self):
        super()._pre_setup()
        self.redis.flushall()

    @classmethod
    def tearDownClass(cls):
        try:
            if hasattr(cls, 'redis'):
                cls.redis.flushall()
                cls.redis.close()
        finally:
            redis_store.set_redis_client(None)
        super().tearDownClass()
