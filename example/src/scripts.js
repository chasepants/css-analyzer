// src/scripts.js
document.addEventListener('DOMContentLoaded', function() {
    // Dynamically add a button with btn-primary class
    const button = document.createElement('button');
    button.className = 'btn-primary';
    button.textContent = 'Dynamic Button';
    document.querySelector('.container').appendChild(button);
    document.querySelector('.btn-primary').classList.add('btn-primary:hover');
    document.querySelector('.nav-item').classList.toggle('nav-item:first-child');
});