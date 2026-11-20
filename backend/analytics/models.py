from django.db import models


class SiteVisitCounter(models.Model):
    """Единственная запись с общим числом посещений сайта."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    total = models.PositiveBigIntegerField('Всего посещений', default=0)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        db_table = 'site_visit_counter'
        verbose_name = 'Счётчик посещений'
        verbose_name_plural = 'Счётчик посещений'

    def __str__(self) -> str:
        return str(self.total)

    def save(self, *args, **kwargs):
        # Счётчик всегда хранится в одной записи
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        """Вернуть (при необходимости создать) единственную запись счётчика."""
        counter, _ = cls.objects.get_or_create(pk=1)
        return counter
