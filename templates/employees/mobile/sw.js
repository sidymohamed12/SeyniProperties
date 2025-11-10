// templates/employees/mobile/sw.js - Service Worker pour PWA

const CACHE_NAME = 'seyni-employees-v{{ version }}';
const API_CACHE_NAME = 'seyni-api-cache-v1';

// Ressources à mettre en cache immédiatement
const STATIC_CACHE_URLS = [
    '/employees/mobile/',
    '/employees/mobile/tasks/',
    '/employees/mobile/interventions/',
    '/employees/mobile/schedule/',
    '/static/css/employees-mobile.css',
    '/static/js/employees-mobile.js',
    '/static/img/icon-192.png',
    '/static/img/icon-512.png',
    '/static/img/favicon.ico',
    // CDN resources
    'https://cdn.tailwindcss.com',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// URLs à mettre en cache dynamiquement
const DYNAMIC_CACHE_PATTERNS = [
    /^\/employees\/mobile\/tasks\/\d+\/$/,
    /^\/employees\/mobile\/interventions\/\d+\/$/,
    /^\/media\/.*\.(jpg|jpeg|png|gif|webp)$/,
    /^\/static\/.*\.(css|js|png|jpg|jpeg|gif|svg|woff|woff2)$/
];

// URLs API à mettre en cache avec stratégie particulière
const API_CACHE_PATTERNS = [
    /^\/employees\/api\/mobile\/offline-data\/$/,
    /^\/employees\/api\/mobile\/my-stats\/$/
];

// URLs qui nécessitent toujours le réseau
const NETWORK_ONLY_PATTERNS = [
    /^\/employees\/mobile\/.*\/(start|complete)\/$/,
    /^\/employees\/mobile\/upload\/.*\/$/,
    /^\/employees\/mobile\/report\/.*\/$/,
    /^\/accounts\/logout\/$/
];

// ===== INSTALLATION =====
self.addEventListener('install', (event) => {
    console.log('[SW] Installation...');
    
    event.waitUntil(
        Promise.all([
            // Cache statique
            caches.open(CACHE_NAME).then((cache) => {
                console.log('[SW] Mise en cache des ressources statiques');
                return cache.addAll(STATIC_CACHE_URLS.filter(url => 
                    !url.startsWith('http') || url.includes('cdnjs') || url.includes('tailwind')
                ));
            }),
            
            // Pré-cache des données offline
            precacheOfflineData()
        ])
    );
    
    // Forcer l'activation immédiate
    self.skipWaiting();
});

// ===== ACTIVATION =====
self.addEventListener('activate', (event) => {
    console.log('[SW] Activation...');
    
    event.waitUntil(
        Promise.all([
            // Nettoyer les anciens caches
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
                            console.log('[SW] Suppression ancien cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            }),
            
            // Prendre le contrôle immédiatement
            self.clients.claim()
        ])
    );
});

// ===== INTERCEPTION DES REQUÊTES =====
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);
    
    // Ignorer les requêtes non-GET et non-HTTP
    if (request.method !== 'GET' || !url.protocol.startsWith('http')) {
        return;
    }
    
    // Stratégie selon le type de requête
    if (isNetworkOnlyRequest(request)) {
        event.respondWith(networkOnlyStrategy(request));
    } else if (isAPIRequest(request)) {
        event.respondWith(apiCacheStrategy(request));
    } else if (isStaticResource(request)) {
        event.respondWith(cacheFirstStrategy(request));
    } else if (isDynamicContent(request)) {
        event.respondWith(networkFirstStrategy(request));
    } else {
        event.respondWith(staleWhileRevalidateStrategy(request));
    }
});

// ===== STRATÉGIES DE CACHE =====

// Réseau uniquement (actions critiques)
async function networkOnlyStrategy(request) {
    try {
        const response = await fetch(request);
        return response;
    } catch (error) {
        console.log('[SW] Erreur réseau pour action critique:', request.url);
        return new Response(JSON.stringify({
            success: false,
            error: 'Action impossible hors ligne',
            offline: true
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Cache d'abord (ressources statiques)
async function cacheFirstStrategy(request) {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[SW] Ressource non disponible:', request.url);
        return new Response('Ressource non disponible hors ligne', { status: 503 });
    }
}

// Réseau d'abord (contenu dynamique)
async function networkFirstStrategy(request) {
    const cache = await caches.open(CACHE_NAME);
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[SW] Utilisation du cache pour:', request.url);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Page d'erreur pour les pages HTML
        if (request.headers.get('accept')?.includes('text/html')) {
            return generateOfflinePage(request);
        }
        
        return new Response('Contenu non disponible', { status: 503 });
    }
}

// Cache stale-while-revalidate (API)
async function staleWhileRevalidateStrategy(request) {
    const cache = await caches.open(API_CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    // Réponse en arrière-plan pour mise à jour
    const fetchPromise = fetch(request).then((networkResponse) => {
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    }).catch(() => {
        // Silencieux en arrière-plan
    });
    
    // Retourner le cache immédiatement ou attendre le réseau
    return cachedResponse || fetchPromise;
}

// API avec cache intelligent
async function apiCacheStrategy(request) {
    const cache = await caches.open(API_CACHE_NAME);
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Stocker avec timestamp pour expiration
            const responseToCache = networkResponse.clone();
            const headers = new Headers(responseToCache.headers);
            headers.set('sw-cached-at', Date.now().toString());
            
            const modifiedResponse = new Response(responseToCache.body, {
                status: responseToCache.status,
                statusText: responseToCache.statusText,
                headers: headers
            });
            
            cache.put(request, modifiedResponse);
        }
        
        return networkResponse;
    } catch (error) {
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            // Vérifier l'âge du cache (15 minutes max)
            const cachedAt = cachedResponse.headers.get('sw-cached-at');
            const now = Date.now();
            const maxAge = 15 * 60 * 1000; // 15 minutes
            
            if (!cachedAt || (now - parseInt(cachedAt)) < maxAge) {
                return cachedResponse;
            }
        }
        
        return new Response(JSON.stringify({
            success: false,
            error: 'Données non disponibles hors ligne',
            offline: true
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// ===== FONCTIONS UTILITAIRES =====

function isNetworkOnlyRequest(request) {
    return NETWORK_ONLY_PATTERNS.some(pattern => pattern.test(request.url));
}

function isAPIRequest(request) {
    return API_CACHE_PATTERNS.some(pattern => pattern.test(request.url)) ||
           request.url.includes('/api/');
}

function isStaticResource(request) {
    return request.url.includes('/static/') ||
           request.url.includes('cdnjs.cloudflare.com') ||
           request.url.includes('cdn.tailwindcss.com') ||
           /\.(css|js|png|jpg|jpeg|gif|svg|woff|woff2)$/.test(request.url);
}

function isDynamicContent(request) {
    return DYNAMIC_CACHE_PATTERNS.some(pattern => pattern.test(request.url));
}

// Page hors ligne personnalisée
async function generateOfflinePage(request) {
    const offlineHTML = `
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hors ligne - Seyni Employés</title>
        <style>
            body {
                font-family: system-ui, -apple-system, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
            }
            .container {
                text-align: center;
                max-width: 400px;
                background: rgba(255,255,255,0.1);
                padding: 40px 30px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            .icon {
                font-size: 4rem;
                margin-bottom: 20px;
                opacity: 0.8;
            }
            h1 {
                margin: 0 0 15px 0;
                font-size: 1.5rem;
                font-weight: 600;
            }
            p {
                margin: 0 0 25px 0;
                opacity: 0.9;
                line-height: 1.5;
            }
            .button {
                background: rgba(255,255,255,0.2);
                border: 1px solid rgba(255,255,255,0.3);
                color: white;
                padding: 12px 24px;
                border-radius: 25px;
                text-decoration: none;
                display: inline-block;
                transition: all 0.3s ease;
                margin: 5px;
            }
            .button:hover {
                background: rgba(255,255,255,0.3);
                transform: translateY(-2px);
            }
            .status {
                margin-top: 20px;
                padding: 10px;
                border-radius: 10px;
                background: rgba(255,255,255,0.1);
                font-size: 0.9rem;
            }
            .online { background: rgba(34, 197, 94, 0.3); }
            .offline { background: rgba(239, 68, 68, 0.3); }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">📱</div>
            <h1>Mode Hors Ligne</h1>
            <p>Cette page nécessite une connexion internet. Vos données locales restent accessibles.</p>
            
            <a href="/employees/mobile/" class="button">🏠 Accueil</a>
            <a href="/employees/mobile/tasks/" class="button">📋 Mes tâches</a>
            
            <div id="status" class="status offline">
                🔴 Hors ligne
            </div>
        </div>
        
        <script>
            function updateStatus() {
                const status = document.getElementById('status');
                if (navigator.onLine) {
                    status.className = 'status online';
                    status.innerHTML = '🟢 En ligne - <a href="#" onclick="location.reload()" style="color: white; text-decoration: underline;">Actualiser</a>';
                } else {
                    status.className = 'status offline';
                    status.innerHTML = '🔴 Hors ligne';
                }
            }
            
            window.addEventListener('online', updateStatus);
            window.addEventListener('offline', updateStatus);
            updateStatus();
        </script>
    </body>
    </html>
    `;
    
    return new Response(offlineHTML, {
        headers: { 'Content-Type': 'text/html; charset=utf-8' }
    });
}

// Pré-cache des données critiques
async function precacheOfflineData() {
    try {
        // Pré-charger les données de base si possible
        const dataResponse = await fetch('/employees/api/mobile/offline-data/');
        
        if (dataResponse.ok) {
            const cache = await caches.open(API_CACHE_NAME);
            cache.put('/employees/api/mobile/offline-data/', dataResponse);
            console.log('[SW] Données offline pré-cachées');
        }
    } catch (error) {
        console.log('[SW] Impossible de pré-cacher les données offline');
    }
}

// ===== GESTION DES MESSAGES =====
self.addEventListener('message', (event) => {
    const { action, data } = event.data;
    
    switch (action) {
        case 'CACHE_NEW_ROUTE':
            cacheNewRoute(data.url);
            break;
            
        case 'CLEAR_CACHE':
            clearSpecificCache(data.pattern);
            break;
            
        case 'GET_CACHE_STATUS':
            getCacheStatus().then(status => {
                event.ports[0].postMessage({ status });
            });
            break;
            
        case 'SYNC_OFFLINE_DATA':
            syncOfflineData();
            break;
    }
});

// Cache d'une nouvelle route
async function cacheNewRoute(url) {
    try {
        const cache = await caches.open(CACHE_NAME);
        await cache.add(url);
        console.log('[SW] Nouvelle route cachée:', url);
    } catch (error) {
        console.log('[SW] Erreur cache nouvelle route:', error);
    }
}

// Nettoyage sélectif du cache
async function clearSpecificCache(pattern) {
    const cacheNames = await caches.keys();
    
    for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const requests = await cache.keys();
        
        for (const request of requests) {
            if (new RegExp(pattern).test(request.url)) {
                await cache.delete(request);
                console.log('[SW] Supprimé du cache:', request.url);
            }
        }
    }
}

// Status du cache
async function getCacheStatus() {
    const cacheNames = await caches.keys();
    const status = {};
    
    for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const requests = await cache.keys();
        status[cacheName] = requests.length;
    }
    
    return status;
}

// Synchronisation des données offline
async function syncOfflineData() {
    // Ici on pourrait implémenter la synchronisation
    // des actions effectuées hors ligne
    console.log('[SW] Synchronisation des données offline...');
}

// ===== GESTION DES NOTIFICATIONS PUSH =====
self.addEventListener('push', (event) => {
    if (!event.data) return;
    
    try {
        const data = event.data.json();
        
        const options = {
            body: data.message,
            icon: '/static/img/icon-192.png',
            badge: '/static/img/badge-72.png',
            tag: data.tag || 'seyni-notification',
            vibrate: [200, 100, 200],
            actions: data.actions || [],
            data: data.url ? { url: data.url } : undefined
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    } catch (error) {
        console.log('[SW] Erreur notification push:', error);
    }
});

// Gestion des clics sur notifications
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    const urlToOpen = event.notification.data?.url || '/employees/mobile/';
    
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Vérifier si l'app est déjà ouverte
                for (const client of clientList) {
                    if (client.url.includes('/employees/mobile/') && 'focus' in client) {
                        client.navigate(urlToOpen);
                        return client.focus();
                    }
                }
                
                // Ouvrir nouvelle fenêtre
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

// ===== BACKGROUND SYNC =====
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync-tasks') {
        event.waitUntil(syncPendingTasks());
    }
});

async function syncPendingTasks() {
    try {
        // Récupérer les tâches en attente de synchronisation
        // depuis IndexedDB ou localStorage
        console.log('[SW] Synchronisation des tâches en arrière-plan...');
        
        // Implémenter la logique de sync ici
        
    } catch (error) {
        console.log('[SW] Erreur sync background:', error);
    }
}

// ===== LOG ET DEBUG =====
console.log('[SW] Service Worker Seyni Employés chargé - Version {{ version }}');