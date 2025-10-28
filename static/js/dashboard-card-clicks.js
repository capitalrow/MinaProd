/**
 * Dashboard Meeting Card Click Handlers
 * Simple, bulletproof implementation for card navigation
 */

(function() {
    'use strict';
    
    console.log('🎯 Dashboard card click handler loaded');
    
    function attachClickHandlers() {
        const cards = document.querySelectorAll('.meeting-card');
        console.log(`🔍 Found ${cards.length} meeting cards to make clickable`);
        
        cards.forEach((card, index) => {
            const sessionId = card.getAttribute('data-session-id');
            const meetingId = card.getAttribute('data-meeting-id');
            const meetingTitle = card.getAttribute('data-meeting-title');
            
            console.log(`Card ${index + 1}: meeting=${meetingId}, session=${sessionId || 'NO SESSION'}`);
            
            if (!sessionId) {
                console.warn(`⚠️ Card ${index + 1} has no session ID - skipping`);
                return;
            }
            
            // Remove any existing handlers
            card.style.cursor = 'pointer';
            
            // Add click handler
            card.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                console.log(`✅ Card clicked! Navigating to /sessions/${sessionId}/refined`);
                window.location.href = `/sessions/${sessionId}/refined`;
            });
            
            console.log(`✅ Handler attached to card ${index + 1}`);
        });
        
        console.log(`🎉 All ${cards.length} clickable cards ready!`);
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', attachClickHandlers);
    } else {
        attachClickHandlers();
    }
    
    // Also export for manual calling
    window.attachDashboardCardHandlers = attachClickHandlers;
    
})();
