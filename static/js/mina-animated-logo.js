// Mina Animated Logo Component
// Based on the premium purple gradient design with breathing glow, 
// animated microphone symbol (3 bars forming M), and wordmark with shine effects

class MinaAnimatedLogo {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            size: 200,
            accent: {
                name: "Premium Purple",
                gradient: ["#C084FC", "#9333EA", "#4C1D95"],
                neon: "#A855F7",
            },
            showWordmark: true,
            wordmarkSize: 72,
            ...options
        };
        
        this.init();
    }
    
    init() {
        this.createAppIcon();
        if (this.options.showWordmark) {
            this.createWordmark();
        }
    }
    
    createAppIcon() {
        const { size, accent } = this.options;
        const radius = size * 0.25;
        
        // Create app icon container
        const appIcon = document.createElement('div');
        appIcon.className = 'mina-app-icon';
        appIcon.style.cssText = `
            width: ${size}px;
            height: ${size}px;
            border-radius: ${radius}px;
            background: radial-gradient(circle at 30% 30%, ${accent.gradient[0]}, ${accent.gradient[1]}, ${accent.gradient[2]});
            box-shadow: 0 0 30px ${accent.neon}88, 0 0 60px ${accent.neon}44, inset 0 2px 4px rgba(255,255,255,0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            animation: minaIconBreathe 5s ease-in-out infinite;
        `;
        
        // Create microphone symbol
        const micSymbol = this.createMicSymbol(size * 0.55);
        appIcon.appendChild(micSymbol);
        
        this.container.appendChild(appIcon);
    }
    
    createMicSymbol(size) {
        const { accent } = this.options;
        const barW = Math.round(size * 0.14);
        const barH = Math.round(size * 0.45);
        const gap = Math.round(barW * 0.65);
        const horizH = Math.max(2, Math.round(size * 0.08));
        const horizW = Math.round(size * 0.65);
        
        const micContainer = document.createElement('div');
        micContainer.className = 'mina-mic-symbol';
        micContainer.style.cssText = `
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            width: ${size}px;
            height: ${size}px;
        `;
        
        // Horizontal connector behind
        const connector = document.createElement('div');
        connector.className = 'mina-mic-connector';
        connector.style.cssText = `
            position: absolute;
            width: ${horizW}px;
            height: ${horizH}px;
            border-radius: ${horizH}px;
            background: linear-gradient(90deg, ${accent.gradient[0]}, ${accent.gradient[2]});
            box-shadow: 0 2px 6px rgba(0,0,0,0.5) inset, 0 2px 4px rgba(255,255,255,0.25);
            opacity: 0.9;
            animation: minaConnectorPulse 4s ease-in-out infinite;
        `;
        micContainer.appendChild(connector);
        
        // Three bars forming M
        const barsContainer = document.createElement('div');
        barsContainer.style.cssText = `
            position: relative;
            z-index: 10;
            display: flex;
            align-items: end;
            gap: ${gap}px;
        `;
        
        [1, 0.75, 1].forEach((scale, i) => {
            const bar = document.createElement('div');
            bar.className = `mina-mic-bar mina-mic-bar-${i}`;
            bar.style.cssText = `
                position: relative;
                width: ${barW}px;
                height: ${barH * scale}px;
                border-radius: ${barW}px;
                background: linear-gradient(180deg, ${accent.gradient[0]}, ${accent.gradient[1]}, ${accent.gradient[2]}, ${accent.gradient[1]});
                box-shadow: inset 0 3px 6px rgba(255,255,255,0.5), inset 0 -4px 8px rgba(0,0,0,0.6), 0 8px 16px rgba(0,0,0,0.4), 0 0 16px ${accent.neon}88;
                overflow: hidden;
                animation: minaBarPulse${i} ${2 + i * 0.3}s ease-in-out infinite;
            `;
            
            // Shimmer sweep
            const shimmer = document.createElement('div');
            shimmer.className = 'mina-bar-shimmer';
            shimmer.style.cssText = `
                position: absolute;
                top: -25%;
                left: -50px;
                height: 220%;
                width: 50px;
                transform: rotate(12deg);
                background: linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,0.35), rgba(255,255,255,0));
                filter: blur(0.6px);
                animation: minaShimmerSweep${i} 3.5s ease-in-out infinite;
                animation-delay: ${i * 0.4}s;
            `;
            bar.appendChild(shimmer);
            
            barsContainer.appendChild(bar);
        });
        
        micContainer.appendChild(barsContainer);
        
        // Gloss reflection
        const gloss = document.createElement('div');
        gloss.className = 'mina-mic-gloss';
        gloss.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 50%;
            border-radius: ${size/2}px ${size/2}px 0 0;
            background: linear-gradient(to bottom, rgba(255,255,255,0.55), rgba(255,255,255,0));
            mix-blend-mode: screen;
            pointer-events: none;
            animation: minaGlossGlide 6.5s ease-in-out infinite;
        `;
        micContainer.appendChild(gloss);
        
        return micContainer;
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
            animation: minaWordmarkFadeIn 1.8s ease-out;
        `;
        wordmark.appendChild(text);
        
        // Shine sweep
        const shine = document.createElement('div');
        shine.className = 'mina-wordmark-shine';
        shine.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            height: 100%;
            width: 100%;
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
    
    // Static method to create logo with text for splash/branding
    static createBrandLogo(container, size = 200) {
        const logo = new MinaAnimatedLogo(container, {
            size: size,
            showWordmark: true,
            wordmarkSize: size * 0.36
        });
        return logo;
    }
}

// CSS Animations - Add to page if not already present
if (!document.querySelector('#mina-logo-animations')) {
    const style = document.createElement('style');
    style.id = 'mina-logo-animations';
    style.textContent = `
        @keyframes minaIconBreathe {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        @keyframes minaConnectorPulse {
            0%, 100% { opacity: 0.8; }
            50% { opacity: 1; }
        }
        
        @keyframes minaBarPulse0 {
            0%, 100% { height: var(--bar-height-0, 65px); }
            50% { height: calc(var(--bar-height-0, 65px) * 1.05); }
        }
        
        @keyframes minaBarPulse1 {
            0%, 100% { height: var(--bar-height-1, 48px); }
            50% { height: calc(var(--bar-height-1, 48px) * 1.05); }
        }
        
        @keyframes minaBarPulse2 {
            0%, 100% { height: var(--bar-height-2, 65px); }
            50% { height: calc(var(--bar-height-2, 65px) * 1.05); }
        }
        
        @keyframes minaShimmerSweep0 {
            0% { transform: translateX(-200px) rotate(12deg); }
            100% { transform: translateX(200px) rotate(12deg); }
        }
        
        @keyframes minaShimmerSweep1 {
            0% { transform: translateX(-200px) rotate(12deg); }
            100% { transform: translateX(200px) rotate(12deg); }
        }
        
        @keyframes minaShimmerSweep2 {
            0% { transform: translateX(-200px) rotate(12deg); }
            100% { transform: translateX(200px) rotate(12deg); }
        }
        
        @keyframes minaGlossGlide {
            0%, 100% { opacity: 0.85; }
            50% { opacity: 0.5; }
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

// Export for use
window.MinaAnimatedLogo = MinaAnimatedLogo;