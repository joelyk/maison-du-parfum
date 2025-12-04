// Gestion du panier
document.addEventListener('DOMContentLoaded', function() {
    // Mise à jour du compteur du panier
    function updateCartCount() {
        fetch('/panier-count')
            .then(response => response.json())
            .then(data => {
                const cartCount = document.getElementById('cart-count');
                if (cartCount) {
                    cartCount.textContent = data.count;
                }
            })
            .catch(error => console.error('Erreur:', error));
    }

    // Ajouter au panier
    const addToCartForms = document.querySelectorAll('.add-to-cart-form');
    addToCartForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch('/ajouter-au-panier', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Mettre à jour le compteur
                    const cartCount = document.getElementById('cart-count');
                    if (cartCount) {
                        cartCount.textContent = data.panier_count;
                    }
                    
                    // Afficher un message de confirmation
                    showNotification('Produit ajouté au panier !', 'success');
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                showNotification('Erreur lors de l\'ajout au panier', 'error');
            });
        });
    });

    // Modifier la quantité dans le panier
    const quantityButtons = document.querySelectorAll('.quantity-btn');
    quantityButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.parentElement.querySelector('.quantity-input');
            let quantity = parseInt(input.value);
            
            if (this.classList.contains('decrease')) {
                quantity = Math.max(1, quantity - 1);
            } else if (this.classList.contains('increase')) {
                quantity += 1;
            }
            
            input.value = quantity;
        });
    });

    // Fonction pour afficher les notifications
    function showNotification(message, type = 'info') {
        // Créer l'élément de notification
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Styles de base pour la notification
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        
        // Couleurs selon le type
        if (type === 'success') {
            notification.style.backgroundColor = '#4CAF50';
        } else if (type === 'error') {
            notification.style.backgroundColor = '#f44336';
        } else {
            notification.style.backgroundColor = '#2196F3';
        }
        
        // Ajouter au DOM
        document.body.appendChild(notification);
        
        // Animation d'entrée
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Supprimer après 3 secondes
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.parentElement.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // Gestion des formulaires d'administration
    const adminForms = document.querySelectorAll('.admin-form');
    adminForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const action = this.getAttribute('action');
            const method = this.getAttribute('method') || 'POST';
            
            fetch(action, {
                method: method,
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Opération réussie !', 'success');
                    // Recharger la page ou mettre à jour le contenu
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showNotification(data.error || 'Erreur lors de l\'opération', 'error');
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                showNotification('Erreur lors de l\'opération', 'error');
            });
        });
    });

    // Initialiser le compteur du panier
    updateCartCount();
});

// Fonction pour formater les prix
function formatPrice(price) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR'
    }).format(price);
}

// Gestion de la recherche (si implémentée)
function searchProducts(query) {
    // Implémentation de la recherche
    console.log('Recherche:', query);
}

// Filtrage des produits par catégorie
function filterByCategory(category) {
    window.location.href = `/boutique?categorie=${category}`;
}