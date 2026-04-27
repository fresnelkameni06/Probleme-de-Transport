"""
=============================================================================
  MODULE : balas_hammer.py
  Rôle   : Algorithme de la proposition initiale — méthode de Balas-Hammer
            (méthode des pénalités).
  État   : À implémenter — squelette prêt.
=============================================================================
"""

from collections import defaultdict, deque

from affichage import (titre_section, info, action, resultat,
                       afficher_matrice_couts, afficher_proposition,
                       afficher_cout_total, afficher_recapitulatif)


# ═════════════════════════════════════════════════════════════════════════════
#  CALCUL DES PÉNALITÉS
# ═════════════════════════════════════════════════════════════════════════════

def calculer_penalites(couts, lignes_actives, cols_actives, n, m):
    """
    Calcule les pénalités de ligne et de colonne.

    Pénalité d'une ligne i   = différence entre les deux plus petits coûts
                               de la ligne i (sur les colonnes encore actives).
    Pénalité d'une colonne j = différence entre les deux plus petits coûts
                               de la colonne j (sur les lignes encore actives).

    Retourne :
        pen_lignes : liste de (pénalité, ligne_i)  pour i dans lignes_actives
        pen_cols   : liste de (pénalité, col_j)    pour j dans cols_actives
    """
    pen_lignes = []
    for i in lignes_actives:
        valeurs = sorted(couts[i][j] for j in cols_actives)
        if len(valeurs) >= 2:
            pen = valeurs[1] - valeurs[0]
        else:
            pen = 0   # une seule colonne disponible : pénalité = 0 (aucun choix)
        pen_lignes.append((pen, i))

    pen_cols = []
    for j in cols_actives:
        valeurs = sorted(couts[i][j] for i in lignes_actives)
        if len(valeurs) >= 2:
            pen = valeurs[1] - valeurs[0]
        else:
            pen = 0   # une seule ligne disponible : pénalité = 0 (aucun choix)
        pen_cols.append((pen, j))

    return pen_lignes, pen_cols


def afficher_penalites(couts, provisions_res, commandes_res,
                       lignes_actives, cols_actives, n, m,
                       pen_lignes, pen_cols, iteration):
    """
    Affiche le tableau des coûts enrichi avec les pénalités
    sur la dernière colonne et la dernière ligne.
    """
    titre_section(f"TABLEAU DES PÉNALITÉS — itération {iteration}", 3)
    info("Pénalité = écart entre les 2 plus petits coûts disponibles.")
    print()

    # Construction du tableau : coûts + provision restante + pénalité ligne
    entetes = [f"C{j+1}" for j in range(m) if j in cols_actives] \
              + ["Reste Prov.", "Pénalité"]
    etiq    = [f"P{i+1}" for i in range(n) if i in lignes_actives] \
              + ["Reste Cmd.", "Pénalité"]

    pen_l_dict = {i: p for p, i in pen_lignes}
    pen_c_dict = {j: p for p, j in pen_cols}

    donnees = []
    for i in lignes_actives:
        row = [couts[i][j] for j in range(m) if j in cols_actives]
        row += [provisions_res[i], pen_l_dict.get(i, "")]
        donnees.append(row)

    # Ligne commandes restantes + pénalités colonnes
    row_cmd = [commandes_res[j] for j in range(m) if j in cols_actives]
    row_cmd += ["", ""]
    donnees.append(row_cmd)

    row_pen = [pen_c_dict.get(j, "") for j in range(m) if j in cols_actives]
    row_pen += ["", ""]
    donnees.append(row_pen)

    from affichage import dessiner_tableau
    dessiner_tableau("COÛTS + PÉNALITÉS", etiq, entetes, donnees,
                     idx_sep=len(lignes_actives))

    # Affichage de la pénalité maximale
    toutes = [(p, f"ligne P{i+1}") for p, i in pen_lignes] \
           + [(p, f"colonne C{j+1}") for p, j in pen_cols]
    max_pen, max_nom = max(toutes, key=lambda x: x[0])
    info(f"Pénalité maximale : {max_pen}  sur la {max_nom}")
    action("")
    return max_pen, max_nom


# ═════════════════════════════════════════════════════════════════════════════
#  ALGORITHME BALAS-HAMMER
# ═════════════════════════════════════════════════════════════════════════════

def balas_hammer(n, m, couts, provisions, commandes):
    """
    Construit la proposition initiale par la méthode de Balas-Hammer
    (méthode des pénalités de Vogel).

    Principe :
      1. Calculer les pénalités de chaque ligne et colonne.
      2. Choisir la ligne ou colonne avec la pénalité maximale.
      3. Dans cette ligne/colonne, affecter le maximum possible
         à la case de coût minimal.
      4. Saturer la ligne ou la colonne épuisée.
      5. Répéter jusqu'à ce que toutes les provisions soient écoulées.

    Retourne :
        transport : matrice n×m des quantités transportées b_{i,j}
    """

    titre_section("ALGORITHME BALAS-HAMMER — CONSTRUCTION DE LA PROPOSITION INITIALE", 1)

    prov           = provisions[:]
    cmd            = commandes[:]
    transport      = [[0] * m for _ in range(n)]
    cases_visitees = set()
    cases_fictives = set()

    lignes_actives = list(range(n))   # indices des fournisseurs encore actifs
    cols_actives   = list(range(m))   # indices des clients encore actifs
    iteration      = 0

    # ── État initial ──────────────────────────────────────────────────────────
    titre_section("ÉTAT INITIAL DU TABLEAU", 2)
    info("Voici le tableau des coûts unitaires (données du problème) :")
    afficher_matrice_couts(couts, provisions, commandes, n, m,
                           "TABLEAU DES COÛTS UNITAIRES")
    info("La proposition de transport est pour l'instant entièrement vide :")
    afficher_proposition(transport, prov[:], cmd[:], n, m,
                         "PROPOSITION INITIALE (vide)",
                         cases_visitees=None)

    titre_section("DÉBUT DE L'ALGORITHME BALAS-HAMMER", 2)
    info("Règle 1 : Calculer la pénalité de chaque ligne et colonne.")
    info("          Pénalité = (2ème plus petit coût) - (plus petit coût).")
    info("Règle 2 : Choisir la ligne ou colonne de pénalité MAXIMALE.")
    info("Règle 3 : Dans cette ligne/colonne, affecter le max possible")
    info("          à la case de coût MINIMAL.")
    info("Règle 4 : Saturer la provision ou commande épuisée, éliminer la ligne/colonne.")
    info("Règle 5 : Recommencer jusqu'à épuisement complet.")
    print()

    # ── Boucle principale ─────────────────────────────────────────────────────
    while lignes_actives and cols_actives:
        iteration += 1

        # 1. Calcul des pénalités
        pen_lignes, pen_cols = calculer_penalites(
            couts, lignes_actives, cols_actives, n, m)

        # 2. Affichage du tableau des pénalités
        afficher_penalites(couts, prov, cmd,
                           lignes_actives, cols_actives, n, m,
                           pen_lignes, pen_cols, iteration)

        # 3. Pénalité maximale (ligne ou colonne) avec tie-break robuste
        max_pen_l, best_l = max(pen_lignes, key=lambda x: x[0])
        max_pen_c, best_c = max(pen_cols,   key=lambda x: x[0])

        if max_pen_l > max_pen_c:
            # La ligne gagne clairement
            i_star = best_l
            j_star = min(cols_actives, key=lambda j: couts[i_star][j])
            action(f"Pénalité max sur ligne P{i_star+1} = {max_pen_l}  (> pén. col. {max_pen_c})")
            action(f"  --> Coût minimal sur P{i_star+1} : case ( P{i_star+1} , C{j_star+1} )"
                   f"  coût = {couts[i_star][j_star]}")

        elif max_pen_c > max_pen_l:
            # La colonne gagne clairement
            j_star = best_c
            i_star = min(lignes_actives, key=lambda i: couts[i][j_star])
            action(f"Pénalité max sur colonne C{j_star+1} = {max_pen_c}  (> pén. ligne {max_pen_l})")
            action(f"  --> Coût minimal sur C{j_star+1} : case ( P{i_star+1} , C{j_star+1} )"
                   f"  coût = {couts[i_star][j_star]}")

        else:
            # ÉGALITÉ des pénalités → tie-break : choisir la case de coût minimal global
            action(f"Égalité des pénalités : ligne = colonne = {max_pen_l}")
            action("  --> Tie-break : on choisit la case de coût minimal global.")
            # Chercher le min parmi toutes les cases (lignes actives × cols actives)
            i_star, j_star = min(
                ((i, j) for i in lignes_actives for j in cols_actives),
                key=lambda ij: couts[ij[0]][ij[1]]
            )
            action(f"  --> Case choisie : ( P{i_star+1} , C{j_star+1} )"
                   f"  coût = {couts[i_star][j_star]}")

        # 4. Affectation
        quantite = min(prov[i_star], cmd[j_star])
        action(f"Quantité à transporter = min( {prov[i_star]} , {cmd[j_star]} ) = {quantite}")
        print()

        transport[i_star][j_star] += quantite
        prov[i_star]              -= quantite
        cmd[j_star]               -= quantite
        cases_visitees.add((i_star, j_star))
        # Toute affectation à 0 est une case fictive (même logique que Nord-Ouest)
        if quantite == 0:
            cases_fictives.add((i_star, j_star))

        info(f"Après affectation de {quantite} unités de P{i_star+1} vers C{j_star+1} :")
        info(f"   Provision restante P{i_star+1}  =  {prov[i_star]}")
        info(f"   Commande  restante C{j_star+1}  =  {cmd[j_star]}")

        afficher_proposition(
            transport, prov[:], cmd[:], n, m,
            titre=f"PROPOSITION EN COURS  (après itération {iteration})",
            cases_visitees=cases_visitees)

        # 5. Élimination de la ligne ou colonne saturée
        #    RÈGLE CAS DÉGÉNÉRÉ : si provision ET commande épuisées simultanément,
        #    on n'élimine QU'UNE SEULE (la ligne), pour conserver n+m-1 cases de base.
        if prov[i_star] == 0 and cmd[j_star] == 0:
            # Cas dégénéré : les deux sont épuisés en même temps
            action(f"CAS DÉGÉNÉRÉ : provision P{i_star+1} ET commande C{j_star+1} épuisées simultanément.")
            action(f"  --> On élimine uniquement la LIGNE P{i_star+1} (on garde la colonne C{j_star+1} active).")
            action(f"  --> Cela garantit n+m-1 = {n+m-1} cases de base (solution non dégénérée).")
            lignes_actives.remove(i_star)
        elif prov[i_star] == 0:
            lignes_actives.remove(i_star)
            action(f"Provision P{i_star+1} épuisée --> ligne P{i_star+1} éliminée.")
        elif cmd[j_star] == 0:
            cols_actives.remove(j_star)
            action(f"Commande C{j_star+1} satisfaite --> colonne C{j_star+1} éliminée.")
        action("")

    # ── Fin ───────────────────────────────────────────────────────────────────
    titre_section("FIN DE L'ALGORITHME BALAS-HAMMER", 2)
    nb_base = sum(1 for ii in range(n) for jj in range(m) if transport[ii][jj] > 0)
    resultat("Toutes les provisions sont écoulées et toutes les commandes satisfaites.")
    resultat(f"Cases de base utilisées : {nb_base}  "
             f"(n + m - 1 = {n + m - 1} pour un problème non dégénérée)")
    print()

    # ── Reconstruction de cases_fictives (cases visitees avec quantite=0) ─────
    cases_fictives = {(ii, jj) for (ii, jj) in cases_visitees
                      if transport[ii][jj] == 0}

    # ── Ajout de fictives pour connecter le graphe si nécessaire ─────────────
    # On construit le graphe corrigé provisoire et on cherche les composantes.
    # Pour chaque composante isolée, on ajoute la fictive minimale qui la relie
    # à la composante principale — exactement comme NO relie via la diagonale.
    def composantes(cv, cf):
        g = defaultdict(set)
        for (ii, jj) in cv:
            g[f"P{ii}"].add(f"C{jj}")
            g[f"C{jj}"].add(f"P{ii}")
        if not g:
            return []
        comps, seen = [], set()
        for start_node in list(g):
            if start_node in seen:
                continue
            comp, q = set(), deque([start_node])
            while q:
                nd = q.popleft()
                if nd in seen:
                    continue
                seen.add(nd); comp.add(nd)
                for nb in g[nd]:
                    if nb not in seen:
                        q.append(nb)
            comps.append(comp)
        return comps

    comps = composantes(cases_visitees, cases_fictives)
    while len(comps) > 1:
        # Trouver une case fictive minimale reliant comp[0] à une autre comp
        main = comps[0]
        added = False
        for ii in range(n):
            if f"P{ii}" not in main:
                continue
            for jj in range(m):
                if f"C{jj}" in main:
                    continue
                # Case (ii,jj) relie P{ii} (dans main) à C{jj} (hors main)
                if (ii, jj) not in cases_visitees:
                    cases_visitees.add((ii, jj))
                    cases_fictives.add((ii, jj))
                    added = True
                    break
            if added:
                break
        if not added:
            break
        comps = composantes(cases_visitees, cases_fictives)

    # ─────────────────────────────────────────────────────────────────────────
    # GRAPHE BRUT (AVANT CORRECTION)
    # ─────────────────────────────────────────────────────────────────────────
    titre_section("GRAPHE NATUREL (AVANT CORRECTION)", 1)

    graph_brut = defaultdict(list)

    for (ii, jj) in cases_visitees:
        if (ii, jj) not in cases_fictives:
            action(f"[BRUT] arête : P{ii+1} ↔ C{jj+1}")
            graph_brut[f"P{ii}"].append(f"C{jj}")
            graph_brut[f"C{jj}"].append(f"P{ii}")

    # ── Connexité brute (BFS) ─────────────────────────────────────────────────
    titre_section("CONNEXITÉ (GRAPHE BRUT) — BFS", 2)

    visited = set()
    start = next(iter(graph_brut))
    queue = deque([start])
    visited.add(start)

    while queue:
        node = queue.popleft()
        action(f"[BRUT] visite : {node}")
        for neigh in graph_brut[node]:
            if neigh not in visited:
                visited.add(neigh)
                queue.append(neigh)

    if len(visited) == len(graph_brut):
        resultat("✔ Graphe brut connexe")
    else:
        resultat("❌ Graphe brut NON connexe")

    # ── Détection de cycle brut (BFS) ─────────────────────────────────────────
    titre_section("CYCLE (GRAPHE BRUT) — BFS", 2)

    visited_c  = {}          # noeud → parent
    queue_c    = deque()
    cycle_brut = False
    start_c    = next(iter(graph_brut))
    queue_c.append((start_c, None))
    visited_c[start_c] = None

    while queue_c and not cycle_brut:
        node, parent = queue_c.popleft()
        action(f"[BRUT] BFS visite : {node}")
        for neigh in graph_brut[node]:
            if neigh not in visited_c:
                visited_c[neigh] = node
                queue_c.append((neigh, node))
            elif neigh != parent:
                action(f"[BRUT] cycle détecté : {node} → {neigh}")
                cycle_brut = True
                break

    if cycle_brut:
        resultat("❌ Cycle présent dans le graphe brut")
    else:
        resultat("✔ Pas de cycle (brut)")

    # ── Nombre d'arêtes brut ──────────────────────────────────────────────────
    titre_section("NOMBRE D'ARÊTES (GRAPHE BRUT)", 2)

    nb_aretes_brut = sum(len(v) for v in graph_brut.values()) // 2
    info(f"[BRUT] arêtes = {nb_aretes_brut}")
    info(f"[BRUT] attendu = {n+m-1}")

    if nb_aretes_brut == n+m-1:
        resultat("✔ Nombre correct")
    else:
        resultat("❌ Nombre incorrect → dégénérescence")

    # ─────────────────────────────────────────────────────────────────────────
    # GRAPHE CORRIGÉ (AVEC CASES FICTIVES)
    # ─────────────────────────────────────────────────────────────────────────
    titre_section("GRAPHE APRÈS CORRECTION (AVEC CASES FICTIVES)", 1)

    graph = defaultdict(list)

    for (ii, jj) in cases_visitees:
        action(f"[CORRIGÉ] arête : P{ii+1} ↔ C{jj+1}")
        graph[f"P{ii}"].append(f"C{jj}")
        graph[f"C{jj}"].append(f"P{ii}")

    # ── Connexité corrigée (BFS) ───────────────────────────────────────────────
    titre_section("CONNEXITÉ (GRAPHE CORRIGÉ) — BFS", 2)

    visited2 = set()
    start2   = next(iter(graph))
    queue2   = deque([start2])
    visited2.add(start2)

    while queue2:
        node = queue2.popleft()
        action(f"[CORRIGÉ] visite : {node}")
        for neigh in graph[node]:
            if neigh not in visited2:
                visited2.add(neigh)
                queue2.append(neigh)

    if len(visited2) == len(graph):
        resultat("✔ Graphe connexe")
    else:
        resultat("❌ Graphe NON connexe")

    # ── Détection de cycle corrigé (BFS) ──────────────────────────────────────
    titre_section("CYCLE (GRAPHE CORRIGÉ) — BFS", 2)

    visited3   = {}          # noeud → parent
    queue3     = deque()
    has_cycle  = False
    start3     = next(iter(graph))
    queue3.append((start3, None))
    visited3[start3] = None

    while queue3 and not has_cycle:
        node, parent = queue3.popleft()
        action(f"[CORRIGÉ] BFS visite : {node}")
        for neigh in graph[node]:
            if neigh not in visited3:
                visited3[neigh] = node
                queue3.append((neigh, node))
            elif neigh != parent:
                action(f"[CORRIGÉ] cycle détecté : {node} → {neigh}")
                has_cycle = True
                break

    if has_cycle:
        resultat("❌ Cycle détecté")
    else:
        resultat("✔ Aucun cycle → arbre valide")

    # ── Nombre d'arêtes final ─────────────────────────────────────────────────
    titre_section("NOMBRE D'ARÊTES (FINAL)", 2)

    nb_base = len(cases_visitees)
    info(f"Cases de base = {nb_base}")
    info(f"Attendu = {n+m-1}")

    if nb_base == n+m-1:
        resultat("✔ Solution NON dégénérée")
    else:
        resultat("❌ Toujours dégénérée")

    titre_section("FIN DE L'ALGORITHME BALAS-HAMMER", 2)

    # Retourne transport ET cases_visitees pour le marche pied
    return transport, cases_visitees


def run(n, m, couts, provisions, commandes):
    """
    Point d'entrée public : exécute Balas-Hammer et affiche le récapitulatif.
    Retourne (transport, cout_total, cases_visitees).
    """
    transport, cases_visitees = balas_hammer(n, m, couts, provisions, commandes)
    cout_total = afficher_cout_total(transport, couts, n, m, algo="Balas-Hammer")
    afficher_recapitulatif(transport, couts, provisions, commandes,
                           n, m, cout_total, algo="Balas-Hammer")
    return transport, cout_total, cases_visitees
