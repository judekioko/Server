// ================================
// Configuration
// ================================
const CONFIG = {
    API_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://127.0.0.1:8000'
        : window.location.origin,
    MAX_FILE_SIZE: 5 * 1024 * 1024, // 5MB in bytes
    ALLOWED_IMAGE_TYPES: ['image/jpeg', 'image/jpg', 'image/png'],
    ALLOWED_DOC_TYPES: ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'],
    REQUEST_TIMEOUT: 30000 // 30 seconds
};

// ================================
// Utility Functions
// ================================
const Utils = {
    /**
     * Get CSRF token from cookie
     */
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

    /**
     * Validate file size and type
     */
    validateFile(file, allowedTypes = CONFIG.ALLOWED_IMAGE_TYPES) {
        if (!file) return { valid: true }; // Optional file

        if (file.size > CONFIG.MAX_FILE_SIZE) {
            return {
                valid: false,
                error: `File size must be less than ${CONFIG.MAX_FILE_SIZE / 1024 / 1024}MB`
            };
        }

        if (!allowedTypes.includes(file.type)) {
            return {
                valid: false,
                error: `File type must be one of: ${allowedTypes.join(', ')}`
            };
        }

        return { valid: true };
    },

    /**
     * Format error messages from DRF
     */
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

    /**
     * Show success notification with confetti
     */
    showSuccessAnimation() {
        if (typeof confetti !== 'undefined') {
            confetti({
                particleCount: 100,
                spread: 70,
                origin: { y: 0.6 }
            });
        }
    }
};

// ================================
// Bursary Page Animations
// ================================
document.addEventListener("DOMContentLoaded", () => {
    // Animate Scholarship SVG
    const svg = document.querySelector(".scholarship-icon svg");
    if (svg) {
        const paths = svg.querySelectorAll("rect, polygon, line, circle");
        
        paths.forEach((path, index) => {
            let length = path.getTotalLength ? path.getTotalLength() : 300;
            path.style.strokeDasharray = length;
            path.style.strokeDashoffset = length;

            setTimeout(() => {
                path.style.transition = "stroke-dashoffset 2s ease";
                path.style.strokeDashoffset = "0";
            }, index * 800);
        });

        setTimeout(() => {
            svg.classList.add("glow");
        }, paths.length * 800 + 500);
    }

    // Scroll reveal for welcome-section
    const revealElements = document.querySelectorAll(
        ".welcome-section h2, .welcome-section h3, .welcome-section h4, .welcome-section p, .info-box, .apply-btn"
    );

    const revealOnScroll = () => {
        let triggerBottom = window.innerHeight * 0.85;
        revealElements.forEach(el => {
            let boxTop = el.getBoundingClientRect().top;
            if (boxTop < triggerBottom) {
                el.classList.add("show");
            }
        });
    };

    if (revealElements.length > 0) {
        window.addEventListener("scroll", revealOnScroll);
        revealOnScroll();
    }

    // Apply Now button bounce
    const applyBtn = document.querySelector(".apply-btn");
    if (applyBtn) {
        applyBtn.addEventListener("mouseenter", () => {
            applyBtn.classList.add("bounce");
        });
        applyBtn.addEventListener("animationend", () => {
            applyBtn.classList.remove("bounce");
        });
    }

    // New application button functionality
    const newAppBtn = document.getElementById('new-application-btn');
    if (newAppBtn) {
        newAppBtn.addEventListener('click', function() {
            const form = document.getElementById('bursaryApplicationForm');
            const successDiv = document.getElementById('success-message');
            
            if (form && successDiv) {
                form.style.display = 'block';
                successDiv.style.display = 'none';
                form.reset();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
    }

    // Copy reference number handler
    const copyBtn = document.getElementById('copy-ref-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', (e) => {
            const refEl = document.getElementById('reference-number');
            if (!refEl) return;
            const refNumber = refEl.textContent;
            navigator.clipboard.writeText(refNumber).then(() => {
                const originalHTML = copyBtn.innerHTML;
                copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                copyBtn.style.background = '#28a745';
                setTimeout(() => {
                    copyBtn.innerHTML = originalHTML;
                    copyBtn.style.background = '#006400';
                }, 2000);
            }).catch(() => {
                alert('Failed to copy reference number. Please copy it manually.');
            });
        });
    }

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
    }
    function showStatus() {
        if (formSection) formSection.style.display = 'none';
        if (editSection) editSection.style.display = 'none';
        if (statusSection) statusSection.style.display = 'block';
    }
    function showEdit() {
        if (statusSection) statusSection.style.display = 'none';
        if (formSection) formSection.style.display = 'none';
        if (editSection) editSection.style.display = 'block';
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

    // Embedded edit: load and prefill for editing within 24 hours
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
            if (!el) return;
            const value = app[apiKey];
            if (el.type === 'checkbox') {
                el.checked = !!value;
            } else {
                el.value = value ?? '';
            }
        });
        // file inputs cannot be prefilled for security; leave empty
    }

    async function postJSON(url, payload) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            throw new Error(data?.error || 'Request failed');
        }
        return data;
    }

    if (editLoadBtn && editRefInput && editEmailInput) {
        // Pre-fill edit inputs from last submission if available
        try {
            const lastRef = sessionStorage.getItem('lastSubmittedRef');
            const lastEmail = sessionStorage.getItem('lastSubmittedEmail');
            if (lastRef) editRefInput.value = lastRef;
            if (lastEmail) editEmailInput.value = lastEmail;
        } catch {}

        editLoadBtn.addEventListener('click', async () => {
            const ref = (editRefInput.value || '').trim();
            const email = (editEmailInput.value || '').trim();
            if (!ref || !email) {
                showEditError('Please enter your reference number and email');
                return;
            }
            showEditError('');
            try {
                // Check eligibility
                const elig = await postJSON(`${CONFIG.API_BASE_URL}/bursary/check-edit-eligibility/`, {
                    reference_number: ref,
                    email
                });
                if (!elig.can_edit) {
                    showEditError(elig.reason || 'You cannot edit this application');
                    return;
                }
                // Fetch application details
                const detail = await postJSON(`${CONFIG.API_BASE_URL}/bursary/get-application-for-edit/`, {
                    reference_number: ref,
                    email
                });
                if (!detail?.application) {
                    showEditError('Failed to load application for editing');
                    return;
                }
                // Prefill form and switch to Apply view
                prefillFormFromApplication(detail.application);
                const hint = document.getElementById('edit-hint');
                if (hint) hint.style.display = 'block';
                window.__editMode = { reference_number: ref, email };
                showApply();
                window.scrollTo({ top: 0, behavior: 'smooth' });
                alert(`Edit window active. Time remaining: ${detail.edit_time_remaining || 'up to 24 hours from submission'}`);
            } catch (e) {
                showEditError(e.message || 'Failed to verify edit eligibility');
            }
        });
    }
    function embFormatAmount(v) {
        const n = parseInt(v || 0, 10);
        return isNaN(n) ? '0' : n.toLocaleString();
    }
    function embPrettyWard(w) {
        return (w || '').replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    async function embeddedFetchStatus(reference) {
        const controller = new AbortController();
        const to = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT);
        try {
            const res = await fetch(`${CONFIG.API_BASE_URL}/bursary/applications/${encodeURIComponent(reference)}/`, {
                method: 'GET',
                headers: { 'Accept': 'application/json' },
                signal: controller.signal
            });
            clearTimeout(to);
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                const msg = data && data.error ? data.error : 'Application not found';
                throw new Error(msg);
            }
            return await res.json();
        } catch (e) {
            clearTimeout(to);
            throw e;
        }
    }
    function renderEmbeddedResult(app) {
        setEmbText('emb-res-ref', app.reference_number);
        setEmbText('emb-res-name', app.full_name);
        setEmbText('emb-res-institution', app.institution_name);
        setEmbText('emb-res-amount', embFormatAmount(app.amount));
        setEmbText('emb-res-ward', embPrettyWard(app.ward));
        try {
            const d = new Date(app.submitted_at);
            setEmbText('emb-res-submitted', d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }));
        } catch {
            setEmbText('emb-res-submitted', app.submitted_at || '');
        }
        const statusEl = document.getElementById('emb-res-status');
        if (statusEl) {
            statusEl.textContent = (app.status || '').toUpperCase();
            statusEl.style.color = app.status === 'approved' ? '#008000' : (app.status === 'rejected' ? '#bb0000' : '#ff9800');
        }
        const err = document.getElementById('embedded-status-error');
        if (err) err.style.display = 'none';
        const resDiv = document.getElementById('embedded-status-result');
        if (resDiv) resDiv.style.display = 'block';
    }
    function showEmbeddedError(msg) {
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
            showEmbeddedError(''); // clear
            try {
                const data = await embeddedFetchStatus(ref);
                renderEmbeddedResult(data);
                window.scrollTo({ top: document.getElementById('status-section').offsetTop - 20, behavior: 'smooth' });
            } catch (e) {
                showEmbeddedError(e.message || 'Failed to fetch status');
            }
        });
    }
});

// ================================
// Navigation Function
// ================================
function openApplicationForm() {
    window.location.href = "bursary-application-form.html";
}

// ================================
// Form Logic & Conditional Fields
// ================================
document.addEventListener("DOMContentLoaded", () => {
    const familyStatus = document.getElementById("family-status");
    const orphanProof = document.getElementById("orphan-proof");
    const incomeFields = document.getElementById("income-fields");

    if (!familyStatus || !orphanProof || !incomeFields) return;

    const fatherIncome = document.getElementById("father-income")?.closest("label");
    const motherIncome = document.getElementById("mother-income")?.closest("label");
    const fatherDeath = document.getElementById("father-death-certificate")?.closest("label");
    const motherDeath = document.getElementById("mother-death-certificate")?.closest("label");

    function toggleOrphanProof() {
        const value = familyStatus.value;

        // Reset visibility
        orphanProof.style.display = "none";
        incomeFields.style.display = "none";

        if (fatherIncome) fatherIncome.style.display = "none";
        if (motherIncome) motherIncome.style.display = "none";
        if (fatherDeath) fatherDeath.style.display = "none";
        if (motherDeath) motherDeath.style.display = "none";

        // Clear required attributes
        const fatherDeathInput = document.getElementById("father-death-certificate");
        const motherDeathInput = document.getElementById("mother-death-certificate");
        if (fatherDeathInput) fatherDeathInput.removeAttribute('required');
        if (motherDeathInput) motherDeathInput.removeAttribute('required');

        // Logic by parental status
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
                break;

            case "partial-orphan":
                orphanProof.style.display = "block";
                incomeFields.style.display = "block";
                if (fatherDeath) fatherDeath.style.display = "block";
                if (motherDeath) motherDeath.style.display = "block";
                if (fatherIncome) fatherIncome.style.display = "block";
                if (motherIncome) motherIncome.style.display = "block";
                break;

            case "total-orphan":
                orphanProof.style.display = "block";
                if (fatherDeath) {
                    fatherDeath.style.display = "block";
                    if (fatherDeathInput) fatherDeathInput.setAttribute('required', 'required');
                }
                if (motherDeath) {
                    motherDeath.style.display = "block";
                    if (motherDeathInput) motherDeathInput.setAttribute('required', 'required');
                }
                break;
        }
    }

    toggleOrphanProof();
    familyStatus.addEventListener("change", toggleOrphanProof);

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
            const allowedTypes = this.accept.includes('pdf') 
                ? CONFIG.ALLOWED_DOC_TYPES 
                : CONFIG.ALLOWED_IMAGE_TYPES;
            
            const validation = Utils.validateFile(file, allowedTypes);
            
            if (!validation.valid) {
                alert(validation.error);
                this.value = '';
            }
        });
    });
});

// ================================
// Form Submission to API
// ================================
async function submitApplicationToAPI() {
    const submitBtn = document.getElementById('submit-btn');
    const loadingDiv = document.getElementById('loading');
    const successDiv = document.getElementById('success-message');
    const errorDiv = document.getElementById('error-message');
    const form = document.getElementById('bursaryApplicationForm');

    // Reset messages
    if (successDiv) successDiv.style.display = 'none';
    if (errorDiv) errorDiv.style.display = 'none';

    // Validate confirmation and consent
    const confirmationCheck = document.getElementById('confirmation');
    const consentCheck = document.getElementById('data-consent');

    if (!confirmationCheck?.checked) {
        showError('Please confirm that all details are correct before submitting.');
        return;
    }

    if (!consentCheck?.checked) {
        showError('You must consent to the data protection terms to submit your application.');
        return;
    }

    // Validate required files
    const frontId = document.getElementById('id-upload-front');
    if (!frontId?.files[0]) {
        showError('Please upload the front side of your ID/Birth Certificate');
        return;
    }

    // Validate email
    const emailInput = document.getElementById('email');
    if (!emailInput?.value || !emailInput.value.includes('@')) {
        showError('Please provide a valid email address');
        return;
    }

    // Validate file sizes
    const fileValidations = [
        { input: frontId, name: 'ID Front' },
        { input: document.getElementById('id-upload-back'), name: 'ID Back' },
        { input: document.getElementById('admission-letter'), name: 'Admission Letter' },
        { input: document.getElementById('father-death-certificate'), name: 'Father Death Certificate' },
        { input: document.getElementById('mother-death-certificate'), name: 'Mother Death Certificate' }
    ];

    for (const { input, name } of fileValidations) {
        if (input?.files[0]) {
            const allowedTypes = input.accept.includes('pdf') 
                ? CONFIG.ALLOWED_DOC_TYPES 
                : CONFIG.ALLOWED_IMAGE_TYPES;
            
            const validation = Utils.validateFile(input.files[0], allowedTypes);
            if (!validation.valid) {
                showError(`${name}: ${validation.error}`);
                return;
            }
        }
    }

    // Show loading
    if (submitBtn) submitBtn.disabled = true;
    if (loadingDiv) loadingDiv.style.display = 'block';

    // Create abort controller for timeout
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT);

    try {
        // Create FormData object
        const formData = new FormData();

        // Map form fields including email
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
            'family-status': 'family_status'
        };

        // Add text fields
        for (const [htmlId, apiName] of Object.entries(fieldMappings)) {
            const element = document.getElementById(htmlId);
            if (element) {
                if (element.type === 'checkbox') {
                    formData.append(apiName, element.checked);
                } else if (apiName === 'amount') {
                    formData.append(apiName, parseInt(element.value));
                } else {
                    formData.append(apiName, element.value);
                }
            }
        }

        // Add consent fields
        formData.append('confirmation', true);
        formData.append('data_consent', consentCheck?.checked || false);
        formData.append('communication_consent', 
            document.getElementById('communication-consent')?.checked || false);

        // Add income fields if they have values
        const fatherIncome = document.getElementById('father-income')?.value;
        const motherIncome = document.getElementById('mother-income')?.value;
        if (fatherIncome) formData.append('father_income', fatherIncome);
        if (motherIncome) formData.append('mother_income', motherIncome);

        // Add file uploads
        const fileFields = [
            { id: 'id-upload-front', name: 'id_upload_front', required: true },
            { id: 'id-upload-back', name: 'id_upload_back', required: false },
            { id: 'admission-letter', name: 'admission_letter', required: false },
            { id: 'father-death-certificate', name: 'father_death_certificate', required: false },
            { id: 'mother-death-certificate', name: 'mother_death_certificate', required: false }
        ];

        for (const { id, name, required } of fileFields) {
            const input = document.getElementById(id);
            if (input?.files[0]) {
                formData.append(name, input.files[0]);
            } else if (required) {
                throw new Error(`Please upload ${name.replace(/_/g, ' ')}`);
            }
        }

        // Get CSRF token and decide create vs edit
        const csrfToken = Utils.getCsrfToken();
        const editMode = window.__editMode || null;
        let url = `${CONFIG.API_BASE_URL}/bursary/apply/`;
        let method = 'POST';
        if (editMode?.reference_number && editMode?.email) {
            formData.append('email', editMode.email);
            url = `${CONFIG.API_BASE_URL}/bursary/applications/${encodeURIComponent(editMode.reference_number)}/edit/`;
            method = 'PUT';
        }

        const response = await fetch(url, {
            method,
            headers: csrfToken ? { 'X-CSRFToken': csrfToken } : {},
            body: formData,
            signal: controller.signal
        });

        clearTimeout(timeout);

        const data = await response.json();

        if (response.ok) {
            // Success
            if (loadingDiv) loadingDiv.style.display = 'none';
            
            // Store application data for success page
            const applicationData = {
                reference_number: data.reference_number,
                full_name: document.getElementById('full-name').value,
                email: document.getElementById('email').value,
                institution_name: document.getElementById('institution-name').value,
                amount: document.getElementById('amount').value,
                ward: document.getElementById('ward').value,
                phone_number: document.getElementById('phone-number').value
            };
            
            if (!editMode) {
                // Save and redirect to standalone success page + store edit hint
                try {
                    sessionStorage.setItem('applicationSuccessData', JSON.stringify(applicationData));
                    sessionStorage.setItem('lastSubmittedRef', applicationData.reference_number || '');
                    sessionStorage.setItem('lastSubmittedEmail', applicationData.email || '');
                } catch (e) {}

                // Hide the form immediately to avoid confusion while redirecting
                if (form) form.style.display = 'none';

                // Prefer replace to avoid back button returning to form submit
                try {
                    window.location.replace('success.html');
                } catch (e) {
                    window.location.href = 'success.html';
                }
                // Fallback in case the browser delays navigation
                setTimeout(() => {
                    if (!document.hidden) {
                        window.location.href = 'success.html';
                    }
                }, 100);
            } else {
                // Editing flow: inform and allow further edits within window
                window.__editMode = null;
                alert(`Application updated successfully${data.edit_time_remaining ? `. Time remaining: ${data.edit_time_remaining}` : ''}`);
            }
            
        } else {
            // Handle errors
            const errorMessage = Utils.formatErrorMessage(data);
            throw new Error(errorMessage);
        }

    } catch (error) {
        if (loadingDiv) loadingDiv.style.display = 'none';
        
        let errorMessage = error.message;
        if (error.name === 'AbortError') {
            errorMessage = 'Request timeout. Please check your connection and try again.';
        } else if (!navigator.onLine) {
            errorMessage = 'No internet connection. Please check your network and try again.';
        }
        
        showError(errorMessage);
    } finally {
        clearTimeout(timeout);
        if (submitBtn) submitBtn.disabled = false;
    }
}

// ================================
// Error Display Function
// ================================
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    
    if (errorText) errorText.textContent = message;
    if (errorDiv) {
        errorDiv.style.display = 'block';
        errorDiv.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Auto-hide after 10 seconds
    setTimeout(() => {
        if (errorDiv) errorDiv.style.display = 'none';
    }, 10000);
}

// ================================
// Populate Success Message with Email Preview
// ================================
function populateSuccessMessage(data) {
    // Update all email preview fields in the success message
    const fields = {
        'success-applicant-name': data.full_name,
        'success-full-name': data.full_name,
        'success-applicant-email': data.email,
        'success-ref-number': data.reference_number,
        'success-institution': data.institution_name,
        'success-amount': parseInt(data.amount).toLocaleString(),
        'success-ward': data.ward.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        'success-phone': data.phone_number
    };
    
    for (const [id, value] of Object.entries(fields)) {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    }
    
    // Set timestamp
    const now = new Date();
    const timestampEl = document.getElementById('success-timestamp');
    if (timestampEl) {
        timestampEl.textContent = now.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    const submissionDateEl = document.getElementById('success-submission-date');
    if (submissionDateEl) {
        submissionDateEl.textContent = now.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
}