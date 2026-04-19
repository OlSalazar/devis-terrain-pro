from datetime import datetime
from fpdf import FPDF
import streamlit as st
import os

# ---------------------------
# Configuration de base
# ---------------------------
CONFIG = {
    "campo": {"rendimento": 200},
    "floresta": {"rendimento": 150},
}

COUTS_BASE = {
    "campo": {1: 0.1193, 2: 0.2386},
    "floresta": {1: 0.1516, 2: 0.3032},
}

TVA = 0.10

TYPE_LABELS = {
    "Champ": "campo",
    "Forêt": "floresta",
}

KEY_TO_LABEL = {
    "campo": "Champ",
    "floresta": "Forêt",
}


# ---------------------------
# UI Base
# ---------------------------
st.set_page_config(page_title="Calculateur de devis terrain", layout="centered")
st.title("📊 Calculateur de devis terrain")
st.markdown("Remplissez les données ci-dessous pour obtenir une estimation :")

type_label = st.selectbox("🪓 Type de coupe :", list(TYPE_LABELS.keys()))
type_key = TYPE_LABELS[type_label]

surface = st.number_input("🧱 Surface du terrain (m²) :", min_value=0.0, step=10.0)
hauteur_cm = st.number_input("🌿 Hauteur de la végétation (cm) :", min_value=0.0, step=1.0)
ouvriers = st.number_input("👷 Nombre d’ouvriers :", min_value=1, step=1)
marge = st.slider("📈 Marge bénéficiaire (%) :", min_value=0, max_value=100, value=25)


# ---------------------------
# Calcul
# ---------------------------
def calculer(type_key, surface, hauteur_cm, ouvriers, marge):
    ouvriers = int(ouvriers)
    rendement = CONFIG[type_key]["rendimento"]
    cout_m2_base = COUTS_BASE[type_key][1 if ouvriers == 1 else 2]

    facteur_vegetation = 1 + (max(0, int((hauteur_cm - 30) / 10)) * 0.10)

    temps_heures = (surface / rendement) * facteur_vegetation / ouvriers

    prix_m2_ht_sans_marge = cout_m2_base * facteur_vegetation
    total_ht_sans_marge = prix_m2_ht_sans_marge * surface

    facteur_marge = 1 + (marge / 100)
    prix_m2_ht = prix_m2_ht_sans_marge * facteur_marge
    total_ht = total_ht_sans_marge * facteur_marge

    total_ttc = total_ht * (1 + TVA)

    return temps_heures, prix_m2_ht, total_ht, total_ttc


# ---------------------------
# Helpers PDF
# ---------------------------
def _compact_lines(*items):
    out = []
    for it in items:
        if it is None:
            continue
        s = str(it).strip()
        if s:
            out.append(s)
    return out


def _get_font_paths():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    regular_path = os.path.join(base_dir, "fonts", "DejaVuSans.ttf")
    bold_path = os.path.join(base_dir, "fonts", "DejaVuSans-Bold.ttf")
    return regular_path, bold_path


def _try_load_unicode_fonts(pdf: FPDF):
    regular_path, bold_path = _get_font_paths()

    if os.path.exists(regular_path) and os.path.exists(bold_path):
        pdf.add_font("DejaVu", style="", fname=regular_path)
        pdf.add_font("DejaVu", style="B", fname=bold_path)
        return True

    return False


def _safe_text(text: str, unicode_ok: bool) -> str:
    if unicode_ok:
        return text

    replacements = {
        "€": "EUR",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "…": "...",
        "É": "E",
        "È": "E",
        "Ê": "E",
        "Ë": "E",
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "À": "A",
        "Â": "A",
        "Ä": "A",
        "à": "a",
        "â": "a",
        "ä": "a",
        "Î": "I",
        "Ï": "I",
        "î": "i",
        "ï": "i",
        "Ô": "O",
        "Ö": "O",
        "ô": "o",
        "ö": "o",
        "Ù": "U",
        "Û": "U",
        "Ü": "U",
        "ù": "u",
        "û": "u",
        "ü": "u",
        "Ç": "C",
        "ç": "c",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def _draw_block_right(pdf: FPDF, y: float, lines: list[str], unicode_ok: bool, box_w: float = 85):
    if not lines:
        return
    x = pdf.w - pdf.r_margin - box_w
    pdf.set_xy(x, y)
    pdf.set_font("DejaVu" if unicode_ok else "Helvetica", "", 10)
    for line in lines:
        pdf.multi_cell(box_w, 5, _safe_text(line, unicode_ok))
        pdf.set_x(x)


def _draw_block_left(pdf: FPDF, y: float, lines: list[str], unicode_ok: bool, box_w: float = 120):
    if not lines:
        return
    x = pdf.l_margin
    pdf.set_xy(x, y)
    pdf.set_font("DejaVu" if unicode_ok else "Helvetica", "", 10)
    for line in lines:
        pdf.multi_cell(box_w, 5, _safe_text(line, unicode_ok))
        pdf.set_x(x)


# ---------------------------
# PDF
# ---------------------------
def generer_pdf(
    type_key, surface, hauteur_cm, ouvriers,
    temps_heures, prix_m2_ht, total_ttc,
    entreprise_nom="", entreprise_id="", entreprise_adresse="", entreprise_tel="", entreprise_email="",
    client_nom="", client_id="", client_adresse="", client_tel="", client_email="",
    lieu_chantier="", validite_jours="", remarques=""
):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    unicode_ok = _try_load_unicode_fonts(pdf)
    font_regular = "DejaVu" if unicode_ok else "Helvetica"
    font_bold = "DejaVu" if unicode_ok else "Helvetica"

    pdf.set_y(10)
    pdf.set_font(font_bold, "B", 16)
    pdf.cell(0, 8, _safe_text("PROPOSITION DE DEVIS", unicode_ok), ln=1, align="C")

    pdf.ln(12)

    entreprise_lines = _compact_lines(
        entreprise_nom,
        f"SIRET / NIF : {entreprise_id}" if entreprise_id else "",
        entreprise_adresse,
        f"Tel : {entreprise_tel}" if entreprise_tel else "",
        f"Email : {entreprise_email}" if entreprise_email else "",
    )

    client_lines = _compact_lines(
        "Client :",
        client_nom,
        f"NIF / Identifiant : {client_id}" if client_id else "",
        client_adresse,
        f"Tel : {client_tel}" if client_tel else "",
        f"Email : {client_email}" if client_email else "",
    )

    header_blocks_top_y = pdf.get_y()
    entreprise_y = header_blocks_top_y
    client_y = entreprise_y + 20

    _draw_block_right(pdf, y=entreprise_y, lines=entreprise_lines, unicode_ok=unicode_ok, box_w=85)
    _draw_block_left(pdf, y=client_y, lines=client_lines, unicode_ok=unicode_ok, box_w=120)

    entreprise_h = len(entreprise_lines) * 5
    client_h = len(client_lines) * 5
    y_after_blocks = max(entreprise_y + entreprise_h, client_y + client_h)

    pdf.set_y(y_after_blocks + 6)
    pdf.set_font(font_regular, "", 10)
    pdf.cell(0, 6, _safe_text(f"Date : {datetime.now().strftime('%d/%m/%Y')}", unicode_ok), ln=1, align="L")

    pdf.ln(2)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(5)

    type_txt = KEY_TO_LABEL[type_key]

    def write_section(title: str, body: str):
        pdf.set_font(font_bold, "B", 11)
        pdf.multi_cell(0, 6, _safe_text(title, unicode_ok))
        pdf.ln(1)
        pdf.set_font(font_regular, "", 10)
        pdf.multi_cell(0, 5, _safe_text(body, unicode_ok))
        pdf.ln(2)

    write_section(
        "Contexte",
        "Suite a votre demande de devis, nous vous presentons notre proposition pour le nettoyage "
        "et le controle de la vegetation, avec une intervention professionnelle realisee dans des "
        "conditions de securite, d'efficacite et de qualite."
    )

    write_section(
        "Resume technique de l'intervention",
        f"- Type de coupe : {type_txt}\n"
        f"- Surface estimee : {surface:.0f} m²\n"
        f"- Hauteur moyenne de la vegetation : {hauteur_cm:.0f} cm\n"
        f"- Equipe prevue : {int(ouvriers)} personne(s)\n"
        f"- Temps estime d'execution : {temps_heures:.1f} heures"
    )

    if str(lieu_chantier).strip():
        write_section("Lieu du chantier", lieu_chantier.strip())

    write_section(
        "Methodologie d'intervention",
        "1) Preparation du terrain et verification des acces, obstacles et zones sensibles "
        "(murs, clotures, arbres, structures).\n"
        "2) Debroussaillage / coupe de la vegetation avec controle des projections et protection "
        "des zones critiques.\n"
        "3) Finitions pres des limites, angles, murs et zones necessitant plus de precision.\n"
        "4) Inspection finale et ajustements eventuels sur les points necessitant un renforcement."
    )

    write_section(
        "Conditions commerciales",
        f"- Prix au m² (HT) : {prix_m2_ht:.4f} €\n"
        f"- Total a payer (TTC) : {total_ttc:.2f} €"
    )

    if str(validite_jours).strip():
        pdf.set_font(font_regular, "", 10)
        pdf.multi_cell(0, 5, _safe_text(f"Validite du devis : {validite_jours.strip()} jours.", unicode_ok))
        pdf.ln(2)

    if str(remarques).strip():
        pdf.set_font(font_bold, "B", 10)
        pdf.cell(0, 6, _safe_text("Remarques :", unicode_ok), ln=1)
        pdf.set_font(font_regular, "", 10)
        pdf.multi_cell(0, 5, _safe_text(remarques.strip(), unicode_ok))
        pdf.ln(2)

    pdf.set_font(font_regular, "", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(
        0, 4,
        _safe_text(
            "Note : Les valeurs sont estimees sur la base des informations fournies. Elles peuvent "
            "etre ajustees en cas de contraintes non visibles (acces, pentes, dechets, obstacles "
            "ou densite anormale de vegetation).",
            unicode_ok
        )
    )

    return bytes(pdf.output(dest="S"))


# ---------------------------
# Debug fontes (remover depois)
# ---------------------------
regular_font_path, bold_font_path = _get_font_paths()
# st.write("DejaVu regular existe:", os.path.exists(regular_font_path))
# st.write("DejaVu bold existe:", os.path.exists(bold_font_path))


# ---------------------------
# Calcul
# ---------------------------
calculer_btn = st.button("📊 Calculer le devis", use_container_width=True)

current_signature = (type_key, float(surface), float(hauteur_cm), int(ouvriers), int(marge))
if st.session_state.get("calc_signature") and st.session_state["calc_signature"] != current_signature:
    st.session_state.pop("calc_signature", None)
    st.session_state.pop("calc_results", None)

if calculer_btn:
    if surface <= 0:
        st.error("La surface doit etre superieure a 0 m².")
    else:
        temps_heures, prix_m2_ht, total_ht, total_ttc = calculer(
            type_key, surface, hauteur_cm, int(ouvriers), marge
        )

        st.session_state["calc_signature"] = current_signature
        st.session_state["calc_results"] = {
            "type_key": type_key,
            "surface": float(surface),
            "hauteur_cm": float(hauteur_cm),
            "ouvriers": int(ouvriers),
            "temps_heures": float(temps_heures),
            "prix_m2_ht": float(prix_m2_ht),
            "total_ht": float(total_ht),
            "total_ttc": float(total_ttc),
        }


# ---------------------------
# Résultats + détails + PDF
# ---------------------------
if "calc_results" in st.session_state:
    r = st.session_state["calc_results"]
    type_txt = KEY_TO_LABEL[r["type_key"]]

    st.markdown("### 🧾 Résumé du devis")
    st.markdown(
        f"""
Nous vous présentons une proposition de devis pour le **nettoyage et le contrôle de végétation** de type **{type_txt}**, sur une surface estimée de **{r['surface']:.0f} m²** avec une végétation moyenne de **{r['hauteur_cm']:.0f} cm**.

L’intervention est prévue avec une équipe de **{r['ouvriers']} personne(s)**, pour une **durée estimée de {r['temps_heures']:.1f} heures**.

Le prix proposé est de **{r['prix_m2_ht']:.4f} € par m² (HT)**, pour un total de **{r['total_ht']:.2f} € HT** et **{r['total_ttc']:.2f} € TTC**.
        """.strip()
    )

    st.divider()
    st.markdown("### ✍️ Détails du devis (optionnel) — remplissez uniquement ce qui est nécessaire")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Entreprise (optionnel)")
        entreprise_nom = st.text_input("Nom de l’entreprise", value="")
        entreprise_id = st.text_input("SIRET / NIF", value="")
        entreprise_adresse = st.text_input("Adresse", value="")
        entreprise_tel = st.text_input("Téléphone", value="")
        entreprise_email = st.text_input("Email", value="")

    with col_b:
        st.markdown("#### Client (optionnel)")
        client_nom = st.text_input("Nom du client", value="")
        client_id = st.text_input("NIF / Identifiant client", value="")
        client_adresse = st.text_input("Adresse du client", value="")
        client_tel = st.text_input("Téléphone du client", value="")
        client_email = st.text_input("Email du client", value="")

    st.markdown("#### Chantier / détails (optionnel)")
    lieu_chantier = st.text_input("Lieu du chantier", value="")
    validite_jours = st.text_input("Validité (jours)", value="")
    remarques = st.text_area("Remarques", value="", height=90)

    pdf_bytes = generer_pdf(
        r["type_key"], r["surface"], r["hauteur_cm"], r["ouvriers"],
        r["temps_heures"], r["prix_m2_ht"], r["total_ttc"],
        entreprise_nom=entreprise_nom, entreprise_id=entreprise_id, entreprise_adresse=entreprise_adresse,
        entreprise_tel=entreprise_tel, entreprise_email=entreprise_email,
        client_nom=client_nom, client_id=client_id, client_adresse=client_adresse,
        client_tel=client_tel, client_email=client_email,
        lieu_chantier=lieu_chantier, validite_jours=validite_jours, remarques=remarques
    )

    st.download_button(
        label="🧾 Générer et télécharger le PDF",
        data=pdf_bytes,
        file_name=f"devis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )