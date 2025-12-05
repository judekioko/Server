// ================================
// Configuration
// ================================
const CONFIG = {
    API_BASE_URL: (() => {
        try {
            if (typeof window.API_BASE_URL === 'string' && /^https?:\/\//.test(window.API_BASE_URL)) {
                return window.API_BASE_URL.replace(/\/+$/,'');
            }
            const ls = localStorage.getItem('API_BASE_URL');
            if (ls && /^https?:\/\//.test(ls)) {
                return ls.replace(/\/+$/,'');
            }
            const meta = document.querySelector('meta[name="api-base"]');
            if (meta && /^https?:\/\//.test(meta.content || '')) {
                return (meta.content || '').replace(/\/+$/,'');
            }
        } catch {}
        const host = window.location.hostname;
        if (host === 'localhost' || host === '127.0.0.1') return 'http://127.0.0.1:8000';
        return window.location.origin;
    })(),
    MAX_FILE_SIZE: 5 * 1024 * 1024,
    ALLOWED_IMAGE_TYPES: ['image/jpeg', 'image/jpg', 'image/png'],
    REQUEST_TIMEOUT: 30000
};

// ================================
// Utility Functions
// ================================
const Utils = {
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },

    validateFile(file, allowedTypes = CONFIG.ALLOWED_IMAGE_TYPES) {
        if (!file) return { valid: true };

        if (file.size > CONFIG.MAX_FILE_SIZE) {
            return {
                valid: false,
                error: `File size must be less than ${CONFIG.MAX_FILE_SIZE / 1024 / 1024}MB`
            };
        }

        if (!allowedTypes.includes(file.type)) {
            return {
                valid: false,
                error: `Only JPG/PNG images allowed. File type must be one of: ${allowedTypes.join(', ')}`
            };
        }

        return { valid: true };
    },

    formatErrorMessage(data) {
        if (data.detail) {
            return data.detail;
        }
        
        if (typeof data === 'object') {
            const errors = [];
            for (const [field, messages] of Object.entries(data)) {
                const fieldName = field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                const errorMsg = Array.isArray(messages) ? messages.join(', ') : messages;
                errors.push(`${fieldName}: ${errorMsg}`);
            }
            return errors.join('\n');
        }
        
        return 'An unexpected error occurred. Please try again.';
    },

    saveToStorage(key, data) {
        try {
            sessionStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (e) {
            console.warn('sessionStorage failed, using fallback:', e);
            if (!window.__tempStorage) window.__tempStorage = {};
            window.__tempStorage[key] = data;
            return false;
        }
    },

    getFromStorage(key) {
        try {
            const data = sessionStorage.getItem(key);
            return data ? JSON.parse(data) : null;
        } catch (e) {
            if (window.__tempStorage && window.__tempStorage[key]) {
                return window.__tempStorage[key];
            }
            return null;
        }
    }
};

// ================================
// Missing Functions
// ================================
function toggleInstitutionDetails() {
    console.log('Level of study changed');
}

function toggleInstitutionFields() {
    console.log('Institution type changed');
}

window.toggleInstitutionDetails = toggleInstitutionDetails;
window.toggleInstitutionFields = toggleInstitutionFields;

// ================================
// Bursary Page Animations and Logic
// ================================
document.addEventListener("DOMContentLoaded", () => {
    console.log('Bursary application form loaded');

    // Toggle between application form and embedded status checker
    const showApplyBtn = document.getElementById('show-apply-btn');
    const showStatusBtn = document.getElementById('show-status-btn');
    const statusSection = document.getElementById('status-section');
    const formSection = document.getElementById('bursaryApplicationForm');
    const showEditBtn = document.getElementById('show-edit-btn');
    const editSection = document.getElementById('edit-section');

    function showApply() {
        if (statusSection) statusSection.style.display = 'none';
        if (editSection) editSection.style.display = 'none';
        if (formSection) formSection.style.display = 'block';
        
        window.__editMode = null;
        const editHint = document.getElementById('edit-hint');
        if (editHint) editHint.style.display = 'none';
    }

    function showStatus() {
        if (formSection) formSection.style.display = 'none';
        if (editSection) editSection.style.display = 'none';
        if (statusSection) statusSection.style.display = 'block';
        
        const statusResult = document.getElementById('embedded-status-result');
        if (statusResult) statusResult.style.display = 'none';
        const statusError = document.getElementById('embedded-status-error');
        if (statusError) statusError.style.display = 'none';
    }

    function showEdit() {
        if (statusSection) statusSection.style.display = 'none';
        if (formSection) formSection.style.display = 'none';
        if (editSection) editSection.style.display = 'block';
        
        const editError = document.getElementById('edit-error');
        if (editError) editError.style.display = 'none';
    }

    if (showApplyBtn) showApplyBtn.addEventListener('click', showApply);
    if (showStatusBtn) showStatusBtn.addEventListener('click', showStatus);
    if (showEditBtn) showEditBtn.addEventListener('click', showEdit);

    // Embedded status checker logic
    const embBtn = document.getElementById('embedded-check-status-btn');
    const embInput = document.getElementById('embedded-ref-input');

    function setEmbText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    // Embedded edit functionality
    const editLoadBtn = document.getElementById('edit-load-btn');
    const editRefInput = document.getElementById('edit-ref-input');
    const editEmailInput = document.getElementById('edit-email-input');

    function showEditError(msg) {
        const el = document.getElementById('edit-error');
        if (el) {
            el.textContent = msg || '';
            el.style.display = msg ? 'block' : 'none';
        }
    }

    function prefillFormFromApplication(app) {
        console.log('Prefilling form with application data:', app);
        
        const mapping = {
            'full_name': 'full-name',
            'email': 'email',
            'gender': 'gender',
            'disability': 'disability',
            'id_number': 'id-number',
            'phone_number': 'phone-number',
            'guardian_phone': 'guardian-phone',
            'guardian_id': 'guardian-id',
            'ward': 'ward',
            'village': 'village',
            'chief_name': 'chief-name',
            'chief_phone': 'chief-phone',
            'sub_chief_name': 'sub-chief-name',
            'sub_chief_phone': 'sub-chief-phone',
            'level_of_study': 'level-of-study',
            'institution_type': 'institution-type',
            'institution_name': 'institution-name',
            'admission_number': 'admission-number',
            'amount': 'amount',
            'mode_of_study': 'mode-of-study',
            'year_of_study': 'year-of-study',
            'family_status': 'family-status',
            'father_income': 'father-income',
            'mother_income': 'mother-income'
        };

        Object.entries(mapping).forEach(([apiKey, htmlId]) => {
            const el = document.getElementById(htmlId);
            if (!el) {
                console.warn(`Element not found: ${htmlId}`);
                return;
            }
            
            const value = app[apiKey];
            console.log(`Setting ${htmlId} to:`, value);
            
            if (el.type === 'checkbox') {
                el.checked = !!value;
            } else if (el.tagName === 'SELECT') {
                const option = Array.from(el.options).find(opt => opt.value === value);
                if (option) {
                    el.value = value;
                }
            } else {
                el.value = value ?? '';
            }
        });

        if (typeof toggleFamilyProof === 'function') {
            toggleFamilyProof();
        }
    }

    async function postJSON(url, payload) {
        console.log('Making POST request to:', url, 'with payload:', payload);
        
        const res = await fetch(url, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': Utils.getCsrfToken() || ''
            },
            body: JSON.stringify(payload)
        });
        
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            throw new Error(data?.error || data?.detail || 'Request failed');
        }
        return data;
    }

    if (editLoadBtn && editRefInput && editEmailInput) {
        editLoadBtn.addEventListener('click', async () => {
            const ref = (editRefInput.value || '').trim();
            const email = (editEmailInput.value || '').trim();
            
            if (!ref) {
                showEditError('Please enter your reference number');
                return;
            }
            
            if (!email) {
                showEditError('Please enter your email address');
                return;
            }

            showEditError('');
            editLoadBtn.disabled = true;
            const originalText = editLoadBtn.innerHTML;
            editLoadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';

            try {
                console.log('Checking edit eligibility for:', ref, email);
                
                const elig = await postJSON(`${CONFIG.API_BASE_URL}/api/bursary/check-edit-eligibility/`, {
                    reference_number: ref,
                    email: email
                });
                
                console.log('Edit eligibility response:', elig);
                
                if (!elig.can_edit) {
                    showEditError(elig.reason || 'You cannot edit this application. Editing is only allowed within 24 hours of submission.');
                    return;
                }

                const detail = await postJSON(`${CONFIG.API_BASE_URL}/api/bursary/get-application-for-edit/`, {
                    reference_number: ref,
                    email: email
                });
                
                console.log('Application detail response:', detail);
                
                if (!detail?.application) {
                    showEditError('Failed to load application for editing');
                    return;
                }

                prefillFormFromApplication(detail.application);
                const hint = document.getElementById('edit-hint');
                if (hint) hint.style.display = 'block';
                
                window.__editMode = { 
                    reference_number: ref, 
                    email: email 
                };
                
                showApply();
                
                const timeRemaining = detail.edit_time_remaining || 'up to 24 hours from submission';
                alert(`Edit mode activated! You can now update your application. Time remaining: ${timeRemaining}`);
                
            } catch (e) {
                console.error('Edit load error:', e);
                showEditError(e.message || 'Failed to verify edit eligibility. Please check your reference number and email.');
            } finally {
                editLoadBtn.disabled = false;
                editLoadBtn.innerHTML = originalText;
            }
        });
    }

    function embFormatAmount(v) {
        const n = parseInt(v || 0, 10);
        return isNaN(n) ? '0' : n.toLocaleString();
    }

    function embPrettyWard(w) {
        return (w || '').replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    async function embeddedFetchStatus(reference) {
        const controller = new AbortController();
        const to = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT);
        
        try {
            console.log('Fetching status for reference:', reference);
            
            const res = await fetch(`${CONFIG.API_BASE_URL}/api/bursary/applications/${encodeURIComponent(reference)}/`, {
                method: 'GET',
                headers: { 'Accept': 'application/json' },
                signal: controller.signal
            });
            
            clearTimeout(to);
            
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                const msg = data?.error || data?.detail || 'Application not found';
                throw new Error(msg);
            }

            const data = await res.json();
            console.log('Status response:', data);
            return data;
            
        } catch (e) {
            clearTimeout(to);
            console.error('Status fetch error:', e);
            throw e;
        }
    }

    function renderEmbeddedResult(app) {
        console.log('Rendering embedded result:', app);
        
        setEmbText('emb-res-ref', app.reference_number);
        setEmbText('emb-res-name', app.full_name);
        setEmbText('emb-res-institution', app.institution_name);
        setEmbText('emb-res-amount', embFormatAmount(app.amount));
        setEmbText('emb-res-ward', embPrettyWard(app.ward));
        
        try {
            const d = new Date(app.submitted_at);
            setEmbText('emb-res-submitted', d.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            }));
        } catch {
            setEmbText('emb-res-submitted', app.submitted_at || '');
        }
        
        const statusEl = document.getElementById('emb-res-status');
        if (statusEl) {
            const status = (app.status || 'pending').toLowerCase();
            statusEl.textContent = status.toUpperCase();
            
            if (status === 'approved') {
                statusEl.style.color = '#008000';
            } else if (status === 'rejected') {
                statusEl.style.color = '#bb0000';
            } else {
                statusEl.style.color = '#ff9800';
            }
        }
        
        const err = document.getElementById('embedded-status-error');
        if (err) err.style.display = 'none';
        
        const resDiv = document.getElementById('embedded-status-result');
        if (resDiv) resDiv.style.display = 'block';
    }

    function showEmbeddedError(msg) {
        console.error('Showing embedded error:', msg);
        
        const err = document.getElementById('embedded-status-error');
        if (err) {
            err.textContent = msg;
            err.style.display = 'block';
        }
        
        const resDiv = document.getElementById('embedded-status-result');
        if (resDiv) resDiv.style.display = 'none';
    }

    if (embBtn && embInput) {
        embBtn.addEventListener('click', async () => {
            const ref = (embInput.value || '').trim();
            if (!ref) {
                showEmbeddedError('Please enter your reference number');
                return;
            }
            
            showEmbeddedError('');
            embBtn.disabled = true;
            const originalText = embBtn.innerHTML;
            embBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';

            try {
                const data = await embeddedFetchStatus(ref);
                renderEmbeddedResult(data);
            } catch (e) {
                console.error('Status check error:', e);
                showEmbeddedError(e.message || 'Failed to fetch application status. Please check your reference number.');
            } finally {
                embBtn.disabled = false;
                embBtn.innerHTML = originalText;
            }
        });

        if (embInput) {
            embInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    embBtn.click();
                }
            });
        }
    }

    // Form Logic & Conditional Fields
    const familyStatus = document.getElementById("family-status");
    const orphanProof = document.getElementById("orphan-proof");
    const incomeFields = document.getElementById("income-fields");
    const singleParentProofContainer = document.getElementById('single-parent-proof-container');
    const orphanSiblingProofContainer = document.getElementById('orphan-sibling-proof-container');
    const motherDeathInput = document.getElementById('mother-death-certificate');
    const fatherDeathInput = document.getElementById('father-death-certificate');
    const disabilityCheckbox = document.getElementById('disability');
    const disabilityProofInput = document.getElementById('disability-proof');
    const deceasedSingleParentContainer = document.getElementById('deceased-single-parent-container');

    if (familyStatus && orphanProof && incomeFields) {
        const fatherIncome = document.getElementById("father-income")?.closest("label");
        const motherIncome = document.getElementById("mother-income")?.closest("label");
        const fatherDeath = document.getElementById("father-death-certificate")?.closest("label");
        const motherDeath = document.getElementById("mother-death-certificate")?.closest("label");

        function toggleFamilyProof() {
            const value = familyStatus.value;
            console.log('Family status changed to:', value);

            orphanProof.style.display = "none";
            incomeFields.style.display = "none";
            if (singleParentProofContainer) singleParentProofContainer.style.display = 'none';
            if (orphanSiblingProofContainer) orphanSiblingProofContainer.style.display = 'none';
            if (deceasedSingleParentContainer) deceasedSingleParentContainer.style.display = 'none';

            if (fatherIncome) fatherIncome.style.display = "none";
            if (motherIncome) motherIncome.style.display = "none";
            if (fatherDeath) fatherDeath.style.display = "none";
            if (motherDeath) motherDeath.style.display = "none";

            const fatherDeathInput = document.getElementById("father-death-certificate");
            const motherDeathInput = document.getElementById("mother-death-certificate");
            if (fatherDeathInput) fatherDeathInput.removeAttribute('required');
            if (motherDeathInput) motherDeathInput.removeAttribute('required');

            switch (value) {
                case "both-parents-alive":
                    incomeFields.style.display = "block";
                    if (fatherIncome) fatherIncome.style.display = "block";
                    if (motherIncome) motherIncome.style.display = "block";
                    break;

                case "single-parent":
                    incomeFields.style.display = "block";
                    if (fatherIncome) fatherIncome.style.display = "block";
                    if (motherIncome) motherIncome.style.display = "block";
                    if (singleParentProofContainer) singleParentProofContainer.style.display = 'block';
                    break;

                case "partial-orphan":
                    orphanProof.style.display = "block";
                    incomeFields.style.display = "block";
                    if (singleParentProofContainer) singleParentProofContainer.style.display = 'block';
                    if (deceasedSingleParentContainer) deceasedSingleParentContainer.style.display = 'block';
                    if (fatherDeath) fatherDeath.style.display = "block";
                    if (motherDeath) motherDeath.style.display = "block";
                    if (fatherIncome) fatherIncome.style.display = "block";
                    if (motherIncome) motherIncome.style.display = "block";
                    break;

                case "total-orphan":
                    orphanProof.style.display = "block";
                    if (singleParentProofContainer) singleParentProofContainer.style.display = 'block';
                    if (deceasedSingleParentContainer) deceasedSingleParentContainer.style.display = 'block';
                    
                    // For total orphan, show both death certificate options
                    if (fatherDeath) fatherDeath.style.display = "block";
                    if (motherDeath) motherDeath.style.display = "block";
                    break;
            }
        }

        window.toggleFamilyProof = toggleFamilyProof;

        toggleFamilyProof();
        familyStatus.addEventListener("change", toggleFamilyProof);
    }
    
    if (motherDeathInput) {
        motherDeathInput.addEventListener('change', () => {
            if (!orphanSiblingProofContainer) return;
            if (motherDeathInput.files && motherDeathInput.files[0]) {
                orphanSiblingProofContainer.style.display = 'block';
            } else {
                orphanSiblingProofContainer.style.display = 'none';
            }
        });
    }
    
    if (fatherDeathInput) {
        fatherDeathInput.addEventListener('change', () => {
            if (!orphanSiblingProofContainer) return;
            if (fatherDeathInput.files && fatherDeathInput.files[0]) {
                orphanSiblingProofContainer.style.display = 'block';
            } else {
                orphanSiblingProofContainer.style.display = 'none';
            }
        });
    }
    
    if (disabilityCheckbox && disabilityProofInput) {
        disabilityCheckbox.addEventListener('change', () => {
            if (disabilityCheckbox.checked) {
                disabilityProofInput.closest('label')?.classList?.add('required');
            } else {
                disabilityProofInput.closest('label')?.classList?.remove('required');
            }
        });
    }

    // Form submission handler
    const submitBtn = document.getElementById('submit-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', function(e) {
            e.preventDefault();
            submitApplicationToAPI();
        });
    }

    // File validation on change
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (!file) return;
            
            const validation = Utils.validateFile(file, CONFIG.ALLOWED_IMAGE_TYPES);
            if (!validation.valid) {
                alert(validation.error);
                this.value = '';
            }
        });
    });

    // Phone number formatting
    const pn = document.getElementById('phone-number');
    const gp = document.getElementById('guardian-phone');
    const cp = document.getElementById('chief-phone');
    const scp = document.getElementById('sub-chief-phone');
    const idn = document.getElementById('id-number');
    
    function digitsOnly(v){ return (v||'').replace(/\D+/g,''); }
    
    function normalizePhone(v){
        const d = digitsOnly(v);
        if (d.startsWith('254') && d.length >= 12) return '+254' + d.slice(3, 12);
        if ((d.startsWith('7') || d.startsWith('1')) && d.length >= 9) return '0' + d.slice(0, 9);
        if (d.startsWith('0') && d.length >= 10) return d.slice(0, 10);
        return v;
    }
    
    [pn, gp, cp, scp].forEach(el => {
        if (!el) return;
        el.addEventListener('input', () => { el.value = normalizePhone(el.value); });
        el.addEventListener('blur', () => { el.value = normalizePhone(el.value); });
    });
    
    if (idn){
        idn.addEventListener('input', () => { 
            idn.value = digitsOnly(idn.value).slice(0,12); 
        });
    }

    // Form validation
    function setFieldError(el, message){
        if (!el) return;
        el.classList.add('invalid');
        try { el.setAttribute('aria-invalid', 'true'); } catch {}
        try { el.setAttribute('aria-describedby', el.id + '-error'); } catch {}
        
        let id = el.id + '-error';
        let err = document.getElementById(id);
        if (!err){
            err = document.createElement('div');
            err.id = id;
            err.className = 'field-error';
            el.insertAdjacentElement('afterend', err);
        }
        err.textContent = message || '';
    }
    
    function clearFieldError(el){
        if (!el) return;
        el.classList.remove('invalid');
        try { el.removeAttribute('aria-invalid'); } catch {}
        try { el.removeAttribute('aria-describedby'); } catch {}
        
        let id = el.id + '-error';
        let err = document.getElementById(id);
        if (err) err.textContent = '';
    }
    
    function validateAll(){
        let ok = true;
        let firstInvalid = null;
        
        const email = document.getElementById('email');
        const amount = document.getElementById('amount');
        const phone = document.getElementById('phone-number');
        const gphone = document.getElementById('guardian-phone');
        const idnum = document.getElementById('id-number');
        const ward = document.getElementById('ward');
        
        [email, amount, phone, gphone, idnum, ward].forEach(clearFieldError);

        // Email validation
        if (email && !email.value.includes('@')){ 
            setFieldError(email, 'Please enter a valid email address'); 
            if (!firstInvalid) firstInvalid = email; 
            ok = false; 
        }

        // Amount validation
        const amtVal = amount ? parseInt(amount.value || '0', 10) : 0;
        if (amount && (!amtVal || amtVal <= 0)){ 
            setFieldError(amount, 'Please enter a valid amount (greater than 0)'); 
            if (!firstInvalid) firstInvalid = amount; 
            ok = false; 
        }

        // Phone validation
        const phonePattern = /^(\+254(?:7|1)\d{8}|0(?:7|1)\d{8})$/;
        if (phone && !phonePattern.test(phone.value)){ 
            setFieldError(phone, 'Please enter a valid phone number (format: 07XXXXXXXX / 01XXXXXXXX or +2547/1XXXXXXXX)'); 
            if (!firstInvalid) firstInvalid = phone; 
            ok = false; 
        }
        
        if (gphone && !phonePattern.test(gphone.value)){ 
            setFieldError(gphone, 'Please enter a valid guardian phone number (format: 07XXXXXXXX / 01XXXXXXXX or +2547/1XXXXXXXX)'); 
            if (!firstInvalid) firstInvalid = gphone; 
            ok = false; 
        }

        // ID validation
        const idDigits = (idnum ? idnum.value : '').replace(/\D+/g,'');
        if (idnum && (idDigits.length < 4 || idDigits.length > 12)){ 
            setFieldError(idnum, 'ID/Birth Certificate number must be 4-12 digits'); 
            if (!firstInvalid) firstInvalid = idnum; 
            ok = false; 
        }

        // Ward validation
        if (ward && !ward.value){ 
            setFieldError(ward, 'Please select your ward'); 
            if (!firstInvalid) firstInvalid = ward; 
            ok = false; 
        }

        if (firstInvalid) {
            firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstInvalid.focus();
        }
        
        return ok;
    }

    ['email','amount','phone-number','guardian-phone','id-number','ward'].forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.addEventListener('input', () => { clearFieldError(el); });
        el.addEventListener('blur', () => { validateAll(); });
    });

    window.validateAll = validateAll;
    
    console.log('Bursary form initialization complete');
});

// ================================
// Form Submission to API - FIXED
// ================================
async function submitApplicationToAPI() {
    console.log('=== FORM SUBMISSION STARTED ===');
    
    const submitBtn = document.getElementById('submit-btn');
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error-message');

    if (errorDiv) errorDiv.style.display = 'none';

    // Basic validation checks
    const confirmationCheck = document.getElementById('confirmation');
    const residencyConfirm = document.getElementById('residency-confirm');
    const consentCheck = document.getElementById('data-consent');

    if (!residencyConfirm?.checked) {
        showError('Please confirm that you are a resident of Masinga Constituency.');
        return;
    }

    if (!confirmationCheck?.checked) {
        showError('Please confirm that all details are correct before submitting.');
        return;
    }

    if (!consentCheck?.checked) {
        showError('You must consent to the data protection terms to submit your application.');
        return;
    }

    // Form validation
    if (typeof window.validateAll === 'function') {
        const ok = window.validateAll();
        if (!ok) {
            showError('Please fix the validation errors above before submitting.');
            return;
        }
    }

    // File validation
    const requiredFiles = [
        { id: 'id-upload-front', name: 'ID Front Side' },
        { id: 'chief-letter', name: 'Chief/Sub-Chief Letter' }
    ];

    for (const { id, name } of requiredFiles) {
        const input = document.getElementById(id);
        if (!input?.files[0]) {
            showError(`Please upload ${name}`);
            return;
        }
    }

    // Show loading state
    if (submitBtn) submitBtn.disabled = true;
    if (loadingDiv) loadingDiv.style.display = 'block';

    const controller = new AbortController();
    const timeout = setTimeout(() => {
        controller.abort();
        showError('Request timeout. Please check your connection and try again.');
        if (submitBtn) submitBtn.disabled = false;
        if (loadingDiv) loadingDiv.style.display = 'none';
    }, CONFIG.REQUEST_TIMEOUT);

    try {
        console.log('Preparing form data...');
        const formData = new FormData();

        // COMPLETE FIELD MAPPINGS - INCLUDING ALL CHECKBOXES
        const fieldMappings = {
            'full-name': 'full_name',
            'gender': 'gender',
            'disability': 'disability',
            'id-number': 'id_number',
            'phone-number': 'phone_number',
            'email': 'email',
            'guardian-phone': 'guardian_phone',
            'guardian-id': 'guardian_id',
            'ward': 'ward',
            'village': 'village',
            'chief-name': 'chief_name',
            'chief-phone': 'chief_phone',
            'sub-chief-name': 'sub_chief_name',
            'sub-chief-phone': 'sub_chief_phone',
            'level-of-study': 'level_of_study',
            'institution-type': 'institution_type',
            'institution-name': 'institution_name',
            'admission-number': 'admission_number',
            'amount': 'amount',
            'mode-of-study': 'mode_of_study',
            'year-of-study': 'year_of_study',
            'family-status': 'family_status',
            'father-income': 'father_income',
            'mother-income': 'mother_income',
            // CHECKBOX FIELDS - ADDED
            'residency-confirm': 'residency_confirm',
            'confirmation': 'confirmation',
            'data-consent': 'data_consent',
            'communication-consent': 'communication_consent'
        };

        console.log('Adding form fields...');
        for (const [htmlId, apiName] of Object.entries(fieldMappings)) {
            const element = document.getElementById(htmlId);
            if (element) {
                if (element.type === 'checkbox') {
                    formData.append(apiName, element.checked);
                    console.log(`Added checkbox: ${apiName} = ${element.checked}`);
                } else if (apiName === 'amount') {
                    formData.append(apiName, parseInt(element.value) || 0);
                    console.log(`Added amount: ${apiName} = ${parseInt(element.value)}`);
                } else {
                    formData.append(apiName, element.value || '');
                    console.log(`Added field: ${apiName} = ${element.value}`);
                }
            } else {
                console.warn(`Field not found: ${htmlId}`);
            }
        }

        // CORRECTED FILE FIELD MAPPINGS
        const fileFields = [
            { id: 'applicant-photo', name: 'applicant_photo' },
            { id: 'id-upload-front', name: 'id_upload_front' },
            { id: 'id-upload-back', name: 'id_upload_back' },
            { id: 'admission-letter', name: 'admission_letter' },
            { id: 'transcript', name: 'transcript' },
            { id: 'chief-letter', name: 'chief_letter' },
            { id: 'disability-proof', name: 'disability_proof' },
            { id: 'single-parent-proof', name: 'single_parent_proof' },
            { id: 'orphan-sibling-proof', name: 'orphan_sibling_proof' },
            { id: 'father-death-certificate', name: 'father_death_certificate' },
            { id: 'mother-death-certificate', name: 'mother_death_certificate' },
            { id: 'deceased-single-parent-certificate', name: 'deceased_single_parent_certificate' }
        ];

        console.log('Adding file fields...');
        for (const { id, name } of fileFields) {
            const input = document.getElementById(id);
            if (input?.files[0]) {
                formData.append(name, input.files[0]);
                console.log(`Added file: ${name}`);
            } else {
                console.log(`No file for: ${name}`);
            }
        }

        // Debug: Show all form data
        console.log('=== FORM DATA DEBUG ===');
        for (let pair of formData.entries()) {
            console.log(pair[0] + ': ', pair[1]);
        }
        console.log('=== END FORM DATA DEBUG ===');

        console.log('Form data prepared, sending to API...');

        const csrfToken = Utils.getCsrfToken();
        const editMode = window.__editMode || null;
        
        let url = `${CONFIG.API_BASE_URL}/api/bursary/apply/`;
        let method = 'POST';
        
        if (editMode?.reference_number && editMode?.email) {
            formData.append('email', editMode.email);
            url = `${CONFIG.API_BASE_URL}/api/bursary/applications/${encodeURIComponent(editMode.reference_number)}/edit/`;
            method = 'PUT';
            console.log('Edit mode activated for reference:', editMode.reference_number);
        }

        console.log(`Making ${method} request to: ${url}`);

        const response = await fetch(url, {
            method: method,
            headers: {
                'X-CSRFToken': csrfToken || '',
            },
            body: formData,
            signal: controller.signal
        });

        clearTimeout(timeout);

        console.log('=== API RESPONSE DEBUG ===');
        console.log('Response status:', response.status);
        console.log('Response OK:', response.ok);
        
        // Get raw response text first for debugging
        const responseText = await response.text();
        console.log('Raw response text:', responseText);

        let data;
        try {
            data = JSON.parse(responseText);
            console.log('Parsed JSON data:', data);
        } catch (e) {
            console.error('JSON parse error:', e);
            throw new Error('Invalid response from server');
        }

        if (!response.ok) {
            console.error('API Error response:', data);
            throw new Error(Utils.formatErrorMessage(data) || `Server error: ${response.status}`);
        }

        console.log('✅ API call successful!');

        // SUCCESS: Handle the response
        if (loadingDiv) loadingDiv.style.display = 'none';

        if (editMode) {
            // Edit mode success
            window.__editMode = null;
            alert(`Application updated successfully${data.edit_time_remaining ? `. Time remaining: ${data.edit_time_remaining}` : ''}`);
            return;
        }

        // NEW APPLICATION SUCCESS
        console.log('🎉 Application submitted successfully!');
        console.log('Reference number from response:', data.reference_number);
        console.log('Full response data:', data);

        // Extract reference number
        const refNumber = data.reference_number;
        if (!refNumber) {
            console.error('No reference number in response:', data);
            throw new Error('No reference number received from server');
        }

        // Prepare application data for success page
        const applicationData = {
            reference_number: refNumber,
            full_name: document.getElementById('full-name').value,
            email: document.getElementById('email').value,
            institution_name: document.getElementById('institution-name').value,
            amount: document.getElementById('amount').value,
            ward: document.getElementById('ward').value,
            phone_number: document.getElementById('phone-number').value,
            submitted_at: new Date().toISOString()
        };

        console.log('Application data for success page:', applicationData);

        // Save to storage FIRST
        const storageSuccess = Utils.saveToStorage('applicationSuccessData', applicationData);
        console.log('Data saved to storage:', storageSuccess);

        // SIMPLIFIED SUCCESS FLOW - Direct redirect without inline success
        console.log('Redirecting to success page...');
        
        // ALWAYS include the reference number in the redirect URL
        const params = new URLSearchParams();
        params.append('ref', applicationData.reference_number);

        let successUrl = 'success.html';

        if (storageSuccess) {
            console.log('Redirecting to success page with session storage...');
            window.location.href = successUrl + '?' + params.toString();
        } else {
            console.log('Using URL parameters for success page (fallback)...');
            // Use full URL parameters as fallback
            params.append('name', applicationData.full_name);
            params.append('email', applicationData.email);
            params.append('institution', applicationData.institution_name);
            params.append('amount', applicationData.amount);
            params.append('ward', applicationData.ward);
            params.append('phone', applicationData.phone_number);
            params.append('submitted', applicationData.submitted_at);

            window.location.href = successUrl + '?' + params.toString();
        }

    } catch (error) {
        clearTimeout(timeout);
        console.error('Submission error:', error);
        
        if (loadingDiv) loadingDiv.style.display = 'none';
        if (submitBtn) submitBtn.disabled = false;
        
        let errorMessage = error.message;
        if (error.name === 'AbortError') {
            errorMessage = 'Request timeout. Please check your connection and try again.';
        } else if (!navigator.onLine) {
            errorMessage = 'No internet connection. Please check your network and try again.';
        }
        
        showError(errorMessage);
    }
}

// ================================
// Error Display Function
// ================================
function showError(message) {
    console.error('Showing error:', message);
    
    const errorDiv = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    
    if (errorText) errorText.textContent = message;
    if (errorDiv) {
        errorDiv.style.display = 'block';
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    // Auto-hide after 10 seconds
    setTimeout(() => {
        if (errorDiv) errorDiv.style.display = 'none';
    }, 10000);
}