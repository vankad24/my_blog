from django.db.models import F
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from users import redis_store
from users.visitors import get_visitor_key

from .models import SiteVisitCounter


class SiteVisitView(APIView):
    """Общий счётчик посещений сайта.

    POST засчитывает посещение не чаще одного раза в SITE_VISIT_TTL секунд
    для каждого посетителя (пользователь, гостевой токен или IP + User-Agent).
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({'total': SiteVisitCounter.get_solo().total})

    def post(self, request):
        counter = SiteVisitCounter.get_solo()

        try:
            counted = redis_store.register_site_visit(get_visitor_key(request))
        except Exception:
            # Redis недоступен: не увеличиваем счётчик, но отдаём текущее значение
            return Response(
                {'counted': False, 'total': counter.total},
                status=status.HTTP_200_OK,
            )

        if counted:
            SiteVisitCounter.objects.filter(pk=counter.pk).update(
                total=F('total') + 1
            )
            counter.refresh_from_db(fields=['total'])

        return Response(
            {'counted': counted, 'total': counter.total},
            status=status.HTTP_200_OK,
        )
