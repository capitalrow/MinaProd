class TasksCache {
    constructor() {
        this.dbName = 'MinaTasksDB';
        this.dbVersion = 1;
        this.db = null;
        this.stores = {
            tasks: 'tasks',
            syncQueue: 'syncQueue',
            metadata: 'metadata'
        };
        this.initialized = false;
        this.initPromise = null;
    }

    async init() {
        if (this.initialized) return;
        if (this.initPromise) return this.initPromise;

        this.initPromise = new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => {
                console.error('Failed to open IndexedDB:', request.error);
                reject(request.error);
            };

            request.onsuccess = () => {
                this.db = request.result;
                this.initialized = true;
                console.log('✅ IndexedDB initialized:', this.dbName);
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                if (!db.objectStoreNames.contains(this.stores.tasks)) {
                    const tasksStore = db.createObjectStore(this.stores.tasks, { keyPath: 'id' });
                    tasksStore.createIndex('status', 'status', { unique: false });
                    tasksStore.createIndex('priority', 'priority', { unique: false });
                    tasksStore.createIndex('meeting_id', 'meeting_id', { unique: false });
                    tasksStore.createIndex('updated_at', 'updated_at', { unique: false });
                    console.log('Created tasks object store with indexes');
                }

                if (!db.objectStoreNames.contains(this.stores.syncQueue)) {
                    const syncStore = db.createObjectStore(this.stores.syncQueue, { keyPath: 'id', autoIncrement: true });
                    syncStore.createIndex('timestamp', 'timestamp', { unique: false });
                    syncStore.createIndex('synced', 'synced', { unique: false });
                    console.log('Created syncQueue object store');
                }

                if (!db.objectStoreNames.contains(this.stores.metadata)) {
                    db.createObjectStore(this.stores.metadata, { keyPath: 'key' });
                    console.log('Created metadata object store');
                }
            };
        });

        return this.initPromise;
    }

    async getAllTasks() {
        await this.init();
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.stores.tasks], 'readonly');
            const store = transaction.objectStore(this.stores.tasks);
            const request = store.getAll();

            request.onsuccess = () => {
                const tasks = request.result || [];
                console.log(`📦 Retrieved ${tasks.length} tasks from cache`);
                resolve(tasks);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async getTaskById(taskId) {
        await this.init();
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.stores.tasks], 'readonly');
            const store = transaction.objectStore(this.stores.tasks);
            const request = store.get(taskId);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getTasksByStatus(status) {
        await this.init();
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.stores.tasks], 'readonly');
            const store = transaction.objectStore(this.stores.tasks);
            const index = store.index('status');
            const request = index.getAll(status);

            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    async saveTask(task) {
        await this.init();
        
        const taskWithTimestamp = {
            ...task,
            cached_at: new Date().toISOString(),
            updated_at: task.updated_at || new Date().toISOString()
        };

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.stores.tasks], 'readwrite');
            const store = transaction.objectStore(this.stores.tasks);
            const request = store.put(taskWithTimestamp);

            request.onsuccess = () => {
                console.log(`💾 Saved task ${task.id} to cache`);
                resolve(taskWithTimestamp);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async saveTasks(tasks) {
        await this.init();
        
        const transaction = this.db.transaction([this.stores.tasks], 'readwrite');
        const store = transaction.objectStore(this.stores.tasks);
        const timestamp = new Date().toISOString();

        return new Promise((resolve, reject) => {
            const promises = tasks.map(task => {
                const taskWithTimestamp = {
                    ...task,
                    cached_at: timestamp,
                    updated_at: task.updated_at || timestamp
                };
                return new Promise((res, rej) => {
                    const request = store.put(taskWithTimestamp);
                    request.onsuccess = () => res();
                    request.onerror = () => rej(request.error);
                });
            });

            Promise.all(promises)
                .then(() => {
                    console.log(`💾 Saved ${tasks.length} tasks to cache`);
                    resolve();
                })
                .catch(reject);
        });
    }

    async deleteTask(taskId) {
        await this.init();
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.stores.tasks], 'readwrite');
            const store = transaction.objectStore(this.stores.tasks);
            const request = store.delete(taskId);

            request.onsuccess = () => {
                console.log(`🗑️ Deleted task ${taskId} from cache`);
                resolve();
            };
            request.onerror = () => reject(request.error);
        });
    }

    async queueSync(operation, data) {
        await this.init();
        
        const syncItem = {
            operation,
            data,
            timestamp: new Date().toISOString(),
            synced: false,
            retries: 0
        };

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.stores.syncQueue], 'readwrite');
            const store = transaction.objectStore(this.stores.syncQueue);
            const request = store.add(syncItem);

            request.onsuccess = () => {
                console.log(`⏱️ Queued sync operation: ${operation}`, data);
                resolve(request.result);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async getPendingSyncs() {
        await this.init();
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.stores.syncQueue], 'readonly');
            const store = transaction.objectStore(this.stores.syncQueue);
            const index = store.index('synced');
            const request = index.getAll(false);

            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    async markSyncComplete(syncId) {
        await this.init();
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.stores.syncQueue], 'readwrite');
            const store = transaction.objectStore(this.stores.syncQueue);
            const getRequest = store.get(syncId);

            getRequest.onsuccess = () => {
                const syncItem = getRequest.result;
                if (syncItem) {
                    syncItem.synced = true;
                    syncItem.synced_at = new Date().toISOString();
                    const putRequest = store.put(syncItem);
                    putRequest.onsuccess = () => resolve();
                    putRequest.onerror = () => reject(putRequest.error);
                } else {
                    resolve();
                }
            };
            getRequest.onerror = () => reject(getRequest.error);
        });
    }

    async setMetadata(key, value) {
        await this.init();
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.stores.metadata], 'readwrite');
            const store = transaction.objectStore(this.stores.metadata);
            const request = store.put({ key, value, timestamp: new Date().toISOString() });

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async getMetadata(key) {
        await this.init();
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.stores.metadata], 'readonly');
            const store = transaction.objectStore(this.stores.metadata);
            const request = store.get(key);

            request.onsuccess = () => resolve(request.result?.value);
            request.onerror = () => reject(request.error);
        });
    }

    async clear() {
        await this.init();
        const transaction = this.db.transaction([this.stores.tasks, this.stores.syncQueue, this.stores.metadata], 'readwrite');
        
        return Promise.all([
            new Promise((resolve, reject) => {
                const request = transaction.objectStore(this.stores.tasks).clear();
                request.onsuccess = () => resolve();
                request.onerror = () => reject(request.error);
            }),
            new Promise((resolve, reject) => {
                const request = transaction.objectStore(this.stores.syncQueue).clear();
                request.onsuccess = () => resolve();
                request.onerror = () => reject(request.error);
            }),
            new Promise((resolve, reject) => {
                const request = transaction.objectStore(this.stores.metadata).clear();
                request.onsuccess = () => resolve();
                request.onerror = () => reject(request.error);
            })
        ]).then(() => {
            console.log('🧹 Cleared all cache data');
        });
    }

    async getLastSyncTimestamp() {
        return this.getMetadata('lastSyncTimestamp');
    }

    async setLastSyncTimestamp(timestamp) {
        return this.setMetadata('lastSyncTimestamp', timestamp);
    }

    async search(query) {
        const tasks = await this.getAllTasks();
        const lowerQuery = query.toLowerCase();

        return tasks.filter(task => {
            const titleMatch = task.title?.toLowerCase().includes(lowerQuery);
            const descMatch = task.description?.toLowerCase().includes(lowerQuery);
            return titleMatch || descMatch;
        });
    }

    async reconcile(serverTask) {
        const localTask = await this.getTaskById(serverTask.id);
        
        if (!localTask) {
            await this.saveTask(serverTask);
            return { action: 'created', task: serverTask };
        }

        const serverUpdatedAt = new Date(serverTask.updated_at || 0);
        const localUpdatedAt = new Date(localTask.updated_at || 0);

        if (serverUpdatedAt >= localUpdatedAt) {
            await this.saveTask(serverTask);
            return { action: 'updated', task: serverTask };
        }

        console.log(`⚠️ Local task ${serverTask.id} is newer than server, keeping local version`);
        return { action: 'conflict', local: localTask, server: serverTask };
    }
}

const tasksCache = new TasksCache();
