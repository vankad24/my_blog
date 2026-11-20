"""Определение посетителя для дедупликации действий (просмотры, посещения)."""
import hashlib


def get_visitor_key(request) -> str:
    """Идентификатор посетителя: пользователь, гостевой токен или IP + User-Agent."""
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        return f'u:{user.pk}'

    visitor_id = getattr(request, 'visitor_id', None)
    if visitor_id:
        return f'g:{visitor_id}'

    # Запасной вариант: IP + User-Agent (например, если гость не получил токен)
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip = forwarded_for.split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    digest = hashlib.sha256(f'{ip}|{user_agent}'.encode('utf-8')).hexdigest()[:16]
    return f'ip:{digest}'
