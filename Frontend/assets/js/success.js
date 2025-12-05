// Add this at the top of success.js
console.log('=== SUCCESS PAGE LOAD DEBUG ===');
console.log('URL parameters:', window.location.search);
console.log('sessionStorage data:', sessionStorage.getItem('applicationSuccessData'));
console.log('tempStorage data:', window.__tempStorage?.applicationSuccessData);

// Enhanced data extraction with fallbacks
function extractApplicationData() {
    let applicationData = null;
    
    // Method 1: sessionStorage (primary method)
    try {
        const raw = sessionStorage.getItem('applicationSuccessData');
        if (raw) {
            console.log('Found data in sessionStorage');
            applicationData = JSON.parse(raw);
            // Don't remove from storage yet - keep it for page refreshes
        }
    } catch (e) {
        console.error('sessionStorage parse error:', e);
    }
    
    // Method 2: URL parameters (fallback method)
    if (!applicationData) {
        console.log('Trying URL parameters...');
        const urlParams = new URLSearchParams(window.location.search);
        const ref = urlParams.get('ref');
        
        if (ref) {
            applicationData = {
                reference_number: ref,
                full_name: decodeURIComponent(urlParams.get('name') || 'Applicant'),
                email: urlParams.get('email') || 'your-email@example.com',
                institution_name: decodeURIComponent(urlParams.get('institution') || 'Your Institution'),
                amount: urlParams.get('amount') || '0',
                ward: urlParams.get('ward') || 'your ward',
                phone_number: urlParams.get('phone') || '+254XXXXXXXXX',
                submitted_at: urlParams.get('submitted') || new Date().toISOString()
            };
            console.log('Using URL parameters data:', applicationData);
        }
    }
    
    // Method 3: tempStorage fallback
    if (!applicationData && window.__tempStorage && window.__tempStorage.applicationSuccessData) {
        console.log('Using tempStorage data');
        applicationData = window.__tempStorage.applicationSuccessData;
    }
    
    // Method 4: Check for direct data attribute (last resort)
    if (!applicationData && window.applicationSuccessData) {
        console.log('Using window global data');
        applicationData = window.applicationSuccessData;
    }
    
    console.log('Final applicationData:', applicationData);
    return applicationData;
}

// Update the DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', () => {
    console.log('Success page loaded, checking for application data...');
    
    try {
        const applicationData = extractApplicationData();
        
        if (!applicationData) {
            console.error('No application data found in any storage method');
            showErrorMessage('No application data found. Your application was submitted successfully. Please check your email for confirmation and save your reference number.');
            return;
        }
        
        console.log('Application data loaded successfully:', applicationData);
        populateSuccessPage(applicationData);
        
    } catch (error) {
        console.error('Error in success page:', error);
        showErrorMessage('Error loading application data. Your application was submitted successfully. Please check your email and contact support if you need assistance.');
    }
});

function populateSuccessPage(applicationData) {
    // Populate all success page fields
    const setText = (id, value) => {
        const el = document.getElementById(id);
        if (el && value !== undefined && value !== null) {
            el.textContent = value;
        } else {
            console.warn(`Element with id '${id}' not found or value is undefined`);
        }
    };

    // Reference numbers
    setText('reference-number', applicationData.reference_number);
    setText('success-ref-number', applicationData.reference_number);
    
    // Personal information
    setText('success-applicant-name', applicationData.full_name);
    setText('success-full-name', applicationData.full_name);
    setText('success-applicant-email', applicationData.email);
    setText('success-phone', applicationData.phone_number);
    
    // Institution details
    setText('success-institution', applicationData.institution_name);
    setText('success-amount', parseInt(applicationData.amount || 0, 10).toLocaleString());
    setText('success-ward', formatWardName(applicationData.ward));

    // Dates
    const submittedDate = applicationData.submitted_at ? new Date(applicationData.submitted_at) : new Date();
    
    const timestampEl = document.getElementById('success-timestamp');
    if (timestampEl) {
        timestampEl.textContent = submittedDate.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
    
    const submissionDateEl = document.getElementById('success-submission-date');
    if (submissionDateEl) {
        submissionDateEl.textContent = submittedDate.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
    }

    // Setup copy button
    setupCopyButton();
    
    // Add animations and confetti
    addAnimations();
    triggerConfetti();
    
    console.log('Success page populated successfully!');
}

function formatWardName(ward) {
    if (!ward) return 'Your Ward';
    return ward.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function setupCopyButton() {
    const copyBtn = document.getElementById('copy-ref-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            const refEl = document.getElementById('reference-number');
            if (!refEl) return;
            
            navigator.clipboard.writeText(refEl.textContent).then(() => {
                const originalHTML = copyBtn.innerHTML;
                copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                copyBtn.style.background = '#28a745';
                setTimeout(() => {
                    copyBtn.innerHTML = originalHTML;
                    copyBtn.style.background = '#006400';
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy:', err);
                alert('Failed to copy reference number. Please copy it manually.');
            });
        });
    }
}

function addAnimations() {
    const blocks = document.querySelectorAll('.success-header-banner, .reference-highlight, .email-notification-preview, .success-actions');
    blocks.forEach(b => { 
        if (b) {
            b.style.opacity = '0';
            b.classList.add('fade-in'); 
            setTimeout(() => {
                b.style.opacity = '1';
            }, 100);
        }
    });
}

function triggerConfetti() {
    if (typeof confetti !== 'undefined') {
        setTimeout(() => {
            confetti({ 
                particleCount: 150, 
                spread: 80, 
                origin: { y: 0.6 },
                colors: ['#006400', '#28a745', '#ffffff', '#ffd700']
            });
        }, 500);
    }
}

function showErrorMessage(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.innerHTML = `
            <h3>Application Status</h3>
            <p>${message}</p>
            <div style="margin-top: 15px;">
                <a href="bursary-application-form.html" style="background: #006400; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin-right: 10px;">
                    Submit New Application
                </a>
                <a href="status.html" style="background: #666; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                    Check Application Status
                </a>
            </div>
        `;
        errorDiv.style.display = 'block';
        
        // Hide the success container
        const successContainer = document.querySelector('.enhanced-success-container');
        if (successContainer) {
            successContainer.style.display = 'none';
        }
    }
}