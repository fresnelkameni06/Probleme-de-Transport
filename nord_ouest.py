"""
=============================================================================
  MODULE : nord_ouest.py
  Rôle   : Algorithme de la proposition initiale — méthode du coin Nord-Ouest.
=============================================================================
"""

from collections import defaultdict, deque

from affichage import (titre_section, info, action, resultat,
                       afficher_matrice_couts, afficher_proposition,
                       afficher_cout_total, afficher_recapitulatif)


def nord_ouest(n, m, couts, provisions, commandes):

    titre_section("ALGORITHME NORD-OUEST — CONSTRUCTION DE LA PROPOSITION INITIALE", 1)

    prov           = provisions[:]
    cmd            = commandes[:]
    transport      = [[0] * m for _ in range(n)]
    cases_visitees = set()
    cases_fictives = set()
    i, j, iteration = 0, 0, 0

    titre_section("ÉTAT INITIAL DU TABLEAU", 2)
    info("Voici le tableau des coûts unitaires (données du problème) :")
    afficher_matrice_couts(couts, provisions, commandes, n, m,
                           "TABLEAU DES COÛTS UNITAIRES")

    info("La proposition de transport est pour l'instant entièrement vide :")
    afficher_proposition(transport, prov[:], cmd[:], n, m,
                         "PROPOSITION INITIALE (vide)",
                         cases_visitees=None)

    while i < n and j < m:
        iteration += 1
        titre_section(f"ITÉRATION {iteration}  —  Case ( P{i+1} , C{j+1} )", 3)

        quantite = min(prov[i], cmd[j])
        action(f"On transporte min({prov[i]}, {cmd[j]}) = {quantite}")

        transport[i][j] += quantite
        prov[i] -= quantite
        cmd[j]  -= quantite
        cases_visitees.add((i, j))

        afficher_proposition(transport, prov[:], cmd[:], n, m,
                             titre=f"PROPOSITION EN COURS (itération {iteration})",
                             cases_visitees=cases_visitees)

        if prov[i] == 0 and cmd[j] == 0:
            action("CAS DÉGÉNÉRÉ détecté (ligne et colonne saturées)")
            action(f"→ Il faut conserver n+m-1 = {n+m-1} cases de base")

            if j + 1 < m:
                action(f"→ On ajoute une case fictive en (P{i+1}, C{j+2})")
                transport[i][j+1] = 0
                cases_visitees.add((i, j+1))
                cases_fictives.add((i, j+1))
            elif i + 1 < n:
                action(f"→ On ajoute une case fictive en (P{i+2}, C{j+1})")
                transport[i+1][j] = 0
                cases_visitees.add((i+1, j))
                cases_fictives.add((i+1, j))

            action("→ Déplacement en diagonale")
            i += 1
            j += 1

        elif prov[i] == 0:
            action("→ Ligne saturée → descente")
            i += 1
        else:
            action("→ Colonne saturée → déplacement droite")
            j += 1

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

    visited_c  = {}
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

    visited3   = {}
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

    titre_section("FIN DE L'ALGORITHME NORD-OUEST", 2)

    # Retourne transport ET cases_visitees pour le marche pied
    return transport, cases_visitees


def run(n, m, couts, provisions, commandes):
    transport, cases_visitees = nord_ouest(n, m, couts, provisions, commandes)
    cout_total = afficher_cout_total(transport, couts, n, m, algo="Nord-Ouest")
    afficher_recapitulatif(transport, couts, provisions, commandes,
                           n, m, cout_total, algo="Nord-Ouest")
    return transport, cout_total, cases_visitees
