"""Общая работа с Redis: клиент, сессии авторизации и гостевые токены."""
import json
import secrets
import uuid

import redis
from django.conf import settings

# Клиент создаётся лениво, чтобы не подключаться к Redis при импорте модуля
_client = None


def get_redis():
    """Вернуть общий клиент Redis (на процесс)."""
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _client


def set_redis_client(client):
    """Подменить клиент Redis (используется в тестах)."""
    global _client
    _client = client


def _refresh_ttl() -> int:
    """TTL сессии в секундах — равен времени жизни refresh-токена."""
    return int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())


def _session_key(sid: str) -> str:
    return f'auth:sid:{sid}'


def _user_sessions_key(user_id) -> str:
    return f'auth:user:{user_id}'


def _guest_key(token: str) -> str:
    return f'auth:guest:{token}'


# ---------------------------------------------------------------------------
# Сессии авторизованных пользователей
# ---------------------------------------------------------------------------

def create_session(user_id, refresh_jti) -> str:
    """Создать серверную сессию и вернуть её идентификатор sid."""
    sid = uuid.uuid4().hex
    payload = json.dumps({
        'user_id': str(user_id),
        'refresh_jti': str(refresh_jti),
    })
    ttl = _refresh_ttl()
    r = get_redis()
    pipe = r.pipeline()
    pipe.set(_session_key(sid), payload, ex=ttl)
    pipe.sadd(_user_sessions_key(user_id), sid)
    pipe.expire(_user_sessions_key(user_id), ttl)
    pipe.execute()
    return sid


def get_session(sid: str):
    """Вернуть данные сессии или None."""
    if not sid:
        return None
    raw = get_redis().get(_session_key(sid))
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def session_exists(sid: str, user_id=None) -> bool:
    """Существует ли сессия (опционально — принадлежит ли она пользователю)."""
    session = get_session(sid)
    if not session:
        return False
    if user_id is None:
        return True
    return str(session.get('user_id')) == str(user_id)


def refresh_jti_matches(sid: str, refresh_jti) -> bool:
    """Совпадает ли jti refresh-токена с текущим в сессии (защита от повторного использования)."""
    session = get_session(sid)
    if not session:
        return False
    return str(session.get('refresh_jti')) == str(refresh_jti)


def update_session(sid: str, refresh_jti=None) -> bool:
    """Обновить jti refresh-токена и продлить TTL сессии."""
    session = get_session(sid)
    if not session:
        return False
    if refresh_jti is not None:
        session['refresh_jti'] = str(refresh_jti)
    ttl = _refresh_ttl()
    user_id = session.get('user_id')
    r = get_redis()
    pipe = r.pipeline()
    pipe.set(_session_key(sid), json.dumps(session), ex=ttl)
    if user_id is not None:
        pipe.sadd(_user_sessions_key(user_id), sid)
        pipe.expire(_user_sessions_key(user_id), ttl)
    pipe.execute()
    return True


def delete_session(sid: str, user_id=None) -> None:
    """Удалить сессию (logout)."""
    if not sid:
        return
    r = get_redis()
    pipe = r.pipeline()
    pipe.delete(_session_key(sid))
    if user_id is not None:
        pipe.srem(_user_sessions_key(user_id), sid)
    pipe.execute()


def invalidate_user_sessions(user_id) -> int:
    """Отозвать все сессии пользователя (смена/сброс пароля). Вернуть количество."""
    r = get_redis()
    sids = r.smembers(_user_sessions_key(user_id)) or set()
    if sids:
        r.delete(*[_session_key(sid) for sid in sids])
    r.delete(_user_sessions_key(user_id))
    return len(sids)


# ---------------------------------------------------------------------------
# Гостевые токены
# ---------------------------------------------------------------------------

def create_guest_session(visitor_id=None):
    """Создать гостевой токен. Вернуть (token, visitor_id)."""
    token = secrets.token_urlsafe(32)
    visitor_id = visitor_id or str(uuid.uuid4())
    get_redis().set(_guest_key(token), visitor_id, ex=settings.GUEST_TOKEN_TTL)
    return token, visitor_id


def get_guest_visitor(token: str, touch: bool = False):
    """Вернуть visitor_id по гостевому токену или None. touch продлевает TTL."""
    if not token:
        return None
    key = _guest_key(token)
    r = get_redis()
    visitor_id = r.get(key)
    if visitor_id and touch:
        r.expire(key, settings.GUEST_TOKEN_TTL)
    return visitor_id


# ---------------------------------------------------------------------------
# Просмотры постов
# ---------------------------------------------------------------------------

def register_post_view(post_id, visitor: str) -> bool:
    """Засчитать просмотр, если посетитель не смотрел пост в последние POST_VIEW_TTL секунд.

    Возвращает True, если просмотр новый (SET NX EX успешен).
    """
    key = f'post:view:{post_id}:{visitor}'
    return bool(
        get_redis().set(key, '1', nx=True, ex=settings.POST_VIEW_TTL)
    )


# ---------------------------------------------------------------------------
# Посещения сайта
# ---------------------------------------------------------------------------

def register_site_visit(visitor: str) -> bool:
    """Засчитать посещение сайта, если посетитель не заходил последние SITE_VISIT_TTL секунд.

    Возвращает True, если посещение новое (SET NX EX успешен).
    """
    key = f'site:visit:{visitor}'
    return bool(
        get_redis().set(key, '1', nx=True, ex=settings.SITE_VISIT_TTL)
    )


# ---------------------------------------------------------------------------
# Ограничение попыток входа и регистрации
# ---------------------------------------------------------------------------

def _rate_limit_key(scope: str, identifier: str) -> str:
    return f'ratelimit:{scope}:{identifier}'


def hit_rate_limit(scope: str, identifier: str, limit: int, window: int):
    """Увеличить счётчик попыток в текущем окне.

    Возвращает (разрешено, сколько секунд ждать до сброса окна).
    """
    key = _rate_limit_key(scope, identifier)
    r = get_redis()
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.ttl(key)
    current, ttl = pipe.execute()

    if ttl is None or ttl < 0:
        r.expire(key, window)
        ttl = window

    return current <= limit, int(ttl)


def reset_rate_limit(scope: str, identifier: str) -> None:
    """Сбросить счётчик попыток (после успешного входа/регистрации)."""
    get_redis().delete(_rate_limit_key(scope, identifier))

