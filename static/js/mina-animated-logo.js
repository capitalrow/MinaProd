// Mina Animated Logo Component - Ultra Premium 3D Implementation
// Creates a sophisticated 3D squircle with advanced lighting and depth effects

class MinaAnimatedLogo {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            size: 200,
            accent: {
                name: "Premium Purple",
                gradient: ["#E4C8FF", "#B985FF", "#8B5CF6", "#6D28D9", "#4C1D95"],
                neon: "#A855F7",
                shadow: "#1E1B4B",
                highlight: "#F8FAFC"
            },
            showWordmark: true,
            wordmarkSize: 72,
            ...options
        };
        
        this.init();
    }
    
    init() {
        this.createUltraPremium3DIcon();
        if (this.options.showWordmark) {
            this.createWordmark();
        }
    }
    
    createUltraPremium3DIcon() {
        const { size, accent } = this.options;
        
        // Create container with enhanced styling
        const container = document.createElement('div');
        container.className = 'mina-ultra-3d-icon';
        container.style.cssText = `
            width: ${size}px;
            height: ${size}px;
            position: relative;
            filter: drop-shadow(0 8px 32px rgba(75, 85, 99, 0.15));
            animation: minaUltraIconBreathe 8s ease-in-out infinite;
        `;
        
        // Create the ultra-premium SVG icon
        const svg = this.createUltraPremiumSVG(size);
        container.appendChild(svg);
        
        this.container.appendChild(container);
    }
    
    createUltraPremiumSVG(size) {
        const micSize = size * 0.66; // Slightly larger for better presence
        const barWidth = micSize * 0.13;
        const barHeights = [micSize * 0.38, micSize * 0.28, micSize * 0.38]; // Perfect proportions
        const gap = barWidth * 0.95;
        const connectorHeight = micSize * 0.055;
        
        // Create SVG element with enhanced settings
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', size);
        svg.setAttribute('height', size);
        svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
        svg.style.cssText = 'display: block; overflow: visible;';
        
        // Create advanced defs for ultra-premium effects
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        
        // Ultra-premium background gradient with depth
        const bgGradient = document.createElementNS('http://www.w3.org/2000/svg', 'radialGradient');
        bgGradient.setAttribute('id', `squircleGradient_${Math.random().toString(36).substr(2, 9)}`);
        bgGradient.setAttribute('cx', '35%');
        bgGradient.setAttribute('cy', '25%');
        bgGradient.setAttribute('r', '85%');
        
        const bgStops = [
            { offset: '0%', color: this.options.accent.gradient[0], opacity: '1' },
            { offset: '25%', color: this.options.accent.gradient[1], opacity: '0.95' },
            { offset: '50%', color: this.options.accent.gradient[2], opacity: '1' },
            { offset: '75%', color: this.options.accent.gradient[3], opacity: '1' },
            { offset: '100%', color: this.options.accent.gradient[4], opacity: '1' }
        ];
        
        bgStops.forEach(stop => {
            const stopEl = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stopEl.setAttribute('offset', stop.offset);
            stopEl.setAttribute('stop-color', stop.color);
            stopEl.setAttribute('stop-opacity', stop.opacity);
            bgGradient.appendChild(stopEl);
        });
        
        // Enhanced bar gradient with sophisticated lighting
        const barGradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        barGradient.setAttribute('id', `barGradient_${Math.random().toString(36).substr(2, 9)}`);
        barGradient.setAttribute('x1', '15%');
        barGradient.setAttribute('y1', '15%');
        barGradient.setAttribute('x2', '85%');
        barGradient.setAttribute('y2', '85%');
        
        const barStops = [
            { offset: '0%', color: this.options.accent.highlight, opacity: '0.4' },
            { offset: '25%', color: this.options.accent.gradient[1], opacity: '0.8' },
            { offset: '60%', color: this.options.accent.gradient[2], opacity: '1' },
            { offset: '85%', color: this.options.accent.gradient[3], opacity: '1' },
            { offset: '100%', color: this.options.accent.shadow, opacity: '0.9' }
        ];
        
        barStops.forEach(stop => {
            const stopEl = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stopEl.setAttribute('offset', stop.offset);
            stopEl.setAttribute('stop-color', stop.color);
            stopEl.setAttribute('stop-opacity', stop.opacity);
            barGradient.appendChild(stopEl);
        });
        
        // Advanced depth filter system
        const depthFilter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        depthFilter.setAttribute('id', `depthFilter_${Math.random().toString(36).substr(2, 9)}`);
        depthFilter.setAttribute('x', '-100%');
        depthFilter.setAttribute('y', '-100%');
        depthFilter.setAttribute('width', '300%');
        depthFilter.setAttribute('height', '300%');
        
        // Inner shadow for depth
        const feGaussianBlur1 = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGaussianBlur1.setAttribute('in', 'SourceAlpha');
        feGaussianBlur1.setAttribute('stdDeviation', '2.5');
        feGaussianBlur1.setAttribute('result', 'innerBlur');
        
        const feOffset1 = document.createElementNS('http://www.w3.org/2000/svg', 'feOffset');
        feOffset1.setAttribute('in', 'innerBlur');
        feOffset1.setAttribute('dx', '1.5');
        feOffset1.setAttribute('dy', '1.5');
        feOffset1.setAttribute('result', 'innerOffset');
        
        const feComposite1 = document.createElementNS('http://www.w3.org/2000/svg', 'feComposite');
        feComposite1.setAttribute('in', 'innerOffset');
        feComposite1.setAttribute('in2', 'SourceGraphic');
        feComposite1.setAttribute('operator', 'in');
        feComposite1.setAttribute('result', 'innerShadow');
        
        // Outer glow for premium effect
        const feGaussianBlur2 = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGaussianBlur2.setAttribute('in', 'SourceGraphic');
        feGaussianBlur2.setAttribute('stdDeviation', '4');
        feGaussianBlur2.setAttribute('result', 'glow');
        
        const feColorMatrix = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
        feColorMatrix.setAttribute('in', 'glow');
        feColorMatrix.setAttribute('type', 'matrix');
        feColorMatrix.setAttribute('values', '0.5 0 0.8 0 0.3  0 0 0.8 0 0.2  0.8 0 1 0 0.4  0 0 0 0.6 0');
        feColorMatrix.setAttribute('result', 'coloredGlow');
        
        // Merge all effects
        const feMerge = document.createElementNS('http://www.w3.org/2000/svg', 'feMerge');
        const feMergeNode1 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        feMergeNode1.setAttribute('in', 'coloredGlow');
        const feMergeNode2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        feMergeNode2.setAttribute('in', 'innerShadow');
        const feMergeNode3 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        feMergeNode3.setAttribute('in', 'SourceGraphic');
        
        feMerge.appendChild(feMergeNode1);
        feMerge.appendChild(feMergeNode2);
        feMerge.appendChild(feMergeNode3);
        
        depthFilter.appendChild(feGaussianBlur1);
        depthFilter.appendChild(feOffset1);
        depthFilter.appendChild(feComposite1);
        depthFilter.appendChild(feGaussianBlur2);
        depthFilter.appendChild(feColorMatrix);
        depthFilter.appendChild(feMerge);
        
        // Ultra-premium outer glow filter
        const ultraGlowFilter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        ultraGlowFilter.setAttribute('id', `ultraGlow_${Math.random().toString(36).substr(2, 9)}`);
        ultraGlowFilter.setAttribute('x', '-150%');
        ultraGlowFilter.setAttribute('y', '-150%');
        ultraGlowFilter.setAttribute('width', '400%');
        ultraGlowFilter.setAttribute('height', '400%');
        
        const feGlow3 = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGlow3.setAttribute('stdDeviation', '8');
        feGlow3.setAttribute('result', 'ultraGlow');
        
        const feColorMatrix2 = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
        feColorMatrix2.setAttribute('in', 'ultraGlow');
        feColorMatrix2.setAttribute('type', 'matrix');
        feColorMatrix2.setAttribute('values', '0.7 0 1 0 0.2  0 0.3 1 0 0.1  1 0.2 1 0 0.5  0 0 0 0.4 0');
        feColorMatrix2.setAttribute('result', 'coloredUltraGlow');
        
        const feMerge2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMerge');
        const feMergeNodeUG1 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        feMergeNodeUG1.setAttribute('in', 'coloredUltraGlow');
        const feMergeNodeUG2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        feMergeNodeUG2.setAttribute('in', 'SourceGraphic');
        
        feMerge2.appendChild(feMergeNodeUG1);
        feMerge2.appendChild(feMergeNodeUG2);
        
        ultraGlowFilter.appendChild(feGlow3);
        ultraGlowFilter.appendChild(feColorMatrix2);
        ultraGlowFilter.appendChild(feMerge2);
        
        defs.appendChild(bgGradient);
        defs.appendChild(barGradient);
        defs.appendChild(depthFilter);
        defs.appendChild(ultraGlowFilter);
        svg.appendChild(defs);
        
        // Create ultra-premium squircle
        const squirclePath = this.createUltraSquirclePath(size);
        const squircle = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        squircle.setAttribute('d', squirclePath);
        squircle.setAttribute('fill', `url(#${bgGradient.getAttribute('id')})`);
        squircle.setAttribute('filter', `url(#${ultraGlowFilter.getAttribute('id')})`);
        squircle.setAttribute('stroke', 'rgba(255, 255, 255, 0.1)');
        squircle.setAttribute('stroke-width', '0.5');
        svg.appendChild(squircle);
        
        // Create microphone symbol group with enhanced positioning
        const micGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        micGroup.setAttribute('transform', `translate(${(size - micSize) / 2}, ${(size - micSize) / 2 + micSize * 0.04})`);
        
        // Enhanced horizontal connector with depth
        const connector = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        const connectorWidth = barWidth * 3 + gap * 2.2;
        connector.setAttribute('x', (micSize - connectorWidth) / 2);
        connector.setAttribute('y', micSize * 0.46);
        connector.setAttribute('width', connectorWidth);
        connector.setAttribute('height', connectorHeight);
        connector.setAttribute('rx', connectorHeight / 2);
        connector.setAttribute('fill', `url(#${barGradient.getAttribute('id')})`);
        connector.setAttribute('opacity', '0.75');
        connector.setAttribute('filter', `url(#${depthFilter.getAttribute('id')})`);
        micGroup.appendChild(connector);
        
        // Three ultra-premium microphone bars
        const startX = (micSize - (barWidth * 3 + gap * 2)) / 2;
        barHeights.forEach((height, i) => {
            const bar = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            bar.setAttribute('x', startX + i * (barWidth + gap));
            bar.setAttribute('y', micSize * 0.54 - height);
            bar.setAttribute('width', barWidth);
            bar.setAttribute('height', height);
            bar.setAttribute('rx', barWidth / 2.2);
            bar.setAttribute('fill', `url(#${barGradient.getAttribute('id')})`);
            bar.setAttribute('filter', `url(#${depthFilter.getAttribute('id')})`);
            bar.setAttribute('stroke', 'rgba(255, 255, 255, 0.08)');
            bar.setAttribute('stroke-width', '0.3');
            
            // Add ultra-subtle premium animation
            const animateTransform = document.createElementNS('http://www.w3.org/2000/svg', 'animateTransform');
            animateTransform.setAttribute('attributeName', 'transform');
            animateTransform.setAttribute('type', 'scale');
            animateTransform.setAttribute('values', '1,1; 1,1.015; 1,1');
            animateTransform.setAttribute('dur', `${6 + i * 0.8}s`);
            animateTransform.setAttribute('repeatCount', 'indefinite');
            animateTransform.setAttribute('begin', `${i * 0.5}s`);
            bar.appendChild(animateTransform);
            
            micGroup.appendChild(bar);
        });
        
        svg.appendChild(micGroup);
        
        // Ultra-premium highlight overlay with sophisticated positioning
        const highlight = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
        highlight.setAttribute('cx', size * 0.38);
        highlight.setAttribute('cy', size * 0.32);
        highlight.setAttribute('rx', size * 0.28);
        highlight.setAttribute('ry', size * 0.16);
        highlight.setAttribute('fill', 'rgba(255, 255, 255, 0.12)');
        highlight.setAttribute('opacity', '0.7');
        highlight.setAttribute('transform', 'rotate(-8)');
        
        // Add subtle highlight animation
        const animateOpacity = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
        animateOpacity.setAttribute('attributeName', 'opacity');
        animateOpacity.setAttribute('values', '0.7; 0.9; 0.7');
        animateOpacity.setAttribute('dur', '12s');
        animateOpacity.setAttribute('repeatCount', 'indefinite');
        highlight.appendChild(animateOpacity);
        
        svg.appendChild(highlight);
        
        return svg;
    }
    
    createUltraSquirclePath(size) {
        // Create an ultra-smooth squircle with perfect mathematical precision
        const cx = size / 2;
        const cy = size / 2;
        const r = size * 0.42;
        const n = 4.8; // Ultra-premium squircle parameter
        
        let path = '';
        const steps = 72; // Higher resolution for smoother curves
        
        for (let i = 0; i <= steps; i++) {
            const angle = (i * 2 * Math.PI) / steps;
            const cosA = Math.cos(angle);
            const sinA = Math.sin(angle);
            const x = cx + r * Math.sign(cosA) * Math.pow(Math.abs(cosA), 2/n);
            const y = cy + r * Math.sign(sinA) * Math.pow(Math.abs(sinA), 2/n);
            
            if (i === 0) {
                path += `M ${x} ${y}`;
            } else {
                path += ` L ${x} ${y}`;
            }
        }
        path += ' Z';
        
        return path;
    }
    
    createWordmark() {
        const { accent, wordmarkSize } = this.options;
        
        const wordmark = document.createElement('div');
        wordmark.className = 'mina-ultra-wordmark';
        wordmark.style.cssText = `
            position: relative;
            margin-top: 28px;
            user-select: none;
        `;
        
        const text = document.createElement('span');
        text.className = 'mina-ultra-wordmark-text';
        text.textContent = 'Mina';
        text.style.cssText = `
            font-size: ${wordmarkSize}px;
            font-weight: 900;
            letter-spacing: -0.025em;
            background: linear-gradient(135deg, ${accent.gradient[0]}, ${accent.gradient[1]}, ${accent.gradient[2]}, ${accent.gradient[3]});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 24px ${accent.neon}55, 0 4px 12px rgba(0,0,0,0.15);
            display: block;
            animation: minaUltraWordmarkReveal 2.2s ease-out;
            position: relative;
            overflow: hidden;
            filter: drop-shadow(0 2px 8px rgba(139, 92, 246, 0.2));
        `;
        
        wordmark.appendChild(text);
        
        // Ultra-premium shine sweep effect
        const shine = document.createElement('div');
        shine.style.cssText = `
            position: absolute;
            top: -10%;
            left: -100%;
            right: -100%;
            bottom: -10%;
            background: linear-gradient(110deg, 
                rgba(255,255,255,0) 25%, 
                rgba(255,255,255,0.8) 45%, 
                rgba(255,255,255,1) 50%, 
                rgba(255,255,255,0.8) 55%, 
                rgba(255,255,255,0) 75%);
            -webkit-mask-image: linear-gradient(90deg, rgba(0,0,0,1), rgba(0,0,0,0.3), rgba(0,0,0,0));
            mask-image: linear-gradient(90deg, rgba(0,0,0,1), rgba(0,0,0,0.3), rgba(0,0,0,0));
            mix-blend-mode: overlay;
            animation: minaUltraShine 6s ease-in-out infinite 3s;
        `;
        wordmark.appendChild(shine);
        
        this.container.appendChild(wordmark);
    }
    
    // Static method to create compact logo for navigation/headers
    static createCompactLogo(container, size = 32) {
        const logo = new MinaAnimatedLogo(container, {
            size: size,
            showWordmark: false
        });
        return logo;
    }
    
    // Static method to create brand logo for splash/hero sections
    static createBrandLogo(container, size = 200) {
        const logo = new MinaAnimatedLogo(container, {
            size: size,
            showWordmark: true,
            wordmarkSize: size * 0.36
        });
        return logo;
    }
}

// Inject ultra-premium CSS animations
function injectUltraMinaLogoStyles() {
    if (document.getElementById('ultra-mina-logo-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'ultra-mina-logo-styles';
    style.textContent = `
        @keyframes minaUltraIconBreathe {
            0%, 100% { 
                transform: scale(1) translateY(0px); 
                filter: drop-shadow(0 8px 32px rgba(75, 85, 99, 0.15)) 
                       drop-shadow(0 0 20px rgba(168, 85, 247, 0.25));
            }
            50% { 
                transform: scale(1.015) translateY(-1px); 
                filter: drop-shadow(0 12px 40px rgba(75, 85, 99, 0.2)) 
                       drop-shadow(0 0 30px rgba(168, 85, 247, 0.35));
            }
        }
        
        @keyframes minaUltraWordmarkReveal {
            0% { 
                opacity: 0; 
                transform: translateY(15px) scale(0.95); 
                filter: blur(2px);
            }
            60% {
                opacity: 0.8;
                transform: translateY(3px) scale(0.98);
                filter: blur(0.5px);
            }
            100% { 
                opacity: 1; 
                transform: translateY(0) scale(1); 
                filter: blur(0px);
            }
        }
        
        @keyframes minaUltraShine {
            0% { transform: translateX(-150%); opacity: 0; }
            15% { transform: translateX(-80%); opacity: 0.6; }
            50% { transform: translateX(0%); opacity: 0.8; }
            85% { transform: translateX(80%); opacity: 0.6; }
            100% { transform: translateX(150%); opacity: 0; }
        }
        
        /* Enhanced responsive scaling */
        @media (max-width: 768px) {
            .mina-ultra-3d-icon {
                filter: drop-shadow(0 4px 16px rgba(75, 85, 99, 0.12));
            }
        }
        
        /* Respect reduced motion preferences */
        @media (prefers-reduced-motion: reduce) {
            .mina-ultra-3d-icon,
            .mina-ultra-wordmark-text,
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
    `;
    document.head.appendChild(style);
}

// Auto-inject ultra-premium styles when script loads
if (typeof window !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectUltraMinaLogoStyles);
    } else {
        injectUltraMinaLogoStyles();
    }
}

// Make available globally
if (typeof window !== 'undefined') {
    window.MinaAnimatedLogo = MinaAnimatedLogo;
}