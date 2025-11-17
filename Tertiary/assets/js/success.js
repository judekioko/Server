document.addEventListener('DOMContentLoaded', () => {
  try {
    const raw = sessionStorage.getItem('applicationSuccessData');
    if (!raw) {
      // If no data present, go back to form
      window.location.replace('bursary-application-form.html');
      return;
    }
    const data = JSON.parse(raw);

    const setText = (id, value) => {
      const el = document.getElementById(id);
      if (el && value !== undefined && value !== null) {
        el.textContent = value;
      }
    };

    setText('reference-number', data.reference_number || 'MNG-XXXXXXXX');
    setText('success-ref-number', data.reference_number || 'MNG-XXXXXXXX');
    setText('success-applicant-name', data.full_name || 'Applicant');
    setText('success-full-name', data.full_name || 'Applicant');
    setText('success-applicant-email', data.email || 'your-email@example.com');
    setText('success-institution', data.institution_name || 'Your Institution');
    setText('success-amount', parseInt(data.amount || 0, 10).toLocaleString());
    setText('success-ward', (data.ward || 'your ward').replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase()));

    const now = new Date();
    const ts = document.getElementById('success-timestamp');
    if (ts) {
      ts.textContent = now.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    }
    const sd = document.getElementById('success-submission-date');
    if (sd) {
      sd.textContent = now.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    }

    const meta = data.notifications || {};
    const title = document.querySelector('.email-preview-title h3');
    if (title) {
      if (meta.email_sent === true) {
        title.textContent = 'Confirmation Email Sent to Your Inbox';
      } else {
        title.textContent = 'Confirmation Email Queued';
      }
    }

    // Copy button
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
        });
      });
    }

    // Confetti
    if (typeof confetti !== 'undefined') {
      confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
    }
  } catch (e) {
    // Fallback: go back to form
    window.location.replace('bursary-application-form.html');
  }
});

