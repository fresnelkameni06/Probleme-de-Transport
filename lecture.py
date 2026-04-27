"""
=============================================================================
  MODULE : lecture.py
  Rôle   : Lecture et validation des fichiers de problèmes de transport.
           Format attendu (fichier problemeN.txt) :
               n  m
               a_{1,1}  a_{1,2} ... a_{1,m}   P_1
               ...
               a_{n,1}  a_{n,2} ... a_{n,m}   P_n
               C_1  C_2 ... C_m
=============================================================================
"""

import os


def lire_fichier(chemin):
    """
    Lit un fichier .txt de problème de transport.

    Retourne :
        n          : nombre de fournisseurs
        m          : nombre de clients
        couts      : matrice n×m des coûts unitaires  a_{i,j}
        provisions : liste des provisions P_i  (longueur n)
        commandes  : liste des commandes  C_j  (longueur m)

    Lève :
        FileNotFoundError si le fichier n'existe pas
        ValueError        si le format est incorrect
    """
    with open(chemin, "r", encoding="utf-8") as f:
        lignes = [l.strip() for l in f if l.strip()]

    try:
        n, m = int(lignes[0].split()[0]), int(lignes[0].split()[1])
    except (IndexError, ValueError):
        raise ValueError("La première ligne doit contenir deux entiers : n et m.")

    couts, provisions = [], []
    for i in range(1, n + 1):
        try:
            vals = list(map(int, lignes[i].split()))
        except (IndexError, ValueError):
            raise ValueError(f"Erreur de lecture à la ligne {i+1} (fournisseur P{i}).")
        if len(vals) != m + 1:
            raise ValueError(
                f"Ligne {i+1} : attendu {m+1} valeurs (m coûts + 1 provision), "
                f"obtenu {len(vals)}.")
        couts.append(vals[:m])
        provisions.append(vals[m])

    try:
        commandes = list(map(int, lignes[n + 1].split()))
    except (IndexError, ValueError):
        raise ValueError("Erreur de lecture de la ligne des commandes.")

    if len(commandes) != m:
        raise ValueError(
            f"Ligne des commandes : attendu {m} valeurs, obtenu {len(commandes)}.")

    return n, m, couts, provisions, commandes


def verifier_equilibre(provisions, commandes):
    """
    Vérifie que le problème est équilibré : Σ Pi = Σ Cj.
    Retourne (True, somme) si équilibré, (False, (somme_p, somme_c)) sinon.
    """
    sp = sum(provisions)
    sc = sum(commandes)
    if sp == sc:
        return True, sp
    return False, (sp, sc)


def lister_fichiers_problemes(dossier):
    """
    Liste tous les fichiers .txt du dossier dont le nom commence par 'probleme'.
    Les trie par numéro de problème.
    Retourne une liste de (numéro, nom_fichier, chemin_complet).
    """
    fichiers = []
    for nom in os.listdir(dossier):
        if nom.endswith(".txt") and nom.lower().startswith("probleme"):
            chemin = os.path.join(dossier, nom)
            # Extraction du numéro (ex: "probleme3.txt" -> 3)
            try:
                numero = int(nom.lower().replace("probleme", "").replace(".txt", ""))
            except ValueError:
                numero = 999  # fichier non numéroté : mis à la fin
            fichiers.append((numero, nom, chemin))
    fichiers.sort(key=lambda x: x[0])
    return fichiers
