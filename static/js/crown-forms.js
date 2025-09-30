/**
 * MINA CROWN+ FORM VALIDATION SYSTEM
 * Enterprise-grade form validation with inline errors and success states
 * - Real-time validation
 * - Custom validation rules
 * - Accessibility compliant (ARIA attributes)
 * - Success/error states
 */

class CrownFormValidator {
    constructor(formElement, options = {}) {
        this.form = formElement;
        this.fields = new Map();
        this.options = {
            validateOnBlur: true,
            validateOnInput: false,
            showSuccessStates: true,
            ...options
        };
        this.init();
    }

    init() {
        if (!this.form) {
            console.error('CrownFormValidator: Form element not found');
            return;
        }

        this.form.setAttribute('novalidate', 'true');

        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.validateAll();
        });

        const inputs = this.form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            this.initField(input);
        });
    }

    initField(input) {
        const fieldData = {
            element: input,
            rules: this.parseRules(input),
            errorElement: null,
            isValid: true
        };

        this.fields.set(input.name || input.id, fieldData);

        if (this.options.validateOnBlur) {
            input.addEventListener('blur', () => this.validateField(input));
        }

        if (this.options.validateOnInput) {
            input.addEventListener('input', () => this.validateField(input));
        }
    }

    parseRules(input) {
        const rules = {};

        if (input.hasAttribute('required')) {
            rules.required = true;
        }

        if (input.hasAttribute('type')) {
            const type = input.getAttribute('type');
            if (type === 'email') {
                rules.email = true;
            }
            if (type === 'url') {
                rules.url = true;
            }
            if (type === 'number') {
                rules.number = true;
            }
        }

        if (input.hasAttribute('minlength')) {
            rules.minlength = parseInt(input.getAttribute('minlength'));
        }

        if (input.hasAttribute('maxlength')) {
            rules.maxlength = parseInt(input.getAttribute('maxlength'));
        }

        if (input.hasAttribute('min')) {
            rules.min = parseFloat(input.getAttribute('min'));
        }

        if (input.hasAttribute('max')) {
            rules.max = parseFloat(input.getAttribute('max'));
        }

        if (input.hasAttribute('pattern')) {
            rules.pattern = new RegExp(input.getAttribute('pattern'));
        }

        if (input.hasAttribute('data-match')) {
            rules.match = input.getAttribute('data-match');
        }

        return rules;
    }

    validateField(input) {
        const fieldKey = input.name || input.id;
        const fieldData = this.fields.get(fieldKey);
        
        if (!fieldData) return true;

        const value = input.value.trim();
        const rules = fieldData.rules;
        let errorMessage = '';

        if (rules.required && !value) {
            errorMessage = 'This field is required';
        } else if (value) {
            if (rules.email && !this.isValidEmail(value)) {
                errorMessage = 'Please enter a valid email address';
            } else if (rules.url && !this.isValidUrl(value)) {
                errorMessage = 'Please enter a valid URL';
            } else if (rules.number && isNaN(value)) {
                errorMessage = 'Please enter a valid number';
            } else if (rules.minlength && value.length < rules.minlength) {
                errorMessage = `Must be at least ${rules.minlength} characters`;
            } else if (rules.maxlength && value.length > rules.maxlength) {
                errorMessage = `Must be no more than ${rules.maxlength} characters`;
            } else if (rules.min !== undefined && parseFloat(value) < rules.min) {
                errorMessage = `Must be at least ${rules.min}`;
            } else if (rules.max !== undefined && parseFloat(value) > rules.max) {
                errorMessage = `Must be no more than ${rules.max}`;
            } else if (rules.pattern && !rules.pattern.test(value)) {
                errorMessage = input.getAttribute('data-pattern-error') || 'Invalid format';
            } else if (rules.match) {
                const matchField = this.form.querySelector(`[name="${rules.match}"]`);
                if (matchField && value !== matchField.value) {
                    errorMessage = 'Fields do not match';
                }
            }
        }

        if (!errorMessage && rules.custom && rules.custom.length > 0) {
            for (const customRule of rules.custom) {
                if (!customRule.validator(value, input)) {
                    errorMessage = customRule.errorMessage;
                    break;
                }
            }
        }

        if (errorMessage) {
            this.showError(input, errorMessage, fieldData);
            return false;
        } else {
            this.showSuccess(input, fieldData);
            return true;
        }
    }

    showError(input, message, fieldData) {
        input.classList.remove('input-success');
        input.classList.add('input-error');
        input.setAttribute('aria-invalid', 'true');

        if (!fieldData.errorElement) {
            fieldData.errorElement = document.createElement('div');
            fieldData.errorElement.className = 'input-error-message';
            fieldData.errorElement.setAttribute('role', 'alert');
            
            const icon = document.createElement('i');
            icon.className = 'fas fa-exclamation-circle';
            fieldData.errorElement.appendChild(icon);
            
            const textSpan = document.createElement('span');
            fieldData.errorElement.appendChild(textSpan);
            
            const inputGroup = input.closest('.input-group');
            if (inputGroup) {
                inputGroup.appendChild(fieldData.errorElement);
            } else {
                input.parentNode.insertBefore(fieldData.errorElement, input.nextSibling);
            }
        }

        fieldData.errorElement.querySelector('span').textContent = message;
        fieldData.errorElement.style.display = 'flex';
        fieldData.isValid = false;
    }

    showSuccess(input, fieldData) {
        input.classList.remove('input-error');
        input.removeAttribute('aria-invalid');

        if (this.options.showSuccessStates && input.value.trim()) {
            input.classList.add('input-success');
        }

        if (fieldData.errorElement) {
            fieldData.errorElement.style.display = 'none';
        }

        fieldData.isValid = true;
    }

    validateAll() {
        let isFormValid = true;
        let firstInvalidField = null;

        this.fields.forEach((fieldData, key) => {
            const isValid = this.validateField(fieldData.element);
            if (!isValid) {
                isFormValid = false;
                if (!firstInvalidField) {
                    firstInvalidField = fieldData.element;
                }
            }
        });

        if (!isFormValid && firstInvalidField) {
            firstInvalidField.focus();
            firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        if (isFormValid && this.options.onSuccess) {
            this.options.onSuccess(this.getFormData());
        } else if (!isFormValid && this.options.onError) {
            this.options.onError();
        }

        return isFormValid;
    }

    getFormData() {
        const formData = {};
        this.fields.forEach((fieldData, key) => {
            formData[key] = fieldData.element.value;
        });
        return formData;
    }

    reset() {
        this.fields.forEach((fieldData) => {
            fieldData.element.classList.remove('input-error', 'input-success');
            fieldData.element.removeAttribute('aria-invalid');
            if (fieldData.errorElement) {
                fieldData.errorElement.style.display = 'none';
            }
            fieldData.isValid = true;
        });
        this.form.reset();
    }

    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    isValidUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }

    addCustomRule(fieldName, validator, errorMessage) {
        const fieldData = this.fields.get(fieldName);
        if (fieldData) {
            if (!fieldData.rules.custom) {
                fieldData.rules.custom = [];
            }
            fieldData.rules.custom.push({ validator, errorMessage });
        }
    }
}

const CrownForms = {
    validators: new Map(),
    formCounter: 0,

    init(formSelector, options = {}) {
        const forms = typeof formSelector === 'string' 
            ? document.querySelectorAll(formSelector)
            : [formSelector];

        forms.forEach(form => {
            if (form && form.tagName === 'FORM') {
                const validator = new CrownFormValidator(form, options);
                const formKey = form.id || form.name || `form-${++this.formCounter}`;
                this.validators.set(formKey, validator);
            }
        });

        console.log('✨ Crown+ Forms initialized');
    },

    getValidator(formIdOrName) {
        return this.validators.get(formIdOrName);
    },

    validateAll() {
        let allValid = true;
        this.validators.forEach(validator => {
            if (!validator.validateAll()) {
                allValid = false;
            }
        });
        return allValid;
    }
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        const forms = document.querySelectorAll('form[data-crown-validate]');
        if (forms.length > 0) {
            forms.forEach(form => {
                CrownForms.init(form);
            });
        }
    });
} else {
    const forms = document.querySelectorAll('form[data-crown-validate]');
    if (forms.length > 0) {
        forms.forEach(form => {
            CrownForms.init(form);
        });
    }
}

window.CrownForms = CrownForms;
window.CrownFormValidator = CrownFormValidator;
