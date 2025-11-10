// static/js/forms_helpers.js - HELPERS POUR FORMULAIRES DYNAMIQUES
console.log('🚀 Chargement des helpers de formulaires...');

/**
 * ===============================================
 * GESTION DES APPARTEMENTS POUR LES FORMULAIRES
 * ===============================================
 */

/**
 * Charge tous les appartements disponibles
 */
async function loadAllAppartements(selectElement, selectedId = null) {
    if (!selectElement) {
        console.error('❌ Élément select non trouvé pour les appartements');
        return;
    }

    console.log('🏠 Chargement des appartements...');
    
    try {
        const response = await fetch('/dashboard/api/properties-all/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();
        
        if (data.success && data.appartements) {
            selectElement.innerHTML = '<option value="">-- Sélectionner un appartement --</option>';
            
            data.appartements.forEach(appartement => {
                const option = document.createElement('option');
                option.value = appartement.id;
                option.textContent = `${appartement.nom} - ${appartement.residence_nom}`;
                
                // Sélectionner l'option si c'est celle qui était déjà sélectionnée
                if (selectedId && selectedId.toString() === appartement.id.toString()) {
                    option.selected = true;
                }
                
                selectElement.appendChild(option);
            });
            
            console.log(`✅ ${data.appartements.length} appartements chargés`);
        } else {
            selectElement.innerHTML = '<option value="">Aucun appartement trouvé</option>';
            console.warn('⚠️ Aucun appartement trouvé dans la réponse');
        }
    } catch (error) {
        console.error('❌ Erreur lors du chargement des appartements:', error);
        selectElement.innerHTML = '<option value="">Erreur de chargement</option>';
    }
}

/**
 * ===============================================
 * GESTION DES EMPLOYÉS POUR LES FORMULAIRES
 * ===============================================
 */

/**
 * Charge tous les employés actifs
 */
async function loadAllEmployees(selectElement, userTypes = ['agent_terrain', 'technicien'], selectedId = null) {
    if (!selectElement) {
        console.error('❌ Élément select non trouvé pour les employés');
        return;
    }

    console.log('👥 Chargement des employés...', userTypes);
    
    try {
        const response = await fetch('/dashboard/api/employees/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                user_types: userTypes,
                active_only: true
            })
        });

        const data = await response.json();
        
        if (data.success && data.employees) {
            selectElement.innerHTML = '<option value="">-- Sélectionner un employé --</option>';
            
            data.employees.forEach(employee => {
                const option = document.createElement('option');
                option.value = employee.id;
                option.textContent = `${employee.first_name} ${employee.last_name} (${employee.user_type_display})`;
                
                // Sélectionner l'option si c'est celle qui était déjà sélectionnée
                if (selectedId && selectedId.toString() === employee.id.toString()) {
                    option.selected = true;
                }
                
                selectElement.appendChild(option);
            });
            
            console.log(`✅ ${data.employees.length} employés chargés`);
        } else {
            selectElement.innerHTML = '<option value="">Aucun employé trouvé</option>';
            console.warn('⚠️ Aucun employé trouvé dans la réponse');
        }
    } catch (error) {
        console.error('❌ Erreur lors du chargement des employés:', error);
        selectElement.innerHTML = '<option value="">Erreur de chargement</option>';
    }
}

/**
 * Charge uniquement les techniciens
 */
async function loadTechnicians(selectElement, selectedId = null) {
    return loadAllEmployees(selectElement, ['technicien'], selectedId);
}

/**
 * ===============================================
 * GESTION DES LOCATAIRES POUR LES FORMULAIRES
 * ===============================================
 */

/**
 * Charge tous les locataires/tenants
 */
async function loadAllTenants(selectElement, selectedId = null) {
    if (!selectElement) {
        console.error('❌ Élément select non trouvé pour les locataires');
        return;
    }

    console.log('🏠 Chargement des locataires...');
    
    try {
        const response = await fetch('/dashboard/api/tenants/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();
        
        if (data.success && data.tenants) {
            selectElement.innerHTML = '<option value="">-- Sélectionner un locataire (optionnel) --</option>';
            
            data.tenants.forEach(tenant => {
                const option = document.createElement('option');
                option.value = tenant.id;
                option.textContent = `${tenant.first_name} ${tenant.last_name}`;
                
                // Ajouter info de l'appartement si disponible
                if (tenant.current_apartment) {
                    option.textContent += ` - ${tenant.current_apartment}`;
                }
                
                // Sélectionner l'option si c'est celle qui était déjà sélectionnée
                if (selectedId && selectedId.toString() === tenant.id.toString()) {
                    option.selected = true;
                }
                
                selectElement.appendChild(option);
            });
            
            console.log(`✅ ${data.tenants.length} locataires chargés`);
        } else {
            selectElement.innerHTML = '<option value="">Aucun locataire trouvé</option>';
            console.warn('⚠️ Aucun locataire trouvé dans la réponse');
        }
    } catch (error) {
        console.error('❌ Erreur lors du chargement des locataires:', error);
        selectElement.innerHTML = '<option value="">Erreur de chargement</option>';
    }
}

/**
 * ===============================================
 * INITIALISATION DES FORMULAIRES
 * ===============================================
 */

/**
 * Initialise les formulaires de tâches
 */
function initTaskForms() {
    console.log('📋 Initialisation des formulaires de tâches...');
    
    // Formulaire principal de tâche
    const taskPropertySelect = document.getElementById('task-property-select');
    const taskEmployeeSelect = document.getElementById('task-employee-select');
    
    if (taskPropertySelect) {
        // Récupérer la valeur sélectionnée s'il y en a une (mode édition)
        const selectedPropertyId = taskPropertySelect.getAttribute('data-selected-id');
        loadAllAppartements(taskPropertySelect, selectedPropertyId);
    }
    
    if (taskEmployeeSelect) {
        // Récupérer la valeur sélectionnée s'il y en a une (mode édition)
        const selectedEmployeeId = taskEmployeeSelect.getAttribute('data-selected-id');
        loadAllEmployees(taskEmployeeSelect, ['agent_terrain', 'technicien'], selectedEmployeeId);
    }
    
    // Formulaires rapides dans les modales
    const quickTaskPropertySelect = document.querySelector('select[name="appartement_id"]');
    const quickTaskEmployeeSelect = document.querySelector('select[name="assigne_a"]');
    
    if (quickTaskPropertySelect) {
        loadAllAppartements(quickTaskPropertySelect);
    }
    
    if (quickTaskEmployeeSelect) {
        loadAllEmployees(quickTaskEmployeeSelect, ['agent_terrain', 'technicien']);
    }
}

/**
 * Initialise les formulaires d'interventions
 */
function initInterventionForms() {
    console.log('🔧 Initialisation des formulaires d\'interventions...');
    
    // Formulaire principal d'intervention
    const interventionPropertySelect = document.getElementById('intervention-property-select');
    const interventionTechnicianSelect = document.getElementById('intervention-technician-select');
    const interventionTenantSelect = document.getElementById('intervention-tenant-select');
    
    if (interventionPropertySelect) {
        const selectedPropertyId = interventionPropertySelect.getAttribute('data-selected-id');
        loadAllAppartements(interventionPropertySelect, selectedPropertyId);
    }
    
    if (interventionTechnicianSelect) {
        const selectedTechnicianId = interventionTechnicianSelect.getAttribute('data-selected-id');
        loadTechnicians(interventionTechnicianSelect, selectedTechnicianId);
    }
    
    if (interventionTenantSelect) {
        const selectedTenantId = interventionTenantSelect.getAttribute('data-selected-id');
        loadAllTenants(interventionTenantSelect, selectedTenantId);
    }
    
    // Formulaires rapides dans les modales
    const quickInterventionPropertySelect = document.querySelector('select[name="bien"]');
    const quickInterventionTechnicianSelect = document.querySelector('select[name="technicien"]');
    
    if (quickInterventionPropertySelect && quickInterventionPropertySelect.id === 'quick-intervention-property') {
        loadAllAppartements(quickInterventionPropertySelect);
    }
    
    if (quickInterventionTechnicianSelect && quickInterventionTechnicianSelect.id === 'quick-intervention-technician') {
        loadTechnicians(quickInterventionTechnicianSelect);
    }
}

/**
 * ===============================================
 * VALIDATION EN TEMPS RÉEL
 * ===============================================
 */

/**
 * Ajoute la validation en temps réel aux formulaires
 */
function setupFormValidation() {
    console.log('✅ Configuration de la validation des formulaires...');
    
    // Validation des champs requis
    const requiredFields = document.querySelectorAll('input[required], select[required], textarea[required]');
    
    requiredFields.forEach(field => {
        field.addEventListener('blur', function() {
            validateField(this);
        });
        
        field.addEventListener('change', function() {
            validateField(this);
        });
    });
    
    // Validation des formulaires à la soumission
    const forms = document.querySelectorAll('form[id$="Form"]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

/**
 * Valide un champ individuel
 */
function validateField(field) {
    const fieldContainer = field.closest('.form-group') || field.parentElement;
    const errorElement = fieldContainer.querySelector('.field-error');
    
    // Supprimer les erreurs précédentes
    if (errorElement) {
        errorElement.remove();
    }
    
    field.classList.remove('is-invalid', 'is-valid');
    
    // Validation selon le type de champ
    let isValid = true;
    let errorMessage = '';
    
    if (field.hasAttribute('required') && !field.value.trim()) {
        isValid = false;
        errorMessage = 'Ce champ est requis.';
    } else if (field.type === 'email' && field.value && !isValidEmail(field.value)) {
        isValid = false;
        errorMessage = 'Adresse email invalide.';
    } else if (field.type === 'datetime-local' && field.value) {
        const selectedDate = new Date(field.value);
        const now = new Date();
        if (selectedDate < now) {
            isValid = false;
            errorMessage = 'La date ne peut pas être dans le passé.';
        }
    }
    
    // Appliquer le style et afficher l'erreur
    if (isValid) {
        field.classList.add('is-valid');
    } else {
        field.classList.add('is-invalid');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error text-red-600 text-sm mt-1';
        errorDiv.textContent = errorMessage;
        fieldContainer.appendChild(errorDiv);
    }
    
    return isValid;
}

/**
 * Valide un formulaire complet
 */
function validateForm(form) {
    const requiredFields = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isFormValid = true;
    
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isFormValid = false;
        }
    });
    
    if (!isFormValid) {
        showNotification('Veuillez corriger les erreurs dans le formulaire.', 'error');
        
        // Scroll vers le premier champ invalide
        const firstInvalidField = form.querySelector('.is-invalid');
        if (firstInvalidField) {
            firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstInvalidField.focus();
        }
    }
    
    return isFormValid;
}

/**
 * ===============================================
 * HELPERS UTILITAIRES
 * ===============================================
 */

/**
 * Récupère le token CSRF
 */
function getCsrfToken() {
    const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]') || 
                        document.querySelector('meta[name=csrf-token]');
    return tokenElement ? tokenElement.value || tokenElement.getAttribute('content') : '';
}

/**
 * Valide une adresse email
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Affiche une notification
 */
function showNotification(message, type = 'info', duration = 5000) {
    // Créer l'élément de notification
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transform translate-x-full transition-transform duration-300 max-w-sm`;
    
    // Définir les styles selon le type
    const styles = {
        success: 'bg-green-600 text-white',
        error: 'bg-red-600 text-white',
        warning: 'bg-yellow-600 text-white',
        info: 'bg-blue-600 text-white'
    };
    
    notification.classList.add(...(styles[type] || styles.info).split(' '));
    
    // Icône selon le type
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    notification.innerHTML = `
        <div class="flex items-center gap-3">
            <i class="${icons[type] || icons.info}"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white/80 hover:text-white">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animation d'entrée
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto-suppression
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 300);
    }, duration);
}

/**
 * ===============================================
 * AUTO-INITIALISATION
 * ===============================================
 */

/**
 * Initialisation automatique au chargement de la page
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 Initialisation automatique des formulaires...');
    
    // Initialiser les formulaires
    initTaskForms();
    initInterventionForms();
    setupFormValidation();
    
    // Observer les changements DOM pour les formulaires chargés dynamiquement
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) { // Element node
                    // Vérifier si c'est un formulaire ou contient des formulaires
                    if (node.matches('form') || node.querySelector('form')) {
                        console.log('🔄 Nouveau formulaire détecté, réinitialisation...');
                        setTimeout(() => {
                            initTaskForms();
                            initInterventionForms();
                            setupFormValidation();
                        }, 100);
                    }
                }
            });
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    console.log('✅ Formulaires initialisés avec succès !');
});

/**
 * ===============================================
 * FONCTIONS GLOBALES EXPOSÉES
 * ===============================================
 */

// Exposer les fonctions principales pour utilisation externe
window.FormHelpers = {
    loadAllAppartements,
    loadAllEmployees,
    loadTechnicians,
    loadAllTenants,
    initTaskForms,
    initInterventionForms,
    setupFormValidation,
    validateForm,
    showNotification,
    getCsrfToken
};

// Alias pour compatibilité
window.refreshTaskAppartements = initTaskForms;
window.refreshInterventionAppartements = initInterventionForms;
window.refreshAppartementSelectors = function() {
    initTaskForms();
    initInterventionForms();
};

console.log('✅ Helpers de formulaires chargés et prêts !');