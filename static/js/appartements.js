// static/js/appartements.js - Gestion des appartements dans les formulaires

// Configuration des URLs (à adapter selon votre configuration)
const URLS = {
    residencesByLandlord: '/dashboard/api/residences-by-landlord/',
    appartementsByResidence: '/dashboard/api/appartements-by-residence/',
    landlords: '/dashboard/api/landlords/'
};

/**
 * Initialise la gestion hiérarchique des sélecteurs
 * Bailleur -> Résidence -> Appartement
 */
function initHierarchicalSelectors() {
    const bailleurSelect = document.querySelector('select[name="bailleur"], #bailleur-select, #landlord-select');
    const residenceSelect = document.querySelector('select[name="residence"], #residence-select');
    const appartementSelect = document.querySelector('select[name="bien"], #intervention-property-select, #task-property-select, #property-select');
    
    if (bailleurSelect && residenceSelect) {
        bailleurSelect.addEventListener('change', function() {
            loadResidencesByLandlord(this.value, residenceSelect, appartementSelect);
        });
    }
    
    if (residenceSelect && appartementSelect) {
        residenceSelect.addEventListener('change', function() {
            loadAppartementsByResidence(this.value, appartementSelect);
        });
    }
    
    // Initialiser les données si un bailleur est déjà sélectionné
    if (bailleurSelect && bailleurSelect.value) {
        loadResidencesByLandlord(bailleurSelect.value, residenceSelect, appartementSelect);
    }
}

/**
 * Charge les résidences d'un bailleur
 */
function loadResidencesByLandlord(bailleurId, residenceSelect, appartementSelect) {
    if (!bailleurId || !residenceSelect) return;
    
    // Réinitialiser les sélecteurs
    residenceSelect.innerHTML = '<option value="">Chargement des résidences...</option>';
    if (appartementSelect) {
        appartementSelect.innerHTML = '<option value="">Sélectionnez d\'abord une résidence</option>';
    }
    
    fetch(`${URLS.residencesByLandlord}${bailleurId}/`, {
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
        if (data.success && data.residences) {
            residenceSelect.innerHTML = '<option value="">Sélectionner une résidence...</option>';
            
            data.residences.forEach(residence => {
                const option = document.createElement('option');
                option.value = residence.id;
                option.textContent = residence.nom;
                residenceSelect.appendChild(option);
            });
            
            console.log(`${data.residences.length} résidences chargées pour le bailleur ${bailleurId}`);
        } else {
            residenceSelect.innerHTML = '<option value="">Aucune résidence trouvée</option>';
        }
    })
    .catch(error => {
        console.error('Erreur lors du chargement des résidences:', error);
        residenceSelect.innerHTML = '<option value="">Erreur de chargement</option>';
    });
}

/**
 * Charge les appartements d'une résidence
 */
function loadAppartementsByResidence(residenceId, appartementSelect) {
    if (!residenceId || !appartementSelect) return;
    
    appartementSelect.innerHTML = '<option value="">Chargement des appartements...</option>';
    
    fetch(`${URLS.appartementsByResidence}${residenceId}/`, {
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
        if (data.success && data.appartements) {
            appartementSelect.innerHTML = '<option value="">Sélectionner un appartement...</option>';
            
            data.appartements.forEach(appartement => {
                const option = document.createElement('option');
                option.value = appartement.id;
                option.textContent = `${appartement.nom} - ${appartement.reference || 'Étage ' + appartement.etage}`;
                // Ajouter des informations supplémentaires si disponibles
                if (appartement.type_bien) {
                    option.textContent += ` (${appartement.type_bien})`;
                }
                appartementSelect.appendChild(option);
            });
            
            console.log(`${data.appartements.length} appartements chargés pour la résidence ${residenceId}`);
        } else {
            appartementSelect.innerHTML = '<option value="">Aucun appartement trouvé</option>';
        }
    })
    .catch(error => {
        console.error('Erreur lors du chargement des appartements:', error);
        appartementSelect.innerHTML = '<option value="">Erreur de chargement</option>';
    });
}

/**
 * Charge tous les appartements (pour les formulaires sans hiérarchie)
 */
function loadAllAppartements(selectElement) {
    if (!selectElement) return;
    
    selectElement.innerHTML = '<option value="">Chargement des appartements...</option>';
    
    // Si on a une API pour tous les appartements
    fetch('/dashboard/api/appartements/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.appartements) {
            selectElement.innerHTML = '<option value="">Sélectionner un appartement...</option>';
            
            data.appartements.forEach(appartement => {
                const option = document.createElement('option');
                option.value = appartement.id;
                option.textContent = `${appartement.nom} - ${appartement.residence_nom}`;
                selectElement.appendChild(option);
            });
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
 * Initialise les formulaires de tâches et interventions
 */
function initTaskInterventionForms() {
    // Formulaires de tâches
    const taskPropertySelect = document.getElementById('task-property-select');
    if (taskPropertySelect) {
        loadAllAppartements(taskPropertySelect);
    }
    
    // Formulaires d'interventions
    const interventionPropertySelect = document.getElementById('intervention-property-select');
    if (interventionPropertySelect) {
        loadAllAppartements(interventionPropertySelect);
    }
}

/**
 * Initialise au chargement de la page
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initialisation de la gestion des appartements');
    
    // Initialiser la gestion hiérarchique
    initHierarchicalSelectors();
    
    // Initialiser les formulaires de tâches et interventions
    initTaskInterventionForms();
    
    // Observer les changements de DOM pour les modals qui se chargent dynamiquement
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Réinitialiser si de nouveaux sélecteurs sont ajoutés
                        const newSelectors = node.querySelectorAll('select[name="bien"], #intervention-property-select, #task-property-select');
                        if (newSelectors.length > 0) {
                            console.log('Nouveaux sélecteurs détectés, réinitialisation...');
                            setTimeout(() => {
                                initHierarchicalSelectors();
                                initTaskInterventionForms();
                            }, 100);
                        }
                    }
                });
            }
        });
    });
    
    // Observer les changements dans le body
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});

// Fonctions utilitaires pour les modals
window.refreshAppartementSelectors = function() {
    console.log('Rafraîchissement des sélecteurs d\'appartements');
    initTaskInterventionForms();
};

window.loadResidencesByLandlord = loadResidencesByLandlord;
window.loadAppartementsByResidence = loadAppartementsByResidence;
window.loadAllAppartements = loadAllAppartements;