"""
=============================================================================
  MODULE : affichage.py
  Rôle   : Affichage des tableaux en terminal (vrais traits Unicode)
           + écriture simultanée dans un fichier trace (.txt)
           + pagination interactive pour les grands tableaux
=============================================================================
"""

import sys
import os

# ═════════════════════════════════════════════════════════════════════════════
#  SYSTÈME DE SORTIE DUALE : terminal  +  fichier trace
#
#  Toute sortie passe par emit().
#  - Elle s'affiche toujours dans le terminal.
#  - Elle est aussi écrite dans le fichier trace si _trace_file est ouvert.
#
#  La pagination (pause après chaque tableau) est activée automatiquement
#  si le tableau dépasse SEUIL_PAGINATION lignes.
# ═════════════════════════════════════════════════════════════════════════════

_trace_file  = None   # fichier trace ouvert (ou None)
_pagination  = True   # True = pause après chaque tableau ; False = défilement libre

SEUIL_PAGINATION = 20  # nombre de lignes de données au-delà duquel on pagine


def configurer_trace(chemin_fichier):
    """
    Ouvre (ou recrée) le fichier trace.
    Appeler depuis main.py avant de lancer un algorithme.
    """
    global _trace_file
    if _trace_file:
        _trace_file.close()
    _trace_file = open(chemin_fichier, "w", encoding="utf-8")
    emit(f"  Trace écrite dans : {chemin_fichier}\n")


def fermer_trace():
    """Ferme le fichier trace proprement."""
    global _trace_file
    if _trace_file:
        _trace_file.close()
        _trace_file = None


def activer_pagination(actif=True):
    """Active ou désactive la pause entre les tableaux."""
    global _pagination
    _pagination = actif


def emit(texte=""):
    """Écrit `texte` dans le terminal ET dans le fichier trace."""
    print(texte)
    if _trace_file:
        _trace_file.write(texte + "\n")
        _trace_file.flush()


def pause(message="  [ Appuyez sur ENTRÉE pour continuer... ]"):
    """Pause interactive — ne bloque pas si on est en mode non-paginé."""
    if _pagination:
        try:
            input(message)
        except EOFError:
            pass   # mode non-interactif (ex: redirection)


# ═════════════════════════════════════════════════════════════════════════════
#  UTILITAIRES DE MISE EN FORME DES MESSAGES
# ═════════════════════════════════════════════════════════════════════════════

def titre_section(texte, niveau=1):
    """Affiche un titre de section bien visible."""
    if niveau == 1:
        b = "═" * (len(texte) + 6)
        emit(f"\n  ╔{b}╗\n  ║   {texte}   ║\n  ╚{b}╝\n")
    elif niveau == 2:
        b = "─" * (len(texte) + 6)
        emit(f"\n  ┌{b}┐\n  │   {texte}   │\n  └{b}┘\n")
    else:
        emit(f"\n  >>>  {texte}")

def info(msg):     emit(f"         {msg}")
def action(msg):   emit(f"  -->  {msg}")
def resultat(msg): emit(f"  [OK]  {msg}")
def erreur(msg):   emit(f"  [ERR]  {msg}")


# ═════════════════════════════════════════════════════════════════════════════
#  MOTEUR DE DESSIN DE TABLEAU
#
#  Résultat visuel :
#
#  ┌────────────────┬───────┬───────┬───────┬────────────────┐
#  │                │  C1   │  C2   │  C3   │  Provision Pi  │
#  ╠════════════════╪═══════╪═══════╪═══════╪════════════════╣
#  │       P1       │  30   │  20   │  20   │      450       │
#  ├────────────────┼───────┼───────┼───────┼────────────────┤
#  │       P2       │  10   │  50   │  20   │      250       │
#  ├────────────────┼───────┼───────┼───────┼────────────────┤
#  │       P3       │  50   │  40   │  30   │      250       │
#  ├────────────────┼───────┼───────┼───────┼────────────────┤
#  │       P4       │  30   │  20   │  30   │      450       │
#  ╠════════════════╪═══════╪═══════╪═══════╪════════════════╣
#  │  Commandes Cj  │  500  │  600  │  300  │                │
#  └────────────────┴───────┴───────┴───────┴────────────────┘
# ═════════════════════════════════════════════════════════════════════════════

def _centrer(valeur, largeur):
    """Centre `valeur` dans `largeur` caractères."""
    s = str(valeur)
    espace = largeur - len(s)
    g = espace // 2
    return " " * g + s + " " * (espace - g)


def dessiner_tableau(titre, etiq_lignes, entetes_cols, donnees, idx_sep=None):
    """
    Dessine un tableau complet dans le terminal avec de vrais traits Unicode.
    Écrit aussi dans le fichier trace si configuré.
    Pagine automatiquement si le tableau dépasse SEUIL_PAGINATION lignes.
    """
    emit("")
    if titre:
        emit(f"  ── {titre}")

    nb_cols        = len(entetes_cols)
    nb_lignes_data = len(etiq_lignes)

    # ── Calcul des largeurs ───────────────────────────────────────────────────
    w_etiq = max(len(str(e)) for e in etiq_lignes + [" "]) + 2

    lc = []
    for j in range(nb_cols):
        w = len(str(entetes_cols[j]))
        for row in donnees:
            if j < len(row):
                w = max(w, len(str(row[j])))
        lc.append(w + 2)

    # ── Constructeurs de lignes ───────────────────────────────────────────────

    def _seg(car, joints):
        cg, cm, cd, ce = joints
        s = cg + car * (w_etiq + 2) + ce
        for k, w in enumerate(lc):
            s += car * (w + 2)
            s += cm if k < nb_cols - 1 else cd
        emit("  " + s)

    def bord(haut=True):
        if haut:
            _seg("─", ("┌", "┬", "┐", "┬"))
        else:
            _seg("─", ("└", "┴", "┘", "┴"))

    def sep_simple():
        _seg("─", ("├", "┼", "┤", "┼"))

    def sep_double():
        _seg("═", ("╠", "╪", "╣", "╪"))

    def ligne(etiq, vals):
        s = "│ " + _centrer(etiq, w_etiq) + " │"
        for k, w in enumerate(lc):
            v = vals[k] if k < len(vals) else ""
            s += " " + _centrer(v, w) + " │"
        emit("  " + s)

    # ── Impression ────────────────────────────────────────────────────────────
    bord(haut=True)
    ligne("", entetes_cols)
    sep_double()

    for i, (etiq, vals) in enumerate(zip(etiq_lignes, donnees)):
        if idx_sep is not None and i == idx_sep:
            sep_double()
        elif i > 0 and (idx_sep is None or i < idx_sep):
            sep_simple()
        ligne(etiq, vals)

    bord(haut=False)
    emit("")

    # ── Pagination : pause si grand tableau ───────────────────────────────────
    if nb_lignes_data > SEUIL_PAGINATION:
        pause()


# ═════════════════════════════════════════════════════════════════════════════
#  WRAPPERS SPÉCIALISÉS
# ═════════════════════════════════════════════════════════════════════════════

def afficher_matrice_couts(couts, provisions, commandes, n, m,
                            titre="TABLEAU DES COÛTS"):
    """Affiche le tableau des coûts unitaires avec provisions et commandes."""
    entetes = [f"C{j+1}" for j in range(m)] + ["Provision Pi"]
    etiq    = [f"P{i+1}" for i in range(n)] + ["Commandes Cj"]
    donnees = [couts[i] + [provisions[i]] for i in range(n)] + [commandes + [""]]
    dessiner_tableau(titre, etiq, entetes, donnees, idx_sep=n)


def afficher_proposition(transport, provisions_res, commandes_res, n, m,
                          titre="PROPOSITION DE TRANSPORT",
                          cases_visitees=None):
    """
    Affiche le tableau de la proposition de transport b_{i,j}.

    cases_visitees :
      None   → tout vide (état initial, avant tout remplissage)
      set()  → affiche la valeur des cases visitées, vide pour les autres
      "all"  → affiche toutes les valeurs (récapitulatif final)
    """
    entetes = [f"C{j+1}" for j in range(m)] + ["Reste Prov."]
    etiq    = [f"P{i+1}" for i in range(n)] + ["Reste Cmd."]
    donnees = []

    for i in range(n):
        row = []
        for j in range(m):
            if cases_visitees is None:
                row.append("")
            elif cases_visitees == "all":
                row.append(transport[i][j])
            elif (i, j) in cases_visitees:
                row.append(transport[i][j])
            else:
                row.append("")
        row.append(provisions_res[i])
        donnees.append(row)

    donnees.append(list(commandes_res) + [""])
    dessiner_tableau(titre, etiq, entetes, donnees, idx_sep=n)


def afficher_cout_total(transport, couts, n, m, algo="Nord-Ouest"):
    """
    Calcule et affiche le coût total de la proposition.
    Retourne le coût total.
    """
    titre_section("CALCUL DU COÛT TOTAL DE LA PROPOSITION", 2)
    info("Formule : Coût total  =  Σ  a(i,j) × b(i,j)  pour toutes les cases de base")
    emit()

    total = 0
    for i in range(n):
        for j in range(m):
            if transport[i][j] > 0:
                c = couts[i][j] * transport[i][j]
                info(f"  P{i+1} --> C{j+1}  :  "
                     f"{couts[i][j]:>6}  ×  {transport[i][j]:>6}  =  {c:>9}")
                total += c

    emit()
    emit("  " + "═" * 58)
    emit(f"       COÛT TOTAL ({algo})  =  {total}")
    emit("  " + "═" * 58)
    emit()
    return total


def afficher_recapitulatif(transport, couts, provisions, commandes, n, m,
                            cout_total, algo="Nord-Ouest"):
    """Affiche le récapitulatif final : proposition, coûts, tableau croisé."""
    titre_section("RÉCAPITULATIF FINAL", 1)

    info(f"Proposition initiale complète obtenue par {algo} :")
    afficher_proposition(
        transport, provisions[:], commandes[:], n, m,
        titre=f"PROPOSITION INITIALE {algo.upper()} (finale)",
        cases_visitees="all")

    info("Rappel de la matrice des coûts :")
    afficher_matrice_couts(couts, provisions, commandes, n, m,
                           "MATRICE DES COÛTS (rappel)")

    # Tableau croisé coût × quantité
    titre_section("TABLEAU CROISÉ : coût unitaire × quantité transportée", 3)
    entetes = [f"C{j+1}" for j in range(m)]
    etiq    = [f"P{i+1}" for i in range(n)]
    donnees = []
    for i in range(n):
        row = [f"{couts[i][j]}×{transport[i][j]}" if transport[i][j] > 0 else ""
               for j in range(m)]
        donnees.append(row)
    dessiner_tableau("CONTRIBUTION DE CHAQUE CASE (coût × quantité)",
                     etiq, entetes, donnees)

    emit("  " + "═" * 58)
    emit(f"       COÛT TOTAL ({algo})  =  {cout_total}")
    emit("  " + "═" * 58)
    emit()
