// Main JavaScript file for Student Management System

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide flash messages after 5 seconds
    setTimeout(function() {
        var flashMessages = document.querySelectorAll('.alert');
        flashMessages.forEach(function(message) {
            var alert = new bootstrap.Alert(message);
            alert.close();
        });
    }, 5000);

    // Subject selection in add mark form
    var subjectSelect = document.getElementById('subject_id');
    if (subjectSelect) {
        subjectSelect.addEventListener('change', function() {
            var subjectId = this.value;
            if (subjectId) {
                window.location.href = window.location.pathname + '?subject_id=' + subjectId;
            }
        });
    }

    // Confirm delete actions
    var deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Toggle password visibility
    var togglePasswordButtons = document.querySelectorAll('.toggle-password');
    togglePasswordButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            var passwordInput = document.querySelector(this.getAttribute('toggle'));
            if (passwordInput) {
                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    this.classList.remove('fa-eye');
                    this.classList.add('fa-eye-slash');
                } else {
                    passwordInput.type = 'password';
                    this.classList.remove('fa-eye-slash');
                    this.classList.add('fa-eye');
                }
            }
        });
    });

    // Date picker initialization
    var dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function(input) {
        if (!input.value) {
            var today = new Date();
            var dd = String(today.getDate()).padStart(2, '0');
            var mm = String(today.getMonth() + 1).padStart(2, '0');
            var yyyy = today.getFullYear();
            input.value = yyyy + '-' + mm + '-' + dd;
        }
    });

    // Mark goal as completed
    var completeGoalButtons = document.querySelectorAll('.complete-goal');
    completeGoalButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            var goalId = this.getAttribute('data-goal-id');
            var form = document.getElementById('complete-goal-form-' + goalId);
            if (form) {
                form.submit();
            }
        });
    });

    // Print functionality
    var printButtons = document.querySelectorAll('.btn-print');
    printButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            window.print();
        });
    });
}); 