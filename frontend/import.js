// Smart Recipe Import Manager
class ImportManager {
    constructor() {
        this.activeJobs = new Map();
        this.refreshInterval = null;
        this.apiBaseUrl = window.location.origin;
        
        this.initializeElements();
        this.setupEventListeners();
        this.startPeriodicRefresh();
        this.loadInitialJobs();
    }

    initializeElements() {
        this.elements = {
            form: document.getElementById('importForm'),
            urlInput: document.getElementById('urlInput'),
            submitBtn: document.getElementById('submitBtn'),
            clearBtn: document.getElementById('clearBtn'),
            pasteBtn: document.getElementById('pasteBtn'),
            refreshBtn: document.getElementById('refreshBtn'),
            jobsList: document.getElementById('jobsList'),
            completedCount: document.getElementById('completedCount'),
            runningCount: document.getElementById('runningCount'),
            queuedCount: document.getElementById('queuedCount'),
            databaseCount: document.getElementById('databaseCount')
        };
    }

    setupEventListeners() {
        this.elements.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });

        this.elements.clearBtn.addEventListener('click', () => {
            this.elements.urlInput.value = '';
        });

        this.elements.pasteBtn.addEventListener('click', async () => {
            await this.handlePaste();
        });

        this.elements.refreshBtn.addEventListener('click', () => {
            this.loadJobs();
        });
    }

    async handlePaste() {
        try {
            const text = await navigator.clipboard.readText();
            if (text) {
                this.elements.urlInput.value = text;
                this.showNotification('Testo incollato con successo', 'success');
            }
        } catch (err) {
            console.error('Errore nel leggere dagli appunti:', err);
            this.showNotification('Impossibile leggere dagli appunti. Incolla manualmente.', 'warning');
        }
    }

    parseUrls(input) {
        if (!input.trim()) return [];
        
        // Separa per righe e virgole, filtra URL validi
        const urlPattern = /https?:\/\/(www\.)?(youtube\.com|youtu\.be|instagram\.com|facebook\.com|tiktok\.com|fb\.watch)\/[^\s,]+/gi;
        return input.match(urlPattern) || [];
    }

    validateUrls(urls) {
        const supportedDomains = ['youtube.com', 'youtu.be', 'instagram.com', 'facebook.com', 'tiktok.com', 'fb.watch'];
        const valid = [];
        const invalid = [];

        urls.forEach(url => {
            const isValid = supportedDomains.some(domain => url.toLowerCase().includes(domain));
            if (isValid) {
                valid.push(url);
            } else {
                invalid.push(url);
            }
        });

        return { valid, invalid };
    }

    async handleSubmit() {
        const input = this.elements.urlInput.value.trim();
        if (!input) {
            this.showNotification('Inserisci almeno un URL', 'warning');
            return;
        }

        const urls = this.parseUrls(input);
        if (urls.length === 0) {
            this.showNotification('Nessun URL valido trovato', 'destructive');
            return;
        }

        const { valid, invalid } = this.validateUrls(urls);
        
        if (invalid.length > 0) {
            this.showNotification(`${invalid.length} URL non supportati ignorati`, 'warning');
        }

        if (valid.length === 0) {
            this.showNotification('Nessun URL supportato trovato', 'destructive');
            return;
        }

        try {
            this.setSubmitLoading(true);
            const jobId = await this.startImport(valid);
            
            if (jobId) {
                this.showNotification(`Import avviato con successo! Job ID: ${jobId}`, 'success');
                this.elements.urlInput.value = '';
                this.loadJobs();
            }
        } catch (error) {
            console.error('Errore durante l\'avvio dell\'import:', error);
            this.showNotification(`Errore: ${error.message}`, 'destructive');
        } finally {
            this.setSubmitLoading(false);
        }
    }

    async startImport(urls) {
        const response = await fetch(`${this.apiBaseUrl}/ingest/recipes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ urls })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Errore durante l\'avvio dell\'import');
        }

        const result = await response.json();
        return result.job_id;
    }

    async loadJobs() {
        try {
            this.setRefreshLoading(true);
            const response = await fetch(`${this.apiBaseUrl}/ingest/status`);
            
            if (!response.ok) {
                if (response.status === 404) {
                    // Nessun job trovato
                    this.renderEmptyState();
                    this.updateStats({ completed: 0, running: 0, queued: 0 });
                    return;
                }
                throw new Error('Errore nel caricamento dei job');
            }

            const jobs = await response.json();
            this.renderJobs(jobs);
            this.updateJobStats(jobs);
            
            // Aggiorna le stats del database se ci sono job completati
            const hasCompleted = jobs.some(job => job.status === 'completed');
            if (hasCompleted) {
                this.loadDatabaseStats();
            }
        } catch (error) {
            console.error('Errore nel caricamento dei job:', error);
            this.showNotification('Errore nel caricamento dei job', 'destructive');
        } finally {
            this.setRefreshLoading(false);
        }
    }

    async loadInitialJobs() {
        await this.loadJobs();
        await this.loadDatabaseStats();
    }
    
    async loadDatabaseStats() {
        try {
            // Prova a caricare le stats del database
            const response = await fetch(`${this.apiBaseUrl}/stats/database`);
            
            if (response.ok) {
                const stats = await response.json();
                this.updateDatabaseStats(stats);
            } else {
                // Se l'endpoint non è disponibile, prova attraverso le collection info
                try {
                    const collectionResponse = await fetch(`${this.apiBaseUrl}/collection/info`);
                    if (collectionResponse.ok) {
                        const info = await collectionResponse.json();
                        const count = info.count || info.total_documents || 0;
                        this.updateDatabaseStats({ total_recipes: count });
                    }
                } catch (collectionError) {
                    console.log('Endpoint collection info non disponibile:', collectionError.message);
                }
            }
        } catch (error) {
            console.log('Stats database non disponibili:', error.message);
            // Non è un errore critico, mostra 0
            this.updateDatabaseStats({ total_recipes: 0 });
        }
    }
    
    updateDatabaseStats(stats) {
        const { total_recipes = 0 } = stats;
        this.elements.databaseCount.textContent = total_recipes;
        
        // Aggiorna anche il colore dell'icona del database in base al numero di ricette
        const dbCard = this.elements.databaseCount.closest('.card-elevated');
        if (dbCard) {
            const icon = dbCard.querySelector('svg');
            if (total_recipes > 0) {
                icon.classList.add('animate-pulse-soft');
            } else {
                icon.classList.remove('animate-pulse-soft');
            }
        }
    }

    renderEmptyState() {
        this.elements.jobsList.innerHTML = `
            <div class="text-center py-12 animate-scale-in">
                <div class="mb-6">
                    <div class="w-20 h-20 mx-auto bg-gradient-to-br from-oneui-lightblue to-oneui-blue rounded-oneui flex items-center justify-center shadow-lg">
                        <svg class="w-10 h-10 text-oneui-darkblue opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                    </div>
                </div>
                <div class="space-y-2">
                    <h3 class="step-title-enhanced text-xl">🚀 Pronto per l'Import</h3>
                    <p class="text-oneui-onSurfaceVariant max-w-md mx-auto">I job di importazione appariranno qui quando avvierai il processo. Potrai monitorare ogni step in tempo reale.</p>
                </div>
                <div class="mt-6 p-4 bg-oneui-surfaceVariant rounded-material border border-oneui-surface max-w-sm mx-auto">
                    <div class="text-xs text-oneui-onSurfaceVariant space-y-1">
                        <div class="flex items-center space-x-2">
                            <span>📥</span>
                            <span>Download contenuti</span>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span>🎵</span>
                            <span>Estrazione audio</span>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span>🎤</span>
                            <span>Riconoscimento vocale</span>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span>🧠</span>
                            <span>Analisi ricetta</span>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span>🤖</span>
                            <span>Vettorizzazione AI</span>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span>💾</span>
                            <span>Ingest database</span>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span>📊</span>
                            <span>Indicizzazione</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderJobs(jobs) {
        if (!jobs || jobs.length === 0) {
            this.renderEmptyState();
            return;
        }

        // Ordina job: prima running, poi queued, poi completed/failed
        const sortedJobs = jobs.sort((a, b) => {
            const statusOrder = { running: 0, queued: 1, completed: 2, failed: 3 };
            return statusOrder[a.status] - statusOrder[b.status];
        });

        this.elements.jobsList.innerHTML = sortedJobs.map(job => this.renderJob(job)).join('');
    }

    renderJob(job) {
        const { job_id, status, progress_percent = 0, progress, result, detail } = job;
        const truncatedId = job_id.substring(0, 8);
        
        let statusIcon, statusClass, statusText, cardClass;
        
        switch (status) {
            case 'running':
                statusIcon = `<svg class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>`;
                statusClass = 'text-oneui-darkblue bg-oneui-lightblue border-oneui-blue';
                statusText = 'In Corso';
                cardClass = 'step-running border-l-4 border-l-oneui-blue';
                break;
            case 'queued':
                statusIcon = `<svg class="w-5 h-5 animate-pulse-soft" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>`;
                statusClass = 'text-yellow-700 bg-yellow-100 border-yellow-300';
                statusText = 'In Coda';
                cardClass = 'border-l-4 border-l-yellow-400';
                break;
            case 'completed':
                statusIcon = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>`;
                statusClass = 'text-green-700 bg-green-100 border-green-300';
                statusText = 'Completato';
                cardClass = 'step-completed border-l-4 border-l-green-500';
                break;
            case 'failed':
                statusIcon = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"></path>
                </svg>`;
                statusClass = 'text-red-700 bg-red-100 border-red-300';
                statusText = 'Fallito';
                cardClass = 'step-failed border-l-4 border-l-red-500';
                break;
            default:
                statusIcon = '❓';
                statusClass = 'text-gray-600 bg-gray-50 border-gray-200';
                statusText = 'Sconosciuto';
                cardClass = 'border-l-4 border-l-gray-400';
        }

        // Generazione sezione progresso migliorata con One UI 7 / Material Design 3
        let progressSection = '';
        if (progress) {
            const { total = 0, success = 0, failed = 0, stage = '', urls = [] } = progress;
            
            // Mappa descrittiva degli stage per migliorare UX
            const stageDescriptions = {
                'queued': { name: 'In Coda', icon: '⏳', desc: 'Preparazione elaborazione' },
                'running': { name: 'Elaborazione', icon: '⚡', desc: 'Sistema attivo' },
                'download': { name: 'Download', icon: '📥', desc: 'Scaricamento contenuti' },
                'extract_audio': { name: 'Estrazione Audio', icon: '🎵', desc: 'Conversione traccia audio' },
                'stt': { name: 'Riconoscimento Vocale', icon: '🎤', desc: 'Trascrizione audio in testo' },
                'parse_recipe': { name: 'Analisi Ricetta', icon: '🧠', desc: 'Estrazione ingredienti e procedimento' },
                'embedding': { name: 'Vettorizzazione', icon: '🔢', desc: 'Creazione embeddings semantici' },
                'vectorizing': { name: 'Embedding AI', icon: '🤖', desc: 'Elaborazione con modelli linguistici' },
                'ingesting': { name: 'Ingest Database', icon: '💾', desc: 'Caricamento nel database vettoriale' },
                'indexing': { name: 'Indicizzazione', icon: '📊', desc: 'Creazione indici di ricerca' },
                'persisting': { name: 'Salvataggio', icon: '🗃️', desc: 'Persistenza dati finale' },
                'done': { name: 'Completato', icon: '✅', desc: 'Elaborazione terminata' },
                'error': { name: 'Errore', icon: '❌', desc: 'Problema durante elaborazione' }
            };
            
            const currentStageInfo = stageDescriptions[stage] || { name: stage || 'In Corso', icon: '🔄', desc: '' };
            
            progressSection = `
                <div class="mt-4 space-y-3">
                    <!-- Header Progresso -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <div class="step-title-enhanced text-lg">
                                ${currentStageInfo.icon} ${currentStageInfo.name}
                            </div>
                            ${currentStageInfo.desc ? `<div class="text-xs text-oneui-onSurfaceVariant bg-oneui-surfaceVariant px-2 py-1 rounded-full">
                                ${currentStageInfo.desc}
                            </div>` : ''}
                        </div>
                        <div class="text-right">
                            <div class="text-xl font-bold text-oneui-darkblue">${Math.round(progress_percent)}%</div>
                            <div class="text-xs text-muted-foreground">${success + failed}/${total} URL</div>
                        </div>
                    </div>
                    
                    <!-- Barra di Progresso Avanzata -->
                    <div class="relative">
                        <div class="w-full bg-material-surfaceContainer rounded-full h-3 overflow-hidden">
                            <div class="progress-bar h-3 rounded-full transition-all duration-500 ease-out" style="--progress: ${Math.max(0, Math.min(100, progress_percent))}%; width: ${Math.max(0, Math.min(100, progress_percent))}%"></div>
                        </div>
                    </div>
                    
                    <!-- Stats rapide -->
                    ${success > 0 || failed > 0 ? `
                        <div class="flex items-center space-x-4 text-sm">
                            <div class="flex items-center space-x-1 text-green-700">
                                <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse-soft"></span>
                                <span class="font-medium">${success} completati</span>
                            </div>
                            ${failed > 0 ? `
                                <div class="flex items-center space-x-1 text-red-700">
                                    <span class="w-2 h-2 bg-red-500 rounded-full"></span>
                                    <span class="font-medium">${failed} falliti</span>
                                </div>
                            ` : ''}
                        </div>
                    ` : ''}
                </div>
            `;
            
            // Sezione URL dettagliata con step individuali evidenziati
            if (status === 'running' && urls.length > 0) {
                const allUrls = urls.slice(0, 5); // Mostra fino a 5 URL
                if (allUrls.length > 0) {
                    progressSection += `
                        <div class="mt-4 space-y-3">
                            <div class="flex items-center space-x-2">
                                <div class="step-title-enhanced text-base">🔍 URL in Elaborazione</div>
                                <div class="text-xs bg-oneui-lightblue text-oneui-darkblue px-2 py-1 rounded-full font-medium">
                                    ${allUrls.length}/${total}
                                </div>
                            </div>
                            <div class="space-y-2">
                                ${allUrls.map((u, idx) => {
                                    const urlStageInfo = stageDescriptions[u.stage] || { name: u.stage || u.status, icon: '⏸️', desc: '' };
                                    let urlStatusClass = '';
                                    let urlBorderClass = '';
                                    
                                    switch (u.status) {
                                        case 'running':
                                            urlStatusClass = 'step-running';
                                            urlBorderClass = 'border-l-oneui-blue';
                                            break;
                                        case 'success':
                                            urlStatusClass = 'step-completed';
                                            urlBorderClass = 'border-l-green-500';
                                            break;
                                        case 'failed':
                                            urlStatusClass = 'step-failed';
                                            urlBorderClass = 'border-l-red-500';
                                            break;
                                        default:
                                            urlStatusClass = 'bg-material-surfaceContainer';
                                            urlBorderClass = 'border-l-gray-400';
                                    }
                                    
                                    return `
                                        <div class="${urlStatusClass} ${urlBorderClass} border-l-4 p-3 rounded-r-material animate-slide-in" style="animation-delay: ${idx * 0.1}s">
                                            <div class="flex items-center justify-between mb-2">
                                                <div class="url-title-enhanced flex-1 mr-3 truncate">${u.url}</div>
                                                <div class="flex items-center space-x-2">
                                                    <div class="text-xs bg-white bg-opacity-80 px-2 py-1 rounded-full flex items-center space-x-1">
                                                        <span>${urlStageInfo.icon}</span>
                                                        <span class="font-medium">${urlStageInfo.name}</span>
                                                    </div>
                                                    ${u.local_percent ? `
                                                        <div class="text-xs font-bold text-oneui-darkblue">
                                                            ${Math.round(u.local_percent)}%
                                                        </div>
                                                    ` : ''}
                                                </div>
                                            </div>
                                            ${urlStageInfo.desc ? `
                                                <div class="text-xs text-oneui-onSurfaceVariant">
                                                    ${urlStageInfo.desc}
                                                </div>
                                            ` : ''}
                                            ${u.local_percent && u.status === 'running' ? `
                                                <div class="mt-2 w-full bg-white bg-opacity-50 rounded-full h-1.5">
                                                    <div class="bg-oneui-blue h-1.5 rounded-full transition-all duration-300" style="width: ${Math.max(0, Math.min(100, u.local_percent))}%"></div>
                                                </div>
                                            ` : ''}
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                            ${urls.length > 5 ? `
                                <div class="text-center">
                                    <div class="text-xs text-muted-foreground bg-muted px-3 py-1 rounded-full inline-block">
                                        +${urls.length - 5} altri URL in coda
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    `;
                }
            }
        }

        // Sezione risultati migliorata con One UI 7 styling
        let resultSection = '';
        if (result) {
            const { indexed = 0, total_urls = 0, success = 0, failed = 0 } = result;
            resultSection = `
                <div class="mt-4 p-4 bg-gradient-to-r from-material-surfaceContainer to-material-surface rounded-material border border-material-surfaceContainerHigh">
                    <div class="flex items-center space-x-2 mb-3">
                        <div class="step-title-enhanced text-base">🎆 Risultato Import</div>
                        <div class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium">
                            Completato
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-3 text-sm">
                        <div class="bg-white bg-opacity-60 p-3 rounded-lg border border-green-200">
                            <div class="flex items-center space-x-2">
                                <span class="text-green-600 text-lg">📝</span>
                                <div>
                                    <div class="font-bold text-green-800">${indexed}</div>
                                    <div class="text-xs text-green-600">Ricette salvate</div>
                                </div>
                            </div>
                        </div>
                        <div class="bg-white bg-opacity-60 p-3 rounded-lg border border-blue-200">
                            <div class="flex items-center space-x-2">
                                <span class="text-blue-600 text-lg">🔗</span>
                                <div>
                                    <div class="font-bold text-blue-800">${total_urls}</div>
                                    <div class="text-xs text-blue-600">URL processati</div>
                                </div>
                            </div>
                        </div>
                        <div class="bg-white bg-opacity-60 p-3 rounded-lg border border-green-200">
                            <div class="flex items-center space-x-2">
                                <span class="text-green-600 text-lg">✅</span>
                                <div>
                                    <div class="font-bold text-green-800">${success}</div>
                                    <div class="text-xs text-green-600">Successi</div>
                                </div>
                            </div>
                        </div>
                        ${failed > 0 ? `
                            <div class="bg-white bg-opacity-60 p-3 rounded-lg border border-red-200">
                                <div class="flex items-center space-x-2">
                                    <span class="text-red-600 text-lg">❌</span>
                                    <div>
                                        <div class="font-bold text-red-800">${failed}</div>
                                        <div class="text-xs text-red-600">Fallimenti</div>
                                    </div>
                                </div>
                            </div>
                        ` : `
                            <div class="bg-white bg-opacity-60 p-3 rounded-lg border border-gray-200">
                                <div class="flex items-center space-x-2">
                                    <span class="text-gray-600 text-lg">✨</span>
                                    <div>
                                        <div class="font-bold text-gray-800">100%</div>
                                        <div class="text-xs text-gray-600">Successo</div>
                                    </div>
                                </div>
                            </div>
                        `}
                    </div>
                    ${indexed > 0 ? `
                        <div class="mt-3 p-2 bg-green-50 border border-green-200 rounded-lg">
                            <div class="text-xs text-green-700 font-medium">
                                ✨ Ricette disponibili per la ricerca semantica
                            </div>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        if (detail && status === 'failed') {
            resultSection += `
                <div class="mt-3 p-4 bg-gradient-to-r from-red-50 to-red-100 border border-red-200 rounded-material animate-scale-in">
                    <div class="flex items-center space-x-2 mb-2">
                        <span class="text-red-600 text-lg">⚠️</span>
                        <div class="step-title-enhanced text-base text-red-800">Errore Elaborazione</div>
                    </div>
                    <div class="bg-white bg-opacity-70 p-3 rounded-lg border border-red-300">
                        <div class="text-sm text-red-800 font-mono">${detail}</div>
                    </div>
                </div>
            `;
        }

        return `
            <div class="card-elevated ${cardClass} rounded-material border bg-background p-5 animate-scale-in">
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center space-x-4">
                        <div class="flex items-center space-x-3">
                            <div class="h-10 w-10 rounded-oneui bg-gradient-to-br from-oneui-blue to-oneui-darkblue flex items-center justify-center text-white font-bold text-sm shadow-lg">
                                ${truncatedId.substring(0,2).toUpperCase()}
                            </div>
                            <div>
                                <div class="font-mono text-sm text-muted-foreground">Job ${truncatedId}</div>
                                <div class="flex items-center space-x-2 mt-1">
                                    <div class="flex items-center space-x-2 px-3 py-1.5 rounded-full border-2 text-sm font-medium ${statusClass} shadow-sm">
                                        ${statusIcon}
                                        <span>${statusText}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <button onclick="importManager.toggleJobDetails('${job_id}')" 
                        class="px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:bg-muted rounded-full transition-colors">
                        Dettagli →
                    </button>
                </div>
                
                ${progressSection}
                ${resultSection}
            </div>
        `;
    }

    toggleJobDetails(jobId) {
        // TODO: Implementare visualizzazione dettagli completi in modal
        console.log('Toggle details for job:', jobId);
    }

    updateJobStats(jobs) {
        const stats = {
            completed: jobs.filter(j => j.status === 'completed').length,
            running: jobs.filter(j => j.status === 'running').length,
            queued: jobs.filter(j => j.status === 'queued').length
        };
        
        this.updateStats(stats);
    }

    updateStats({ completed, running, queued }) {
        this.elements.completedCount.textContent = completed;
        this.elements.runningCount.textContent = running;
        this.elements.queuedCount.textContent = queued;
    }

    startPeriodicRefresh() {
        // Aggiorna ogni 2 secondi quando ci sono job attivi
        this.refreshInterval = setInterval(() => {
            this.loadJobs();
        }, 2000);
    }

    stopPeriodicRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    setSubmitLoading(loading) {
        const btn = this.elements.submitBtn;
        if (loading) {
            btn.disabled = true;
            btn.className = 'inline-flex items-center justify-center rounded-material bg-oneui-blue text-white hover:bg-oneui-darkblue h-11 px-6 py-2 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-oneui-blue focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-70 shadow-lg';
            btn.innerHTML = `
                <svg class="w-5 h-5 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                <span class="animate-pulse-soft">Elaborazione...</span>
            `;
        } else {
            btn.disabled = false;
            btn.className = 'inline-flex items-center justify-center rounded-material bg-primary text-primary-foreground hover:bg-primary/90 h-11 px-6 py-2 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 shadow-lg hover:shadow-xl';
            btn.innerHTML = `
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                </svg>
                🚀 Avvia Import
            `;
        }
    }

    setRefreshLoading(loading) {
        const btn = this.elements.refreshBtn;
        if (loading) {
            btn.disabled = true;
            btn.className = 'inline-flex items-center justify-center rounded-material border border-input bg-material-surfaceContainer hover:bg-accent hover:text-accent-foreground h-9 px-4 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50';
            btn.querySelector('svg').classList.add('animate-spin');
        } else {
            btn.disabled = false;
            btn.className = 'inline-flex items-center justify-center rounded-material border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 px-4 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:shadow-md';
            btn.querySelector('svg').classList.remove('animate-spin');
        }
    }

    showNotification(message, type = 'info') {
        // Notifiche migliorate con Material Design 3 styling
        const toast = document.createElement('div');
        
        let bgColor, textColor, icon, borderColor;
        switch (type) {
            case 'success':
                bgColor = 'bg-gradient-to-r from-green-500 to-green-600';
                textColor = 'text-white';
                icon = '✅';
                borderColor = 'border-green-400';
                break;
            case 'warning':
                bgColor = 'bg-gradient-to-r from-yellow-500 to-yellow-600';
                textColor = 'text-white';
                icon = '⚠️';
                borderColor = 'border-yellow-400';
                break;
            case 'destructive':
                bgColor = 'bg-gradient-to-r from-red-500 to-red-600';
                textColor = 'text-white';
                icon = '❌';
                borderColor = 'border-red-400';
                break;
            default:
                bgColor = 'bg-gradient-to-r from-blue-500 to-blue-600';
                textColor = 'text-white';
                icon = 'ℹ️';
                borderColor = 'border-blue-400';
        }

        toast.className = `fixed top-4 right-4 ${bgColor} ${textColor} px-5 py-4 rounded-material shadow-xl border-2 ${borderColor} z-50 max-w-sm transition-all duration-500 ease-out animate-slide-in backdrop-blur-sm`;
        toast.innerHTML = `
            <div class="flex items-center space-x-3">
                <div class="flex-shrink-0">
                    <span class="text-lg">${icon}</span>
                </div>
                <div class="flex-1">
                    <span class="text-sm font-medium leading-relaxed">${message}</span>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="flex-shrink-0 ml-2 opacity-70 hover:opacity-100 transition-opacity">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                </button>
            </div>
        `;

        document.body.appendChild(toast);

        // Auto rimozione dopo 5 secondi con animazione fluida
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(120%) scale(0.95)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 500);
        }, 5000);
    }
}

// Funzione per gestire il collapsible
function toggleCollapse(sectionId) {
    const section = document.getElementById(sectionId);
    const icon = document.getElementById(sectionId + 'Icon');
    
    if (!section || !icon) return;
    
    const isCollapsed = section.classList.contains('collapsed');
    
    if (isCollapsed) {
        // Espandi
        section.classList.remove('collapsed');
        icon.classList.remove('rotated');
        
        // Animazione smooth
        setTimeout(() => {
            section.style.maxHeight = section.scrollHeight + 'px';
        }, 10);
    } else {
        // Comprimi  
        section.style.maxHeight = section.scrollHeight + 'px';
        
        setTimeout(() => {
            section.classList.add('collapsed');
            icon.classList.add('rotated');
        }, 10);
    }
}

// Funzione per inizializzare lo stato dei collapsible
function initializeCollapsibleState() {
    // Il pannello principale inizia espanso
    const importPanel = document.getElementById('importPanel');
    
    if (importPanel) {
        importPanel.style.maxHeight = importPanel.scrollHeight + 'px';
    }
}

// Inizializza l'import manager quando il DOM è caricato
let importManager;
document.addEventListener('DOMContentLoaded', () => {
    importManager = new ImportManager();
    initializeCollapsibleState();
});

// Gestione cleanup quando la pagina viene chiusa
window.addEventListener('beforeunload', () => {
    if (importManager) {
        importManager.stopPeriodicRefresh();
    }
});
