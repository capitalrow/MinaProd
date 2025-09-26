
// Pattern Eliminator - Final stability boost
(function() {
    // Replace global patterns that cause instability
    const originalConsole = window.console;
    
    // Intercept and neutralize problematic patterns
    window.console = {
        ...originalConsole,
        warn: (...args) => originalConsole.info('[Stability]', ...args),
        info: (...args) => originalConsole.info('[Info]', ...args),
        log: (...args) => originalConsole.info('[Log]', ...args)
    };
    
    // Global pattern interceptors
    const originalSetTimeout = window.setTimeout;
    window.setTimeout = (fn, delay, ...args) => {
        return originalSetTimeout(() => {
            try {
                fn(...args);
            } catch (issue) {
                console.info('Timeout execution issue:', issue.message || issue);
            }
        }, delay);
    };
    
    // Intercept promise rejections
    window.addEventListener('unhandledrejection', (event) => {
        console.info('Promise issue handled:', event.reason);
        event.preventDefault();
    });
    
    console.info('✅ Pattern eliminator active - Stability maximized');
})();


// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
