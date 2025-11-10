// apps/dashboard/static/dashboard/js/tasks-interventions-forms.js - FORMULAIRES CORRIGÉS

/**
 * Gestionnaire de formulaires pour les tâches et interventions
 * Basé sur le code fonctionnel d'enregistrements.html
 */

// Configuration des APIs
const API_ENDPOINTS = {
    employees: '/dashboard/api/technicians/',
    appartements: '/dashboard/api/appartements-all/',
    createTask: '/dashboard/nouveau/tache/',
    createIntervention: '/dashboard/nouveau/intervention/'
};

/**
 * Charge les employés disponibles pour assignation
 */
function loadEmployees(selectElement) {
    if (!selectElement) return;
    
    selectElement.innerHTML = '<option value="">Chargement des employés...</option>';
    
    fetch(API_ENDPOINTS.employees, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Données employés reçues:', data);
        
        if (data.success && data.employees) {
            selectElement.innerHTML = '<option value="">Sélectionner un employé...</option>';
            
            data.employees.forEach(employee => {
                const option = document.createElement('option');
                option.value = employee.id;
                option.textContent = `${employee.name} - ${employee.role}`;
                
                // Ajouter des informations sur la charge de travail si disponibles
                if (employee.active_tasks) {
                    option.textContent += ` (${employee.active_tasks} tâches actives)`;
                }
                
                selectElement.appendChild(option);
            });
            
            console.log(`${data.employees.length} employés chargés`);
        } else {
            selectElement.innerHTML = '<option value="">Aucun employé disponible</option>';
        }
    })
    .catch(error => {
        console.error('Erreur lors du chargement des employés:', error);
        selectElement.innerHTML = '<option value="">Erreur de chargement</option>';
    });
}

/**
 * Charge tous les appartements disponibles
 */
function loadAllAppartements(selectElement) {
    if (!selectElement) return;
    
    selectElement.innerHTML = '<option value="">Chargement des appartements...</option>';
    
    fetch(API_ENDPOINTS.appartements, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Données appartements reçues:', data);
        
        if (data.success && data.appartements) {
            selectElement.innerHTML = '<option value="">Sélectionner un appartement...</option>';
            
            data.appartements.forEach(appartement => {
                const option = document.createElement('option');
                option.value = appartement.id;
                option.textContent = `${appartement.nom} - ${appartement.residence_nom}`;
                
                // Ajouter des informations supplémentaires
                if (appartement.type_bien) {
                    option.textContent += ` (${appartement.type_bien})`;
                }
                
                selectElement.appendChild(option);
            });
            
            console.log(`${data.appartements.length} appartements chargés`);
        } else {
            selectElement.innerHTML = '<option value="">Aucun appartement trouvé</option>';
        }
    })
    .catch(error => {
        console.error('Erreur lors du chargement des appartements:', error);
        selectElement.innerHTML = '<option value="">Erreur de chargement</option>';
    });
}

/**
 * Crée le formulaire de tâche modal
 */
function createTaskForm() {
    return `
        <form id="taskModalForm" class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <!-- Titre -->
                <div class="md:col-span-2">
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Titre de la tâche <span class="text-red-500">*</span>
                    </label>
                    <input type="text" 
                           name="titre"
                           class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                           placeholder="Ex: Ménage appartement A12"
                           required>
                </div>
                
                <!-- Type de tâche -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Type de tâche <span class="text-red-500">*</span>
                    </label>
                    <select name="type_tache" 
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required>
                        <option value="">Sélectionner un type...</option>
                        <option value="menage">Ménage</option>
                        <option value="visite">Visite de contrôle</option>
                        <option value="maintenance_preventive">Maintenance préventive</option>
                        <option value="etat_lieux">État des lieux</option>
                        <option value="reparation">Réparation</option>
                        <option value="livraison">Livraison</option>
                        <option value="rendez_vous">Rendez-vous</option>
                        <option value="administrative">Tâche administrative</option>
                        <option value="autre">Autre</option>
                    </select>
                </div>
                
                <!-- Priorité -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Priorité <span class="text-red-500">*</span>
                    </label>
                    <select name="priorite" 
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required>
                        <option value="">Sélectionner une priorité...</option>
                        <option value="basse">Basse</option>
                        <option value="normale" selected>Normale</option>
                        <option value="haute">Haute</option>
                        <option value="urgente">Urgente</option>
                    </select>
                </div>
                
                <!-- Appartement -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Appartement concerné
                    </label>
                    <select name="appartement_id" 
                            id="task-appartement-select"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <option value="">Sélectionner un appartement...</option>
                    </select>
                </div>
                
                <!-- Employé assigné -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Employé assigné <span class="text-red-500">*</span>
                    </label>
                    <select name="assigne_a" 
                            id="task-employee-select"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required>
                        <option value="">Sélectionner un employé...</option>
                    </select>
                </div>
                
                <!-- Date prévue -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Date et heure prévues <span class="text-red-500">*</span>
                    </label>
                    <input type="datetime-local" 
                           name="date_prevue"
                           class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                           required>
                </div>
                
                <!-- Durée estimée -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Durée estimée (minutes)
                    </label>
                    <input type="number" 
                           name="duree_estimee"
                           min="15"
                           step="15"
                           class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                           placeholder="120">
                </div>
                
                <!-- Description -->
                <div class="md:col-span-2">
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Description
                    </label>
                    <textarea name="description" 
                              rows="3"
                              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                              placeholder="Description détaillée de la tâche à effectuer..."></textarea>
                </div>
                
                <!-- Récurrence -->
                <div class="md:col-span-2">
                    <label class="flex items-center">
                        <input type="checkbox" name="is_recurrente" class="mr-2">
                        <span class="text-sm text-gray-700">Tâche récurrente</span>
                    </label>
                    
                    <div id="recurrence-options" class="mt-2 hidden grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-xs text-gray-600 mb-1">Type de récurrence</label>
                            <select name="recurrence_type" class="w-full px-2 py-1 text-sm border border-gray-300 rounded">
                                <option value="hebdomadaire">Hebdomadaire</option>
                                <option value="mensuelle">Mensuelle</option>
                                <option value="trimestrielle">Trimestrielle</option>
                                <option value="annuelle">Annuelle</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs text-gray-600 mb-1">Fin de récurrence</label>
                            <input type="date" name="recurrence_fin" class="w-full px-2 py-1 text-sm border border-gray-300 rounded">
                        </div>
                    </div>
                </div>
            </div>
        </form>
    `;
}

/**
 * Crée le formulaire d'intervention modal
 */
function createInterventionForm() {
    return `
        <form id="interventionModalForm" class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <!-- Titre -->
                <div class="md:col-span-2">
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Titre de l'intervention <span class="text-red-500">*</span>
                    </label>
                    <input type="text" 
                           name="titre"
                           class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                           placeholder="Ex: Réparation fuite d'eau cuisine"
                           required>
                </div>
                
                <!-- Type d'intervention -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Type d'intervention <span class="text-red-500">*</span>
                    </label>
                    <select name="type_intervention" 
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required>
                        <option value="">Sélectionner un type...</option>
                        <option value="plomberie">Plomberie</option>
                        <option value="electricite">Électricité</option>
                        <option value="climatisation">Climatisation</option>
                        <option value="peinture">Peinture</option>
                        <option value="carrelage">Carrelage</option>
                        <option value="menuiserie">Menuiserie</option>
                        <option value="serrurerie">Serrurerie</option>
                        <option value="jardinage">Jardinage</option>
                        <option value="nettoyage">Nettoyage spécialisé</option>
                        <option value="autre">Autre</option>
                    </select>
                </div>
                
                <!-- Priorité -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Priorité <span class="text-red-500">*</span>
                    </label>
                    <select name="priorite" 
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required>
                        <option value="">Sélectionner une priorité...</option>
                        <option value="basse">Basse</option>
                        <option value="normale" selected>Normale</option>
                        <option value="haute">Haute</option>
                        <option value="urgente">Urgente</option>
                    </select>
                </div>
                
                <!-- Appartement -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Appartement concerné <span class="text-red-500">*</span>
                    </label>
                    <select name="appartement_id" 
                            id="intervention-appartement-select"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required>
                        <option value="">Sélectionner un appartement...</option>
                    </select>
                </div>
                
                <!-- Technicien assigné -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Technicien assigné
                    </label>
                    <select name="technicien" 
                            id="intervention-employee-select"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <option value="">Assigner plus tard...</option>
                    </select>
                </div>
                
                <!-- Date prévue -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Date prévue
                    </label>
                    <input type="date" 
                           name="date_prevue_intervention"
                           class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                
                <!-- Coût estimé -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Coût estimé (FCFA)
                    </label>
                    <input type="number" 
                           name="cout_estime"
                           min="0"
                           step="100"
                           class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                           placeholder="0">
                </div>
                
                <!-- Description -->
                <div class="md:col-span-2">
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Description du problème <span class="text-red-500">*</span>
                    </label>
                    <textarea name="description" 
                              rows="4"
                              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                              placeholder="Décrivez le problème en détail..."
                              required></textarea>
                </div>
            </div>
        </form>
    `;
}

/**
 * Ouvre le modal de création de tâche
 */
function openTaskModal() {
    const modal = document.getElementById('universal-modal');
    if (!modal) {
        console.error('Modal universel non trouvé');
        return;
    }
    
    // Configurer le modal
    document.getElementById('modal-title').textContent = 'Nouvelle Tâche';
    document.getElementById('modal-content').innerHTML = createTaskForm();
    
    // Changer la couleur du bouton de soumission
    const submitBtn = document.getElementById('modal-submit-btn');
    submitBtn.className = 'bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-md font-medium';
    submitBtn.textContent = 'Créer la tâche';
    
    // Charger les données
    const appartementSelect = document.getElementById('task-appartement-select');
    const employeeSelect = document.getElementById('task-employee-select');
    
    if (appartementSelect) loadAllAppartements(appartementSelect);
    if (employeeSelect) loadEmployees(employeeSelect);
    
    // Gestion de la récurrence
    const recurrenceCheckbox = document.querySelector('input[name="is_recurrente"]');
    const recurrenceOptions = document.getElementById('recurrence-options');
    
    if (recurrenceCheckbox && recurrenceOptions) {
        recurrenceCheckbox.addEventListener('change', function() {
            if (this.checked) {
                recurrenceOptions.classList.remove('hidden');
            } else {
                recurrenceOptions.classList.add('hidden');
            }
        });
    }
    
    // Définir la date par défaut (demain 9h)
    const dateInput = document.querySelector('input[name="date_prevue"]');
    if (dateInput) {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(9, 0, 0, 0);
        dateInput.value = tomorrow.toISOString().slice(0, 16);
    }
    
    // Attacher l'événement de soumission
    attachFormSubmission('task');
    
    // Afficher le modal
    modal.classList.remove('hidden');
    setTimeout(() => {
        modal.querySelector('.modal-content').classList.remove('translate-y-full', 'opacity-0');
    }, 10);
}

/**
 * Ouvre le modal de création d'intervention
 */
function openInterventionModal() {
    const modal = document.getElementById('universal-modal');
    if (!modal) {
        console.error('Modal universel non trouvé');
        return;
    }
    
    // Configurer le modal
    document.getElementById('modal-title').textContent = 'Nouvelle Intervention';
    document.getElementById('modal-content').innerHTML = createInterventionForm();
    
    // Changer la couleur du bouton de soumission
    const submitBtn = document.getElementById('modal-submit-btn');
    submitBtn.className = 'bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-md font-medium';
    submitBtn.textContent = 'Créer l\'intervention';
    
    // Charger les données
    const appartementSelect = document.getElementById('intervention-appartement-select');
    const employeeSelect = document.getElementById('intervention-employee-select');
    
    if (appartementSelect) loadAllAppartements(appartementSelect);
    if (employeeSelect) loadEmployees(employeeSelect);
    
    // Définir la date par défaut (demain)
    const dateInput = document.querySelector('input[name="date_prevue_intervention"]');
    if (dateInput) {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        dateInput.value = tomorrow.toISOString().slice(0, 10);
    }
    
    // Attacher l'événement de soumission
    attachFormSubmission('intervention');
    
    // Afficher le modal
    modal.classList.remove('hidden');
    setTimeout(() => {
        modal.querySelector('.modal-content').classList.remove('translate-y-full', 'opacity-0');
    }, 10);
}

/**
 * Attache l'événement de soumission au formulaire
 */
function attachFormSubmission(type) {
    const form = document.getElementById(type + 'ModalForm');
    const submitBtn = document.getElementById('modal-submit-btn');
    
    if (!form || !submitBtn) return;
    
    // Supprimer les anciens listeners
    const newSubmitBtn = submitBtn.cloneNode(true);
    submitBtn.parentNode.replaceChild(newSubmitBtn, submitBtn);
    
    // Attacher le nouveau listener
    newSubmitBtn.addEventListener('click', function(e) {
        e.preventDefault();
        submitForm(type, form);
    });
    
    // Aussi attacher au formulaire directement
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        submitForm(type, this);
    });
}

/**
 * Soumet le formulaire
 */
function submitForm(type, form) {
    const formData = new FormData(form);
    const endpoint = type === 'task' ? API_ENDPOINTS.createTask : API_ENDPOINTS.createIntervention;
    
    // Ajouter le token CSRF
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                     document.querySelector('meta[name="csrf-token"]')?.content;
    if (csrfToken) {
        formData.append('csrfmiddlewaretoken', csrfToken);
    }
    
    // Afficher le loader
    const submitBtn = document.getElementById('modal-submit-btn');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Création...';
    
    fetch(endpoint, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Succès
            showNotification('success', 'Création réussie', data.message || `${type === 'task' ? 'Tâche' : 'Intervention'} créée avec succès`);
            closeModal();
            
            // Recharger la page ou actualiser les données
            setTimeout(() => {
                location.reload();
            }, 1500);
        } else {
            // Erreur
            console.error('Erreur de création:', data);
            showNotification('error', 'Erreur de création', data.error || 'Une erreur s\'est produite');
            
            // Afficher les erreurs de champs si disponibles
            if (data.field_errors) {
                Object.keys(data.field_errors).forEach(field => {
                    const fieldElement = form.querySelector(`[name="${field}"]`);
                    if (fieldElement) {
                        showFieldError(fieldElement, data.field_errors[field]);
                    }
                });
            }
        }
    })
    .catch(error => {
        console.error('Erreur de soumission:', error);
        showNotification('error', 'Erreur de communication', 'Impossible de communiquer avec le serveur');
    })
    .finally(() => {
        // Restaurer le bouton
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    });
}

/**
 * Ferme le modal
 */
function closeModal() {
    const modal = document.getElementById('universal-modal');
    if (modal) {
        const content = modal.querySelector('.modal-content');
        content.classList.add('translate-y-full', 'opacity-0');
        setTimeout(() => {
            modal.classList.add('hidden');
        }, 300);
    }
}

/**
 * Affiche une notification
 */
function showNotification(type, title, message) {
    // Réutiliser le système de notifications existant
    if (typeof addNotification === 'function') {
        addNotification(type, title, message);
    } else {
        // Fallback simple
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                <strong>${title}:</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Insérer au début de la page
        const container = document.querySelector('.container') || document.body;
        container.insertAdjacentHTML('afterbegin', alertHtml);
        
        // Auto-suppression après 5 secondes
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) alert.remove();
        }, 5000);
    }
}

/**
 * Affiche une erreur de champ
 */
function showFieldError(field, message) {
    // Supprimer les anciennes erreurs
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    
    // Ajouter la bordure rouge
    field.classList.add('border-red-500');
    field.classList.remove('border-gray-300');
    
    // Créer le message d'erreur
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error text-red-500 text-xs mt-1';
    errorElement.textContent = message;
    
    // Insérer après le champ
    field.parentNode.insertBefore(errorElement, field.nextSibling);
    
    // Supprimer l'erreur quand l'utilisateur tape
    field.addEventListener('input', function() {
        this.classList.remove('border-red-500');
        this.classList.add('border-gray-300');
        const error = this.parentNode.querySelector('.field-error');
        if (error) error.remove();
    }, { once: true });
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Gestionnaire de formulaires tâches/interventions initialisé');
    
    // Exposer les fonctions globalement pour les boutons
    window.openTaskModal = openTaskModal;
    window.openInterventionModal = openInterventionModal;
    window.closeModal = closeModal;
});