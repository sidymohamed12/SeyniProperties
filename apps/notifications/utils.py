# apps/notifications/utils.py
# (Ajouter ces fonctions à la fin du fichier existant)

from .email_utils import (
    send_intervention_assigned_email,
    send_task_assigned_email,
    send_urgent_notification_email
)


def notify_intervention_assigned_with_email(intervention, assigned_to):
    """
    Notifie un technicien qu'une intervention lui a été assignée
    + Envoie un email
    """
    # Créer la notification dans l'app
    notification = Notification.objects.create(
        destinataire=assigned_to,
        type_notification='intervention_assigned',
        canal='app',
        message=f"Une intervention {intervention.get_priorite_display().lower()} vous a été assignée pour {intervention.property}.",
        statut='envoye'
    )
    
    # Vérifier si l'utilisateur accepte les emails
    try:
        config = assigned_to.notification_config
        if config.receive_email and config.interventions:
            # Envoyer l'email
            send_intervention_assigned_email(intervention, assigned_to)
    except:
        # Si pas de config, envoyer quand même
        send_intervention_assigned_email(intervention, assigned_to)
    
    return notification


def notify_task_assigned_with_email(task, assigned_to):
    """
    Notifie un technicien qu'une tâche lui a été assignée
    + Envoie un email
    """
    # Créer la notification dans l'app
    notification = Notification.objects.create(
        destinataire=assigned_to,
        type_notification='task_assigned',
        canal='app',
        message=f"La tâche '{task.titre}' vous a été assignée.",
        statut='envoye'
    )
    
    # Vérifier si l'utilisateur accepte les emails
    try:
        config = assigned_to.notification_config
        if config.receive_email and config.taches:
            # Envoyer l'email
            send_task_assigned_email(task, assigned_to)
    except:
        # Si pas de config, envoyer quand même
        send_task_assigned_email(task, assigned_to)
    
    return notification


def notify_technicians_with_email(
    titre,
    message,
    type_notification='intervention',
    link_url='',
    technician_ids=None,
    send_emails=True
):
    """
    Envoie une notification à tous les techniciens ou à une liste spécifique
    + Envoie des emails si activé
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Types d'utilisateurs techniciens
    technician_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
    
    if technician_ids:
        users = User.objects.filter(
            id__in=technician_ids,
            user_type__in=technician_types,
            is_active=True
        )
    else:
        users = User.objects.filter(
            user_type__in=technician_types,
            is_active=True
        )
    
    notifications = []
    for user in users:
        # Créer la notification dans l'app
        notif = Notification.objects.create(
            destinataire=user,
            type_notification=type_notification,
            canal='app',
            message=message,
            statut='envoye'
        )
        notifications.append(notif)
        
        # Envoyer email si activé
        if send_emails:
            try:
                config = user.notification_config
                if config.receive_email:
                    is_urgent = 'urgent' in titre.lower() or 'urgente' in message.lower()
                    if is_urgent:
                        send_urgent_notification_email(
                            recipient_email=user.email,
                            recipient_name=user.get_full_name(),
                            title=titre,
                            message=message,
                            link_url=link_url
                        )
            except:
                pass
    
    return notifications