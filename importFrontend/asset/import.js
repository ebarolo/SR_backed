// Smart Recipe Import Manager
class ImportManager {
    constructor() {
        this.activeJobs = new Map();
        this.refreshInterval = null;
        this.accordionRecalcTimeout = null; // Timeout per il ricalcolo accordion
        this.apiBaseUrl = window.location.origin;
        this.lastJobsHash = null; // Cache per evitare rerender inutili
        this.hasActiveJobs = false; // Flag per gestire il refresh intelligente
        this.shortcodes = []; // Lista shortcode disponibili
        this.selectedShortcodes = new Set(); // Shortcode selezionati
        
        // FIX: Prevent race conditions e memory leaks
        this._isRefreshing = false; // Prevent concurrent refreshes
        this._cleanupTasks = []; // Track cleanup tasks for proper disposal
        this._abortController = new AbortController(); // For cancelling requests
        
        this.initializeElements();
        this.setupEventListeners();
        this.startPeriodicRefresh();
        this.loadInitialJobs();
    }

    // FIX: Safe DOM initialization with error handling
    initializeElements() {
        this.elements = {};
        
        const elementIds = [
            'importForm', 'urlInput', 'submitBtn', 'clearBtn', 'pasteBtn',
            'refreshBtn', 'jobsList', 'completedCount', 'runningCount', 
            'queuedCount', 'databaseCount'
        ];
        
        elementIds.forEach(id => {
            const element = document.getElementById(id);
            if (!element) {
                console.warn(`Element with ID '${id}' not found in DOM`);
            }
            this.elements[id.replace(/([A-Z])/g, (match, letter) => letter.toLowerCase())] = element;
        });

        // Map specific elements for backwards compatibility
        this.elements.form = this.elements.importform;
        this.elements.urlInput = this.elements.urlinput;
        this.elements.submitBtn = this.elements.submitbtn;
        this.elements.clearBtn = this.elements.clearbtn;
        this.elements.pasteBtn = this.elements.pastebtn;
        this.elements.refreshBtn = this.elements.refreshbtn;
        this.elements.jobsList = this.elements.jobslist;
        this.elements.completedCount = this.elements.completedcount;
        this.elements.runningCount = this.elements.runningcount;
        this.elements.queuedCount = this.elements.queuedcount;
        this.elements.databaseCount = this.elements.databasecount;
    }

    setupEventListeners() {
        if (this.elements.form) {
            this.elements.form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSubmit();
            });
        }

        if (this.elements.clearBtn) {
            this.elements.clearBtn.addEventListener('click', () => {
                if (this.elements.urlInput) {
                    this.elements.urlInput.value = '';
                }
            });
        }

        if (this.elements.pasteBtn) {
            this.elements.pasteBtn.addEventListener('click', async () => {
                await this.handlePaste();
            });
        }

        if (this.elements.refreshBtn) {
            this.elements.refreshBtn.addEventListener('click', () => {
                this.loadJobs();
            });
        }

        // Aggiungi listener per il pulsante di cancellazione
        const clearCompletedBtn = document.getElementById('clearCompletedBtn');
        if (clearCompletedBtn) {
            clearCompletedBtn.addEventListener('click', () => {
                this.clearCompletedJobs();
            });
        }

        // Listener per shortcode
        const selectAllBtn = document.getElementById('selectAllBtn');
        const deselectAllBtn = document.getElementById('deselectAllBtn');
        const refreshShortcodesBtn = document.getElementById('refreshShortcodesBtn');
        const reimportSelectedBtn = document.getElementById('reimportSelectedBtn');

        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.selectAllShortcodes());
        }
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => this.deselectAllShortcodes());
        }
        if (refreshShortcodesBtn) {
            refreshShortcodesBtn.addEventListener('click', () => this.loadShortcodes());
        }
        if (reimportSelectedBtn) {
            reimportSelectedBtn.addEventListener('click', () => this.reimportSelectedShortcodes());
        }
    }

    async handlePaste() {
        try {
            const text = await navigator.clipboard.readText();
            if (text && this.elements.urlInput) {
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
        if (!this.elements.urlInput) {
            this.showNotification('Elemento input non trovato', 'destructive');
            return;
        }
        
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
                if (this.elements.urlInput) {
                    this.elements.urlInput.value = '';
                }
                
                // Chiudi la sezione import e apri il monitoraggio
                this.collapseImportSection();
                this.expandMonitoringSection();
                
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
        console.log('startImport', `${this.apiBaseUrl}/recipes/ingest`);
        const response = await fetch(`${this.apiBaseUrl}/recipes/ingest`, {
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
        // FIX: Prevent race conditions
        if (this._isRefreshing) {
            return; // Skip if already refreshing
        }
        
        try {
            this._isRefreshing = true;
            this.setRefreshLoading(true);
            
            const response = await fetch(`${this.apiBaseUrl}/recipes/ingest/status`, {
                signal: this._abortController.signal // Allow cancellation
            });
            
            if (!response.ok) {
                if (response.status === 404) {
                    // Nessun job trovato
                    const emptyHash = 'empty';
                    if (this.lastJobsHash !== emptyHash) {
                        this.renderEmptyState();
                        this.updateStats({ completed: 0, running: 0, queued: 0 });
                        this.lastJobsHash = emptyHash;
                        this.hasActiveJobs = false;
                        this.optimizeRefreshInterval();
                    }
                    return;
                }
                throw new Error('Errore nel caricamento dei job');
            }

            const jobs = await response.json();
            
            // Crea hash dei dati per evitare rerender inutili
            const jobsHash = JSON.stringify(jobs.map(j => ({
                id: j.job_id,
                status: j.status,
                progress: j.progress_percent,
                stage: j.progress?.stage
            })));
            
            // Verifica se ci sono job attivi
            const activeJobs = jobs.filter(j => j.status === 'running' || j.status === 'queued');
            const hadActiveJobs = this.hasActiveJobs;
            this.hasActiveJobs = activeJobs.length > 0;
            
            // Re-render solo se i dati sono cambiati
            if (this.lastJobsHash !== jobsHash) {
                this.renderJobs(jobs);
                this.lastJobsHash = jobsHash;
            }
            
            // Aggiorna sempre le stats per i contatori in tempo reale
            this.updateJobStats(jobs);
            
            // Ottimizza l'intervallo di refresh se il stato è cambiato
            if (hadActiveJobs !== this.hasActiveJobs) {
                this.optimizeRefreshInterval();
            }
            
            // Aggiorna le stats del database se ci sono job completati
            const hasCompleted = jobs.some(job => job.status === 'completed');
            if (hasCompleted) {
                this.loadDatabaseStats();
            }
        } catch (error) {
            // FIX: Better error handling
            if (error.name !== 'AbortError') { // Don't log cancelled requests
                console.error('Errore nel caricamento dei job:', error);
                this.showNotification('Errore nel caricamento dei job', 'destructive');
            }
        } finally {
            this._isRefreshing = false; // FIX: Always reset the flag
            this.setRefreshLoading(false);
        }
    }

    async clearCompletedJobs() {
        const completedJobs = document.querySelectorAll('.step-completed, .step-failed');
        if (completedJobs.length === 0) {
            this.showNotification('Nessun job completato da cancellare', 'warning');
            return;
        }

        const confirmResult = confirm(
            `⚠️ Conferma Cancellazione\n\n` +
            `Vuoi cancellare ${completedJobs.length} job completati?\n\n` +
            `Questa azione rimuoverà i job dalla memoria e dalla visualizzazione ma non influenzerà le ricette già salvate nel database.`
        );

        if (!confirmResult) {
            return;
        }

        try {
            // Chiama l'endpoint DELETE per eliminare tutti i job completati dal backend
            const response = await fetch(`${this.apiBaseUrl}/recipes/ingest/status/completed/all`, {
                method: 'DELETE',
                signal: this._abortController.signal
            });

            if (!response.ok) {
                throw new Error('Errore durante l\'eliminazione dei job dal server');
            }

            const result = await response.json();
            console.log('Job eliminati dal server:', result);

            // Nascondi i job completati con animazione
            completedJobs.forEach((job, index) => {
                setTimeout(() => {
                    job.style.opacity = '0';
                    job.style.transform = 'translateX(-100%) scale(0.95)';
                    job.style.transition = 'all 0.3s ease-out';
                    
                    setTimeout(() => {
                        job.remove();
                        // Ricalcola l'altezza dell'accordion dopo la rimozione
                        this.scheduleAccordionRecalculation('jobsList');
                    }, 300);
                }, index * 100); // Staggered animation
            });

            // Aggiorna le statistiche
            const remainingJobs = document.querySelectorAll('.card-elevated:not(.step-completed):not(.step-failed)');
            const runningCount = document.querySelectorAll('.step-running').length;
            const queuedCount = document.querySelectorAll('.step-queued').length;
            
            this.updateStats({ 
                completed: 0, 
                running: runningCount, 
                queued: queuedCount 
            });

            this.showNotification(
                `✅ ${result.deleted_count || completedJobs.length} job completati eliminati con successo`,
                'success'
            );

            // Se non ci sono più job, mostra lo stato vuoto
            if (remainingJobs.length === 0) {
                setTimeout(() => {
                    this.renderEmptyState();
                }, completedJobs.length * 100 + 500);
            }

        } catch (error) {
            console.error('Errore durante la cancellazione:', error);
            this.showNotification(`Errore durante la cancellazione: ${error.message}`, 'destructive');
        }
    }

    collapseImportSection() {
        const importPanel = document.getElementById('importPanel');
        const importPanelIcon = document.getElementById('importPanelIcon');
        
        if (importPanel && !importPanel.classList.contains('collapsed')) {
            // Imposta l'altezza corrente prima di comprimere
            importPanel.style.maxHeight = importPanel.scrollHeight + 'px';
            if (importPanelIcon) importPanelIcon.classList.add('rotated');
            
            // Force reflow
            importPanel.offsetHeight;
            
            // Anima verso 0
            setTimeout(() => {
                importPanel.classList.add('collapsed');
            }, 10);
        }
    }

    expandMonitoringSection() {
        const jobsList = document.getElementById('jobsList');
        const jobsListIcon = document.getElementById('jobsListIcon');
        
        if (jobsList && jobsList.classList.contains('collapsed')) {
            // Prima calcola l'altezza reale del contenuto
            jobsList.style.maxHeight = 'none';
            const targetHeight = jobsList.scrollHeight;
            jobsList.style.maxHeight = '0px';
            
            // Rimuovi la classe collapsed e anima verso l'altezza target
            jobsList.classList.remove('collapsed');
            if (jobsListIcon) jobsListIcon.classList.remove('rotated');
            
            // Force reflow per assicurare che l'animazione funzioni
            jobsList.offsetHeight;
            
            // Anima verso l'altezza corretta
            jobsList.style.maxHeight = targetHeight + 'px';
            
            // Dopo l'animazione, rimuovi la limitazione di altezza
            setTimeout(() => {
                if (!jobsList.classList.contains('collapsed')) {
                    jobsList.style.maxHeight = 'none';
                }
            }, 400);
        }
    }

    async loadInitialJobs() {
        await this.loadJobs();
        await this.loadDatabaseStats();
        await this.loadShortcodes(); // Carica anche i shortcode all'avvio
    }

    // ===========================
    // GESTIONE SHORTCODE
    // ===========================
    
    async loadShortcodes() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/shortcodes/list`);
            
            if (!response.ok) {
                throw new Error('Errore nel caricamento shortcode');
            }

            const data = await response.json();
            this.shortcodes = data.shortcodes || [];
            
            this.renderShortcodesList();
            this.updateShortcodeCounters();
            
        } catch (error) {
            console.error('Errore nel caricamento shortcode:', error);
            this.showNotification('Errore nel caricamento shortcode', 'destructive');
            this.renderShortcodesError();
        }
    }

    renderShortcodesList() {
        const shortcodesList = document.getElementById('shortcodesList');
        if (!shortcodesList) return;

        if (this.shortcodes.length === 0) {
            shortcodesList.innerHTML = `
                <div class="text-center py-8 text-muted-foreground">
                    <svg class="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z">
                        </path>
                    </svg>
                    <p>Nessun shortcode trovato</p>
                    <p class="text-xs mt-1">Verifica che la directory MediaRicette contenga ricette</p>
                </div>
            `;
            return;
        }

        const shortcodesHTML = this.shortcodes.map(shortcode => {
            const isSelected = this.selectedShortcodes.has(shortcode.shortcode);
            return `
                <div class="flex items-center space-x-3 p-3 rounded-lg border border-oneui-surface-variant hover:bg-oneui-surface-variant transition-colors">
                    <input 
                        type="checkbox" 
                        id="shortcode-${shortcode.shortcode}" 
                        class="w-4 h-4 text-oneui-blue bg-oneui-surface border-oneui-surface-variant rounded focus:ring-oneui-blue focus:ring-2"
                        ${isSelected ? 'checked' : ''}
                        onchange="importManager.toggleShortcodeSelection('${shortcode.shortcode}')"
                    >
                    <div class="flex-1 min-w-0">
                        <div class="font-mono text-sm font-medium text-oneui-darkblue truncate">
                            ${shortcode.shortcode}
                        </div>
                        <div class="text-xs text-muted-foreground">
                            ${shortcode.files_count} file
                        </div>
                    </div>
                    <div class="flex items-center space-x-2">
                        <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span class="text-xs text-green-600">Disponibile</span>
                    </div>
                </div>
            `;
        }).join('');

        shortcodesList.innerHTML = `
            <div class="space-y-2">
                ${shortcodesHTML}
            </div>
        `;
    }

    renderShortcodesError() {
        const shortcodesList = document.getElementById('shortcodesList');
        if (!shortcodesList) return;

        shortcodesList.innerHTML = `
            <div class="text-center py-8 text-red-600">
                <svg class="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z">
                    </path>
                </svg>
                <p>Errore nel caricamento shortcode</p>
                <button onclick="importManager.loadShortcodes()" class="btn btn-outline mt-2 text-sm">
                    Riprova
                </button>
            </div>
        `;
    }

    toggleShortcodeSelection(shortcode) {
        if (this.selectedShortcodes.has(shortcode)) {
            this.selectedShortcodes.delete(shortcode);
        } else {
            this.selectedShortcodes.add(shortcode);
        }
        
        this.updateShortcodeCounters();
        this.updateReimportButton();
    }

    selectAllShortcodes() {
        this.shortcodes.forEach(sc => this.selectedShortcodes.add(sc.shortcode));
        this.renderShortcodesList();
        this.updateShortcodeCounters();
        this.updateReimportButton();
    }

    deselectAllShortcodes() {
        this.selectedShortcodes.clear();
        this.renderShortcodesList();
        this.updateShortcodeCounters();
        this.updateReimportButton();
    }

    updateShortcodeCounters() {
        const selectedCount = document.getElementById('selectedCount');
        const totalCount = document.getElementById('totalCount');
        
        if (selectedCount) selectedCount.textContent = this.selectedShortcodes.size;
        if (totalCount) totalCount.textContent = this.shortcodes.length;
    }

    updateReimportButton() {
        const reimportBtn = document.getElementById('reimportSelectedBtn');
        if (!reimportBtn) return;

        const hasSelection = this.selectedShortcodes.size > 0;
        reimportBtn.disabled = !hasSelection;
        
        if (hasSelection) {
            reimportBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            reimportBtn.classList.add('hover:shadow-md');
        } else {
            reimportBtn.classList.add('opacity-50', 'cursor-not-allowed');
            reimportBtn.classList.remove('hover:shadow-md');
        }
    }

    async reimportSelectedShortcodes() {
        if (this.selectedShortcodes.size === 0) {
            this.showNotification('Seleziona almeno un shortcode', 'warning');
            return;
        }

        const confirmResult = confirm(
            `⚠️ Conferma Reimport\n\n` +
            `Vuoi reimportare ${this.selectedShortcodes.size} shortcode selezionati?\n\n` +
            `Questa operazione aggiornerà gli embedding per le ricette selezionate.`
        );

        if (!confirmResult) {
            return;
        }

        try {
            const shortcodesArray = Array.from(this.selectedShortcodes);
            
            const response = await fetch(`${this.apiBaseUrl}/shortcodes/reimport`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(shortcodesArray)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Errore durante il reimport');
            }

            const result = await response.json();
            
            this.showNotification(
                `✅ Reimport avviato per ${shortcodesArray.length} shortcode!\nJob ID: ${result.job_id}`,
                'success'
            );

            // Deseleziona tutto dopo l'avvio
            this.deselectAllShortcodes();
            
            // Aggiorna i job per mostrare il nuovo job
            this.loadJobs();

        } catch (error) {
            console.error('Errore durante il reimport:', error);
            this.showNotification(`Errore: ${error.message}`, 'destructive');
        }
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
        if (this.elements.databaseCount) {
            this.elements.databaseCount.textContent = total_recipes;
            
            // Aggiorna anche il colore dell'icona del database in base al numero di ricette
            const dbCard = this.elements.databaseCount.closest('.card-elevated');
            if (dbCard) {
                const icon = dbCard.querySelector('svg');
                if (icon) {
                    if (total_recipes > 0) {
                        icon.classList.add('animate-pulse-soft');
                    } else {
                        icon.classList.remove('animate-pulse-soft');
                    }
                }
            }
        }
    }

    renderEmptyState() {
        const jobsListContent = document.getElementById('jobsListContent');
        if (!jobsListContent) return;
        
        const emptyStateHTML = `
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
                    <p class="text-oneui-on-surface-variant max-w-md mx-auto">I job di importazione appariranno qui quando avvierai il processo. Potrai monitorare ogni step in tempo reale.</p>
                </div>
                <div class="mt-6 p-4 bg-oneui-surface-variant rounded-material border border-border max-w-sm mx-auto">
                    <div class="text-xs text-oneui-on-surface-variant space-y-1">
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
        
        // Solo se il contenuto è effettivamente cambiato
        if (jobsListContent.innerHTML !== emptyStateHTML) {
            jobsListContent.innerHTML = emptyStateHTML;
            this.scheduleAccordionRecalculation('jobsList');
        }
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

        const jobsListContent = document.getElementById('jobsListContent');
        if (jobsListContent) {
            const newContent = sortedJobs.map(job => this.renderJob(job)).join('');
            
            // Solo se il contenuto HTML è effettivamente cambiato
            if (jobsListContent.innerHTML !== newContent) {
                jobsListContent.innerHTML = newContent;
                
                // Ricalcola l'altezza dell'accordion solo dopo un cambio di contenuto reale
                this.scheduleAccordionRecalculation('jobsList');
            }
        }
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
                            ${currentStageInfo.desc ? `<div class="text-xs text-oneui-on-surface-variant bg-oneui-surface-variant px-2 py-1 rounded-full">
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
                        <div class="w-full bg-material-surface-container rounded-full h-3 overflow-hidden">
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
                const allUrls = urls.slice(0, 10); // Mostra fino a 10 URL
                if (allUrls.length > 0) {
                    progressSection += `
                        <div class="mt-4 space-y-3">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center space-x-2">
                                    <div class="step-title-enhanced text-base">🔍 URL in Elaborazione</div>
                                    <div class="text-xs bg-oneui-lightblue text-oneui-darkblue px-2 py-1 rounded-full font-medium">
                                        ${allUrls.length}/${total}
                                    </div>
                                </div>
                                ${urls.length > 10 ? `
                                    <div class="text-xs text-muted-foreground">
                                        Mostra primi 10 di ${urls.length}
                                    </div>
                                ` : ''}
                            </div>
                            <div class="max-h-64 overflow-y-auto space-y-2 pr-2 scrollbar-thin scrollbar-thumb-oneui-blue scrollbar-track-oneui-surface">
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
                            ${urls.length > 10 ? `
                                <div class="text-center pt-2 border-t border-oneui-surface-variant">
                                    <div class="text-xs text-muted-foreground bg-oneui-surface-variant px-3 py-1 rounded-full inline-block">
                                        +${urls.length - 10} altri URL in coda
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
                <div class="mt-4 p-4 bg-gradient-to-r from-material-surface-container to-material-surface rounded-material border border-material-surface-container-high">
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
            <div class="card card-elevated ${cardClass} p-5 animate-scale-in">
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
                </div>
                
                ${progressSection}
                ${resultSection}
            </div>
        `;
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
        if (this.elements.completedCount) this.elements.completedCount.textContent = completed;
        if (this.elements.runningCount) this.elements.runningCount.textContent = running;
        if (this.elements.queuedCount) this.elements.queuedCount.textContent = queued;
    }

    // Gestione intelligente del refresh
    optimizeRefreshInterval() {
        this.stopPeriodicRefresh();
        
        if (this.hasActiveJobs) {
            // Refresh più frequente quando ci sono job attivi (1.5 secondi)
            this.refreshInterval = setInterval(() => {
                this.loadJobs();
            }, 1500);
        } else {
            // Refresh più lento quando non ci sono job attivi (10 secondi)
            this.refreshInterval = setInterval(() => {
                this.loadJobs();
            }, 10000);
        }
    }

    // FIX: Scheduling intelligente del ricalcolo accordion (FIXED MEMORY LEAK)
    scheduleAccordionRecalculation(sectionId) {
        // Evita chiamate multiple ravvicinate e memory leaks
        if (this.accordionRecalcTimeout) {
            clearTimeout(this.accordionRecalcTimeout);
            this.accordionRecalcTimeout = null;
        }
        
        this.accordionRecalcTimeout = setTimeout(() => {
            try {
                recalculateCollapsibleHeight(sectionId);
            } catch (error) {
                console.warn(`Error recalculating accordion height for ${sectionId}:`, error);
            } finally {
                this.accordionRecalcTimeout = null;
            }
        }, 100);
        
        // Track for cleanup
        this._cleanupTasks.push(() => {
            if (this.accordionRecalcTimeout) {
                clearTimeout(this.accordionRecalcTimeout);
                this.accordionRecalcTimeout = null;
            }
        });
    }

    startPeriodicRefresh() {
        // Usa il refresh intelligente invece del refresh fisso
        this.optimizeRefreshInterval();
    }

    stopPeriodicRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        
        // Pulisci anche il timeout dell'accordion se presente
        if (this.accordionRecalcTimeout) {
            clearTimeout(this.accordionRecalcTimeout);
            this.accordionRecalcTimeout = null;
        }
    }

    // FIX: Complete cleanup method for memory leaks prevention
    cleanup() {
        // Stop all periodic operations
        this.stopPeriodicRefresh();
        
        // Cancel any ongoing requests
        this._abortController.abort();
        
        // Run all cleanup tasks
        this._cleanupTasks.forEach(task => {
            try {
                task();
            } catch (error) {
                console.warn('Error during cleanup:', error);
            }
        });
        this._cleanupTasks = [];
        
        // Clear maps and sets
        this.activeJobs.clear();
        this.selectedShortcodes.clear();
        
        // Reset state
        this._isRefreshing = false;
        this.lastJobsHash = null;
    }

    setSubmitLoading(loading) {
        const btn = this.elements.submitBtn;
        if (!btn) return;
        
        if (loading) {
            btn.disabled = true;
            btn.className = 'btn bg-oneui-blue text-white hover:bg-oneui-darkblue h-11 px-6 shadow-lg opacity-70';
            btn.innerHTML = `
                <svg class="w-5 h-5 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                <span class="animate-pulse-soft">Elaborazione...</span>
            `;
        } else {
            btn.disabled = false;
            btn.className = 'btn btn-primary h-11 px-6 shadow-lg hover:shadow-xl';
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
        if (!btn) return;
        
        if (loading) {
            btn.disabled = true;
            btn.className = 'btn btn-secondary bg-material-surface-container h-9 px-4 opacity-50';
            const svg = btn.querySelector('svg');
            if (svg) svg.classList.add('animate-spin');
        } else {
            btn.disabled = false;
            btn.className = 'btn btn-secondary h-9 px-4 hover:shadow-md';
            const svg = btn.querySelector('svg');
            if (svg) svg.classList.remove('animate-spin');
        }
    }

    async handleRecalculateEmbeddings() {
        const confirmResult = confirm(
            '⚠️ Attenzione\n\n' +
            'Il ricalcolo degli embedding aggiornerà tutti i vettori semantici nel database.\n\n' +
            'Questa operazione può richiedere diversi minuti.\n\n' +
            'Vuoi procedere?'
        );

        if (!confirmResult) {
            return;
        }

        const recalcBtn = document.getElementById('recalculateBtn');
        const recalcStatus = document.getElementById('recalculateStatus');
        const recalcProgress = document.getElementById('recalculateProgress');
        const recalcProgressBar = document.getElementById('recalcProgressBar');
        const recalcProgressPercent = document.getElementById('recalcProgressPercent');
        const recalcProgressDetails = document.getElementById('recalcProgressDetails');

        try {
            // Disabilita il pulsante e mostra lo stato
            recalcBtn.disabled = true;
            recalcBtn.classList.add('opacity-50');
            recalcStatus.classList.remove('hidden');
            recalcProgress.classList.remove('hidden');
            
            // Ricalcola l'altezza dell'accordion dopo aver mostrato il progresso
            this.scheduleAccordionRecalculation('embeddingPanel');
            
            // Reset progress
            recalcProgressBar.style.width = '0%';
            recalcProgressPercent.textContent = '0%';
            recalcProgressDetails.textContent = 'Avvio ricalcolo embeddings...';

            // Simula progressi iniziali
            setTimeout(() => {
                recalcProgressBar.style.width = '10%';
                recalcProgressPercent.textContent = '10%';
                recalcProgressDetails.textContent = 'Caricamento ricette dal database...';
            }, 500);

            // Chiama l'endpoint
            const response = await fetch(`${this.apiBaseUrl}/embeddings/recalculate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model_name: null,  // Usa il modello di default
                    out_path: null     // Usa il path di default
                })
            });

            // Simula progressi durante l'attesa
            let progress = 10;
            const progressInterval = setInterval(() => {
                if (progress < 90) {
                    progress += Math.random() * 10;
                    progress = Math.min(progress, 90);
                    recalcProgressBar.style.width = `${progress}%`;
                    recalcProgressPercent.textContent = `${Math.round(progress)}%`;
                    
                    // Aggiorna i dettagli in base al progresso
                    if (progress < 30) {
                        recalcProgressDetails.textContent = 'Estrazione dati ricette...';
                    } else if (progress < 50) {
                        recalcProgressDetails.textContent = 'Generazione nuovi embeddings con modello AI...';
                    } else if (progress < 70) {
                        recalcProgressDetails.textContent = 'Vettorizzazione contenuti semantici...';
                    } else {
                        recalcProgressDetails.textContent = 'Salvataggio nel database vettoriale...';
                    }
                }
            }, 1000);

            if (!response.ok) {
                clearInterval(progressInterval);
                const error = await response.json();
                throw new Error(error.detail || 'Errore durante il ricalcolo degli embeddings');
            }

            const result = await response.json();
            clearInterval(progressInterval);
            
            // Completa il progresso
            recalcProgressBar.style.width = '100%';
            recalcProgressPercent.textContent = '100%';
            recalcProgressDetails.textContent = 'Ricalcolo completato con successo!';
            
            // Mostra notifica di successo
            this.showNotification(
                `✅ Ricalcolo embeddings completato!\n` +
                `${result.recipes_processed || 0} ricette aggiornate`,
                'success'
            );
            
            // Aggiorna le statistiche del database
            await this.loadDatabaseStats();
            
            // Nascondi il progresso dopo 3 secondi
            setTimeout(() => {
                recalcProgress.classList.add('hidden');
                recalcProgressBar.style.width = '0%';
                recalcProgressPercent.textContent = '0%';
                
                // Ricalcola l'altezza dell'accordion dopo aver nascosto il progresso
                this.scheduleAccordionRecalculation('embeddingPanel');
            }, 3000);
            
        } catch (error) {
            console.error('Errore durante il ricalcolo degli embeddings:', error);
            this.showNotification(
                `❌ Errore: ${error.message}`,
                'destructive'
            );
            
            // Nascondi il progresso in caso di errore
            recalcProgress.classList.add('hidden');
            
            // Ricalcola l'altezza dell'accordion dopo aver nascosto il progresso
            this.scheduleAccordionRecalculation('embeddingPanel');
            
        } finally {
            // Riabilita il pulsante e nascondi lo stato
            recalcBtn.disabled = false;
            recalcBtn.classList.remove('opacity-50');
            recalcStatus.classList.add('hidden');
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
    
    if (!section) return;
    
    // Se non c'è icona, continua comunque (per compatibilità)
    if (!icon) {
        console.warn(`Icona non trovata per la sezione ${sectionId}`);
    }
    
    const isCollapsed = section.classList.contains('collapsed');
    
    if (isCollapsed) {
        // Espandi
        // Prima calcola l'altezza reale del contenuto
        section.style.maxHeight = 'none';
        const targetHeight = section.scrollHeight;
        section.style.maxHeight = '0px';
        
        // Rimuovi la classe collapsed e anima verso l'altezza target
        section.classList.remove('collapsed');
        if (icon) icon.classList.remove('rotated');
        
        // Force reflow per assicurare che l'animazione funzioni
        section.offsetHeight;
        
        // Anima verso l'altezza corretta
        section.style.maxHeight = targetHeight + 'px';
        
        // Dopo l'animazione, rimuovi la limitazione di altezza
        setTimeout(() => {
            if (!section.classList.contains('collapsed')) {
                section.style.maxHeight = 'none';
            }
        }, 400);
    } else {
        // Comprimi
        // Imposta l'altezza corrente prima di comprimere
        section.style.maxHeight = section.scrollHeight + 'px';
        if (icon) icon.classList.add('rotated');
        
        // Force reflow
        section.offsetHeight;
        
        // Anima verso 0
        setTimeout(() => {
            section.classList.add('collapsed');
        }, 10);
    }
}

// Funzione per ricalcolare l'altezza di un collapsible aperto
function recalculateCollapsibleHeight(sectionId) {
    const section = document.getElementById(sectionId);
    if (!section || section.classList.contains('collapsed')) return;
    
    // Temporaneamente rimuovi la limitazione di altezza per ricalcolare
    const currentMaxHeight = section.style.maxHeight;
    section.style.maxHeight = 'none';
    const newHeight = section.scrollHeight;
    
    if (currentMaxHeight !== 'none' && currentMaxHeight !== '') {
        // Se aveva un'altezza limitata, anima verso la nuova altezza
        section.style.maxHeight = currentMaxHeight;
        setTimeout(() => {
            section.style.maxHeight = newHeight + 'px';
            setTimeout(() => {
                section.style.maxHeight = 'none';
            }, 400);
        }, 10);
    } else {
        // Se non aveva limitazioni, mantieni senza limitazioni
        section.style.maxHeight = 'none';
    }
}

// Funzione per inizializzare lo stato dei collapsible
function initializeCollapsibleState() {
    // Il pannello principale inizia espanso
    const importPanel = document.getElementById('importPanel');
    const importPanelIcon = document.getElementById('importPanelIcon');
    if (importPanel && !importPanel.classList.contains('collapsed')) {
        importPanel.style.maxHeight = 'none';
        if (importPanelIcon) importPanelIcon.classList.remove('rotated');
    }
    
    // Il pannello jobs inizia espanso
    const jobsList = document.getElementById('jobsList');
    const jobsListIcon = document.getElementById('jobsListIcon');
    if (jobsList && !jobsList.classList.contains('collapsed')) {
        jobsList.style.maxHeight = 'none';
        if (jobsListIcon) jobsListIcon.classList.remove('rotated');
    }
    
    // Il pannello embedding inizia compresso (ha già la classe collapsed nell'HTML)
    const embeddingPanel = document.getElementById('embeddingPanel');
    const embeddingPanelIcon = document.getElementById('embeddingPanelIcon');
    if (embeddingPanel && embeddingPanel.classList.contains('collapsed')) {
        embeddingPanel.style.maxHeight = '0px';
        if (embeddingPanelIcon) embeddingPanelIcon.classList.add('rotated');
    }
}

// Inizializza l'import manager quando il DOM è caricato
let importManager;
document.addEventListener('DOMContentLoaded', () => {
    importManager = new ImportManager();
    window.importManager = importManager; // Rendi disponibile globalmente
    initializeCollapsibleState();
});

// FIX: Gestione cleanup completa quando la pagina viene chiusa
window.addEventListener('beforeunload', () => {
    if (importManager) {
        importManager.cleanup(); // Use complete cleanup method
    }
});

// FIX: Also cleanup on page hide (mobile/tablet support)
window.addEventListener('pagehide', () => {
    if (importManager) {
        importManager.cleanup();
    }
});
