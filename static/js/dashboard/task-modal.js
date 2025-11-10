// static/js/dashboard/task-modal.js

class TaskModal {
    constructor() {
        this.modal = null;
        this.form = null;
        this.isLoading = false;
        this.init();
    }

    init() {
        // Créer le modal si il n'existe pas
        this.createModal();
        this.bindEvents();
    }

    createModal() {
        const modalHTML = `
        <div id="taskModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full hidden z-50">
            <div class="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
                <div class="mt-3">
                    <!-- Header -->
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-semibold text-gray-900">
                            <i class="fas fa-tasks text-blue-500 mr-2"></i>
                            Nouvelle Tâche
                        </h3>
                        <button type="button" class="text-gray-400 hover:text-gray-600" onclick="closeTaskModal()">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>

                    <!-- Form -->
                    <form id="taskForm" class="space-y-4">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <!-- Titre -->
                            <div class="md:col-span-2">
                                <label for="task_titre" class="block text-sm font-medium text-gray-700 mb-1">
                                    Titre de la tâche <span class="text-red-500">*</span>
                                </label>
                                <input type="text" id="task_titre" name="titre" required 
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Ex: Nettoyage appartement A1">
                            </div>

                            <!-- Type de tâche -->
                            <div>
                                <label for="task_type" class="block text-sm font-medium text-gray-700 mb-1">
                                    Type de tâche <span class="text-red-500">*</span>
                                </label>
                                <select id="task_type" name="type_tache" required 
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                                    <option value="">Sélectionner...</option>
                                </select>
                            </div>

                            <!-- Priorité -->
                            <div>
                                <label for="task_priority" class="block text-sm font-medium text-gray-700 mb-1">
                                    Priorité
                                </label>
                                <select id="task_priority" name="priorite"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                                    <option value="normale">Normale</option>
                                    <option value="basse">Basse</option>
                                    <option value="haute">Haute</option>
                                    <option value="urgente">Urgente</option>
                                </select>
                            </div>

                            <!-- Employé assigné -->
                            <div>
                                <label for="task_employee" class="block text-sm font-medium text-gray-700 mb-1">
                                    Assigné à <span class="text-red-500">*</span>
                                </label>
                                <select id="task_employee" name="assigne_a_id" required
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                                    <option value="">Sélectionner un employé...</option>
                                </select>
                                <div id="employee_availability" class="mt-1 text-xs"></div>
                            </div>

                            <!-- Bien concerné -->
                            <div>
                                <label for="task_property" class="block text-sm font-medium text-gray-700 mb-1">
                                    Bien concerné
                                </label>
                                <select id="task_property" name="bien_id"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                                    <option value="">Tâche générale</option>
                                </select>
                            </div>

                            <!-- Date prévue -->
                            <div>
                                <label for="task_date" class="block text-sm font-medium text-gray-700 mb-1">
                                    Date prévue <span class="text-red-500">*</span>
                                </label>
                                <input type="datetime-local" id="task_date" name="date_prevue" required
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                            </div>

                            <!-- Durée estimée -->
                            <div>
                                <label for="task_duration" class="block text-sm font-medium text-gray-700 mb-1">
                                    Durée estimée (minutes)
                                </label>
                                <input type="number" id="task_duration" name="duree_estimee" min="15" step="15"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="60">
                            </div>

                            <!-- Description -->
                            <div class="md:col-span-2">
                                <label for="task_description" class="block text-sm font-medium text-gray-700 mb-1">
                                    Description
                                </label>
                                <textarea id="task_description" name="description" rows="3"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Détails de la tâche à effectuer..."></textarea>
                            </div>

                            <!-- Récurrence -->
                            <div class="md:col-span-2">
                                <div class="flex items-center space-x-4">
                                    <label class="flex items-center">
                                        <input type="checkbox" id="task_recurrent" name="is_recurrente" 
                                            class="mr-2 text-blue-600 border-gray-300 rounded focus:ring-blue-500">
                                        <span class="text-sm text-gray-700">Tâche récurrente</span>
                                    </label>
                                </div>
                                
                                <div id="recurrence_options" class="mt-3 p-3 bg-gray-50 rounded-md hidden">
                                    <div class="grid grid-cols-2 gap-3">
                                        <div>
                                            <label class="block text-sm font-medium text-gray-700 mb-1">Type de récurrence</label>
                                            <select name="recurrence_type" 
                                                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                                                <option value="quotidien">Quotidien</option>
                                                <option value="hebdomadaire">Hebdomadaire</option>
                                                <option value="mensuel">Mensuel</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label class="block text-sm font-medium text-gray-700 mb-1">Fin de récurrence</label>
                                            <input type="date" name="recurrence_fin"
                                                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Buttons -->
                        <div class="flex justify-end space-x-3 pt-4 border-t">
                            <button type="button" onclick="closeTaskModal()" 
                                class="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors">
                                Annuler
                            </button>
                            <button type="submit" id="submit_task_btn"
                                class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                                <span class="submit-text">Créer la tâche</span>
                                <span class="loading-text hidden">
                                    <i class="fas fa-spinner fa-spin mr-2"></i>Création...
                                </span>
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>`;

        // Ajouter le modal au DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('taskModal');
        this.form = document.getElementById('taskForm');
    }

    bindEvents() {
        // Submit du formulaire
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitTask();
        });

        // Gestion de la récurrence
        document.getElementById('task_recurrent').addEventListener('change', (e) => {
            const recurrenceOptions = document.getElementById('recurrence_options');
            if (e.target.checked) {
                recurrenceOptions.classList.remove('hidden');
            } else {
                recurrenceOptions.classList.add('hidden');
            }
        });

        // Vérification de disponibilité employé
        document.getElementById('task_employee').addEventListener('change', (e) => {
            if (e.target.value) {
                this.checkEmployeeAvailability(e.target.value);
            }
        });

        // Mise à jour disponibilité quand date change
        document.getElementById('task_date').addEventListener('change', (e) => {
            const employeeId = document.getElementById('task_employee').value;
            if (employeeId && e.target.value) {
                this.checkEmployeeAvailability(employeeId, e.target.value.split('T')[0]);
            }
        });

        // Fermer modal avec Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.modal.classList.contains('hidden')) {
                this.close();
            }
        });

        // Fermer modal en cliquant à l'extérieur
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
    }

    async open() {
        try {
            // Charger les données du formulaire
            await this.loadFormData();
            
            // Définir la date par défaut (demain à 9h)
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            tomorrow.setHours(9, 0, 0, 0);
            document.getElementById('task_date').value = tomorrow.toISOString().slice(0, 16);
            
            // Afficher le modal
            this.modal.classList.remove('hidden');
            document.getElementById('task_titre').focus();
            
        } catch (error) {
            console.error('Erreur lors de l\'ouverture du modal:', error);
            showNotification('Erreur lors du chargement du formulaire', 'error');
        }
    }

    close() {
        this.modal.classList.add('hidden');
        this.form.reset();
        document.getElementById('recurrence_options').classList.add('hidden');
        document.getElementById('employee_availability').innerHTML = '';
        this.isLoading = false;
        this.updateSubmitButton();
    }

    async loadFormData() {
        try {
            const response = await fetch('/dashboard/nouvelle-tache/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                }
            });

            if (!response.ok) {
                throw new Error('Erreur lors du chargement des données');
            }

            const data = await response.json();

            // Remplir les employés
            const employeeSelect = document.getElementById('task_employee');
            employeeSelect.innerHTML = '<option value="">Sélectionner un employé...</option>';
            data.employees.forEach(emp => {
                const option = document.createElement('option');
                option.value = emp.id;
                option.textContent = `${emp.name} (${emp.type})`;
                employeeSelect.appendChild(option);
            });

            // Remplir les biens
            const propertySelect = document.getElementById('task_property');
            propertySelect.innerHTML = '<option value="">Tâche générale</option>';
            data.properties.forEach(prop => {
                const option = document.createElement('option');
                option.value = prop.id;
                option.textContent = prop.name;
                propertySelect.appendChild(option);
            });

            // Remplir les types de tâche
            const typeSelect = document.getElementById('task_type');
            typeSelect.innerHTML = '<option value="">Sélectionner...</option>';
            data.task_types.forEach(type => {
                const option = document.createElement('option');
                option.value = type[0];
                option.textContent = type[1];
                typeSelect.appendChild(option);
            });

        } catch (error) {
            console.error('Erreur loadFormData:', error);
            throw error;
        }
    }

    async checkEmployeeAvailability(employeeId, date = null) {
        try {
            const selectedDate = date || document.getElementById('task_date').value.split('T')[0];
            const url = `/dashboard/employee-availability/${employeeId}/?date=${selectedDate}`;
            
            const response = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.displayAvailability(data);
            }
        } catch (error) {
            console.error('Erreur vérification disponibilité:', error);
        }
    }

    displayAvailability(data) {
        const container = document.getElementById('employee_availability');
        
        if (data.success) {
            let statusClass = 'text-green-600';
            let statusText = 'Disponible';
            let icon = 'fas fa-check-circle';

            if (!data.is_available) {
                statusClass = 'text-red-600';
                statusText = 'Indisponible';
                icon = 'fas fa-times-circle';
            } else if (data.workload_status === 'heavy') {
                statusClass = 'text-orange-600';
                statusText = 'Charge élevée';
                icon = 'fas fa-exclamation-triangle';
            }

            container.innerHTML = `
                <div class="flex items-center ${statusClass}">
                    <i class="${icon} mr-1"></i>
                    <span>${statusText} (${data.active_tasks_count} tâches actives)</span>
                </div>
                ${data.tasks_on_date.length > 0 ? `
                    <div class="mt-1 text-xs text-gray-500">
                        ${data.tasks_on_date.length} tâche(s) prévue(s) ce jour
                    </div>
                ` : ''}
            `;
        }
    }

    async submitTask() {
        if (this.isLoading) return;

        this.isLoading = true;
        this.updateSubmitButton();

        try {
            const formData = new FormData(this.form);
            
            const response = await fetch('/dashboard/nouvelle-tache/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                }
            });

            const data = await response.json();

            if (data.success) {
                showNotification(data.message, 'success');
                this.close();
                
                // Actions de suivi
                if (data.follow_up_actions && data.follow_up_actions.length > 0) {
                    this.showFollowUpActions(data.follow_up_actions);
                }
                
                // Recharger les statistiques si on est sur la page d'enregistrements
                if (typeof updateDashboardStats === 'function') {
                    updateDashboardStats();
                }
                
            } else {
                showNotification(data.error || 'Erreur lors de la création de la tâche', 'error');
            }

        } catch (error) {
            console.error('Erreur submit:', error);
            showNotification('Erreur de connexion', 'error');
        } finally {
            this.isLoading = false;
            this.updateSubmitButton();
        }
    }

    updateSubmitButton() {
        const btn = document.getElementById('submit_task_btn');
        const submitText = btn.querySelector('.submit-text');
        const loadingText = btn.querySelector('.loading-text');

        if (this.isLoading) {
            btn.disabled = true;
            btn.classList.add('opacity-50', 'cursor-not-allowed');
            submitText.classList.add('hidden');
            loadingText.classList.remove('hidden');
        } else {
            btn.disabled = false;
            btn.classList.remove('opacity-50', 'cursor-not-allowed');
            submitText.classList.remove('hidden');
            loadingText.classList.add('hidden');
        }
    }

    showFollowUpActions(actions) {
        const actionsHTML = actions.map(action => `
            <button type="button" 
                class="inline-flex items-center px-3 py-2 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors mr-2 mb-2"
                onclick="${action.onclick || `window.location.href='${action.url}'`}">
                <i class="${action.icon} mr-2"></i>
                ${action.label}
            </button>
        `).join('');

        showNotification(`
            <div class="mb-3">Tâche créée avec succès !</div>
            <div class="space-y-2">
                <div class="text-sm font-medium">Actions suggérées :</div>
                <div>${actionsHTML}</div>
            </div>
        `, 'success', 8000);
    }
}

// Fonctions globales
let taskModal = null;

function openQuickTaskModal() {
    if (!taskModal) {
        taskModal = new TaskModal();
    }
    taskModal.open();
}

function closeTaskModal() {
    if (taskModal) {
        taskModal.close();
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    // Créer l'instance du modal
    taskModal = new TaskModal();
    
    // Ajouter les boutons d'ouverture du modal
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-action="open-task-modal"]') || 
            e.target.closest('[data-action="open-task-modal"]')) {
            e.preventDefault();
            openQuickTaskModal();
        }
    });
});

// Fonction utilitaire pour afficher les notifications
function showNotification(message, type = 'info', duration = 5000) {
    // Créer l'élément de notification
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 max-w-md p-4 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full`;
    
    // Styles selon le type
    const styles = {
        success: 'bg-green-100 border border-green-400 text-green-700',
        error: 'bg-red-100 border border-red-400 text-red-700',
        warning: 'bg-yellow-100 border border-yellow-400 text-yellow-700',
        info: 'bg-blue-100 border border-blue-400 text-blue-700'
    };
    
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle', 
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    notification.className += ` ${styles[type] || styles.info}`;
    
    notification.innerHTML = `
        <div class="flex items-start">
            <i class="${icons[type] || icons.info} mt-1 mr-3"></i>
            <div class="flex-1">
                ${message}
            </div>
            <button type="button" class="ml-3 text-current opacity-70 hover:opacity-100" onclick="this.closest('.fixed').remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    // Ajouter au DOM
    document.body.appendChild(notification);
    
    // Animation d'entrée
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    // Auto-suppression
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, duration);
}

// Fonction pour mettre à jour les stats du dashboard
function updateDashboardStats() {
    // Cette fonction sera appelée pour rafraîchir les statistiques
    fetch('/dashboard/stats-api/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
        }
    })
    .then(response => response.json())
    .then(data => {
        // Mettre à jour les éléments de stats sur la page
        const statsElements = {
            'pending_interventions': data.pending_interventions,
            'total_properties': data.total_properties,
            'occupied_properties': data.occupied_properties,
            'overdue_invoices': data.overdue_invoices
        };
        
        Object.entries(statsElements).forEach(([key, value]) => {
            const element = document.querySelector(`[data-stat="${key}"]`);
            if (element) {
                element.textContent = value;
            }
        });
    })
    .catch(error => {
        console.error('Erreur mise à jour stats:', error);
    });
}