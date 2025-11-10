// apps/dashboard/static/dashboard/js/notifications.js - SYSTÈME DE NOTIFICATIONS

/**
 * Système de notifications pour les formulaires
 */

// Configuration des notifications
const NOTIFICATION_CONFIG = {
    duration: 5000, // 5 secondes par défaut
    maxNotifications: 3,
    positions: {
        'top-right': 'top-4 right-4',
        'top-left': 'top-4 left-4',
        'bottom-right': 'bottom-4 right-4',
        'bottom-left': 'bottom-4 left-4'
    }
};

// Container pour les notifications
let notificationContainer = null;

/**
 * Initialise le container de notifications
 */
function initNotificationContainer() {
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'notification-container';
        notificationContainer.className = 'fixed top-4 right-4 z-50 space-y-3 max-w-md';
        document.body.appendChild(notificationContainer);
    }
    return notificationContainer;
}

/**
 * Affiche une notification
 * @param {string} type - Type de notification (success, error, warning, info)
 * @param {string} title - Titre de la notification
 * @param {string} message - Message de la notification
 * @param {object} options - Options supplémentaires
 */
function showNotification(type, title, message, options = {}) {
    const container = initNotificationContainer();
    
    // Limiter le nombre de notifications
    const existingNotifications = container.querySelectorAll('.notification');
    if (existingNotifications.length >= NOTIFICATION_CONFIG.maxNotifications) {
        existingNotifications[0].remove();
    }
    
    // Configuration du style selon le type
    const typeConfig = {
        success: {
            bgColor: 'bg-green-50',
            borderColor: 'border-green-200',
            textColor: 'text-green-800',
            iconColor: 'text-green-400',
            icon: 'fas fa-check-circle'
        },
        error: {
            bgColor: 'bg-red-50',
            borderColor: 'border-red-200',
            textColor: 'text-red-800',
            iconColor: 'text-red-400',
            icon: 'fas fa-exclamation-circle'
        },
        warning: {
            bgColor: 'bg-yellow-50',
            borderColor: 'border-yellow-200',
            textColor: 'text-yellow-800',
            iconColor: 'text-yellow-400',
            icon: 'fas fa-exclamation-triangle'
        },
        info: {
            bgColor: 'bg-blue-50',
            borderColor: 'border-blue-200',
            textColor: 'text-blue-800',
            iconColor: 'text-blue-400',
            icon: 'fas fa-info-circle'
        }
    };
    
    const config = typeConfig[type] || typeConfig.info;
    const duration = options.duration || NOTIFICATION_CONFIG.duration;
    const isSticky = options.sticky || false;
    
    // Créer l'élément notification
    const notification = document.createElement('div');
    notification.className = `notification ${config.bgColor} ${config.borderColor} ${config.textColor} border rounded-lg p-4 shadow-lg transform transition-all duration-300 ease-in-out translate-x-full opacity-0`;
    
    notification.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <i class="${config.icon} ${config.iconColor} text-lg"></i>
            </div>
            <div class="ml-3 flex-1">
                <h4 class="text-sm font-semibold">${title}</h4>
                <p class="text-sm mt-1">${message}</p>
            </div>
            <div class="ml-4 flex-shrink-0">
                <button class="notification-close inline-flex ${config.textColor} hover:${config.textColor.replace('800', '600')} focus:outline-none">
                    <i class="fas fa-times text-sm"></i>
                </button>
            </div>
        </div>
        ${!isSticky ? `<div class="notification-progress mt-2 h-1 bg-gray-200 rounded-full overflow-hidden">
            <div class="notification-progress-bar h-full bg-current opacity-50 transition-all ease-linear" style="width: 100%; transition-duration: ${duration}ms;"></div>
        </div>` : ''}
    `;
    
    // Ajouter au container
    container.appendChild(notification);
    
    // Animation d'entrée
    setTimeout(() => {
        notification.classList.remove('translate-x-full', 'opacity-0');
    }, 10);
    
    // Événement de fermeture
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        removeNotification(notification);
    });
    
    // Auto-suppression si pas sticky
    if (!isSticky) {
        const progressBar = notification.querySelector('.notification-progress-bar');
        if (progressBar) {
            setTimeout(() => {
                progressBar.style.width = '0%';
            }, 100);
        }
        
        setTimeout(() => {
            removeNotification(notification);
        }, duration);
    }
    
    return notification;
}

/**
 * Supprime une notification avec animation
 * @param {HTMLElement} notification - L'élément notification à supprimer
 */
function removeNotification(notification) {
    if (!notification || !notification.parentNode) return;
    
    notification.classList.add('translate-x-full', 'opacity-0');
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 300);
}

/**
 * Supprime toutes les notifications
 */
function clearAllNotifications() {
    if (notificationContainer) {
        const notifications = notificationContainer.querySelectorAll('.notification');
        notifications.forEach(notification => {
            removeNotification(notification);
        });
    }
}

/**
 * Fonctions de convenance pour les différents types
 */
function showSuccessNotification(title, message, options = {}) {
    return showNotification('success', title, message, options);
}

function showErrorNotification(title, message, options = {}) {
    return showNotification('error', title, message, options);
}

function showWarningNotification(title, message, options = {}) {
    return showNotification('warning', title, message, options);
}

function showInfoNotification(title, message, options = {}) {
    return showNotification('info', title, message, options);
}

/**
 * Affiche une notification de création d'entité avec détails
 * @param {string} entityType - Type d'entité (tâche, intervention, etc.)
 * @param {string} entityName - Nom de l'entité créée
 * @param {object} details - Détails supplémentaires
 */
function showEntityCreatedNotification(entityType, entityName, details = {}) {
    const typeConfig = {
        'tâche': {
            icon: 'fas fa-tasks',
            color: 'indigo'
        },
        'intervention': {
            icon: 'fas fa-tools',
            color: 'red'
        },
        'appartement': {
            icon: 'fas fa-building',
            color: 'blue'
        },
        'résidence': {
            icon: 'fas fa-home',
            color: 'green'
        },
        'locataire': {
            icon: 'fas fa-user',
            color: 'purple'
        },
        'employé': {
            icon: 'fas fa-user-tie',
            color: 'teal'
        }
    };
    
    const config = typeConfig[entityType.toLowerCase()] || typeConfig['tâche'];
    
    let message = `${entityType.charAt(0).toUpperCase() + entityType.slice(1)} "${entityName}" créée avec succès.`;
    
    if (details.assignedTo) {
        message += ` Assignée à ${details.assignedTo}.`;
    }
    
    if (details.dueDate) {
        message += ` Échéance: ${details.dueDate}.`;
    }
    
    return showNotification('success', `${entityType.charAt(0).toUpperCase() + entityType.slice(1)} créée`, message);
}

/**
 * Affiche une notification d'erreur de validation avec détails des champs
 * @param {object} fieldErrors - Objet contenant les erreurs par champ
 * @param {string} generalMessage - Message général d'erreur
 */
function showValidationErrorNotification(fieldErrors = {}, generalMessage = 'Erreurs de validation') {
    const errorCount = Object.keys(fieldErrors).length;
    let message = generalMessage;
    
    if (errorCount > 0) {
        message += ` (${errorCount} erreur${errorCount > 1 ? 's' : ''} détectée${errorCount > 1 ? 's' : ''})`;
    }
    
    return showNotification('error', 'Formulaire invalide', message, { duration: 7000 });
}

/**
 * Affiche une notification de chargement
 * @param {string} message - Message de chargement
 * @returns {HTMLElement} - L'élément notification pour pouvoir le supprimer plus tard
 */
function showLoadingNotification(message = 'Chargement...') {
    const notification = document.createElement('div');
    notification.className = 'notification bg-blue-50 border border-blue-200 text-blue-800 rounded-lg p-4 shadow-lg';
    notification.innerHTML = `
        <div class="flex items-center">
            <div class="flex-shrink-0">
                <i class="fas fa-spinner fa-spin text-blue-400 text-lg"></i>
            </div>
            <div class="ml-3">
                <p class="text-sm font-medium">${message}</p>
            </div>
        </div>
    `;
    
    const container = initNotificationContainer();
    container.appendChild(notification);
    
    return notification;
}

/**
 * Met à jour une notification de chargement en notification de succès ou d'erreur
 * @param {HTMLElement} loadingNotification - La notification de chargement à mettre à jour
 * @param {string} type - Type final (success ou error)
 * @param {string} title - Titre final
 * @param {string} message - Message final
 */
function updateLoadingNotification(loadingNotification, type, title, message) {
    if (!loadingNotification || !loadingNotification.parentNode) return;
    
    // Supprimer la notification de chargement
    removeNotification(loadingNotification);
    
    // Afficher la notification finale après un court délai
    setTimeout(() => {
        showNotification(type, title, message);
    }, 100);
}

// Exposer les fonctions globalement
window.showNotification = showNotification;
window.showSuccessNotification = showSuccessNotification;
window.showErrorNotification = showErrorNotification;
window.showWarningNotification = showWarningNotification;
window.showInfoNotification = showInfoNotification;
window.showEntityCreatedNotification = showEntityCreatedNotification;
window.showValidationErrorNotification = showValidationErrorNotification;
window.showLoadingNotification = showLoadingNotification;
window.updateLoadingNotification = updateLoadingNotification;
window.clearAllNotifications = clearAllNotifications;

// Auto-initialisation
document.addEventListener('DOMContentLoaded', function() {
    initNotificationContainer();
    console.log('Système de notifications initialisé');
});