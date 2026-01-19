// Enhanced session timeout with countdown timer and auto-extend feedback
let inactivityTime = function () {
    let time;
    let warningTime;
    let countdownInterval;
    let secondsLeft = 30; // 30-second countdown in warning
    let isWarningActive = false;
    
    // Reset timer on various user activities
    const events = [
        'mousemove', 'keypress', 'scroll', 'click', 'keydown', 
        'touchstart', 'touchmove', 'mousedown', 'input',
        'wheel', 'resize', 'focus', 'change'
    ];
    
    events.forEach(event => {
        document.addEventListener(event, function() {
            resetTimer();
            if (isWarningActive) {
                showActivityDetected();
            }
        }, true);
    });
    
    function showWarning() {
        // Check if warning already exists
        if (document.getElementById('sessionWarningModal')) {
            return;
        }
        
        isWarningActive = true;
        secondsLeft = 30; // Reset countdown to 30 seconds
        
        // Create warning modal with countdown
        let modal = document.createElement('div');
        modal.id = 'sessionWarningModal';
        modal.innerHTML = `
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 9999; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(2px);">
                <div style="background: linear-gradient(135deg, #fff, #f8f9fa); padding: 35px; border-radius: 20px; box-shadow: 0 15px 40px rgba(0,0,0,0.4); max-width: 520px; width: 90%; text-align: center; animation: modalSlideIn 0.4s ease-out; border: 3px solid #e74c3c;">
                    <div style="margin-bottom: 25px;">
                        <div style="font-size: 52px; color: #e74c3c; margin-bottom: 15px; animation: bellRing 2s infinite;">🔔</div>
                        <h3 style="color: #2c3e50; margin-bottom: 10px; font-size: 26px; font-weight: 700;">Session Timeout Warning</h3>
                        <div style="height: 3px; background: linear-gradient(90deg, #e74c3c, #f39c12); width: 80px; margin: 0 auto 15px;"></div>
                    </div>
                    
                    <p style="margin-bottom: 25px; color: #555; font-size: 17px; line-height: 1.6;">
                        Your session will expire due to inactivity in:
                    </p>
                    
                    <div style="margin-bottom: 30px; background: rgba(231, 76, 60, 0.1); padding: 20px; border-radius: 12px; border-left: 4px solid #e74c3c;">
                        <div id="countdownTimer" style="font-size: 36px; font-weight: 800; color: #e74c3c; margin: 10px 0; font-family: 'Courier New', monospace;">
                            <span id="countdownSeconds" style="background: rgba(0,0,0,0.1); padding: 5px 15px; border-radius: 8px;">30</span> seconds
                        </div>
                        <div style="width: 100%; background: rgba(236, 240, 241, 0.8); border-radius: 12px; height: 10px; overflow: hidden; margin: 15px 0;">
                            <div id="countdownBar" style="height: 100%; background: linear-gradient(90deg, #e74c3c, #f39c12); width: 100%; transition: width 1s linear; border-radius: 12px;"></div>
                        </div>
                    </div>
                    
                    <div style="background: linear-gradient(135deg, #e8f5e8, #d4edda); padding: 18px; border-radius: 12px; margin-bottom: 20px; border: 2px solid #27ae60;">
                        <p style="margin: 0; color: #155724; font-size: 15px; line-height: 1.5; font-weight: 600;">
                            🎯 <strong>Auto-extend enabled!</strong><br>
                            <span style="font-weight: normal;">Any mouse movement, typing, or clicking will automatically extend your session</span>
                        </p>
                    </div>
                    
                    <div style="display: flex; align-items: center; justify-content: center; gap: 8px; color: #27ae60; font-weight: 600; font-size: 14px; background: rgba(39, 174, 96, 0.1); padding: 12px; border-radius: 8px;">
                        <span style="animation: pulse 2s infinite;">🔄</span>
                        <span>Session auto-extends on any activity</span>
                    </div>
                </div>
            </div>
            <style>
                @keyframes modalSlideIn {
                    from { opacity: 0; transform: translateY(-30px) scale(0.9); }
                    to { opacity: 1; transform: translateY(0) scale(1); }
                }
                
                @keyframes bellRing {
                    0%, 50%, 100% { transform: rotate(0); }
                    5%, 15% { transform: rotate(-10deg); }
                    10%, 20% { transform: rotate(10deg); }
                }
                
                @keyframes pulse {
                    0% { transform: scale(1); opacity: 1; }
                    50% { transform: scale(1.1); opacity: 0.8; }
                    100% { transform: scale(1); opacity: 1; }
                }
                
                @keyframes extendFlash {
                    0% { 
                        background: linear-gradient(135deg, #d4edda, #c3e6cb);
                        border-color: #27ae60;
                        transform: scale(1);
                    }
                    50% { 
                        background: linear-gradient(135deg, #c3e6cb, #b1dfbb);
                        border-color: #219653;
                        transform: scale(1.02);
                    }
                    100% { 
                        background: linear-gradient(135deg, #fff, #f8f9fa);
                        border-color: #e74c3c;
                        transform: scale(1);
                    }
                }
                
                .countdown-warning {
                    animation: pulse 0.8s infinite !important;
                }
                
                .session-extended {
                    animation: extendFlash 1s ease-in-out !important;
                }
                
                .activity-detected {
                    animation: pulse 0.5s 2 !important;
                }
            </style>
        `;
        document.body.appendChild(modal);
        
        // Start countdown
        startCountdown();
    }
    
    function startCountdown() {
        clearInterval(countdownInterval);
        
        countdownInterval = setInterval(function() {
            secondsLeft--;
            
            // Update countdown display
            const countdownElement = document.getElementById('countdownSeconds');
            const countdownBar = document.getElementById('countdownBar');
            
            if (countdownElement && countdownBar) {
                countdownElement.textContent = secondsLeft;
                
                // Update progress bar
                const progressPercent = (secondsLeft / 30) * 100; // 30-second total
                countdownBar.style.width = progressPercent + '%';
                
                // Change color when time is running out
                if (secondsLeft <= 10) {
                    countdownElement.parentElement.classList.add('countdown-warning');
                    countdownBar.style.background = 'linear-gradient(90deg, #c0392b, #e74c3c)';
                } else if (secondsLeft <= 15) {
                    countdownBar.style.background = 'linear-gradient(90deg, #e67e22, #f39c12)';
                }
            }
            
            // Auto logout when countdown reaches 0
            if (secondsLeft <= 0) {
                clearInterval(countdownInterval);
                logout();
            }
        }, 1000);
    }
    
    function showActivityDetected() {
        const modal = document.getElementById('sessionWarningModal');
        if (modal) {
            const content = modal.querySelector('div > div');
            content.classList.add('activity-detected');
            
            // Show "Activity Detected" message briefly
            const activityMsg = document.createElement('div');
            activityMsg.innerHTML = `
                <div style="background: #27ae60; color: white; padding: 8px 15px; border-radius: 20px; font-size: 14px; font-weight: bold; margin-bottom: 10px; animation: slideDown 0.3s ease-out;">
                    ✅ Activity detected - Session extended!
                </div>
                <style>
                    @keyframes slideDown {
                        from { transform: translateY(-10px); opacity: 0; }
                        to { transform: translateY(0); opacity: 1; }
                    }
                </style>
            `;
            
            const existingMsg = modal.querySelector('.activity-message');
            if (existingMsg) {
                existingMsg.remove();
            }
            
            activityMsg.classList.add('activity-message');
            modal.querySelector('div > div').insertBefore(activityMsg, modal.querySelector('div > div').lastElementChild);
            
            // Remove message after 1.5 seconds
            setTimeout(() => {
                if (activityMsg.parentNode) {
                    activityMsg.style.animation = 'slideDown 0.3s reverse';
                    setTimeout(() => {
                        if (activityMsg.parentNode) {
                            activityMsg.remove();
                        }
                    }, 300);
                }
            }, 1500);
        }
    }
    
    function showSessionExtended() {
        isWarningActive = false;
        const modal = document.getElementById('sessionWarningModal');
        if (modal) {
            // Flash green to indicate session extended
            modal.querySelector('div > div').classList.add('session-extended');
            
            // Remove the modal after a brief delay
            setTimeout(() => {
                if (modal.parentNode) {
                    modal.style.animation = 'modalSlideIn 0.3s reverse';
                    setTimeout(() => {
                        if (modal.parentNode) {
                            modal.remove();
                        }
                    }, 300);
                }
            }, 1000);
        }
        
        // Show brief success message
        showTempMessage('Session extended! ✅ Continuing your work...', 'success');
    }
    
    function logout() {
        isWarningActive = false;
        window.location.href = '/session_timeout';
    }
    
    function showTempMessage(message, type) {
        // Remove existing message if any
        const existingMsg = document.getElementById('tempSessionMessage');
        if (existingMsg) {
            existingMsg.remove();
        }
        
        const msgDiv = document.createElement('div');
        msgDiv.id = 'tempSessionMessage';
        msgDiv.innerHTML = `
            <div style="position: fixed; top: 25px; right: 25px; background: ${type === 'success' ? '#27ae60' : '#e74c3c'}; color: white; padding: 15px 25px; border-radius: 10px; box-shadow: 0 6px 20px rgba(0,0,0,0.3); z-index: 10000; animation: messageSlideIn 0.4s ease-out; font-weight: 600; border-left: 4px solid ${type === 'success' ? '#219653' : '#c0392b'};">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 18px;">${type === 'success' ? '✅' : '❌'}</span>
                    <span>${message}</span>
                </div>
            </div>
            <style>
                @keyframes messageSlideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            </style>
        `;
        document.body.appendChild(msgDiv);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            if (msgDiv.parentNode) {
                msgDiv.style.animation = 'messageSlideIn 0.4s reverse';
                setTimeout(() => {
                    if (msgDiv.parentNode) {
                        msgDiv.remove();
                    }
                }, 400);
            }
        }, 3000);
    }
    
    function resetTimer() {
        // Clear existing timers
        clearTimeout(time);
        clearTimeout(warningTime);
        clearInterval(countdownInterval);
        
        // If warning is showing and user becomes active, show extended feedback
        const modal = document.getElementById('sessionWarningModal');
        if (modal) {
            showSessionExtended();
        }
        
        // Set main timeout for 3 minutes (180000 ms)
        time = setTimeout(logout, 180000);
        
        // Show warning after 2.5 minutes (150000 ms)
        warningTime = setTimeout(showWarning, 150000);
    }
    
    // Initialize the timer
    resetTimer();
};

// Initialize only if page is fully loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inactivityTime);
} else {
    inactivityTime();
}

// Additional: Reset timer when page becomes visible (tab switch)
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        // Page is visible again, reset timer
        resetTimer();
    }
});