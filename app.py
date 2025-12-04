from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash,
)
import os
from datetime import datetime
from functools import wraps

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "votre_cle_secrete_tres_securisee"

# ---------- CONFIG BDD ----------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    BASE_DIR, "maison_du_parfum.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------- CONFIG UPLOAD AVATAR & PRODUITS ----------
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# Avatars clients
UPLOAD_FOLDER = os.path.join("static", "images", "avatars")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Images produits
PRODUCT_UPLOAD_FOLDER = os.path.join("static", "images", "products")
os.makedirs(PRODUCT_UPLOAD_FOLDER, exist_ok=True)

# ⚠ À mettre dans des variables d'environnement en production
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH") or generate_password_hash(
    "admin123"
)


# ---------- MODELES ----------
class Utilisateur(db.Model):
    __tablename__ = "utilisateurs"
    id = db.Column(db.Integer, primary_key=True)
    prenom = db.Column(db.String(100), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(255), default="avatars/default.png")
    cree_le = db.Column(db.DateTime, default=datetime.utcnow)

    commandes = db.relationship("Commande", backref="utilisateur", lazy=True)
    avis = db.relationship("AvisProduit", backref="utilisateur", lazy=True)


class Produit(db.Model):
    __tablename__ = "produits"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    prix = db.Column(db.Float, nullable=False)
    categorie = db.Column(db.String(100), nullable=False)
    description_courte = db.Column(db.String(255))
    description = db.Column(db.Text)
    image = db.Column(db.String(255))  # nom de fichier dans static/images/products
    stock = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    contenance = db.Column(db.String(50))
    type_peau = db.Column(db.String(100))
    pour_qui = db.Column(db.String(50))
    cree_le = db.Column(db.DateTime, default=datetime.utcnow)

    lignes_commande = db.relationship("LigneCommande", backref="produit", lazy=True)
    avis = db.relationship("AvisProduit", backref="produit", lazy=True)


class Commande(db.Model):
    __tablename__ = "commandes"
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    email = db.Column(db.String(150))
    telephone = db.Column(db.String(50))
    adresse = db.Column(db.String(255))
    ville = db.Column(db.String(100))
    code_postal = db.Column(db.String(20))
    pays = db.Column(db.String(100))
    total = db.Column(db.Float, nullable=False)
    statut = db.Column(db.String(50), default="en_attente")

    lignes = db.relationship("LigneCommande", backref="commande", lazy=True)


class LigneCommande(db.Model):
    __tablename__ = "lignes_commande"
    id = db.Column(db.Integer, primary_key=True)
    commande_id = db.Column(db.Integer, db.ForeignKey("commandes.id"), nullable=False)
    produit_id = db.Column(db.Integer, db.ForeignKey("produits.id"), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Float, nullable=False)
    sous_total = db.Column(db.Float, nullable=False)


class AvisProduit(db.Model):
    __tablename__ = "avis_produits"
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=False)
    produit_id = db.Column(db.Integer, db.ForeignKey("produits.id"), nullable=False)
    note = db.Column(db.Integer, nullable=False)  # 1 à 5
    commentaire = db.Column(db.Text)
    cree_le = db.Column(db.DateTime, default=datetime.utcnow)


# ---------- DECORATEURS ----------
def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)

    return decorated_function


def client_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("connexion", next=request.path))
        return f(*args, **kwargs)

    return decorated_function


# ---------- UTILS ----------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def seed_initial_products():
    """Insère quelques produits de démo si la table est vide."""
    if Produit.query.count() == 0:
        p1 = Produit(
            nom="Parfum Élégance",
            prix=89.90,
            categorie="parfums",
            description_courte="Un parfum raffiné aux notes florales et boisées",
            description="Ce parfum délicat mêle des notes de rose, de jasmin et de santal pour une élégance intemporelle. Parfait pour les occasions spéciales.",
            image="parfum-elegance.jpg",
            stock=15,
            notes="Notes de tête: Bergamote, Notes de cœur: Rose, Jasmin, Notes de fond: Santal, Vanille",
            contenance="100ml",
            type_peau="Tous types",
            pour_qui="Femme",
        )
        p2 = Produit(
            nom="Crème Hydratante Luxe",
            prix=45.50,
            categorie="soins-visage",
            description_courte="Hydratation intense pour une peau rayonnante",
            description="Cette crème riche en actifs naturels nourrit en profondeur et redonne éclat à votre peau. Formulée avec de l'acide hyaluronique et des extraits de rose.",
            image="creme-hydratante.jpg",
            stock=25,
            notes="",
            contenance="50ml",
            type_peau="Peau sèche et normale",
            pour_qui="Femme",
        )
        db.session.add_all([p1, p2])
        db.session.commit()


def init_db():
    """Création des tables + produits de démo."""
    db.create_all()
    seed_initial_products()


# ---------- ROUTES PRINCIPALES ----------
@app.route("/")
def index():
    produits = Produit.query.order_by(Produit.cree_le.desc()).all()
    nouveaux_produits = produits[:4]
    bestsellers = produits[-4:] if len(produits) >= 4 else produits
    return render_template(
        "index.html", nouveaux_produits=nouveaux_produits, bestsellers=bestsellers
    )


@app.route("/boutique")
def boutique():
    categorie = request.args.get("categorie", "")
    query = Produit.query

    if categorie:
        query = query.filter_by(categorie=categorie)

    produits = query.all()
    categories = [c[0] for c in db.session.query(Produit.categorie).distinct()]
    return render_template(
        "boutique.html",
        produits=produits,
        categories=categories,
        categorie_actuelle=categorie,
    )


@app.route("/produit/<int:produit_id>")
def produit(produit_id):
    produit = Produit.query.get_or_404(produit_id)

    similaires = (
        Produit.query.filter(
            Produit.categorie == produit.categorie, Produit.id != produit.id
        )
        .limit(4)
        .all()
    )

    # Avis de ce produit
    avis_liste = AvisProduit.query.filter_by(produit_id=produit.id).order_by(
        AvisProduit.cree_le.desc()
    ).all()
    nb_avis = len(avis_liste)
    note_moyenne = None
    if nb_avis > 0:
        note_moyenne = sum(a.note for a in avis_liste) / nb_avis

    avis_utilisateur = None
    if session.get("user_id"):
        avis_utilisateur = AvisProduit.query.filter_by(
            produit_id=produit.id, utilisateur_id=session["user_id"]
        ).first()

    return render_template(
        "produit.html",
        produit=produit,
        similaires=similaires,
        avis_liste=avis_liste,
        nb_avis=nb_avis,
        note_moyenne=note_moyenne,
        avis_utilisateur=avis_utilisateur,
    )


@app.route("/produit/<int:produit_id>/noter", methods=["POST"])
@client_login_required
def noter_produit(produit_id):
    produit = Produit.query.get_or_404(produit_id)
    try:
        note = int(request.form.get("note", 0))
    except ValueError:
        note = 0
    commentaire = request.form.get("commentaire", "").strip()

    if note < 1 or note > 5:
        flash("La note doit être entre 1 et 5 étoiles.", "error")
        return redirect(url_for("produit", produit_id=produit.id))

    utilisateur_id = session["user_id"]

    avis = AvisProduit.query.filter_by(
        produit_id=produit.id, utilisateur_id=utilisateur_id
    ).first()

    if avis:
        avis.note = note
        avis.commentaire = commentaire
        avis.cree_le = datetime.utcnow()
    else:
        avis = AvisProduit(
            produit_id=produit.id,
            utilisateur_id=utilisateur_id,
            note=note,
            commentaire=commentaire or None,
        )
        db.session.add(avis)

    db.session.commit()
    flash("Merci pour votre avis 💖", "success")
    return redirect(url_for("produit", produit_id=produit.id))


# ---------- PANIER ----------
@app.route("/panier")
def panier():
    panier = session.get("panier", [])
    panier_complet = []
    total = 0

    for item in panier:
        produit = Produit.query.get(item["id"])
        if produit:
            sous_total = produit.prix * item["quantite"]
            panier_complet.append(
                {
                    "id": produit.id,
                    "nom": produit.nom,
                    "image": produit.image,
                    "description_courte": produit.description_courte,
                    "prix": produit.prix,
                    "quantite": item["quantite"],
                    "sous_total": sous_total,
                }
            )
            total += sous_total

    return render_template("panier.html", panier=panier_complet, total=total)


@app.route("/panier-count")
def panier_count():
    panier = session.get("panier", [])
    return jsonify({"count": len(panier)})


@app.route("/ajouter-au-panier", methods=["POST"])
def ajouter_au_panier():
    produit_id = int(request.form.get("produit_id"))
    quantite = int(request.form.get("quantite", 1))

    panier = session.get("panier", [])

    produit_existant = next((item for item in panier if item["id"] == produit_id), None)

    if produit_existant:
        produit_existant["quantite"] += quantite
    else:
        panier.append({"id": produit_id, "quantite": quantite})

    session["panier"] = panier
    return jsonify({"success": True, "panier_count": len(panier)})


@app.route("/modifier-quantite-panier", methods=["POST"])
def modifier_quantite_panier():
    produit_id = int(request.form.get("produit_id"))
    nouvelle_quantite = int(request.form.get("quantite"))

    panier = session.get("panier", [])

    for item in panier:
        if item["id"] == produit_id:
            if nouvelle_quantite <= 0:
                panier.remove(item)
            else:
                item["quantite"] = nouvelle_quantite
            break

    session["panier"] = panier
    return jsonify({"success": True})


@app.route("/supprimer-du-panier", methods=["POST"])
def supprimer_du_panier():
    produit_id = int(request.form.get("produit_id"))

    panier = session.get("panier", [])
    panier = [item for item in panier if item["id"] != produit_id]

    session["panier"] = panier
    return jsonify({"success": True})


# ---------- COMMANDE ----------
@app.route("/commande")
@client_login_required
def commande():
    panier = session.get("panier", [])
    if not panier:
        return redirect(url_for("panier"))

    panier_complet = []
    total = 0

    for item in panier:
        produit = Produit.query.get(item["id"])
        if produit:
            sous_total = produit.prix * item["quantite"]
            panier_complet.append(
                {
                    "id": produit.id,
                    "nom": produit.nom,
                    "image": produit.image,
                    "prix": produit.prix,
                    "quantite": item["quantite"],
                    "sous_total": sous_total,
                }
            )
            total += sous_total

    return render_template("commande.html", panier=panier_complet, total=total)


@app.route("/traiter-commande", methods=["POST"])
@client_login_required
def traiter_commande():
    nom = request.form.get("nom")
    prenom = request.form.get("prenom")
    email = request.form.get("email")
    telephone = request.form.get("telephone")
    adresse = request.form.get("adresse")
    ville = request.form.get("ville")
    code_postal = request.form.get("code_postal")
    pays = request.form.get("pays")

    panier = session.get("panier", [])
    if not panier:
        return redirect(url_for("panier"))

    total = 0
    for item in panier:
        produit = Produit.query.get(item["id"])
        if produit:
            total += produit.prix * item["quantite"]

    commande = Commande(
        utilisateur_id=session.get("user_id"),
        nom=nom,
        prenom=prenom,
        email=email,
        telephone=telephone,
        adresse=adresse,
        ville=ville,
        code_postal=code_postal,
        pays=pays,
        total=total,
        statut="en_attente",
    )
    db.session.add(commande)
    db.session.flush()

    for item in panier:
        produit = Produit.query.get(item["id"])
        if produit:
            sous_total = produit.prix * item["quantite"]
            ligne = LigneCommande(
                commande_id=commande.id,
                produit_id=produit.id,
                quantite=item["quantite"],
                prix_unitaire=produit.prix,
                sous_total=sous_total,
            )
            db.session.add(ligne)

    db.session.commit()
    session["panier"] = []

    return render_template("commande-confirmee.html", commande=commande)


# ---------- PAGES STATIQUES ----------
@app.route("/a-propos")
def a_propos():
    return render_template("apropos.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


# ---------- AUTH CLIENT ----------
@app.route("/inscription", methods=["GET", "POST"])
def inscription():
    if session.get("user_id"):
        return redirect(url_for("index"))

    erreur = None

    if request.method == "POST":
        prenom = request.form.get("prenom", "").strip()
        nom = request.form.get("nom", "").strip()
        email = request.form.get("email", "").strip().lower()
        mot_de_passe = request.form.get("mot_de_passe", "").strip()
        confirmation = request.form.get("confirmation", "").strip()

        if not prenom or not nom or not email or not mot_de_passe:
            erreur = "Veuillez remplir tous les champs."
        elif mot_de_passe != confirmation:
            erreur = "Les mots de passe ne correspondent pas."
        else:
            if Utilisateur.query.filter_by(email=email).first():
                erreur = "Un compte existe déjà avec cet e-mail."
            else:
                nouvel_utilisateur = Utilisateur(
                    prenom=prenom,
                    nom=nom,
                    email=email,
                    mot_de_passe_hash=generate_password_hash(mot_de_passe),
                )
                db.session.add(nouvel_utilisateur)
                db.session.commit()

                session["user_id"] = nouvel_utilisateur.id
                session["user_email"] = nouvel_utilisateur.email
                session["user_prenom"] = nouvel_utilisateur.prenom

                return redirect(url_for("index"))

    return render_template("inscription.html", erreur=erreur)


@app.route("/connexion", methods=["GET", "POST"])
def connexion():
    if session.get("user_id"):
        return redirect(url_for("index"))

    erreur = None
    next_url = request.args.get("next") or url_for("index")

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        mot_de_passe = request.form.get("mot_de_passe", "").strip()
        next_url = request.form.get("next") or url_for("index")

        utilisateur = Utilisateur.query.filter_by(email=email).first()

        if not utilisateur or not check_password_hash(
            utilisateur.mot_de_passe_hash, mot_de_passe
        ):
            erreur = "Identifiants incorrects."
        else:
            session["user_id"] = utilisateur.id
            session["user_email"] = utilisateur.email
            session["user_prenom"] = utilisateur.prenom
            return redirect(next_url)

    return render_template("connexion.html", erreur=erreur, next=next_url)


@app.route("/deconnexion")
def deconnexion():
    session.pop("user_id", None)
    session.pop("user_email", None)
    session.pop("user_prenom", None)
    return redirect(url_for("index"))


@app.route("/mon-compte", methods=["GET", "POST"])
@client_login_required
def mon_compte():
    utilisateur = Utilisateur.query.get(session.get("user_id"))
    if not utilisateur:
        return redirect(url_for("deconnexion"))

    if request.method == "POST":
        prenom = request.form.get("prenom", "").strip()
        nom = request.form.get("nom", "").strip()
        email = request.form.get("email", "").strip().lower()

        email_existant = Utilisateur.query.filter(
            Utilisateur.email == email, Utilisateur.id != utilisateur.id
        ).first()

        if email_existant:
            flash("Cet e-mail est déjà utilisé par un autre compte.", "error")
        else:
            utilisateur.prenom = prenom
            utilisateur.nom = nom
            utilisateur.email = email

            if "avatar" in request.files:
                file = request.files["avatar"]
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"user_{utilisateur.id}_" + file.filename)
                    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(filepath)
                    utilisateur.avatar = "avatars/" + filename

            db.session.commit()

            session["user_email"] = utilisateur.email
            session["user_prenom"] = utilisateur.prenom

            flash("Vos informations ont été mises à jour avec succès 💖", "success")

    commandes = (
        Commande.query.filter_by(utilisateur_id=utilisateur.id)
        .order_by(Commande.date.desc())
        .all()
    )
    return render_template(
        "mon-compte.html", utilisateur=utilisateur, commandes=commandes
    )


# ---------- ADMIN ----------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == ADMIN_USERNAME and check_password_hash(
            ADMIN_PASSWORD_HASH, password
        ):
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Identifiants incorrects"

    return render_template("admin/login.html", error=error)


@app.route("/admin/dashboard")
@admin_login_required
def admin_dashboard():
    produits = Produit.query.all()
    commandes = Commande.query.order_by(Commande.date.desc()).all()
    total_commandes = len(commandes)
    total_produits = len(produits)
    total_ca = sum(c.total for c in commandes) if commandes else 0

    return render_template(
        "admin/dashboard.html",
        produits=produits,
        commandes=commandes,
        total_commandes=total_commandes,
        total_produits=total_produits,
        total_ca=total_ca,
    )


@app.route("/admin/produits")
@admin_login_required
def admin_produits():
    produits = Produit.query.order_by(Produit.cree_le.desc()).all()
    return render_template("admin/gestion-produits.html", produits=produits)


@app.route("/admin/ajouter-produit", methods=["POST"])
@admin_login_required
def admin_ajouter_produit():
    nom = request.form.get("nom")
    prix = request.form.get("prix")
    categorie = request.form.get("categorie")
    stock = request.form.get("stock", 0)

    if not nom or not prix or not categorie:
        return jsonify(
            {"success": False, "error": "Nom, prix et catégorie sont obligatoires."}
        )

    image_filename = None
    file = request.files.get("image_file")
    if file and allowed_file(file.filename):
        filename = secure_filename(
            f"prod_{datetime.utcnow().timestamp()}_" + file.filename
        )
        filepath = os.path.join(PRODUCT_UPLOAD_FOLDER, filename)
        file.save(filepath)
        image_filename = filename

    produit = Produit(
        nom=nom,
        prix=float(prix),
        categorie=categorie,
        description_courte=request.form.get("description_courte") or None,
        description=request.form.get("description") or None,
        image=image_filename,
        stock=int(stock),
        notes=request.form.get("notes") or None,
        contenance=request.form.get("contenance") or None,
        type_peau=request.form.get("type_peau") or None,
        pour_qui=request.form.get("pour_qui") or None,
    )

    db.session.add(produit)
    db.session.commit()

    return jsonify({"success": True})


@app.route("/admin/modifier-produit/<int:produit_id>", methods=["POST"])
@admin_login_required
def admin_modifier_produit(produit_id):
    produit = Produit.query.get_or_404(produit_id)

    produit.nom = request.form.get("nom") or produit.nom

    prix = request.form.get("prix")
    if prix:
        produit.prix = float(prix)

    categorie = request.form.get("categorie")
    if categorie:
        produit.categorie = categorie

    produit.description_courte = request.form.get("description_courte") or None
    produit.description = request.form.get("description") or None

    stock = request.form.get("stock")
    if stock is not None and stock != "":
        produit.stock = int(stock)

    produit.notes = request.form.get("notes") or None
    produit.contenance = request.form.get("contenance") or None
    produit.type_peau = request.form.get("type_peau") or None
    produit.pour_qui = request.form.get("pour_qui") or None

    file = request.files.get("image_file")
    if file and allowed_file(file.filename):
        filename = secure_filename(f"prod_{produit.id}_" + file.filename)
        filepath = os.path.join(PRODUCT_UPLOAD_FOLDER, filename)
        file.save(filepath)
        produit.image = filename

    db.session.commit()
    return jsonify({"success": True})


@app.route("/admin/supprimer-produit/<int:produit_id>", methods=["POST"])
@admin_login_required
def admin_supprimer_produit(produit_id):
    produit = Produit.query.get_or_404(produit_id)
    db.session.delete(produit)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/admin/logout")
@admin_login_required
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("index"))

with app.app_context():
    init_db()

# ---------- LANCEMENT ----------
if __name__ == "__main__":
   # with app.app_context():
        # 💡 En dev, si tu modifies les modèles, supprime "maison_du_parfum.db"
        # puis relance pour recréer les tables proprement.
      #  init_db()
    app.run(debug=True)
