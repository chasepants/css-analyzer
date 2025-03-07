// src/scripts.js
document.addEventListener('DOMContentLoaded', function() {
    // Dynamically add a button with btn-primary class
    const button = document.createElement('button');
    button.className = 'btn-primary';
    button.textContent = 'Dynamic Button';
    document.querySelector('.container').appendChild(button);
});