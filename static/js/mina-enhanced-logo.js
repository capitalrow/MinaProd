// Mina Enhanced Logo Component - Premium Audio-Focused Design
// Based on reference image: Purple gradient app icon with sophisticated 3D audio wave bars

class MinaEnhancedLogo {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            size: 200,
            
            // Enhanced Purple Gradient System (matching reference image)
            colors: {
                primary: {
                    gradient: [
                        "#E879F9", // Bright purple highlight
                        "#D946EF", // Vibrant magenta
                        "#C026D3", // Rich purple
                        "#A21CAF", // Deep purple
                        "#86198F", // Dark purple
                        "#701A75", // Very dark purple
                        "#581C87"  // Purple-black depth
                    ],
                    glow: "#E879F9",
                    highlight: "#F3E8FF",
                    shadow: "#1E1B4B",
                    glass: "rgba(248, 250, 255, 0.2)"
                },
                
                // Audio wave specific colors
                audio: {
                    primary: "#E879F9",
                    secondary: "#C026D3", 
                    accent: "#A21CAF",
                    metallic: "#F8FAFF",
                    chrome: "#E2E8F0"
                }
            },
            
            // Audio wave configuration
            audioWaves: {
                count: 3,
                heights: [0.6, 0.4, 0.6], // Relative heights
                width: 0.08, // Relative to icon size
                gap: 0.12, // Gap between bars
                borderRadius: 0.5, // Rounded edges
                connector: {
                    height: 0.04,
                    opacity: 0.7
                }
            },
            
            // Animation settings
            animation: {
                breatheDuration: 8,
                pulseDuration: 4,
                waveDuration: 3,
                enabled: true
            },
            
            showWordmark: true,
            wordmarkSize: 48,
            ...options
        };
        
        this.init();
    }
    
    init() {
        this.createPremiumAudioIcon();
        if (this.options.showWordmark) {
            this.createEnhancedWordmark();
        }
        this.setupAnimations();
    }
    
    createPremiumAudioIcon() {
        const { size, colors } = this.options;
        
        // Main container with premium styling
        const container = document.createElement('div');
        container.className = 'mina-enhanced-logo-container';
        container.style.cssText = `
            width: ${size}px;
            height: ${size}px;
            position: relative;
            filter: drop-shadow(0 20px 60px rgba(139, 69, 255, 0.3)) 
                   drop-shadow(0 8px 32px rgba(30, 27, 75, 0.4));
            transform-style: preserve-3d;
            perspective: 1000px;
        `;
        
        // Create the premium SVG icon
        const svg = this.createPremiumSVG(size);
        container.appendChild(svg);
        
        this.container.appendChild(container);
        this.iconContainer = container;
    }
    
    createPremiumSVG(size) {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', size);
        svg.setAttribute('height', size);
        svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
        svg.style.cssText = 'display: block; overflow: visible;';
        
        // Create advanced defs
        const defs = this.createAdvancedDefs(size);
        svg.appendChild(defs);
        
        // Create premium app icon background (squircle)
        const background = this.createPremiumBackground(size);
        svg.appendChild(background);
        
        // Create sophisticated audio wave system
        const audioWaves = this.createSophisticatedAudioWaves(size);
        svg.appendChild(audioWaves);
        
        // Add premium glass overlay
        const glassOverlay = this.createGlassOverlay(size);
        svg.appendChild(glassOverlay);
        
        return svg;
    }
    
    createAdvancedDefs(size) {
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const { colors } = this.options;
        
        // Premium purple gradient for background
        const bgGradient = document.createElementNS('http://www.w3.org/2000/svg', 'radialGradient');
        const bgId = `premiumPurpleGradient_${Math.random().toString(36).substr(2, 9)}`;
        bgGradient.setAttribute('id', bgId);
        bgGradient.setAttribute('cx', '25%');
        bgGradient.setAttribute('cy', '15%');
        bgGradient.setAttribute('r', '95%');
        
        const bgStops = [
            { offset: '0%', color: colors.primary.gradient[0], opacity: '1' },
            { offset: '20%', color: colors.primary.gradient[1], opacity: '1' },
            { offset: '40%', color: colors.primary.gradient[2], opacity: '1' },
            { offset: '60%', color: colors.primary.gradient[3], opacity: '1' },
            { offset: '80%', color: colors.primary.gradient[4], opacity: '1' },
            { offset: '95%', color: colors.primary.gradient[5], opacity: '1' },
            { offset: '100%', color: colors.primary.gradient[6], opacity: '1' }
        ];
        
        bgStops.forEach(stop => {
            const stopEl = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stopEl.setAttribute('offset', stop.offset);
            stopEl.setAttribute('stop-color', stop.color);
            stopEl.setAttribute('stop-opacity', stop.opacity);
            bgGradient.appendChild(stopEl);
        });
        
        // Audio wave metallic gradient
        const waveGradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        const waveId = `audioWaveGradient_${Math.random().toString(36).substr(2, 9)}`;
        waveGradient.setAttribute('id', waveId);
        waveGradient.setAttribute('x1', '0%');
        waveGradient.setAttribute('y1', '0%');
        waveGradient.setAttribute('x2', '100%');
        waveGradient.setAttribute('y2', '100%');
        
        const waveStops = [
            { offset: '0%', color: colors.primary.highlight, opacity: '0.95' },
            { offset: '25%', color: colors.audio.metallic, opacity: '1' },
            { offset: '50%', color: colors.audio.primary, opacity: '1' },
            { offset: '75%', color: colors.audio.secondary, opacity: '1' },
            { offset: '100%', color: colors.audio.accent, opacity: '0.9' }
        ];
        
        waveStops.forEach(stop => {
            const stopEl = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stopEl.setAttribute('offset', stop.offset);
            stopEl.setAttribute('stop-color', stop.color);
            stopEl.setAttribute('stop-opacity', stop.opacity);
            waveGradient.appendChild(stopEl);
        });
        
        // Premium 3D shadow filter
        const shadowFilter = this.createPremium3DShadowFilter();
        
        // Glass morphism filter
        const glassFilter = this.createGlassMorphismFilter();
        
        defs.appendChild(bgGradient);
        defs.appendChild(waveGradient);
        defs.appendChild(shadowFilter);
        defs.appendChild(glassFilter);
        
        // Store IDs for later use
        this.gradientIds = { background: bgId, waves: waveId };
        this.filterIds = { shadow: shadowFilter.getAttribute('id'), glass: glassFilter.getAttribute('id') };
        
        return defs;
    }
    
    createPremium3DShadowFilter() {
        const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        const filterId = `premium3DShadow_${Math.random().toString(36).substr(2, 9)}`;
        filter.setAttribute('id', filterId);
        filter.setAttribute('x', '-150%');
        filter.setAttribute('y', '-150%');
        filter.setAttribute('width', '400%');
        filter.setAttribute('height', '400%');
        
        // Deep shadow
        const blur1 = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        blur1.setAttribute('in', 'SourceAlpha');
        blur1.setAttribute('stdDeviation', '8');
        blur1.setAttribute('result', 'deepBlur');
        
        const offset1 = document.createElementNS('http://www.w3.org/2000/svg', 'feOffset');
        offset1.setAttribute('in', 'deepBlur');
        offset1.setAttribute('dx', '6');
        offset1.setAttribute('dy', '10');
        offset1.setAttribute('result', 'deepOffset');
        
        const colorMatrix1 = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
        colorMatrix1.setAttribute('in', 'deepOffset');
        colorMatrix1.setAttribute('type', 'matrix');
        colorMatrix1.setAttribute('values', '0.3 0.1 0.6 0 0  0.1 0 0.4 0 0  0.6 0.2 0.8 0 0  0 0 0 0.4 0');
        colorMatrix1.setAttribute('result', 'deepShadow');
        
        // Close shadow
        const blur2 = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        blur2.setAttribute('in', 'SourceAlpha');
        blur2.setAttribute('stdDeviation', '4');
        blur2.setAttribute('result', 'closeBlur');
        
        const offset2 = document.createElementNS('http://www.w3.org/2000/svg', 'feOffset');
        offset2.setAttribute('in', 'closeBlur');
        offset2.setAttribute('dx', '3');
        offset2.setAttribute('dy', '5');
        offset2.setAttribute('result', 'closeOffset');
        
        const colorMatrix2 = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
        colorMatrix2.setAttribute('in', 'closeOffset');
        colorMatrix2.setAttribute('type', 'matrix');
        colorMatrix2.setAttribute('values', '0.4 0.2 0.7 0 0  0.2 0.1 0.5 0 0  0.7 0.3 0.9 0 0  0 0 0 0.3 0');
        colorMatrix2.setAttribute('result', 'closeShadow');
        
        // Merge shadows
        const merge = document.createElementNS('http://www.w3.org/2000/svg', 'feMerge');
        const mergeNode1 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        mergeNode1.setAttribute('in', 'deepShadow');
        const mergeNode2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        mergeNode2.setAttribute('in', 'closeShadow');
        const mergeNode3 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        mergeNode3.setAttribute('in', 'SourceGraphic');
        
        merge.appendChild(mergeNode1);
        merge.appendChild(mergeNode2);
        merge.appendChild(mergeNode3);
        
        filter.appendChild(blur1);
        filter.appendChild(offset1);
        filter.appendChild(colorMatrix1);
        filter.appendChild(blur2);
        filter.appendChild(offset2);
        filter.appendChild(colorMatrix2);
        filter.appendChild(merge);
        
        return filter;
    }
    
    createGlassMorphismFilter() {
        const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        const filterId = `glassMorphism_${Math.random().toString(36).substr(2, 9)}`;
        filter.setAttribute('id', filterId);
        filter.setAttribute('x', '-50%');
        filter.setAttribute('y', '-50%');
        filter.setAttribute('width', '200%');
        filter.setAttribute('height', '200%');
        
        const blur = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        blur.setAttribute('in', 'SourceGraphic');
        blur.setAttribute('stdDeviation', '2');
        blur.setAttribute('result', 'glassBlur');
        
        filter.appendChild(blur);
        
        return filter;
    }
    
    createPremiumBackground(size) {
        // Create premium squircle path (app icon style)
        const squirclePath = this.createSquirclePath(size);
        
        const background = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        background.setAttribute('d', squirclePath);
        background.setAttribute('fill', `url(#${this.gradientIds.background})`);
        background.setAttribute('filter', `url(#${this.filterIds.shadow})`);
        background.setAttribute('stroke', 'rgba(255, 255, 255, 0.2)');
        background.setAttribute('stroke-width', '1');
        
        return background;
    }
    
    createSquirclePath(size) {
        // Premium squircle (superellipse) for app icon look
        const radius = size * 0.15; // Corner radius
        const padding = size * 0.08;
        const width = size - (padding * 2);
        const height = size - (padding * 2);
        const x = padding;
        const y = padding;
        
        return `
            M ${x + radius},${y}
            L ${x + width - radius},${y}
            Q ${x + width},${y} ${x + width},${y + radius}
            L ${x + width},${y + height - radius}
            Q ${x + width},${y + height} ${x + width - radius},${y + height}
            L ${x + radius},${y + height}
            Q ${x},${y + height} ${x},${y + height - radius}
            L ${x},${y + radius}
            Q ${x},${y} ${x + radius},${y}
            Z
        `;
    }
    
    createSophisticatedAudioWaves(size) {
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        const { audioWaves, colors } = this.options;
        
        // Calculate dimensions
        const waveAreaSize = size * 0.5; // Audio waves take up 50% of icon
        const waveWidth = waveAreaSize * audioWaves.width;
        const waveGap = waveAreaSize * audioWaves.gap;
        const totalWaveWidth = (waveWidth * audioWaves.count) + (waveGap * (audioWaves.count - 1));
        
        // Center the wave group
        const waveStartX = (size - totalWaveWidth) / 2;
        const waveBaseY = size * 0.65; // Base position for waves
        
        // Create connector line
        const connector = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        connector.setAttribute('x', waveStartX - (waveGap * 0.3));
        connector.setAttribute('y', waveBaseY + (waveAreaSize * 0.1));
        connector.setAttribute('width', totalWaveWidth + (waveGap * 0.6));
        connector.setAttribute('height', waveAreaSize * audioWaves.connector.height);
        connector.setAttribute('rx', (waveAreaSize * audioWaves.connector.height) / 2);
        connector.setAttribute('fill', `url(#${this.gradientIds.waves})`);
        connector.setAttribute('opacity', audioWaves.connector.opacity);
        group.appendChild(connector);
        
        // Create audio wave bars
        audioWaves.heights.forEach((height, i) => {
            const waveHeight = waveAreaSize * height;
            const waveX = waveStartX + (i * (waveWidth + waveGap));
            const waveY = waveBaseY - waveHeight;
            
            const wave = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            wave.setAttribute('x', waveX);
            wave.setAttribute('y', waveY);
            wave.setAttribute('width', waveWidth);
            wave.setAttribute('height', waveHeight);
            wave.setAttribute('rx', waveWidth * audioWaves.borderRadius);
            wave.setAttribute('fill', `url(#${this.gradientIds.waves})`);
            wave.setAttribute('filter', `url(#${this.filterIds.shadow})`);
            wave.setAttribute('stroke', 'rgba(255, 255, 255, 0.15)');
            wave.setAttribute('stroke-width', '0.5');
            
            // Add individual wave animation
            if (this.options.animation.enabled) {
                const animateHeight = document.createElementNS('http://www.w3.org/2000/svg', 'animateTransform');
                animateHeight.setAttribute('attributeName', 'transform');
                animateHeight.setAttribute('type', 'scale');
                animateHeight.setAttribute('values', '1,1; 1,1.1; 1,0.9; 1,1');
                animateHeight.setAttribute('dur', `${this.options.animation.waveDuration + (i * 0.3)}s`);
                animateHeight.setAttribute('repeatCount', 'indefinite');
                animateHeight.setAttribute('begin', `${i * 0.2}s`);
                wave.appendChild(animateHeight);
            }
            
            group.appendChild(wave);
        });
        
        return group;
    }
    
    createGlassOverlay(size) {
        // Subtle glass morphism overlay for premium feel
        const squirclePath = this.createSquirclePath(size);
        
        const overlay = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        overlay.setAttribute('d', squirclePath);
        overlay.setAttribute('fill', this.options.colors.primary.glass);
        overlay.setAttribute('filter', `url(#${this.filterIds.glass})`);
        overlay.setAttribute('pointer-events', 'none');
        
        return overlay;
    }
    
    createEnhancedWordmark() {
        const wordmark = document.createElement('div');
        wordmark.className = 'mina-enhanced-wordmark';
        wordmark.textContent = 'Mina';
        wordmark.style.cssText = `
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: ${this.options.wordmarkSize}px;
            font-weight: 700;
            background: linear-gradient(135deg, ${this.options.colors.primary.gradient[0]} 0%, ${this.options.colors.primary.gradient[2]} 50%, ${this.options.colors.primary.gradient[4]} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-align: center;
            margin-top: 16px;
            letter-spacing: -0.02em;
            text-shadow: 0 4px 16px rgba(139, 69, 255, 0.2);
            filter: drop-shadow(0 2px 8px rgba(139, 69, 255, 0.3));
        `;
        
        this.container.appendChild(wordmark);
    }
    
    setupAnimations() {
        if (!this.options.animation.enabled || !this.iconContainer) return;
        
        // Add premium breathing animation
        this.iconContainer.style.animation = `
            minaEnhancedBreathe ${this.options.animation.breatheDuration}s ease-in-out infinite,
            minaEnhancedPulse ${this.options.animation.pulseDuration}s ease-in-out infinite alternate
        `;
        
        // Add CSS animations
        this.addAnimationStyles();
    }
    
    addAnimationStyles() {
        if (document.getElementById('mina-enhanced-animations')) return;
        
        const style = document.createElement('style');
        style.id = 'mina-enhanced-animations';
        style.textContent = `
            @keyframes minaEnhancedBreathe {
                0%, 100% { transform: scale(1) translateZ(0); }
                50% { transform: scale(1.02) translateZ(10px); }
            }
            
            @keyframes minaEnhancedPulse {
                0% { filter: 
                    drop-shadow(0 20px 60px rgba(139, 69, 255, 0.3)) 
                    drop-shadow(0 8px 32px rgba(30, 27, 75, 0.4)); }
                100% { filter: 
                    drop-shadow(0 25px 80px rgba(139, 69, 255, 0.4)) 
                    drop-shadow(0 12px 40px rgba(30, 27, 75, 0.5)); }
            }
            
            .mina-enhanced-logo-container:hover {
                transform: scale(1.05) rotateY(5deg) rotateX(2deg) !important;
                transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            @media (prefers-reduced-motion: reduce) {
                .mina-enhanced-logo-container,
                .mina-enhanced-logo-container * {
                    animation: none !important;
                    transition: none !important;
                }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    // Static methods for easy usage
    static createBrandLogo(container, size = 200) {
        return new MinaEnhancedLogo(container, {
            size,
            showWordmark: true,
            wordmarkSize: size * 0.24
        });
    }
    
    static createCompactLogo(container, size = 32) {
        return new MinaEnhancedLogo(container, {
            size,
            showWordmark: false,
            animation: {
                breatheDuration: 10,
                pulseDuration: 6,
                waveDuration: 4,
                enabled: true
            }
        });
    }
    
    static createHeroLogo(container, size = 300) {
        return new MinaEnhancedLogo(container, {
            size,
            showWordmark: true,
            wordmarkSize: size * 0.20,
            animation: {
                breatheDuration: 6,
                pulseDuration: 3,
                waveDuration: 2,
                enabled: true
            }
        });
    }
}

// Make it globally available
window.MinaEnhancedLogo = MinaEnhancedLogo;