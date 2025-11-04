document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.app-card').forEach(function(card) {
        card.addEventListener('click', function() {
            window.location.href = this.dataset.href;
        });
    });
});