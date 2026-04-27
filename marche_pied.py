"""
=============================================================================
  MODULE : marche_pied.py
  Rôle   : Optimisation par la méthode du marche pied avec potentiels.

  Signature run() conforme à main.py :
    run(n, m, couts, transport, provisions, commandes, algo="")

  Algorithme par itération :
    1. Racine BFS = sommet de degré maximal dans l'arbre de base
       E(racine) = 0
    2. Propagation BFS : E(Pi) - E(Cj) = c(i,j)
       → E(Cj) = E(Pi) - c(i,j)   si E(Pi) connu
       → E(Pi) = E(Cj) + c(i,j)   si E(Cj) connu
    3. Tableau des coûts potentiels : c*(i,j) = E(Pi) - E(Cj)
    4. Tableau des coûts marginaux  : d(i,j)  = c(i,j) - c*(i,j)
    5. Si tous d >= 0 → OPTIMAL → coût total affiché
       Sinon → case pivot = d le plus négatif
    6. Cycle rectangle fermé dans les cases de base
       case pivot reçoit (+Δ), alternance +/- sur le cycle
    7. Δ = min des quantités sur les cases (-)
    8. +Δ sur les (+), -Δ sur les (-),
       case (-) tombée à 0 sort de la base, case pivot entre
    9. Recommencer depuis 1
=============================================================================
"""

from collections import defaultdict, deque

from affichage import (titre_section, info, action, resultat,
                       afficher_matrice_couts, afficher_proposition,
                       afficher_cout_total, afficher_recapitulatif,
                       dessiner_tableau)


# ═════════════════════════════════════════════════════════════════════════════
#  1. CHOIX DE LA RACINE  (sommet de degré maximal dans l'arbre de base)
# ═════════════════════════════════════════════════════════════════════════════

def choisir_racine(cases_base):
    """
    Compte le degré de chaque sommet Pi / Cj dans l'arbre de base.
    Retourne la clé (str) du sommet de degré maximal.
    Complexité : O(n+m)
    """
    degre = defaultdict(int)
    for (i, j) in cases_base:
        degre[f"P{i}"] += 1
        degre[f"C{j}"] += 1

    racine  = max(degre, key=degre.get)
    deg_max = degre[racine]

    titre_section("CHOIX DE LA RACINE (POTENTIEL DE RÉFÉRENCE)", 2)
    info("On choisit le sommet ayant le plus de connexions dans l'arbre.")
    info("Cela minimise la profondeur du BFS et donc la complexité.")
    print()

    # Tableau des degrés
    entetes_deg = sorted(degre.keys(), key=lambda x: (x[0], int(x[1:])))
    vals_deg    = [degre[k] for k in entetes_deg]
    dessiner_tableau(
        "DEGRÉS DES SOMMETS",
        ["Degré"],
        entetes_deg,
        [vals_deg]
    )

    info(f"Racine choisie : {racine}  (degré maximal = {deg_max})")
    info(f"→ E({racine}) = 0  (potentiel de référence)")
    print()
    return racine


# ═════════════════════════════════════════════════════════════════════════════
#  2. CALCUL DES POTENTIELS PAR BFS
# ═════════════════════════════════════════════════════════════════════════════

def calculer_potentiels(couts, cases_base, racine):
    """
    Propage E par BFS depuis la racine.
    E(Pi) - E(Cj) = c(i,j)
      si E(Pi) connu : E(Cj) = E(Pi) - c(i,j)
      si E(Cj) connu : E(Pi) = E(Cj) + c(i,j)
    Retourne E : dict  "P{i}" / "C{j}"  →  valeur (int)
    Complexité : O(n+m)
    """
    titre_section("CALCUL DES POTENTIELS — BFS", 2)
    info("Formule de base : E(Pi) - E(Cj) = c(i,j)  pour chaque case de base.")
    info("On propage depuis la racine en utilisant les cases déjà calculées.")
    print()

    adj = defaultdict(list)
    for (i, j) in cases_base:
        adj[f"P{i}"].append((f"C{j}", i, j))
        adj[f"C{j}"].append((f"P{i}", i, j))

    E     = {racine: 0}
    queue = deque([racine])

    while queue:
        node = queue.popleft()
        for (voisin, i, j) in adj[node]:
            if voisin in E:
                continue
            if node == f"P{i}":
                # E(Pi) connu → E(Cj) = E(Pi) - c(i,j)
                E[voisin] = E[node] - couts[i][j]
                action(f"E({node}) - E({voisin}) = {couts[i][j]}"
                       f"  →  E({voisin}) = {E[node]} - {couts[i][j]}"
                       f" = {E[voisin]}")
            else:
                # E(Cj) connu → E(Pi) = E(Cj) + c(i,j)
                E[voisin] = E[node] + couts[i][j]
                action(f"E({voisin}) - E({node}) = {couts[i][j]}"
                       f"  →  E({voisin}) = {E[node]} + {couts[i][j]}"
                       f" = {E[voisin]}")
            queue.append(voisin)

    print()
    return E


# ═════════════════════════════════════════════════════════════════════════════
#  3. TABLEAU DES COÛTS POTENTIELS  c*(i,j) = E(Pi) - E(Cj)
# ═════════════════════════════════════════════════════════════════════════════

def afficher_tableau_potentiels(E, couts_pot, cases_base, n, m):
    """
    Affiche les valeurs des potentiels puis le tableau n×m
    des coûts potentiels c*(i,j). Même style que NO/BH.
    """
    # Potentiels
    titre_section("VALEURS DES POTENTIELS", 2)
    info("E(racine) = 0  puis propagation par BFS.")
    print()

    entetes_p = [f"P{i+1}" for i in range(n)]
    entetes_c = [f"C{j+1}" for j in range(m)]
    vals_p    = [E.get(f"P{i}", "?") for i in range(n)]
    vals_c    = [E.get(f"C{j}", "?") for j in range(m)]

    dessiner_tableau("POTENTIELS FOURNISSEURS", ["E(Pi)"], entetes_p, [vals_p])
    dessiner_tableau("POTENTIELS CLIENTS",      ["E(Cj)"], entetes_c, [vals_c])

    # Tableau des coûts potentiels
    titre_section("TABLEAU DES COÛTS POTENTIELS   c*(i,j) = E(Pi) - E(Cj)", 2)
    info("Cases de base (B) : c*(i,j) = c(i,j)  par construction des potentiels.")
    print()

    entetes = [f"C{j+1}" for j in range(m)]
    etiq    = [f"P{i+1}" for i in range(n)]
    donnees = []
    for i in range(n):
        row = []
        for j in range(m):
            val = couts_pot[i][j]
            row.append(f"{val}(B)" if (i, j) in cases_base else str(val))
        donnees.append(row)
    dessiner_tableau("COÛTS POTENTIELS", etiq, entetes, donnees)


# ═════════════════════════════════════════════════════════════════════════════
#  4. TABLEAU DES COÛTS MARGINAUX  d(i,j) = c(i,j) - c*(i,j)
# ═════════════════════════════════════════════════════════════════════════════

def afficher_tableau_marginaux(d, cases_base, n, m):
    """
    Affiche le tableau des coûts marginaux.
    Retourne (min_val, case_pivot) ou (None, None) si optimal.
    """
    titre_section("TABLEAU DES COÛTS MARGINAUX   d(i,j) = c(i,j) - c*(i,j)", 2)
    info("Cases de base (B) : d = 0  (par définition des potentiels).")
    info("Valeur négative ← : amélioration possible sur cette case.")
    print()

    entetes = [f"C{j+1}" for j in range(m)]
    etiq    = [f"P{i+1}" for i in range(n)]
    donnees = []
    min_val, min_case = None, None

    for i in range(n):
        row = []
        for j in range(m):
            if (i, j) in cases_base:
                row.append("0(B)")
            else:
                v = d[(i, j)]
                row.append(f"{v} ←" if v < 0 else str(v))
                if v < 0 and (min_val is None or v < min_val):
                    min_val  = v
                    min_case = (i, j)
        donnees.append(row)

    dessiner_tableau("COÛTS MARGINAUX", etiq, entetes, donnees)

    if min_case is None:
        resultat("✔ Tous les coûts marginaux sont >= 0 → solution OPTIMALE")
    else:
        action(f"Coût marginal le plus négatif : "
               f"d( P{min_case[0]+1} , C{min_case[1]+1} ) = {min_val}")
        action(f"→ Case pivot choisie : ( P{min_case[0]+1} , C{min_case[1]+1} )")
    print()

    return min_val, min_case


# ═════════════════════════════════════════════════════════════════════════════
#  5. CYCLE DU MARCHE PIED
# ═════════════════════════════════════════════════════════════════════════════

def trouver_cycle(cases_base, i_piv, j_piv):
    """
    Trouve le cycle rectangle fermé créé par l'ajout de (i_piv, j_piv).
    BFS dans l'arbre de base entre P{i_piv} et C{j_piv}.
    Case pivot = (+Δ), alternance -/+ sur le chemin.
    Retourne [(i, j, signe), ...]  pivot en premier.
    Complexité : O(n+m)
    """
    adj = defaultdict(set)
    for (i, j) in cases_base:
        adj[f"P{i}"].add(f"C{j}")
        adj[f"C{j}"].add(f"P{i}")

    src = f"P{i_piv}"
    dst = f"C{j_piv}"

    parent = {src: None}
    queue  = deque([src])
    while queue:
        node = queue.popleft()
        if node == dst:
            break
        for voisin in adj[node]:
            if voisin not in parent:
                parent[voisin] = node
                queue.append(voisin)

    # Reconstituer chemin src → dst
    chemin, node = [], dst
    while node is not None:
        chemin.append(node)
        node = parent.get(node)
    chemin.reverse()

    # Construire les cases du cycle avec signes
    cases_cycle = [(i_piv, j_piv, '+')]
    for k in range(len(chemin) - 1):
        n1, n2 = chemin[k], chemin[k + 1]
        if n1.startswith('P'):
            i_c, j_c = int(n1[1:]), int(n2[1:])
        else:
            i_c, j_c = int(n2[1:]), int(n1[1:])
        signe = '-' if (k % 2 == 0) else '+'
        cases_cycle.append((i_c, j_c, signe))

    return cases_cycle


# ═════════════════════════════════════════════════════════════════════════════
#  6. MISE À JOUR DE LA PROPOSITION
# ═════════════════════════════════════════════════════════════════════════════

def mettre_a_jour(transport, cases_cycle, cases_base):
    """
    Δ = min des quantités sur les cases (-).
    +Δ sur les (+), -Δ sur les (-).
    Case (-) tombée à 0 → sort de la base.
    Case pivot → entre dans la base.
    Retourne (Δ, case_sortante).
    """
    cases_moins = [(i, j) for i, j, s in cases_cycle if s == '-']
    delta       = min(transport[i][j] for i, j in cases_moins)

    for i, j, s in cases_cycle:
        if s == '+':
            transport[i][j] += delta
        else:
            transport[i][j] -= delta

    case_sortante = next(
        (i, j) for i, j in cases_moins if transport[i][j] == 0)

    i_piv, j_piv, _ = cases_cycle[0]
    cases_base.discard(case_sortante)
    cases_base.add((i_piv, j_piv))

    return delta, case_sortante


# ═════════════════════════════════════════════════════════════════════════════
#  ALGORITHME PRINCIPAL
# ═════════════════════════════════════════════════════════════════════════════

def marche_pied(n, m, couts, transport_init, cases_visitees,
                provisions, commandes, algo=""):
    """
    Optimise transport_init par la méthode du marche pied avec potentiels.
    Les cases de base sont reconstruites depuis transport_init (valeur >= 0
    et case visitée = toute case non nulle OU case à 0 si fictive).
    """
    titre_section("MÉTHODE DU MARCHE PIED AVEC POTENTIELS", 1)
    info(f"Optimisation de la proposition initiale obtenue par : {algo}")
    print()
    info("Rappel de l'algorithme :")
    info("  1. Racine = sommet de degré max → E(racine) = 0")
    info("  2. Propagation BFS : E(Pi) - E(Cj) = c(i,j)")
    info("  3. Tableau des coûts potentiels  c*(i,j) = E(Pi) - E(Cj)")
    info("  4. Tableau des coûts marginaux   d(i,j)  = c(i,j) - c*(i,j)")
    info("  5. Si tous d >= 0 → OPTIMAL → coût total")
    info("     Sinon → case pivot (d le plus négatif) → cycle → Δ → mise à jour")
    print()

    # Copie de travail
    transport = [row[:] for row in transport_init]

    # cases_visitees transmis directement par NO ou BH (cases réelles + fictives)
    cases_base = set(cases_visitees)

    cout_initial = sum(couts[i][j] * transport[i][j]
                       for i in range(n) for j in range(m))

    # Affichage de la proposition de départ (dernière de NO/BH)
    titre_section(f"PROPOSITION FINALE DE {algo.upper()} — POINT DE DÉPART", 2)
    info("Tableau reproduit depuis la dernière itération de "
         f"{algo} (cases fictives incluses).")
    print()
    afficher_proposition(
        transport, provisions[:], commandes[:], n, m,
        titre=f"PROPOSITION INITIALE — {algo}",
        cases_visitees=cases_base)

    info(f"Coût de la proposition initiale ({algo}) = {cout_initial}")
    print()

    # Arbre de base avec coûts
    titre_section("ARBRE DE BASE (cases de base avec coûts)", 2)
    info("Arêtes de l'arbre (cases visitées, fictives incluses) :")
    for (i, j) in sorted(cases_base):
        fictive = " [fictive]" if transport[i][j] == 0 else ""
        info(f"   P{i+1} ↔ C{j+1}   "
             f"coût unitaire = {couts[i][j]}   "
             f"quantité = {transport[i][j]}{fictive}")
    print()

    iteration = 0

    while True:
        iteration += 1
        titre_section(f"ITÉRATION {iteration} — MARCHE PIED", 1)

        # ── 1. Racine ─────────────────────────────────────────────────────────
        racine = choisir_racine(cases_base)

        # ── 2. Potentiels ─────────────────────────────────────────────────────
        E = calculer_potentiels(couts, cases_base, racine)

        # ── 3. Coûts potentiels ───────────────────────────────────────────────
        couts_pot = [[E.get(f"P{i}", 0) - E.get(f"C{j}", 0)
                      for j in range(m)] for i in range(n)]
        afficher_tableau_potentiels(E, couts_pot, cases_base, n, m)

        # ── 4. Coûts marginaux ────────────────────────────────────────────────
        d = {}
        for i in range(n):
            for j in range(m):
                if (i, j) in cases_base:
                    d[(i, j)] = 0
                else:
                    d[(i, j)] = couts[i][j] - couts_pot[i][j]

        min_val, case_pivot = afficher_tableau_marginaux(d, cases_base, n, m)

        # ── 5. Critère d'optimalité ───────────────────────────────────────────
        if case_pivot is None:
            break

        # ── 6. Cycle ──────────────────────────────────────────────────────────
        titre_section("CYCLE DU MARCHE PIED", 2)
        i_piv, j_piv = case_pivot
        action(f"Case pivot : ( P{i_piv+1} , C{j_piv+1} )  reçoit (+Δ).")
        action("Construction du cycle rectangle en passant "
               "uniquement par les cases de base.")
        print()

        cases_cycle = trouver_cycle(cases_base, i_piv, j_piv)

        info("Cycle construit (alternance +Δ / -Δ) :")
        for i, j, s in cases_cycle:
            info(f"   ( P{i+1} , C{j+1} )  {s}Δ"
                 f"   quantité actuelle = {transport[i][j]}")
        print()

        # Tableau des signes du cycle
        titre_section("TABLEAU DES SIGNES DU CYCLE", 3)
        signe_map = {(i, j): s for i, j, s in cases_cycle}
        entetes_s = [f"C{j+1}" for j in range(m)]
        etiq_s    = [f"P{i+1}" for i in range(n)]
        donnees_s = []
        for i in range(n):
            row = []
            for j in range(m):
                if (i, j) in signe_map:
                    row.append(f"{signe_map[(i,j)]}Δ")
                elif (i, j) in cases_base:
                    row.append("(base)")
                else:
                    row.append("")
            donnees_s.append(row)
        dessiner_tableau("SIGNES DU CYCLE", etiq_s, entetes_s, donnees_s)

        # Δ
        cases_moins = [(i, j) for i, j, s in cases_cycle if s == '-']
        delta       = min(transport[i][j] for i, j in cases_moins)
        action("Δ = min des quantités sur les cases (−) :")
        for i, j in cases_moins:
            action(f"   quantité( P{i+1} , C{j+1} ) = {transport[i][j]}")
        action(f"→ Δ = {delta}")
        print()

        # ── 7. Mise à jour ────────────────────────────────────────────────────
        titre_section("MISE À JOUR DE LA PROPOSITION", 2)
        action(f"On ajoute Δ={delta} aux cases (+Δ) "
               f"et on retire Δ={delta} des cases (−Δ).")
        print()

        info("Détail des modifications :")
        for i, j, s in cases_cycle:
            avant = transport[i][j]
            apres = avant + delta if s == '+' else avant - delta
            info(f"   ( P{i+1} , C{j+1} )  {s}Δ :  "
                 f"{avant} {'+' if s == '+' else '-'} {delta} = {apres}")
        print()

        delta_val, case_sortante = mettre_a_jour(
            transport, cases_cycle, cases_base)

        action(f"Case entrante : ( P{i_piv+1} , C{j_piv+1} ) "
               f"→ entre dans la base.")
        action(f"Case sortante : ( P{case_sortante[0]+1} , "
               f"C{case_sortante[1]+1} ) → tombe à 0, sort de la base.")
        print()

        afficher_proposition(
            transport, provisions[:], commandes[:], n, m,
            titre=f"PROPOSITION APRÈS ITÉRATION {iteration}",
            cases_visitees=cases_base)

        cout_iter = sum(couts[i][j] * transport[i][j]
                        for i in range(n) for j in range(m))
        info(f"Coût après itération {iteration} : {cout_iter}")
        info("→ Recalcul complet depuis les potentiels.")
        print()

    # ── Résultat final ────────────────────────────────────────────────────────
    cout_total = afficher_cout_total(
        transport, couts, n, m, algo="Marche Pied")
    afficher_recapitulatif(
        transport, couts, provisions, commandes,
        n, m, cout_total, algo="Marche Pied")

    return transport, cout_total


# ═════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE PUBLIC  —  signature exacte de main.py
# ═════════════════════════════════════════════════════════════════════════════

def run(n, m, couts, transport, cases_visitees, provisions, commandes, algo=""):
    """
    Appelé depuis main.py :
        transport_opt, cout_opt = algo_mp.run(
            n, m, couts, transport, cases_visitees,
            provisions, commandes, algo=nom_algo)
    """
    return marche_pied(n, m, couts, transport, cases_visitees,
                       provisions, commandes, algo)
