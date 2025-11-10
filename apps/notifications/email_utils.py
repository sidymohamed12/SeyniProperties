# apps/notifications/email_utils.py

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def send_notification_email(
    recipient_email,
    subject,
    message,
    template_name=None,
    context=None,
    from_email=None
):
    """
    Envoie un email de notification
    
    Args:
        recipient_email: Email du destinataire
        subject: Sujet de l'email
        message: Message texte brut
        template_name: Template HTML optionnel
        context: Contexte pour le template
        from_email: Email expéditeur (défaut: settings.DEFAULT_FROM_EMAIL)
    
    Returns:
        bool: True si envoyé avec succès
    """
    if not from_email:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@imany.sn')
    
    try:
        if template_name and context:
            # Email HTML avec template
            html_content = render_to_string(template_name, context)
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[recipient_email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
        else:
            # Email texte simple
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
        
        return True
    
    except Exception as e:
        print(f"Erreur envoi email: {str(e)}")
        return False


def send_intervention_assigned_email(intervention, assigned_to):
    """
    Envoie un email quand une intervention est assignée à un technicien
    """
    subject = f"Nouvelle intervention assignée - {intervention.get_priorite_display()}"
    
    context = {
        'technicien': assigned_to.get_full_name(),
        'intervention': intervention,
        'priority_color': {
            'urgente': '#dc2626',
            'haute': '#f59e0b',
            'normale': '#3b82f6',
            'basse': '#6b7280'
        }.get(intervention.priorite, '#6b7280')
    }
    
    return send_notification_email(
        recipient_email=assigned_to.email,
        subject=subject,
        message=f"Bonjour {assigned_to.get_full_name()},\n\nUne intervention {intervention.get_priorite_display().lower()} vous a été assignée.\n\nDétails:\n- Bien: {intervention.property}\n- Description: {intervention.description}\n- Priorité: {intervention.get_priorite_display()}\n\nConnectez-vous à la plateforme pour plus de détails.",
        template_name='notifications/emails/intervention_assigned.html',
        context=context
    )


def send_task_assigned_email(task, assigned_to):
    """
    Envoie un email quand une tâche est assignée
    """
    subject = f"Nouvelle tâche assignée - {task.titre}"
    
    context = {
        'technicien': assigned_to.get_full_name(),
        'task': task,
    }
    
    return send_notification_email(
        recipient_email=assigned_to.email,
        subject=subject,
        message=f"Bonjour {assigned_to.get_full_name()},\n\nLa tâche '{task.titre}' vous a été assignée.\n\nÉchéance: {task.date_limite.strftime('%d/%m/%Y') if task.date_limite else 'Non définie'}\n\nConnectez-vous à la plateforme pour plus de détails.",
        template_name='notifications/emails/task_assigned.html',
        context=context
    )


def send_urgent_notification_email(recipient_email, recipient_name, title, message, link_url=None):
    """
    Envoie un email pour une notification urgente
    """
    subject = f"🚨 URGENT - {title}"
    
    context = {
        'recipient_name': recipient_name,
        'title': title,
        'message': message,
        'link_url': link_url
    }
    
    return send_notification_email(
        recipient_email=recipient_email,
        subject=subject,
        message=f"URGENT\n\n{title}\n\n{message}",
        template_name='notifications/emails/urgent_notification.html',
        context=context
    )