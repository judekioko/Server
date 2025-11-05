// ================================
// Bursary Page Animations
// ================================

document.addEventListener("DOMContentLoaded", () => {
    // Animate Scholarship SVG
    const svg = document.querySelector(".scholarship-icon svg");
    const paths = svg.querySelectorAll("rect, polygon, line, circle");
    // Add new application button functionality
document.getElementById('new-application-btn')?.addEventListener('click', function() {
    const form = document.getElementById('bursaryApplicationForm');
    const successDiv = document.getElementById('success-message');
    
    // Show form and hide success message
    form.style.display = 'block';
    successDiv.style.display = 'none';
    
    // Reset form
    form.reset();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

    paths.forEach((path, index) => {
        let length = path.getTotalLength ? path.getTotalLength() : 300;
        path.style.strokeDasharray = length;
        path.style.strokeDashoffset = length;

        // Animate each path with staggered timing
        setTimeout(() => {
            path.style.transition = "stroke-dashoffset 2s ease";
            path.style.strokeDashoffset = "0";
        }, index * 800);
    });

    // After full animation, glow effect
    setTimeout(() => {
        svg.classList.add("glow");
    }, paths.length * 800 + 500);

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

    window.addEventListener("scroll", revealOnScroll);
    revealOnScroll();

    // Apply Now button bounce
    const applyBtn = document.querySelector(".apply-btn");
    applyBtn.addEventListener("mouseenter", () => {
        applyBtn.classList.add("bounce");
    });
    applyBtn.addEventListener("animationend", () => {
        applyBtn.classList.remove("bounce");
    });
});

// assets/js/bursary.js
function openApplicationForm() {
    window.location.href = "bursary-application-form.html"; 
}


// ================================
// Bursary Form Page Logic
// ================================

document.addEventListener("DOMContentLoaded", () => {
    const familyStatus = document.getElementById("family-status");
    const orphanProof = document.getElementById("orphan-proof");
    const incomeFields = document.getElementById("income-fields");

    const fatherIncome = document.getElementById("father-income")?.closest("label") || null;
    const motherIncome = document.getElementById("mother-income")?.closest("label") || null;

    const fatherDeath = document.getElementById("father-death-certificate")?.closest("label") || null;
    const motherDeath = document.getElementById("mother-death-certificate")?.closest("label") || null;

    function toggleOrphanProof() {
        const value = familyStatus.value;

        // Reset visibility
        orphanProof.style.display = "none";
        incomeFields.style.display = "none";

        if (fatherIncome) fatherIncome.style.display = "none";
        if (motherIncome) motherIncome.style.display = "none";
        if (fatherDeath) fatherDeath.style.display = "none";
        if (motherDeath) motherDeath.style.display = "none";

        // Logic by parental status
        switch (value) {
            case "both-parents-alive":
                incomeFields.style.display = "block";
                if (fatherIncome) fatherIncome.style.display = "block";
                if (motherIncome) motherIncome.style.display = "block";
                break;

            case "single-parent":
                incomeFields.style.display = "block";
                // Let’s assume "father alive" (keep father’s income)
                if (fatherIncome) fatherIncome.style.display = "block";
                break;

            case "partial-orphan":
                orphanProof.style.display = "block";
                incomeFields.style.display = "block";
                // Assume father deceased, so show father’s death + mother income
                if (fatherDeath) fatherDeath.style.display = "block";
                if (motherIncome) motherIncome.style.display = "block";
                break;

            case "total-orphan":
                orphanProof.style.display = "block";
                if (fatherDeath) fatherDeath.style.display = "block";
                if (motherDeath) motherDeath.style.display = "block";
                break;
        }
    }

    // Run once on page load
    toggleOrphanProof();

    // Listen to family status change
    familyStatus.addEventListener("change", toggleOrphanProof);

    // Handle form submission success (simulation only)
    const submitBtn = document.getElementById('submit-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', function(e) {
            e.preventDefault();
            submitApplicationToAPI();
        });
    }
});




// Add this to your existing bursary.js file
async function submitApplicationToAPI() {
    const submitBtn = document.getElementById('submit-btn');
    const loadingDiv = document.getElementById('loading');
    const successDiv = document.getElementById('success-message');
    const errorDiv = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    const form = document.getElementById('bursaryApplicationForm');

    // Reset messages
    successDiv.style.display = 'none';
    errorDiv.style.display = 'none';

    // Validate confirmation and consent
    if (!document.getElementById('confirmation').checked) {
        showError('Please confirm that all details are correct before submitting.');
        return;
    }

    if (!document.getElementById('data-consent').checked) {
        showError('You must consent to the data protection terms to submit your application.');
        return;
    }

    // Show loading
    submitBtn.disabled = true;
    loadingDiv.style.display = 'block';

    try {
        // Create FormData object
        const formData = new FormData();

        // Map form field names to model field names
        formData.append('full_name', document.getElementById('full-name').value);
        formData.append('gender', document.getElementById('gender').value);
        formData.append('disability', document.getElementById('disability').checked);
        formData.append('id_number', document.getElementById('id-number').value);
        formData.append('phone_number', document.getElementById('phone-number').value);
        formData.append('email', document.getElementById('email').value);
        formData.append('guardian_phone', document.getElementById('guardian-phone').value);
        formData.append('guardian_id', document.getElementById('guardian-id').value);
        
        // Residence details
        formData.append('ward', document.getElementById('ward').value);
        formData.append('village', document.getElementById('village').value);
        formData.append('chief_name', document.getElementById('chief-name').value);
        formData.append('chief_phone', document.getElementById('chief-phone').value);
        formData.append('sub_chief_name', document.getElementById('sub-chief-name').value);
        formData.append('sub_chief_phone', document.getElementById('sub-chief-phone').value);
        
        // Institution details
        formData.append('level_of_study', document.getElementById('level-of-study').value);
        formData.append('institution_type', document.getElementById('institution-type').value);
        formData.append('institution_name', document.getElementById('institution-name').value);
        formData.append('admission_number', document.getElementById('admission-number').value);
        formData.append('amount', parseInt(document.getElementById('amount').value));
        formData.append('mode_of_study', document.getElementById('mode-of-study').value);
        formData.append('year_of_study', document.getElementById('year-of-study').value);
        
        // Family details
        formData.append('family_status', document.getElementById('family-status').value);
        formData.append('confirmation', true);
        formData.append('data_consent', true);
        formData.append('communication_consent', document.getElementById('communication-consent').checked);

        // Add income fields if they have values
        const fatherIncome = document.getElementById('father-income').value;
        const motherIncome = document.getElementById('mother-income').value;
        if (fatherIncome) formData.append('father_income', fatherIncome);
        if (motherIncome) formData.append('mother_income', motherIncome);

        // Add file uploads - FRONT ID IS STILL REQUIRED
        if (document.getElementById('id-upload-front').files[0]) {
            formData.append('id_upload_front', document.getElementById('id-upload-front').files[0]);
        } else {
            throw new Error('Please upload the front side of your ID/Birth Certificate');
        }

        // BACK ID IS NOW OPTIONAL
        if (document.getElementById('id-upload-back').files[0]) {
            formData.append('id_upload_back', document.getElementById('id-upload-back').files[0]);
        }

        // ADMISSION LETTER IS NOW OPTIONAL
        if (document.getElementById('admission-letter').files[0]) {
            formData.append('admission_letter', document.getElementById('admission-letter').files[0]);
        }

        // Add death certificates if they exist
        const fatherDeathCert = document.getElementById('father-death-certificate').files[0];
        const motherDeathCert = document.getElementById('mother-death-certificate').files[0];
        if (fatherDeathCert) formData.append('father_death_certificate', fatherDeathCert);
        if (motherDeathCert) formData.append('mother_death_certificate', motherDeathCert);

        // Make API call to DRF endpoint
        const response = await fetch('http://127.0.0.1:8000/bursary/apply/', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            // Success - Hide form and show success message
            loadingDiv.style.display = 'none';
            form.style.display = 'none';
            
            // Display reference number
            document.getElementById('reference-number').textContent = data.reference_number || 'MAS-' + Date.now();
            successDiv.style.display = 'block';
            
        } else {
            // Handle validation errors from DRF
            let errorMessage = 'Failed to submit application. ';
            if (data.detail) {
                errorMessage += data.detail;
            } else if (typeof data === 'object') {
                // Format field validation errors
                const fieldErrors = [];
                for (const [field, errors] of Object.entries(data)) {
                    fieldErrors.push(`${field}: ${Array.isArray(errors) ? errors.join(', ') : errors}`);
                }
                errorMessage += fieldErrors.join('; ');
            } else {
                errorMessage += 'Please check your information and try again.';
            }
            throw new Error(errorMessage);
        }

    } catch (error) {
        loadingDiv.style.display = 'none';
        showError(error.message);
    } finally {
        submitBtn.disabled = false;
    }
}

// Duplicate block removed — submitApplicationToAPI already handles success/error and completes with its own try/catch/finally.

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    
    errorText.textContent = message;
    errorDiv.style.display = 'block';
    
    // Scroll to error message
    errorDiv.scrollIntoView({ behavior: 'smooth' });
}

// Keep your existing functions (toggleInstitutionDetails, toggleInstitutionFields, toggleOrphanProof, scanIDDocument)
// These remain unchanged