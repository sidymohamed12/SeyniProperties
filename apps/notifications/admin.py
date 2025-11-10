from django.contrib import admin
from .models import Notification, MessageTemplate, NotificationConfig

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('destinataire', 'type_notification', 'canal', 'statut', 'date_programmee')
    list_filter = ('type_notification', 'canal', 'statut', 'date_envoi')
    search_fields = ('destinataire__username', 'sujet', 'message')

@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'type_notification', 'canal', 'is_active')
    list_filter = ('type_notification', 'canal', 'is_active')
    search_fields = ('code', 'nom')

@admin.register(NotificationConfig)
class NotificationConfigAdmin(admin.ModelAdmin):
    list_display = ('user', 'receive_sms', 'receive_whatsapp', 'receive_email', 'langue_preference')
    list_filter = ('receive_sms', 'receive_whatsapp', 'receive_email', 'langue_preference')