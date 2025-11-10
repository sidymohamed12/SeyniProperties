from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class BaseModel(models.Model):
    """Modèle de base avec timestamps automatiques"""
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        """Override save pour permettre des hooks personnalisés"""
        super().save(*args, **kwargs)


class TimestampedModel(BaseModel):
    """Alias pour BaseModel pour compatibilité"""
    class Meta:
        abstract = True


class AuditModel(BaseModel):
    """Modèle avec audit trail (qui a créé/modifié)"""
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_created',
        verbose_name="Créé par"
    )
    
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_updated',
        verbose_name="Modifié par"
    )
    
    class Meta:
        abstract = True