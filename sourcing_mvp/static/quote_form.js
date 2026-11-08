// Language translations
const translations = {
    en: {
        title: "Submit Your Quotation",
        productLabel: "Product Inquiry",
        quantityLabel: "Quantity:",
        deadlineLabel: "Quote Deadline:",
        labelPrice: "Unit Price *",
        labelMoq: "MOQ (Minimum Order Quantity) *",
        labelLeadtime: "Lead Time *",
        labelTrade: "Trade Terms *",
        labelValid: "Quote Valid Until *",
        labelPayment: "Payment Terms",
        labelNotes: "Specification Differences / Notes",
        btnSubmit: "Submit Quotation",
        footerText: "Submitted quotes cannot be edited. Please verify all information before submission.",
        hintMoq: "units",
        hintLeadtime: "days",
        submitting: "Submitting...",
        success: "✅ Quote submitted successfully!",
        errorTitle: "❌ Submission Failed",
        confirmSubmit: "Are you sure you want to submit this quotation? You cannot edit it after submission.",
    },
    zh: {
        title: "提交报价",
        productLabel: "产品询价",
        quantityLabel: "数量：",
        deadlineLabel: "报价截止：",
        labelPrice: "单价 *",
        labelMoq: "起订量 (MOQ) *",
        labelLeadtime: "交货期 *",
        labelTrade: "贸易条款 *",
        labelValid: "报价有效期 *",
        labelPayment: "付款条件",
        labelNotes: "规格差异说明",
        btnSubmit: "提交报价",
        footerText: "提交后的报价无法修改，请仔细核对后再提交。",
        hintMoq: "件",
        hintLeadtime: "天",
        submitting: "提交中...",
        success: "✅ 报价提交成功！",
        errorTitle: "❌ 提交失败",
        confirmSubmit: "确定要提交此报价吗？提交后无法修改。",
    }
};

let currentLang = 'en';

// Toggle language
function toggleLanguage() {
    currentLang = currentLang === 'en' ? 'zh' : 'en';
    updateLanguage();
}

// Update UI language
function updateLanguage() {
    const t = translations[currentLang];

    document.getElementById('title').textContent = t.title;
    document.getElementById('product-label').textContent = t.productLabel;
    document.getElementById('quantity-label').textContent = t.quantityLabel;
    document.getElementById('deadline-label').textContent = t.deadlineLabel;
    document.getElementById('label-price').textContent = t.labelPrice;
    document.getElementById('label-moq').textContent = t.labelMoq;
    document.getElementById('label-leadtime').textContent = t.labelLeadtime;
    document.getElementById('label-trade').textContent = t.labelTrade;
    document.getElementById('label-valid').textContent = t.labelValid;
    document.getElementById('label-payment').textContent = t.labelPayment;
    document.getElementById('label-notes').textContent = t.labelNotes;
    document.getElementById('btn-submit').textContent = t.btnSubmit;
    document.getElementById('footer-text').textContent = t.footerText;
    document.getElementById('hint-moq').textContent = t.hintMoq;
    document.getElementById('hint-leadtime').textContent = t.hintLeadtime;

    // Update language switch button
    document.querySelector('.lang-switch').textContent = currentLang === 'en' ? '中文' : 'English';
}

// Format deadline display
function formatDeadline() {
    const deadlineEl = document.getElementById('deadline-value');
    if (deadlineEl) {
        const isoDate = deadlineEl.textContent.trim();
        try {
            const date = new Date(isoDate);
            const formatted = date.toLocaleString(currentLang === 'zh' ? 'zh-CN' : 'en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            deadlineEl.textContent = formatted;
        } catch (e) {
            console.error('Date parsing error:', e);
        }
    }
}

// Set minimum valid date (tomorrow)
function setMinValidDate() {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const minDate = tomorrow.toISOString().split('T')[0];
    document.getElementById('quote_valid_until').setAttribute('min', minDate);
}

// Validate form
function validateForm(formData) {
    const errors = [];

    // Price validation
    const price = parseFloat(formData.unit_price);
    if (isNaN(price) || price <= 0) {
        errors.push('Unit price must be a positive number');
    }

    // MOQ validation
    const moq = parseInt(formData.moq);
    if (isNaN(moq) || moq <= 0) {
        errors.push('MOQ must be a positive integer');
    }

    // Lead time validation
    const leadTime = parseInt(formData.lead_time_days);
    if (isNaN(leadTime) || leadTime <= 0) {
        errors.push('Lead time must be a positive integer');
    }

    // Valid until date
    const validUntil = new Date(formData.quote_valid_until);
    if (validUntil <= new Date()) {
        errors.push('Valid until date must be in the future');
    }

    return errors;
}

// Submit quote
async function submitQuote(event) {
    event.preventDefault();

    const t = translations[currentLang];
    const form = event.target;
    const submitBtn = document.getElementById('btn-submit');
    const messageDiv = document.getElementById('message');

    // Confirm submission
    if (!confirm(t.confirmSubmit)) {
        return;
    }

    // Collect form data
    const formData = {
        token: document.getElementById('token').value,
        unit_price: document.getElementById('unit_price').value.trim(),
        currency: document.getElementById('currency').value,
        moq: parseInt(document.getElementById('moq').value),
        lead_time_days: parseInt(document.getElementById('lead_time_days').value),
        trade_term: document.getElementById('trade_term').value,
        quote_valid_until: new Date(document.getElementById('quote_valid_until').value).toISOString(),
        payment_terms: document.getElementById('payment_terms').value.trim() || null,
        specification_notes: document.getElementById('specification_notes').value.trim() || null,
    };

    // Validate
    const errors = validateForm(formData);
    if (errors.length > 0) {
        showMessage(errors.join('; '), 'error');
        return;
    }

    // Disable form
    submitBtn.disabled = true;
    submitBtn.classList.add('loading');
    submitBtn.textContent = t.submitting;
    messageDiv.style.display = 'none';

    try {
        const response = await fetch('/api/quote/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        });

        const result = await response.json();

        if (response.ok) {
            // Success
            form.reset();
            showMessage(t.success, 'success');

            // Disable form permanently
            const inputs = form.querySelectorAll('input, select, textarea, button');
            inputs.forEach(input => input.disabled = true);
        } else {
            // Error
            showMessage(`${t.errorTitle}: ${result.detail || 'Unknown error'}`, 'error');
            submitBtn.disabled = false;
            submitBtn.classList.remove('loading');
            submitBtn.textContent = t.btnSubmit;
        }
    } catch (error) {
        console.error('Submission error:', error);
        showMessage(`${t.errorTitle}: ${error.message}`, 'error');
        submitBtn.disabled = false;
        submitBtn.classList.remove('loading');
        submitBtn.textContent = t.btnSubmit;
    }
}

// Show message
function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.style.display = 'block';

    // Scroll to message
    messageDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    formatDeadline();
    setMinValidDate();
    updateLanguage();
});
