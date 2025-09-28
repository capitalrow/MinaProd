// Mina Animated Logo Component - Enterprise-Grade Ultra-Premium 3D Implementation
// Creates a sophisticated multi-layered holographic diamond with maximum depth perception

class MinaAnimatedLogo {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            size: 200,
            accent: {
                name: "Enterprise Diamond",
                gradient: [
                    "#FFFFFF", "#F8FAFF", "#E8EFFF", "#D1E3FF", "#B8D4FF", 
                    "#9AC5FF", "#7BB3FF", "#5A9EFF", "#3B82F6", "#2563EB", 
                    "#1D4ED8", "#1E40AF", "#1E3A8A", "#172554", "#0F172A"
                ],
                metallic: ["#F8FAFF", "#E1E8F0", "#C4D1E0", "#8B9DC3", "#4F5B7A", "#2D3748"],
                neon: "#60A5FA",
                shadow: "#0F172A",
                highlight: "#FFFFFF",
                depth: "#020617",
                glass: "rgba(255, 255, 255, 0.15)",
                chrome: "#E2E8F0"
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
        
        // Enterprise holographic diamond gradient with ultra-premium layering
        const bgGradient = document.createElementNS('http://www.w3.org/2000/svg', 'radialGradient');
        bgGradient.setAttribute('id', `diamondGradient_${Math.random().toString(36).substr(2, 9)}`);
        bgGradient.setAttribute('cx', '30%');
        bgGradient.setAttribute('cy', '20%');
        bgGradient.setAttribute('r', '95%');
        
        const bgStops = [
            { offset: '0%', color: this.options.accent.gradient[0], opacity: '1' },
            { offset: '8%', color: this.options.accent.gradient[1], opacity: '0.95' },
            { offset: '16%', color: this.options.accent.gradient[2], opacity: '0.98' },
            { offset: '25%', color: this.options.accent.gradient[3], opacity: '1' },
            { offset: '35%', color: this.options.accent.gradient[4], opacity: '1' },
            { offset: '45%', color: this.options.accent.gradient[5], opacity: '1' },
            { offset: '55%', color: this.options.accent.gradient[6], opacity: '1' },
            { offset: '65%', color: this.options.accent.gradient[7], opacity: '1' },
            { offset: '72%', color: this.options.accent.gradient[8], opacity: '1' },
            { offset: '79%', color: this.options.accent.gradient[9], opacity: '1' },
            { offset: '86%', color: this.options.accent.gradient[10], opacity: '1' },
            { offset: '91%', color: this.options.accent.gradient[11], opacity: '1' },
            { offset: '95%', color: this.options.accent.gradient[12], opacity: '1' },
            { offset: '98%', color: this.options.accent.gradient[13], opacity: '1' },
            { offset: '100%', color: this.options.accent.gradient[14], opacity: '1' }
        ];
        
        bgStops.forEach(stop => {
            const stopEl = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stopEl.setAttribute('offset', stop.offset);
            stopEl.setAttribute('stop-color', stop.color);
            stopEl.setAttribute('stop-opacity', stop.opacity);
            bgGradient.appendChild(stopEl);
        });
        
        // Ultra-premium metallic chrome bar gradient with holographic effects
        const barGradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        barGradient.setAttribute('id', `chromeBarGradient_${Math.random().toString(36).substr(2, 9)}`);
        barGradient.setAttribute('x1', '5%');
        barGradient.setAttribute('y1', '3%');
        barGradient.setAttribute('x2', '95%');
        barGradient.setAttribute('y2', '97%');
        
        const barStops = [
            { offset: '0%', color: this.options.accent.highlight, opacity: '0.85' },
            { offset: '12%', color: this.options.accent.metallic[0], opacity: '0.9' },
            { offset: '25%', color: this.options.accent.metallic[1], opacity: '1' },
            { offset: '38%', color: this.options.accent.gradient[8], opacity: '1' },
            { offset: '50%', color: this.options.accent.gradient[9], opacity: '1' },
            { offset: '62%', color: this.options.accent.gradient[10], opacity: '1' },
            { offset: '75%', color: this.options.accent.metallic[4], opacity: '1' },
            { offset: '88%', color: this.options.accent.metallic[5], opacity: '1' },
            { offset: '100%', color: this.options.accent.depth, opacity: '0.98' }
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
        
        // Enterprise Holographic Aura Filter with Premium Light Dispersion
        const holographicAuraFilter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        holographicAuraFilter.setAttribute('id', `holographicAura_${Math.random().toString(36).substr(2, 9)}`);
        holographicAuraFilter.setAttribute('x', '-250%');
        holographicAuraFilter.setAttribute('y', '-250%');
        holographicAuraFilter.setAttribute('width', '600%');
        holographicAuraFilter.setAttribute('height', '600%');
        
        // Outer holographic aura - diamond light dispersion
        const feGlow1 = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGlow1.setAttribute('stdDeviation', '20');
        feGlow1.setAttribute('result', 'holographicAura');
        
        const feColorMatrix6 = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
        feColorMatrix6.setAttribute('in', 'holographicAura');
        feColorMatrix6.setAttribute('type', 'matrix');
        feColorMatrix6.setAttribute('values', '0.4 0.6 1 0 0.25  0.2 0.7 1 0 0.35  0.8 0.9 1 0 0.7  0 0 0 0.18 0');
        feColorMatrix6.setAttribute('result', 'coloredHolographicAura');
        
        // Mid-range diamond glow - premium enterprise effect
        const feGlow2 = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGlow2.setAttribute('in', 'SourceGraphic');
        feGlow2.setAttribute('stdDeviation', '12');
        feGlow2.setAttribute('result', 'diamondGlow');
        
        const feColorMatrix7 = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
        feColorMatrix7.setAttribute('in', 'diamondGlow');
        feColorMatrix7.setAttribute('type', 'matrix');
        feColorMatrix7.setAttribute('values', '0.3 0.8 1 0 0.3  0.1 0.6 1 0 0.4  0.7 0.85 1 0 0.8  0 0 0 0.25 0');
        feColorMatrix7.setAttribute('result', 'coloredDiamondGlow');
        
        // Close range crystalline glow - ultra-premium effect
        const feGlow3 = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGlow3.setAttribute('in', 'SourceGraphic');
        feGlow3.setAttribute('stdDeviation', '6');
        feGlow3.setAttribute('result', 'crystallineGlow');
        
        const feColorMatrix8 = document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix');
        feColorMatrix8.setAttribute('in', 'crystallineGlow');
        feColorMatrix8.setAttribute('type', 'matrix');
        feColorMatrix8.setAttribute('values', '0.2 0.9 1 0 0.35  0.05 0.5 1 0 0.45  0.6 0.8 1 0 0.85  0 0 0 0.35 0');
        feColorMatrix8.setAttribute('result', 'coloredCrystallineGlow');
        
        // Merge all holographic effects
        const holographicMerge = document.createElementNS('http://www.w3.org/2000/svg', 'feMerge');
        const holographicMergeNode1 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        holographicMergeNode1.setAttribute('in', 'coloredHolographicAura');
        const holographicMergeNode2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        holographicMergeNode2.setAttribute('in', 'coloredDiamondGlow');
        const holographicMergeNode3 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        holographicMergeNode3.setAttribute('in', 'coloredCrystallineGlow');
        const holographicMergeNode4 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        holographicMergeNode4.setAttribute('in', 'SourceGraphic');
        
        holographicMerge.appendChild(holographicMergeNode1);
        holographicMerge.appendChild(holographicMergeNode2);
        holographicMerge.appendChild(holographicMergeNode3);
        holographicMerge.appendChild(holographicMergeNode4);
        
        holographicAuraFilter.appendChild(feGlow1);
        holographicAuraFilter.appendChild(feColorMatrix6);
        holographicAuraFilter.appendChild(feGlow2);
        holographicAuraFilter.appendChild(feColorMatrix7);
        holographicAuraFilter.appendChild(feGlow3);
        holographicAuraFilter.appendChild(feColorMatrix8);
        holographicAuraFilter.appendChild(holographicMerge);
        
        defs.appendChild(bgGradient);
        defs.appendChild(barGradient);
        defs.appendChild(deepShadowFilter);
        defs.appendChild(bevelFilter);
        defs.appendChild(holographicAuraFilter);
        svg.appendChild(defs);
        
        // Create enterprise holographic diamond with ultra-premium layered effects
        const diamondPath = this.createUltraSquirclePath(size);
        const diamond = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        diamond.setAttribute('d', diamondPath);
        diamond.setAttribute('fill', `url(#${bgGradient.getAttribute('id')})`);
        diamond.setAttribute('filter', `url(#${deepShadowFilter.getAttribute('id')}) url(#${holographicAuraFilter.getAttribute('id')})`);
        diamond.setAttribute('stroke', 'rgba(255, 255, 255, 0.2)');
        diamond.setAttribute('stroke-width', '0.8');
        svg.appendChild(diamond);
        
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

// Function to inject enhanced logo symbol for template usage
function injectEnhancedLogoSymbol() {
    if (document.getElementById('minaEnhancedLogo')) return;
    
    let svgDefs = document.querySelector('#mina-logo-defs');
    if (!svgDefs) {
        svgDefs = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svgDefs.id = 'mina-logo-defs';
        svgDefs.style.cssText = 'position: absolute; width: 0; height: 0; pointer-events: none;';
        document.body.appendChild(svgDefs);
    }
    
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    
    // Enhanced logo symbol
    const symbol = document.createElementNS('http://www.w3.org/2000/svg', 'symbol');
    symbol.id = 'minaEnhancedLogo';
    symbol.setAttribute('viewBox', '0 0 24 24');
    
    // Define gradients
    const primaryGrad = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
    primaryGrad.id = 'minaEnhancedPrimary';
    primaryGrad.setAttribute('x1', '0%');
    primaryGrad.setAttribute('y1', '0%');
    primaryGrad.setAttribute('x2', '100%');
    primaryGrad.setAttribute('y2', '100%');
    primaryGrad.innerHTML = `
        <stop offset="0%" stop-color="var(--mina-icon-highlight, #7DD3FC)"/>
        <stop offset="30%" stop-color="var(--mina-icon-primary, #38BDF8)"/>
        <stop offset="70%" stop-color="var(--mina-icon-secondary, #8B5CF6)"/>
        <stop offset="100%" stop-color="var(--mina-icon-accent, #A855F7)"/>
    `;
    
    const depthGrad = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
    depthGrad.id = 'minaEnhancedDepth';
    depthGrad.setAttribute('x1', '0%');
    depthGrad.setAttribute('y1', '0%');
    depthGrad.setAttribute('x2', '100%');
    depthGrad.setAttribute('y2', '100%');
    depthGrad.innerHTML = `
        <stop offset="0%" stop-color="var(--mina-icon-depth, #7C3AED)"/>
        <stop offset="100%" stop-color="var(--mina-icon-depth-deep, #6B46C1)"/>
    `;
    
    // Audio wave background
    const waveGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    waveGroup.className = 'mina-waves';
    waveGroup.setAttribute('opacity', '0.2');
    for (let i = 0; i < 5; i++) {
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', '12');
        circle.setAttribute('cy', '12');
        circle.setAttribute('r', 4 + i * 2);
        circle.setAttribute('fill', 'none');
        circle.setAttribute('stroke', 'var(--mina-icon-wave, rgba(139, 92, 246, 0.2))');
        circle.setAttribute('stroke-width', '0.5');
        
        const animate = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
        animate.setAttribute('attributeName', 'opacity');
        animate.setAttribute('values', '0;0.8;0');
        animate.setAttribute('dur', '2s');
        animate.setAttribute('repeatCount', 'indefinite');
        animate.setAttribute('begin', `${i * 0.4}s`);
        circle.appendChild(animate);
        
        waveGroup.appendChild(circle);
    }
    
    // Main bars with enhanced effects
    const barsGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    barsGroup.className = 'mina-bars';
    
    // Left bar
    const leftBar = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    leftBar.className = 'mina-bar-left';
    leftBar.setAttribute('x', '4');
    leftBar.setAttribute('y', '6');
    leftBar.setAttribute('width', '2.5');
    leftBar.setAttribute('height', '10');
    leftBar.setAttribute('rx', '1.25');
    leftBar.setAttribute('fill', 'url(#minaEnhancedPrimary)');
    leftBar.setAttribute('filter', 'drop-shadow(0 2px 4px var(--mina-icon-shadow))');
    
    // Middle bar
    const middleBar = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    middleBar.className = 'mina-bar-middle';
    middleBar.setAttribute('x', '10.75');
    middleBar.setAttribute('y', '8');
    middleBar.setAttribute('width', '2.5');
    middleBar.setAttribute('height', '8');
    middleBar.setAttribute('rx', '1.25');
    middleBar.setAttribute('fill', 'url(#minaEnhancedPrimary)');
    middleBar.setAttribute('filter', 'drop-shadow(0 2px 4px var(--mina-icon-shadow))');
    
    // Right bar  
    const rightBar = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rightBar.className = 'mina-bar-right';
    rightBar.setAttribute('x', '17.5');
    rightBar.setAttribute('y', '6');
    rightBar.setAttribute('width', '2.5');
    rightBar.setAttribute('height', '10');
    rightBar.setAttribute('rx', '1.25');
    rightBar.setAttribute('fill', 'url(#minaEnhancedPrimary)');
    rightBar.setAttribute('filter', 'drop-shadow(0 2px 4px var(--mina-icon-shadow))');
    
    // Baseline
    const baseline = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    baseline.setAttribute('x', '4');
    baseline.setAttribute('y', '18');
    baseline.setAttribute('width', '16');
    baseline.setAttribute('height', '1.5');
    baseline.setAttribute('rx', '0.75');
    baseline.setAttribute('fill', 'url(#minaEnhancedDepth)');
    baseline.setAttribute('filter', 'drop-shadow(0 1px 2px var(--mina-icon-shadow))');
    
    // Metallic overlay
    const metallicOverlay = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    metallicOverlay.className = 'mina-metallic-overlay';
    metallicOverlay.setAttribute('opacity', '0.3');
    
    const highlight = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
    highlight.setAttribute('cx', '12');
    highlight.setAttribute('cy', '10');
    highlight.setAttribute('rx', '8');
    highlight.setAttribute('ry', '4');
    highlight.setAttribute('fill', 'var(--mina-icon-specular, #F8FAFC)');
    highlight.setAttribute('opacity', '0.4');
    metallicOverlay.appendChild(highlight);
    
    // Sheen effect
    const sheen = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    sheen.className = 'mina-sheen';
    sheen.setAttribute('x', '-6');
    sheen.setAttribute('y', '-6');
    sheen.setAttribute('width', '4');
    sheen.setAttribute('height', '36');
    sheen.setAttribute('fill', 'var(--mina-icon-specular, #F8FAFC)');
    sheen.setAttribute('opacity', '0');
    sheen.setAttribute('transform', 'rotate(-45)');
    
    // Assemble symbol
    defs.appendChild(primaryGrad);
    defs.appendChild(depthGrad);
    symbol.appendChild(waveGroup);
    barsGroup.appendChild(leftBar);
    barsGroup.appendChild(middleBar);
    barsGroup.appendChild(rightBar);
    symbol.appendChild(barsGroup);
    symbol.appendChild(baseline);
    symbol.appendChild(metallicOverlay);
    symbol.appendChild(sheen);
    
    defs.appendChild(symbol);
    svgDefs.appendChild(defs);
    
    // Enable fallbacks after symbol creation
    setTimeout(() => {
        const logoElements = document.querySelectorAll('svg[aria-label*="logo"] .mina-fallback');
        logoElements.forEach(fallback => {
            const useElement = fallback.parentElement.querySelector('use[href="#minaEnhancedLogo"]');
            if (useElement && !document.getElementById('minaEnhancedLogo').childElementCount) {
                fallback.style.display = 'block';
            }
        });
    }, 100);
}

// Auto-inject ultra-depth styles when script loads
if (typeof window !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            injectUltraDepthMinaLogoStyles();
            injectEnhancedLogoSymbol();
            minaLogoManager = new MinaLogoManager();
            minaLogoManager.autoInitialize();
        });
    } else {
        injectUltraDepthMinaLogoStyles();
        injectEnhancedLogoSymbol();
        minaLogoManager = new MinaLogoManager();
        minaLogoManager.autoInitialize();
    }
    
    // Enterprise-grade performance and accessibility monitoring
    const enterprisePerformanceMonitor = {
        metrics: {
            renderCount: 0,
            avgRenderTime: 0,
            lastRenderTime: 0,
            memoryUsage: 0
        },
        
        setupAccessibilityFeatures() {
            // Respect prefers-reduced-motion for enterprise accessibility compliance
            if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                document.documentElement.style.setProperty('--mina-animation-duration', '0s');
                document.querySelectorAll('.mina-ultra-depth-3d-icon').forEach(logo => {
                    logo.style.animation = 'none';
                });
            }
            
            // High contrast mode support for enterprise environments
            if (window.matchMedia('(prefers-contrast: high)').matches) {
                document.documentElement.style.setProperty('--mina-filter-intensity', '1.5');
            }
            
            // Enterprise keyboard navigation support
            document.querySelectorAll('[data-mina-logo]').forEach(logo => {
                logo.setAttribute('tabindex', '0');
                logo.setAttribute('role', 'img');
                logo.setAttribute('aria-label', 'Mina Enterprise Logo');
            });
        },
        
        trackPerformance() {
            // Monitor memory usage for enterprise applications
            if (performance.memory) {
                this.metrics.memoryUsage = performance.memory.usedJSHeapSize;
            }
            
            // Log performance metrics for enterprise monitoring
            if (this.metrics.renderCount > 0 && this.metrics.renderCount % 10 === 0) {
                console.debug('Mina Logo Performance Metrics:', {
                    renders: this.metrics.renderCount,
                    avgTime: `${this.metrics.avgRenderTime.toFixed(2)}ms`,
                    memory: `${(this.metrics.memoryUsage / 1024 / 1024).toFixed(2)}MB`
                });
            }
        }
    };
    
    // Handle visibility changes for enterprise performance optimization
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && minaLogoManager) {
            minaLogoManager.pauseAnimationsOnLowPower();
        }
        enterprisePerformanceMonitor.trackPerformance();
    });
    
    // Enterprise accessibility setup
    enterprisePerformanceMonitor.setupAccessibilityFeatures();
    
    // Monitor media query changes for dynamic accessibility
    window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
        if (e.matches) {
            document.documentElement.style.setProperty('--mina-animation-duration', '0s');
        } else {
            document.documentElement.style.removeProperty('--mina-animation-duration');
        }
    });
}

// Make available globally
if (typeof window !== 'undefined') {
    window.MinaAnimatedLogo = MinaAnimatedLogo;
    window.MinaLogoManager = minaLogoManager;
}