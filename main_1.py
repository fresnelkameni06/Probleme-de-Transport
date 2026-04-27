"""
=============================================================================
  FICHIER  : main.py
  Rôle     : Point d'entrée principal du programme de transport.

  Comportement des traces :
    - Si on REFUSE l'optimisation  → un seul fichier trace (NO ou BH)
    - Si on ACCEPTE l'optimisation → même fichier trace (NO/BH + Marche Pied)
=============================================================================
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lecture   import lire_fichier, verifier_equilibre, lister_fichiers_problemes
from affichage import (titre_section, info, resultat, erreur,
                       configurer_trace, fermer_trace, activer_pagination, emit)
import nord_ouest  as algo_no
import balas_hammer as algo_bh
import marche_pied  as algo_mp

DOSSIER_TRACES   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "traces")
DOSSIER_TABLEAUX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tableaux")


# ═════════════════════════════════════════════════════════════════════════════
#  MENUS
# ═════════════════════════════════════════════════════════════════════════════

def menu_fichier():
    if not os.path.isdir(DOSSIER_TABLEAUX):
        print(f"\n  [ERR] Dossier introuvable : {DOSSIER_TABLEAUX}")
        sys.exit(1)

    fichiers = lister_fichiers_problemes(DOSSIER_TABLEAUX)
    if not fichiers:
        print(f"\n  [ERR] Aucun fichier 'problemeN.txt' trouvé dans : {DOSSIER_TABLEAUX}")
        sys.exit(1)

    lmax    = max(len(nom) for _, nom, _ in fichiers)
    largeur = max(lmax + 12, 54)
    bord    = "─" * (largeur + 2)

    print()
    print(f"  ┌{bord}┐")
    print(f"  │  {'PROBLÈMES DE TRANSPORT DISPONIBLES':^{largeur}}  │")
    print(f"  ├{bord}┤")
    for num, nom, _ in fichiers:
        ligne = f"  [{num:2d}]   {nom}"
        print(f"  │{ligne:<{largeur+2}}│")
    print(f"  │{'':^{largeur+2}}│")
    print(f"  │{'   [0]   Entrer un chemin manuellement':<{largeur+2}}│")
    print(f"  └{bord}┘")
    print()

    nums_valides = {num for num, _, _ in fichiers}
    chemins      = {num: chemin for num, _, chemin in fichiers}

    while True:
        choix = input("  --> Numéro du problème à traiter : ").strip()
        if choix == "0":
            chemin = input("  --> Chemin complet du fichier : ").strip()
            if os.path.isfile(chemin):
                return chemin
            print("  [ERR] Fichier introuvable. Réessayez.")
        elif choix.isdigit() and int(choix) in nums_valides:
            return chemins[int(choix)]
        else:
            valides = ", ".join(str(n) for n in sorted(nums_valides))
            print(f"  [ERR] Choix invalide. Numéros disponibles : {valides}")


def menu_algorithme(nom_fichier):
    print()
    print(f"  ┌──────────────────────────────────────────────────────────┐")
    print(f"  │         CHOIX DE L'ALGORITHME — {nom_fichier:<26}│")
    print(f"  ├──────────────────────────────────────────────────────────┤")
    print(f"  │   [1]   Nord-Ouest   (NO)                                │")
    print(f"  │   [2]   Balas-Hammer (BH)                                │")
    print(f"  └──────────────────────────────────────────────────────────┘")
    print()
    while True:
        choix = input("  --> Votre choix : ").strip()
        if choix == "1":
            return "NO"
        elif choix == "2":
            return "BH"
        else:
            print("  [ERR] Entrez 1 (Nord-Ouest) ou 2 (Balas-Hammer).")


def menu_optimisation():
    print()
    print(f"  ┌──────────────────────────────────────────────────────────┐")
    print(f"  │         OPTIMISATION PAR MARCHE PIED AVEC POTENTIELS     │")
    print(f"  ├──────────────────────────────────────────────────────────┤")
    print(f"  │   [1]   Oui — lancer l'optimisation (même fichier trace) │")
    print(f"  │   [2]   Non — garder la proposition initiale             │")
    print(f"  └──────────────────────────────────────────────────────────┘")
    print()
    while True:
        choix = input("  --> Votre choix : ").strip()
        if choix == "1":
            return True
        elif choix == "2":
            return False
        else:
            print("  [ERR] Entrez 1 (Oui) ou 2 (Non).")


def menu_mode(n):
    SEUIL = 8
    if n <= SEUIL:
        return "page"
    print()
    print(f"  ┌──────────────────────────────────────────────────────────┐")
    print(f"  │   Tableau de taille n={n:<3} — trace potentiellement longue  │")
    print(f"  ├──────────────────────────────────────────────────────────┤")
    print(f"  │   [1]  Mode paginé  (pause après chaque tableau)         │")
    print(f"  │   [2]  Mode fichier (tout dans trace_XXX.txt)            │")
    print(f"  └──────────────────────────────────────────────────────────┘")
    while True:
        choix = input("  --> Votre choix : ").strip()
        if choix == "1":
            return "page"
        elif choix == "2":
            return "fichier"
        else:
            print("  [ERR] Entrez 1 ou 2.")


# ═════════════════════════════════════════════════════════════════════════════
#  BOUCLE PRINCIPALE
# ═════════════════════════════════════════════════════════════════════════════

def main():
    print()
    print("  ╔══════════════════════════════════════════════════════════════╗")
    print("  ║         RÉSOLUTION D'UN PROBLÈME DE TRANSPORT               ║")
    print("  ║   Algorithmes : Nord-Ouest  |  Balas-Hammer  |  Marche Pied ║")
    print("  ╚══════════════════════════════════════════════════════════════╝")

    os.makedirs(DOSSIER_TRACES, exist_ok=True)
    continuer = True

    while continuer:

        # ── 1. Fichier ────────────────────────────────────────────────────────
        chemin      = menu_fichier()
        nom_fichier = os.path.basename(chemin)
        nom_base    = os.path.splitext(nom_fichier)[0]
        print(f"\n  --> Fichier sélectionné : {nom_fichier}\n")

        # ── 2. Lecture ────────────────────────────────────────────────────────
        try:
            n, m, couts, provisions, commandes = lire_fichier(chemin)
        except FileNotFoundError:
            erreur(f"Fichier introuvable : {chemin}"); continue
        except ValueError as e:
            erreur(f"Erreur de format : {e}"); continue
        except Exception as e:
            erreur(f"Erreur inattendue : {e}"); continue

        info(f"Fournisseurs (n) = {n}     Clients (m) = {m}")
        info(f"Somme des provisions : {sum(provisions)}")
        info(f"Somme des commandes  : {sum(commandes)}")

        equilibre, val = verifier_equilibre(provisions, commandes)
        if not equilibre:
            sp, sc = val
            print(f"\n  [ERR] Problème NON ÉQUILIBRÉ : Σ Pi = {sp}  ≠  Σ Cj = {sc}\n")
            continue
        resultat(f"Problème équilibré : Σ Pi = Σ Cj = {val}\n")

        # ── 3. Algorithme ─────────────────────────────────────────────────────
        algo    = menu_algorithme(nom_fichier)
        suffixe = "no" if algo == "NO" else "bh"
        nom_algo = "Nord-Ouest" if algo == "NO" else "Balas-Hammer"

        # ── 4. Optimisation ? (on demande AVANT d'ouvrir la trace) ───────────
        optimiser = menu_optimisation()

        # ── 5. Nom du fichier trace (un seul fichier dans tous les cas) ───────
        if optimiser:
            nom_trace = os.path.join(DOSSIER_TRACES,
                                     f"trace_{nom_base}_{suffixe}_avec_marche.txt")
        else:
            nom_trace = os.path.join(DOSSIER_TRACES,
                                     f"trace_{nom_base}_{suffixe}.txt")

        # ── 6. Mode d'affichage ───────────────────────────────────────────────
        mode = menu_mode(n)

        # Ouverture unique du fichier trace
        configurer_trace(nom_trace)

        if mode == "page":
            activer_pagination(True)
        else:
            activer_pagination(False)
            print(f"\n  Trace en cours d'écriture dans : {nom_trace}\n")

        emit(f"  Problème : {nom_fichier}   |   Algorithme : {nom_algo}"
             + ("  +  Marche Pied" if optimiser else ""))
        emit("")

        # ── 7. Exécution de l'algorithme initial ──────────────────────────────
        # NO et BH retournent maintenant (transport, cout_initial, cases_visitees)
        if algo == "NO":
            transport, cout_initial, cases_visitees = algo_no.run(
                n, m, couts, provisions, commandes)
        else:
            transport, cout_initial, cases_visitees = algo_bh.run(
                n, m, couts, provisions, commandes)

        # ── 8. Marche pied (dans le MÊME fichier trace) ───────────────────────
        if optimiser:
            transport_opt, cout_opt = algo_mp.run(
                n, m, couts, transport, cases_visitees,
                provisions, commandes, algo=nom_algo)

            # Résumé final dans le terminal
            fermer_trace()
            print()
            print(f"  [OK]  Trace complète sauvegardée dans : {nom_trace}")
            print()
            print("  " + "═" * 62)
            print(f"       COÛT INITIAL  ({nom_algo:<12})  =  {cout_initial}")
            print(f"       COÛT OPTIMAL  (Marche Pied)  =  {cout_opt}")
            print(f"       AMÉLIORATION                 =  {cout_initial - cout_opt}")
            print("  " + "═" * 62)
        else:
            fermer_trace()
            print()
            print(f"  [OK]  Trace sauvegardée dans : {nom_trace}")

        # ── 9. Continuer ? ────────────────────────────────────────────────────
        print()
        print("  ┌──────────────────────────────────────────────────────────┐")
        print("  │   [1]  Traiter un autre problème                         │")
        print("  │   [0]  Quitter                                           │")
        print("  └──────────────────────────────────────────────────────────┘")
        continuer = (input("  --> Votre choix : ").strip() == "1")

    print("\n  Au revoir !\n")


if __name__ == "__main__":
    main()
