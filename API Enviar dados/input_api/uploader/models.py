from django.db import models

class Input(models.Model):
    name = models.CharField(max_length=255)
    content = models.JSONField()
    created_at = models.DateTimeField()
    is_used = models.BooleanField()

    class Meta:
        db_table = 'inputs'       # Nome exato da tabela que criaste
        managed = False           # Impede o Django de criar/modificar a tabela

    def __str__(self):
        return self.name
