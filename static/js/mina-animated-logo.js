// Mina Animated Logo Component - Premium 3D SVG Implementation
// Creates a true 3D squircle with beveled microphone bars matching the premium design

class MinaAnimatedLogo {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            size: 200,
            accent: {
                name: "Premium Purple",
                gradient: ["#D5B6FF", "#A56CFF", "#6D2BE3", "#3A11A5"],
                neon: "#A855F7",
            },
            showWordmark: true,
            wordmarkSize: 72,
            ...options
        };
        
        this.init();
    }
    
    init() {
        this.createPremium3DIcon();
        if (this.options.showWordmark) {
            this.createWordmark();
        }
    }
    
    createPremium3DIcon() {
        const { size, accent } = this.options;
        
        // Create container
        const container = document.createElement('div');
        container.className = 'mina-3d-icon';
        container.style.cssText = `
            width: ${size}px;
            height: ${size}px;
            position: relative;
            animation: minaIconBreathe 6s ease-in-out infinite;
        `;
        
        // Create the 3D SVG icon
        const svg = this.createSquircleSVG(size);
        container.appendChild(svg);
        
        this.container.appendChild(container);
    }
    
    createSquircleSVG(size) {
        const micSize = size * 0.64; // Slightly larger than current 55%
        const barWidth = micSize * 0.14;
        const barHeights = [micSize * 0.35, micSize * 0.26, micSize * 0.35]; // [1, 0.75, 1] ratio
        const gap = barWidth * 1.0;
        const connectorHeight = micSize * 0.06;
        
        // Create SVG element
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', size);
        svg.setAttribute('height', size);
        svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
        svg.style.cssText = 'display: block;';
        
        // Create defs for gradients and filters
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        
        // Background squircle gradient
        const bgGradient = document.createElementNS('http://www.w3.org/2000/svg', 'radialGradient');
        bgGradient.setAttribute('id', 'squircleGradient');
        bgGradient.setAttribute('cx', '30%');
        bgGradient.setAttribute('cy', '30%');
        bgGradient.setAttribute('r', '80%');
        
        const bgStops = [
            { offset: '0%', color: this.options.accent.gradient[0], opacity: '1' },
            { offset: '40%', color: this.options.accent.gradient[1], opacity: '1' },
            { offset: '70%', color: this.options.accent.gradient[2], opacity: '1' },
            { offset: '100%', color: this.options.accent.gradient[3], opacity: '1' }
        ];
        
        bgStops.forEach(stop => {
            const stopEl = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stopEl.setAttribute('offset', stop.offset);
            stopEl.setAttribute('stop-color', stop.color);
            stopEl.setAttribute('stop-opacity', stop.opacity);
            bgGradient.appendChild(stopEl);
        });
        
        // Bar gradient (for 3D effect)
        const barGradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        barGradient.setAttribute('id', 'barGradient');
        barGradient.setAttribute('x1', '0%');
        barGradient.setAttribute('y1', '0%');
        barGradient.setAttribute('x2', '100%');
        barGradient.setAttribute('y2', '100%');
        
        const barStops = [
            { offset: '0%', color: '#FFFFFF', opacity: '0.3' },
            { offset: '30%', color: this.options.accent.gradient[1], opacity: '0.9' },
            { offset: '70%', color: this.options.accent.gradient[2], opacity: '1' },
            { offset: '100%', color: this.options.accent.gradient[3], opacity: '1' }
        ];
        
        barStops.forEach(stop => {
            const stopEl = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stopEl.setAttribute('offset', stop.offset);
            stopEl.setAttribute('stop-color', stop.color);
            stopEl.setAttribute('stop-opacity', stop.opacity);
            barGradient.appendChild(stopEl);
        });
        
        // Inner shadow filter
        const innerShadowFilter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        innerShadowFilter.setAttribute('id', 'innerShadow');
        innerShadowFilter.setAttribute('x', '-50%');
        innerShadowFilter.setAttribute('y', '-50%');
        innerShadowFilter.setAttribute('width', '200%');
        innerShadowFilter.setAttribute('height', '200%');
        
        const feGaussianBlur = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGaussianBlur.setAttribute('in', 'SourceAlpha');
        feGaussianBlur.setAttribute('stdDeviation', '3');
        feGaussianBlur.setAttribute('result', 'blur');
        
        const feOffset = document.createElementNS('http://www.w3.org/2000/svg', 'feOffset');
        feOffset.setAttribute('in', 'blur');
        feOffset.setAttribute('dx', '2');
        feOffset.setAttribute('dy', '2');
        feOffset.setAttribute('result', 'offsetBlur');
        
        const feComposite = document.createElementNS('http://www.w3.org/2000/svg', 'feComposite');
        feComposite.setAttribute('in', 'offsetBlur');
        feComposite.setAttribute('in2', 'SourceGraphic');
        feComposite.setAttribute('operator', 'in');
        feComposite.setAttribute('result', 'innerShadow');
        
        innerShadowFilter.appendChild(feGaussianBlur);
        innerShadowFilter.appendChild(feOffset);
        innerShadowFilter.appendChild(feComposite);
        
        // Outer glow filter
        const glowFilter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        glowFilter.setAttribute('id', 'glow');
        glowFilter.setAttribute('x', '-50%');
        glowFilter.setAttribute('y', '-50%');
        glowFilter.setAttribute('width', '200%');
        glowFilter.setAttribute('height', '200%');
        
        const feGlow = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGlow.setAttribute('stdDeviation', '6');
        feGlow.setAttribute('result', 'coloredBlur');
        
        const feMerge = document.createElementNS('http://www.w3.org/2000/svg', 'feMerge');
        const feMergeNode1 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        feMergeNode1.setAttribute('in', 'coloredBlur');
        const feMergeNode2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        feMergeNode2.setAttribute('in', 'SourceGraphic');
        
        feMerge.appendChild(feMergeNode1);
        feMerge.appendChild(feMergeNode2);
        glowFilter.appendChild(feGlow);
        glowFilter.appendChild(feMerge);
        
        defs.appendChild(bgGradient);
        defs.appendChild(barGradient);
        defs.appendChild(innerShadowFilter);
        defs.appendChild(glowFilter);
        svg.appendChild(defs);
        
        // Create squircle path (true superellipse)
        const squirclePath = this.createSquirclePath(size);
        const squircle = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        squircle.setAttribute('d', squirclePath);
        squircle.setAttribute('fill', 'url(#squircleGradient)');
        squircle.setAttribute('filter', 'url(#glow)');
        svg.appendChild(squircle);
        
        // Create microphone symbol group
        const micGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        micGroup.setAttribute('transform', `translate(${(size - micSize) / 2}, ${(size - micSize) / 2 + micSize * 0.05})`);
        
        // Horizontal connector
        const connector = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        const connectorWidth = barWidth * 3 + gap * 2;
        connector.setAttribute('x', (micSize - connectorWidth) / 2);
        connector.setAttribute('y', micSize * 0.45);
        connector.setAttribute('width', connectorWidth);
        connector.setAttribute('height', connectorHeight);
        connector.setAttribute('rx', connectorHeight / 2);
        connector.setAttribute('fill', 'url(#barGradient)');
        connector.setAttribute('opacity', '0.8');
        micGroup.appendChild(connector);
        
        // Three microphone bars
        const startX = (micSize - (barWidth * 3 + gap * 2)) / 2;
        barHeights.forEach((height, i) => {
            const bar = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            bar.setAttribute('x', startX + i * (barWidth + gap));
            bar.setAttribute('y', micSize * 0.52 - height);
            bar.setAttribute('width', barWidth);
            bar.setAttribute('height', height);
            bar.setAttribute('rx', barWidth / 2);
            bar.setAttribute('fill', 'url(#barGradient)');
            bar.setAttribute('filter', 'url(#innerShadow)');
            
            // Add subtle animation
            const animateHeight = document.createElementNS('http://www.w3.org/2000/svg', 'animateTransform');
            animateHeight.setAttribute('attributeName', 'transform');
            animateHeight.setAttribute('type', 'scale');
            animateHeight.setAttribute('values', '1,1; 1,1.02; 1,1');
            animateHeight.setAttribute('dur', `${4 + i * 0.5}s`);
            animateHeight.setAttribute('repeatCount', 'indefinite');
            bar.appendChild(animateHeight);
            
            micGroup.appendChild(bar);
        });
        
        svg.appendChild(micGroup);
        
        // Top-left highlight overlay
        const highlight = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
        highlight.setAttribute('cx', size * 0.35);
        highlight.setAttribute('cy', size * 0.35);
        highlight.setAttribute('rx', size * 0.25);
        highlight.setAttribute('ry', size * 0.15);
        highlight.setAttribute('fill', 'rgba(255, 255, 255, 0.15)');
        highlight.setAttribute('opacity', '0.6');
        svg.appendChild(highlight);
        
        return svg;
    }
    
    createSquirclePath(size) {
        // Create a true squircle (superellipse) path
        const cx = size / 2;
        const cy = size / 2;
        const r = size * 0.4;
        const n = 5; // Squircle parameter
        
        let path = '';
        for (let i = 0; i <= 360; i += 5) {
            const angle = (i * Math.PI) / 180;
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
        wordmark.className = 'mina-wordmark';
        wordmark.style.cssText = `
            position: relative;
            margin-top: 24px;
            user-select: none;
        `;
        
        const text = document.createElement('span');
        text.className = 'mina-wordmark-text';
        text.textContent = 'Mina';
        text.style.cssText = `
            font-size: ${wordmarkSize}px;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(90deg, ${accent.gradient[0]}, ${accent.gradient[1]}, ${accent.gradient[2]});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 18px ${accent.neon}66, 0 2px 10px rgba(0,0,0,0.2);
            display: block;
            animation: minaWordmarkFadeIn 1.8s ease-out;
            position: relative;
            overflow: hidden;
        `;
        
        wordmark.appendChild(text);
        
        // Shine sweep effect
        const shine = document.createElement('div');
        shine.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(120deg, rgba(255,255,255,0), rgba(255,255,255,0.7), rgba(255,255,255,0));
            -webkit-mask-image: linear-gradient(90deg, rgba(0,0,0,1), rgba(0,0,0,0));
            mask-image: linear-gradient(90deg, rgba(0,0,0,1), rgba(0,0,0,0));
            mix-blend-mode: overlay;
            animation: minaShineSweep 4s ease-in-out infinite 2s;
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

// Inject CSS animations
function injectMinaLogoStyles() {
    if (document.getElementById('mina-logo-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'mina-logo-styles';
    style.textContent = `
        @keyframes minaIconBreathe {
            0%, 100% { 
                transform: scale(1); 
                filter: drop-shadow(0 0 15px rgba(168, 85, 247, 0.4));
            }
            50% { 
                transform: scale(1.02); 
                filter: drop-shadow(0 0 25px rgba(168, 85, 247, 0.6));
            }
        }
        
        @keyframes minaWordmarkFadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes minaShineSweep {
            0% { transform: translateX(-200%); }
            100% { transform: translateX(200%); }
        }
    `;
    document.head.appendChild(style);
}

// Auto-inject styles when script loads
if (typeof window !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectMinaLogoStyles);
    } else {
        injectMinaLogoStyles();
    }
}

// Make available globally
if (typeof window !== 'undefined') {
    window.MinaAnimatedLogo = MinaAnimatedLogo;
}