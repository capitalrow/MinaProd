// Mina Animated Logo Component - Ultra-Premium Ultra-Depth 3D Implementation
// Creates a sophisticated multi-layered 3D squircle with advanced depth perception

class MinaAnimatedLogo {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            size: 200,
            accent: {
                name: "Premium Purple",
                gradient: ["#F3EAFF", "#E4C8FF", "#B985FF", "#8B5CF6", "#6D28D9", "#4C1D95", "#1E1B4B"],
                neon: "#A855F7",
                shadow: "#1E1B4B",
                highlight: "#FFFFFF",
                depth: "#0F0F23"
            },
            showWordmark: true,
            wordmarkSize: 72,
            ...options
        };
        
        this.init();
    }
    
    init() {
        this.createUltraDepth3DIcon();
        if (this.options.showWordmark) {
            this.createWordmark();
        }
    }
    
    createUltraDepth3DIcon() {
        const { size, accent } = this.options;
        
        // Create container with enhanced styling
        const container = document.createElement('div');
        container.className = 'mina-ultra-depth-3d-icon';
        container.style.cssText = `
            width: ${size}px;
            height: ${size}px;
            position: relative;
            filter: drop-shadow(0 12px 48px rgba(75, 85, 99, 0.25)) 
                   drop-shadow(0 4px 16px rgba(30, 27, 75, 0.3));
            animation: minaUltraDepthIconBreathe 10s ease-in-out infinite;
            transform-style: preserve-3d;
        `;
        
        // Create the ultra-depth SVG icon
        const svg = this.createUltraDepthSVG(size);
        container.appendChild(svg);
        
        this.container.appendChild(container);
    }
    
    createUltraDepthSVG(size) {
        const micSize = size * 0.68; // Slightly larger for better presence
        const barWidth = micSize * 0.14;
        const barHeights = [micSize * 0.42, micSize * 0.31, micSize * 0.42]; // Perfect proportions
        const gap = barWidth * 0.92;
        const connectorHeight = micSize * 0.06;
        
        // Create SVG element with enhanced settings
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', size);
        svg.setAttribute('height', size);
        svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
        svg.style.cssText = 'display: block; overflow: visible;';
        
        // Create ultra-advanced defs for maximum depth effects
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        
        // Ultra-depth background gradient with enhanced layering
        const bgGradient = document.createElementNS('http://www.w3.org/2000/svg', 'radialGradient');
        bgGradient.setAttribute('id', `squircleGradient_${Math.random().toString(36).substr(2, 9)}`);
        bgGradient.setAttribute('cx', '38%');
        bgGradient.setAttribute('cy', '22%');
        bgGradient.setAttribute('r', '90%');
        
        const bgStops = [
            { offset: '0%', color: this.options.accent.gradient[0], opacity: '1' },
            { offset: '15%', color: this.options.accent.gradient[1], opacity: '0.98' },
            { offset: '35%', color: this.options.accent.gradient[2], opacity: '1' },
            { offset: '55%', color: this.options.accent.gradient[3], opacity: '1' },
            { offset: '75%', color: this.options.accent.gradient[4], opacity: '1' },
            { offset: '90%', color: this.options.accent.gradient[5], opacity: '1' },
            { offset: '100%', color: this.options.accent.gradient[6], opacity: '1' }
        ];
        
        bgStops.forEach(stop => {
            const stopEl = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stopEl.setAttribute('offset', stop.offset);
            stopEl.setAttribute('stop-color', stop.color);
            stopEl.setAttribute('stop-opacity', stop.opacity);
            bgGradient.appendChild(stopEl);
        });
        
        // Enhanced 3D beveled bar gradient
        const barGradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        barGradient.setAttribute('id', `barGradient_${Math.random().toString(36).substr(2, 9)}`);
        barGradient.setAttribute('x1', '12%');
        barGradient.setAttribute('y1', '8%');
        barGradient.setAttribute('x2', '88%');
        barGradient.setAttribute('y2', '92%');
        
        const barStops = [
            { offset: '0%', color: this.options.accent.highlight, opacity: '0.5' },
            { offset: '15%', color: this.options.accent.gradient[1], opacity: '0.85' },
            { offset: '35%', color: this.options.accent.gradient[2], opacity: '1' },
            { offset: '60%', color: this.options.accent.gradient[3], opacity: '1' },
            { offset: '85%', color: this.options.accent.gradient[4], opacity: '1' },
            { offset: '100%', color: this.options.accent.depth, opacity: '0.95' }
        ];
        
        barStops.forEach(stop => {
            const stopEl = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stopEl.setAttribute('offset', stop.offset);
            stopEl.setAttribute('stop-color', stop.color);
            stopEl.setAttribute('stop-opacity', stop.opacity);
            barGradient.appendChild(stopEl);
        });
        
        // Multi-Layer Depth Filter System - Layer 1: Deep Shadows
        const deepShadowFilter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        deepShadowFilter.setAttribute('id', `deepShadow_${Math.random().toString(36).substr(2, 9)}`);
        deepShadowFilter.setAttribute('x', '-200%');
        deepShadowFilter.setAttribute('y', '-200%');
        deepShadowFilter.setAttribute('width', '500%');
        deepShadowFilter.setAttribute('height', '500%');
        
        // Deep shadow layer
        const feGaussianBlur1 = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGaussianBlur1.setAttribute('in', 'SourceAlpha');
        feGaussianBlur1.setAttribute('stdDeviation', '12');
        feGaussianBlur1.setAttribute('result', 'deepBlur');
        
        const feOffset1 = document.createElementNS('http://www.w3.org/2000/svg', 'feOffset');
        feOffset1.setAttribute('in', 'deepBlur');
        feOffset1.setAttribute('dx', '8');
        feOffset1.setAttribute('dy', '12');
        feOffset1.setAttribute('result', 'deepOffset');
        
        const feColorMatrix1 = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
        feColorMatrix1.setAttribute('in', 'deepOffset');
        feColorMatrix1.setAttribute('type', 'matrix');
        feColorMatrix1.setAttribute('values', '0 0 0 0 0.05  0 0 0 0 0.02  0 0 0 0 0.15  0 0 0 0.6 0');
        feColorMatrix1.setAttribute('result', 'deepShadow');
        
        // Medium shadow layer
        const feGaussianBlur2 = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGaussianBlur2.setAttribute('in', 'SourceAlpha');
        feGaussianBlur2.setAttribute('stdDeviation', '6');
        feGaussianBlur2.setAttribute('result', 'mediumBlur');
        
        const feOffset2 = document.createElementNS('http://www.w3.org/2000/svg', 'feOffset');
        feOffset2.setAttribute('in', 'mediumBlur');
        feOffset2.setAttribute('dx', '4');
        feOffset2.setAttribute('dy', '6');
        feOffset2.setAttribute('result', 'mediumOffset');
        
        const feColorMatrix2 = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
        feColorMatrix2.setAttribute('in', 'mediumOffset');
        feColorMatrix2.setAttribute('type', 'matrix');
        feColorMatrix2.setAttribute('values', '0 0 0 0 0.1  0 0 0 0 0.05  0 0 0 0 0.25  0 0 0 0.4 0');
        feColorMatrix2.setAttribute('result', 'mediumShadow');
        
        // Close shadow layer
        const feGaussianBlur3 = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGaussianBlur3.setAttribute('in', 'SourceAlpha');
        feGaussianBlur3.setAttribute('stdDeviation', '3');
        feGaussianBlur3.setAttribute('result', 'closeBlur');
        
        const feOffset3 = document.createElementNS('http://www.w3.org/2000/svg', 'feOffset');
        feOffset3.setAttribute('in', 'closeBlur');
        feOffset3.setAttribute('dx', '2');
        feOffset3.setAttribute('dy', '3');
        feOffset3.setAttribute('result', 'closeOffset');
        
        const feColorMatrix3 = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
        feColorMatrix3.setAttribute('in', 'closeOffset');
        feColorMatrix3.setAttribute('type', 'matrix');
        feColorMatrix3.setAttribute('values', '0 0 0 0 0.15  0 0 0 0 0.1  0 0 0 0 0.35  0 0 0 0.3 0');
        feColorMatrix3.setAttribute('result', 'closeShadow');
        
        // Merge shadow layers
        const shadowMerge = document.createElementNS('http://www.w3.org/2000/svg', 'feMerge');
        const shadowMergeNode1 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        shadowMergeNode1.setAttribute('in', 'deepShadow');
        const shadowMergeNode2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        shadowMergeNode2.setAttribute('in', 'mediumShadow');
        const shadowMergeNode3 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        shadowMergeNode3.setAttribute('in', 'closeShadow');
        const shadowMergeNode4 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        shadowMergeNode4.setAttribute('in', 'SourceGraphic');
        
        shadowMerge.appendChild(shadowMergeNode1);
        shadowMerge.appendChild(shadowMergeNode2);
        shadowMerge.appendChild(shadowMergeNode3);
        shadowMerge.appendChild(shadowMergeNode4);
        
        deepShadowFilter.appendChild(feGaussianBlur1);
        deepShadowFilter.appendChild(feOffset1);
        deepShadowFilter.appendChild(feColorMatrix1);
        deepShadowFilter.appendChild(feGaussianBlur2);
        deepShadowFilter.appendChild(feOffset2);
        deepShadowFilter.appendChild(feColorMatrix2);
        deepShadowFilter.appendChild(feGaussianBlur3);
        deepShadowFilter.appendChild(feOffset3);
        deepShadowFilter.appendChild(feColorMatrix3);
        deepShadowFilter.appendChild(shadowMerge);
        
        // Advanced Beveling and Inner Depth Filter
        const bevelFilter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        bevelFilter.setAttribute('id', `bevelFilter_${Math.random().toString(36).substr(2, 9)}`);
        bevelFilter.setAttribute('x', '-150%');
        bevelFilter.setAttribute('y', '-150%');
        bevelFilter.setAttribute('width', '400%');
        bevelFilter.setAttribute('height', '400%');
        
        // Inner highlight (top-left bevel)
        const feGaussianBlur4 = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGaussianBlur4.setAttribute('in', 'SourceAlpha');
        feGaussianBlur4.setAttribute('stdDeviation', '2');
        feGaussianBlur4.setAttribute('result', 'highlightBlur');
        
        const feOffset4 = document.createElementNS('http://www.w3.org/2000/svg', 'feOffset');
        feOffset4.setAttribute('in', 'highlightBlur');
        feOffset4.setAttribute('dx', '-1');
        feOffset4.setAttribute('dy', '-1.5');
        feOffset4.setAttribute('result', 'highlightOffset');
        
        const feComposite1 = document.createElementNS('http://www.w3.org/2000/svg', 'feComposite');
        feComposite1.setAttribute('in', 'highlightOffset');
        feComposite1.setAttribute('in2', 'SourceGraphic');
        feComposite1.setAttribute('operator', 'in');
        feComposite1.setAttribute('result', 'innerHighlight');
        
        const feColorMatrix4 = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
        feColorMatrix4.setAttribute('in', 'innerHighlight');
        feColorMatrix4.setAttribute('type', 'matrix');
        feColorMatrix4.setAttribute('values', '1 1 1 0 0.8  1 1 1 0 0.9  1 1 1 0 1  0 0 0 0.4 0');
        feColorMatrix4.setAttribute('result', 'brightHighlight');
        
        // Inner shadow (bottom-right bevel)
        const feGaussianBlur5 = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGaussianBlur5.setAttribute('in', 'SourceAlpha');
        feGaussianBlur5.setAttribute('stdDeviation', '2.5');
        feGaussianBlur5.setAttribute('result', 'innerShadowBlur');
        
        const feOffset5 = document.createElementNS('http://www.w3.org/2000/svg', 'feOffset');
        feOffset5.setAttribute('in', 'innerShadowBlur');
        feOffset5.setAttribute('dx', '1.5');
        feOffset5.setAttribute('dy', '2');
        feOffset5.setAttribute('result', 'innerShadowOffset');
        
        const feComposite2 = document.createElementNS('http://www.w3.org/2000/svg', 'feComposite');
        feComposite2.setAttribute('in', 'innerShadowOffset');
        feComposite2.setAttribute('in2', 'SourceGraphic');
        feComposite2.setAttribute('operator', 'in');
        feComposite2.setAttribute('result', 'innerShadow');
        
        const feColorMatrix5 = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
        feColorMatrix5.setAttribute('in', 'innerShadow');
        feColorMatrix5.setAttribute('type', 'matrix');
        feColorMatrix5.setAttribute('values', '0 0 0 0 0.05  0 0 0 0 0.02  0 0 0 0 0.15  0 0 0 0.5 0');
        feColorMatrix5.setAttribute('result', 'darkInnerShadow');
        
        // Merge bevel effects
        const bevelMerge = document.createElementNS('http://www.w3.org/2000/svg', 'feMerge');
        const bevelMergeNode1 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        bevelMergeNode1.setAttribute('in', 'SourceGraphic');
        const bevelMergeNode2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        bevelMergeNode2.setAttribute('in', 'darkInnerShadow');
        const bevelMergeNode3 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        bevelMergeNode3.setAttribute('in', 'brightHighlight');
        
        bevelMerge.appendChild(bevelMergeNode1);
        bevelMerge.appendChild(bevelMergeNode2);
        bevelMerge.appendChild(bevelMergeNode3);
        
        bevelFilter.appendChild(feGaussianBlur4);
        bevelFilter.appendChild(feOffset4);
        bevelFilter.appendChild(feComposite1);
        bevelFilter.appendChild(feColorMatrix4);
        bevelFilter.appendChild(feGaussianBlur5);
        bevelFilter.appendChild(feOffset5);
        bevelFilter.appendChild(feComposite2);
        bevelFilter.appendChild(feColorMatrix5);
        bevelFilter.appendChild(bevelMerge);
        
        // Ultra-Premium Atmospheric Glow Filter
        const atmosphericGlowFilter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        atmosphericGlowFilter.setAttribute('id', `atmosphericGlow_${Math.random().toString(36).substr(2, 9)}`);
        atmosphericGlowFilter.setAttribute('x', '-200%');
        atmosphericGlowFilter.setAttribute('y', '-200%');
        atmosphericGlowFilter.setAttribute('width', '500%');
        atmosphericGlowFilter.setAttribute('height', '500%');
        
        // Outer atmospheric glow
        const feGlow1 = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGlow1.setAttribute('stdDeviation', '16');
        feGlow1.setAttribute('result', 'atmosphericGlow');
        
        const feColorMatrix6 = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
        feColorMatrix6.setAttribute('in', 'atmosphericGlow');
        feColorMatrix6.setAttribute('type', 'matrix');
        feColorMatrix6.setAttribute('values', '0.8 0 1 0 0.3  0 0.4 1 0 0.15  1 0.3 1 0 0.6  0 0 0 0.25 0');
        feColorMatrix6.setAttribute('result', 'coloredAtmosphericGlow');
        
        // Mid-range glow
        const feGlow2 = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGlow2.setAttribute('in', 'SourceGraphic');
        feGlow2.setAttribute('stdDeviation', '8');
        feGlow2.setAttribute('result', 'midGlow');
        
        const feColorMatrix7 = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
        feColorMatrix7.setAttribute('in', 'midGlow');
        feColorMatrix7.setAttribute('type', 'matrix');
        feColorMatrix7.setAttribute('values', '0.9 0 1 0 0.25  0 0.5 1 0 0.12  1 0.4 1 0 0.55  0 0 0 0.35 0');
        feColorMatrix7.setAttribute('result', 'coloredMidGlow');
        
        // Close range glow
        const feGlow3 = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGlow3.setAttribute('in', 'SourceGraphic');
        feGlow3.setAttribute('stdDeviation', '4');
        feGlow3.setAttribute('result', 'closeGlow');
        
        const feColorMatrix8 = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
        feColorMatrix8.setAttribute('in', 'closeGlow');
        feColorMatrix8.setAttribute('type', 'matrix');
        feColorMatrix8.setAttribute('values', '1 0 1 0 0.2  0 0.6 1 0 0.1  1 0.5 1 0 0.5  0 0 0 0.45 0');
        feColorMatrix8.setAttribute('result', 'coloredCloseGlow');
        
        // Merge all glows
        const glowMerge = document.createElementNS('http://www.w3.org/2000/svg', 'feMerge');
        const glowMergeNode1 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        glowMergeNode1.setAttribute('in', 'coloredAtmosphericGlow');
        const glowMergeNode2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        glowMergeNode2.setAttribute('in', 'coloredMidGlow');
        const glowMergeNode3 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        glowMergeNode3.setAttribute('in', 'coloredCloseGlow');
        const glowMergeNode4 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        glowMergeNode4.setAttribute('in', 'SourceGraphic');
        
        glowMerge.appendChild(glowMergeNode1);
        glowMerge.appendChild(glowMergeNode2);
        glowMerge.appendChild(glowMergeNode3);
        glowMerge.appendChild(glowMergeNode4);
        
        atmosphericGlowFilter.appendChild(feGlow1);
        atmosphericGlowFilter.appendChild(feColorMatrix6);
        atmosphericGlowFilter.appendChild(feGlow2);
        atmosphericGlowFilter.appendChild(feColorMatrix7);
        atmosphericGlowFilter.appendChild(feGlow3);
        atmosphericGlowFilter.appendChild(feColorMatrix8);
        atmosphericGlowFilter.appendChild(glowMerge);
        
        defs.appendChild(bgGradient);
        defs.appendChild(barGradient);
        defs.appendChild(deepShadowFilter);
        defs.appendChild(bevelFilter);
        defs.appendChild(atmosphericGlowFilter);
        svg.appendChild(defs);
        
        // Create ultra-depth squircle with layered effects
        const squirclePath = this.createUltraSquirclePath(size);
        const squircle = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        squircle.setAttribute('d', squirclePath);
        squircle.setAttribute('fill', `url(#${bgGradient.getAttribute('id')})`);
        squircle.setAttribute('filter', `url(#${deepShadowFilter.getAttribute('id')}) url(#${atmosphericGlowFilter.getAttribute('id')})`);
        squircle.setAttribute('stroke', 'rgba(255, 255, 255, 0.12)');
        squircle.setAttribute('stroke-width', '0.6');
        svg.appendChild(squircle);
        
        // Create microphone symbol group with enhanced depth positioning
        const micGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        micGroup.setAttribute('transform', `translate(${(size - micSize) / 2}, ${(size - micSize) / 2 + micSize * 0.035})`);
        
        // Enhanced horizontal connector with depth
        const connector = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        const connectorWidth = barWidth * 3 + gap * 2.3;
        connector.setAttribute('x', (micSize - connectorWidth) / 2);
        connector.setAttribute('y', micSize * 0.465);
        connector.setAttribute('width', connectorWidth);
        connector.setAttribute('height', connectorHeight);
        connector.setAttribute('rx', connectorHeight / 2);
        connector.setAttribute('fill', `url(#${barGradient.getAttribute('id')})`);
        connector.setAttribute('opacity', '0.78');
        connector.setAttribute('filter', `url(#${bevelFilter.getAttribute('id')})`);
        connector.setAttribute('stroke', 'rgba(255, 255, 255, 0.08)');
        connector.setAttribute('stroke-width', '0.3');
        micGroup.appendChild(connector);
        
        // Three ultra-depth microphone bars with enhanced 3D effects
        const startX = (micSize - (barWidth * 3 + gap * 2)) / 2;
        barHeights.forEach((height, i) => {
            const bar = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            bar.setAttribute('x', startX + i * (barWidth + gap));
            bar.setAttribute('y', micSize * 0.545 - height);
            bar.setAttribute('width', barWidth);
            bar.setAttribute('height', height);
            bar.setAttribute('rx', barWidth / 2.1);
            bar.setAttribute('fill', `url(#${barGradient.getAttribute('id')})`);
            bar.setAttribute('filter', `url(#${bevelFilter.getAttribute('id')})`);
            bar.setAttribute('stroke', 'rgba(255, 255, 255, 0.1)');
            bar.setAttribute('stroke-width', '0.4');
            
            // Add ultra-subtle premium depth animation
            const animateTransform = document.createElementNS('http://www.w3.org/2000/svg', 'animateTransform');
            animateTransform.setAttribute('attributeName', 'transform');
            animateTransform.setAttribute('type', 'scale');
            animateTransform.setAttribute('values', '1,1; 1,1.02; 1,1');
            animateTransform.setAttribute('dur', `${7 + i * 1.2}s`);
            animateTransform.setAttribute('repeatCount', 'indefinite');
            animateTransform.setAttribute('begin', `${i * 0.6}s`);
            bar.appendChild(animateTransform);
            
            micGroup.appendChild(bar);
        });
        
        svg.appendChild(micGroup);
        
        // Ultra-depth highlight overlay with enhanced positioning and depth
        const highlight = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
        highlight.setAttribute('cx', size * 0.365);
        highlight.setAttribute('cy', size * 0.315);
        highlight.setAttribute('rx', size * 0.32);
        highlight.setAttribute('ry', size * 0.18);
        highlight.setAttribute('fill', 'rgba(255, 255, 255, 0.15)');
        highlight.setAttribute('opacity', '0.75');
        highlight.setAttribute('transform', 'rotate(-9)');
        
        // Add enhanced highlight animation with depth variation
        const animateOpacity = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
        animateOpacity.setAttribute('attributeName', 'opacity');
        animateOpacity.setAttribute('values', '0.75; 0.95; 0.75');
        animateOpacity.setAttribute('dur', '14s');
        animateOpacity.setAttribute('repeatCount', 'indefinite');
        highlight.appendChild(animateOpacity);
        
        svg.appendChild(highlight);
        
        // Additional depth layer - subtle secondary highlight
        const secondaryHighlight = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
        secondaryHighlight.setAttribute('cx', size * 0.42);
        secondaryHighlight.setAttribute('cy', size * 0.28);
        secondaryHighlight.setAttribute('rx', size * 0.15);
        secondaryHighlight.setAttribute('ry', size * 0.08);
        secondaryHighlight.setAttribute('fill', 'rgba(255, 255, 255, 0.08)');
        secondaryHighlight.setAttribute('opacity', '0.6');
        secondaryHighlight.setAttribute('transform', 'rotate(-12)');
        
        svg.appendChild(secondaryHighlight);
        
        return svg;
    }
    
    createUltraSquirclePath(size) {
        // Create an ultra-smooth squircle with perfect mathematical precision
        const cx = size / 2;
        const cy = size / 2;
        const r = size * 0.425;
        const n = 5.2; // Enhanced squircle parameter for more depth
        
        let path = '';
        const steps = 96; // Ultra-high resolution for perfect smoothness
        
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
        wordmark.className = 'mina-ultra-depth-wordmark';
        wordmark.style.cssText = `
            position: relative;
            margin-top: 32px;
            user-select: none;
        `;
        
        const text = document.createElement('span');
        text.className = 'mina-ultra-depth-wordmark-text';
        text.textContent = 'Mina';
        text.style.cssText = `
            font-size: ${wordmarkSize}px;
            font-weight: 900;
            letter-spacing: -0.03em;
            background: linear-gradient(135deg, ${accent.gradient[0]}, ${accent.gradient[1]}, ${accent.gradient[2]}, ${accent.gradient[3]}, ${accent.gradient[4]});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 32px ${accent.neon}55, 0 6px 16px rgba(0,0,0,0.2), 0 2px 8px rgba(30,27,75,0.3);
            display: block;
            animation: minaUltraDepthWordmarkReveal 2.5s ease-out;
            position: relative;
            overflow: hidden;
            filter: drop-shadow(0 3px 12px rgba(139, 92, 246, 0.25));
        `;
        
        wordmark.appendChild(text);
        
        // Ultra-depth shine sweep effect
        const shine = document.createElement('div');
        shine.style.cssText = `
            position: absolute;
            top: -15%;
            left: -120%;
            right: -120%;
            bottom: -15%;
            background: linear-gradient(115deg, 
                rgba(255,255,255,0) 20%, 
                rgba(255,255,255,0.9) 42%, 
                rgba(255,255,255,1) 50%, 
                rgba(255,255,255,0.9) 58%, 
                rgba(255,255,255,0) 80%);
            -webkit-mask-image: linear-gradient(90deg, rgba(0,0,0,1), rgba(0,0,0,0.4), rgba(0,0,0,0));
            mask-image: linear-gradient(90deg, rgba(0,0,0,1), rgba(0,0,0,0.4), rgba(0,0,0,0));
            mix-blend-mode: overlay;
            animation: minaUltraDepthShine 7s ease-in-out infinite 3.5s;
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

// Inject ultra-depth CSS animations
function injectUltraDepthMinaLogoStyles() {
    if (document.getElementById('ultra-depth-mina-logo-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'ultra-depth-mina-logo-styles';
    style.textContent = `
        @keyframes minaUltraDepthIconBreathe {
            0%, 100% { 
                transform: scale(1) translateY(0px) rotateX(0deg); 
                filter: drop-shadow(0 12px 48px rgba(75, 85, 99, 0.25)) 
                       drop-shadow(0 4px 16px rgba(30, 27, 75, 0.3))
                       drop-shadow(0 0 24px rgba(168, 85, 247, 0.28));
            }
            50% { 
                transform: scale(1.018) translateY(-1.5px) rotateX(1deg); 
                filter: drop-shadow(0 16px 56px rgba(75, 85, 99, 0.32)) 
                       drop-shadow(0 6px 20px rgba(30, 27, 75, 0.4))
                       drop-shadow(0 0 36px rgba(168, 85, 247, 0.4));
            }
        }
        
        @keyframes minaUltraDepthWordmarkReveal {
            0% { 
                opacity: 0; 
                transform: translateY(18px) scale(0.92); 
                filter: blur(3px);
            }
            40% {
                opacity: 0.6;
                transform: translateY(6px) scale(0.96);
                filter: blur(1px);
            }
            70% {
                opacity: 0.9;
                transform: translateY(1px) scale(0.99);
                filter: blur(0.2px);
            }
            100% { 
                opacity: 1; 
                transform: translateY(0) scale(1); 
                filter: blur(0px);
            }
        }
        
        @keyframes minaUltraDepthShine {
            0% { transform: translateX(-160%); opacity: 0; }
            12% { transform: translateX(-90%); opacity: 0.7; }
            50% { transform: translateX(0%); opacity: 0.9; }
            88% { transform: translateX(90%); opacity: 0.7; }
            100% { transform: translateX(160%); opacity: 0; }
        }
        
        /* Enhanced responsive scaling with depth preservation */
        @media (max-width: 768px) {
            .mina-ultra-depth-3d-icon {
                filter: drop-shadow(0 6px 24px rgba(75, 85, 99, 0.2)) 
                       drop-shadow(0 2px 8px rgba(30, 27, 75, 0.25));
            }
        }
        
        @media (max-width: 480px) {
            .mina-ultra-depth-3d-icon {
                filter: drop-shadow(0 4px 16px rgba(75, 85, 99, 0.18)) 
                       drop-shadow(0 1px 6px rgba(30, 27, 75, 0.22));
            }
        }
        
        /* Respect reduced motion preferences */
        @media (prefers-reduced-motion: reduce) {
            .mina-ultra-depth-3d-icon,
            .mina-ultra-depth-wordmark-text,
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        
        /* Enhanced focus states for accessibility */
        .mina-ultra-depth-3d-icon:focus-visible,
        .mina-ultra-depth-wordmark:focus-visible {
            outline: 2px solid rgba(168, 85, 247, 0.6);
            outline-offset: 4px;
            border-radius: 8px;
        }
    `;
    document.head.appendChild(style);
}

// Centralized Logo Management System
class MinaLogoManager {
    constructor() {
        this.instances = new Map();
        this.prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.isLowPowerMode = navigator.hardwareConcurrency <= 2;
        this.intersectionObserver = null;
        this.initializeObserver();
    }
    
    initializeObserver() {
        if ('IntersectionObserver' in window) {
            this.intersectionObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && !this.instances.has(entry.target)) {
                        this.initializeLogo(entry.target);
                    }
                });
            }, { rootMargin: '50px' });
        }
    }
    
    // Auto-initialize all logos with data attributes
    autoInitialize() {
        const logoElements = document.querySelectorAll('[data-mina-logo]');
        logoElements.forEach(element => {
            if (this.intersectionObserver) {
                this.intersectionObserver.observe(element);
            } else {
                this.initializeLogo(element);
            }
        });
    }
    
    initializeLogo(element) {
        if (this.instances.has(element)) return;
        
        const options = this.parseDataAttributes(element);
        
        // Add accessibility attributes
        element.setAttribute('role', 'img');
        element.setAttribute('aria-label', 'Mina logo');
        if (options.decorative) {
            element.setAttribute('aria-hidden', 'true');
            element.removeAttribute('aria-label');
        }
        
        // Apply reduced motion preferences
        if (this.prefersReducedMotion) {
            options.animation = 'none';
        }
        
        // Performance optimization for low-power devices
        if (this.isLowPowerMode && options.size < 64) {
            this.createStaticFallback(element, options);
            return;
        }
        
        try {
            const logo = new MinaAnimatedLogo(element, options);
            this.instances.set(element, logo);
        } catch (error) {
            console.warn('Failed to initialize Mina logo:', error);
            this.createStaticFallback(element, options);
        }
    }
    
    parseDataAttributes(element) {
        const dataset = element.dataset;
        return {
            size: parseInt(dataset.minaLogoSize) || 32,
            showWordmark: dataset.minaLogoWordmark !== 'false',
            animation: dataset.minaLogoAnimation || 'subtle',
            decorative: dataset.minaLogoDecorative === 'true',
            theme: dataset.minaLogoTheme || 'auto'
        };
    }
    
    createStaticFallback(element, options) {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', options.size);
        svg.setAttribute('height', options.size);
        svg.setAttribute('viewBox', '0 0 100 100');
        svg.setAttribute('fill', 'none');
        
        // Simple static squircle with microphone bars
        const squircle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        squircle.setAttribute('x', '10');
        squircle.setAttribute('y', '10');
        squircle.setAttribute('width', '80');
        squircle.setAttribute('height', '80');
        squircle.setAttribute('rx', '20');
        squircle.setAttribute('fill', 'url(#staticGradient)');
        
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        gradient.setAttribute('id', 'staticGradient');
        gradient.innerHTML = `
            <stop offset="0%" stop-color="#B985FF"/>
            <stop offset="100%" stop-color="#6D28D9"/>
        `;
        defs.appendChild(gradient);
        
        // Microphone bars
        const bars = [
            { x: 35, height: 20 },
            { x: 45, height: 15 },
            { x: 55, height: 20 }
        ];
        
        bars.forEach(bar => {
            const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('x', bar.x);
            rect.setAttribute('y', 60 - bar.height);
            rect.setAttribute('width', '6');
            rect.setAttribute('height', bar.height);
            rect.setAttribute('rx', '3');
            rect.setAttribute('fill', '#FFFFFF');
            rect.setAttribute('opacity', '0.9');
            svg.appendChild(rect);
        });
        
        svg.appendChild(defs);
        svg.appendChild(squircle);
        element.appendChild(svg);
    }
    
    // Performance monitoring
    pauseAnimationsOnLowPower() {
        if (navigator.getBattery) {
            navigator.getBattery().then(battery => {
                if (battery.level < 0.2 || battery.charging === false) {
                    this.instances.forEach(logo => {
                        if (logo.pauseAnimations) {
                            logo.pauseAnimations();
                        }
                    });
                }
            });
        }
    }
    
    // Cleanup
    destroy() {
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }
        this.instances.clear();
    }
}

// Global initialization
let minaLogoManager = null;

// Auto-inject ultra-depth styles when script loads
if (typeof window !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            injectUltraDepthMinaLogoStyles();
            minaLogoManager = new MinaLogoManager();
            minaLogoManager.autoInitialize();
        });
    } else {
        injectUltraDepthMinaLogoStyles();
        minaLogoManager = new MinaLogoManager();
        minaLogoManager.autoInitialize();
    }
    
    // Handle visibility changes for performance
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && minaLogoManager) {
            minaLogoManager.pauseAnimationsOnLowPower();
        }
    });
}

// Make available globally
if (typeof window !== 'undefined') {
    window.MinaAnimatedLogo = MinaAnimatedLogo;
    window.MinaLogoManager = minaLogoManager;
}