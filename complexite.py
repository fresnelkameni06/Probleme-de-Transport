"""
=============================================================================
  MODULE : complexite.py
  Rôle   : Analyse expérimentale de la complexité dans le pire des cas
           des algorithmes de transport : Nord-Ouest, Balas-Hammer,
           Marche-Pied (sur NO) et Marche-Pied (sur BH).

  Méthodologie (conforme au cahier des charges) :
    - Problèmes carrés n×n  (n = m)
    - Coûts c(i,j) : entiers aléatoires dans [1, 100]
    - Provisions Pi et commandes Cj générées via une matrice auxiliaire
      temp(i,j) ∈ [1, 100]  :  Pi = Σj temp(i,j),  Cj = Σi temp(i,j)
      → garantit Σ Pi = Σ Cj  (problème équilibré)
    - 100 instances indépendantes par valeur de n
    - Exécution séquentielle (jamais parallèle)
    - Mesure avec time.perf_counter()  (résolution sub-microseconde)
    - Résultats stockés, nuages de points + enveloppe max tracés
    - Comparaison aux classes O(n), O(n log n), O(n²), O(n³)

  Sorties :
    - Console     : tableau récapitulatif des max par n
    - Fichier CSV : complexite_resultats.csv
    - Graphiques  : 6 figures PNG sauvegardées dans ./complexite_plots/
=============================================================================
"""

import random
import time
import os
import csv
import math

# ── Import des algorithmes (suppression de toute sortie console/trace) ───────
# On redirige stdout/stderr pendant l'exécution des algos pour ne mesurer
# que le CPU pur, sans I/O.
import io
import sys

# Chemins relatifs
_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)

import nord_ouest   as algo_no
import balas_hammer as algo_bh
import marche_pied  as algo_mp

DOSSIER_PLOTS = os.path.join(_DIR, "complexite_plots")
FICHIER_CSV   = os.path.join(_DIR, "complexite_resultats.csv")

# Valeurs de n à tester (conformes au cahier des charges)
VALEURS_N = [10, 40, 100, 400, 1000, 4000, 10000]

# Nombre de répétitions par valeur de n
NB_REPETITIONS = 100


# ═════════════════════════════════════════════════════════════════════════════
#  GÉNÉRATION D'UN PROBLÈME ALÉATOIRE ÉQUILIBRÉ  n×n
# ═════════════════════════════════════════════════════════════════════════════

def generer_probleme(n):
    """
    Génère un problème de transport carré n×n aléatoire équilibré.

    Méthode (conforme au cahier des charges) :
      1. c(i,j) ∈ [1, 100]  aléatoire entier
      2. temp(i,j) ∈ [1, 100] aléatoire entier (matrice auxiliaire)
      3. Pi = Σj temp(i,j)     (provision du fournisseur i)
      4. Cj = Σi temp(i,j)     (commande du client j)
      → Σ Pi = Σ Cj = Σ_{i,j} temp(i,j)  ✔

    Retourne : (n, n, couts, provisions, commandes)
    """
    couts      = [[random.randint(1, 100) for _ in range(n)] for _ in range(n)]
    temp       = [[random.randint(1, 100) for _ in range(n)] for _ in range(n)]
    provisions = [sum(temp[i][j] for j in range(n)) for i in range(n)]
    commandes  = [sum(temp[i][j] for i in range(n)) for j in range(n)]
    return n, n, couts, provisions, commandes


# ═════════════════════════════════════════════════════════════════════════════
#  EXÉCUTION SILENCIEUSE  (supprime toute sortie console pendant la mesure)
# ═════════════════════════════════════════════════════════════════════════════

class _SuppressOutput:
    """
    Redirige stdout, stderr ET stdin pendant le bloc with.
    Suspend aussi l'écriture dans le fichier trace d'affichage.py.
    - stdout/stderr → StringIO  (supprime tout affichage)
    - stdin         → StringIO vide  (empêche input()/pause() de bloquer)
    - affichage._trace_file → None  (suspend l'écriture dans le fichier trace)
    """
    def __enter__(self):
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        self._stdin  = sys.stdin
        sys.stdout   = io.StringIO()
        sys.stderr   = io.StringIO()
        sys.stdin    = io.StringIO()   # input() lira "" → EOFError → ignoré

        # Suspendre le fichier trace d'affichage.py
        try:
            import affichage as _aff
            self._trace_file      = _aff._trace_file
            self._pagination_save = _aff._pagination
            _aff._trace_file      = None   # suspend l'écriture
            _aff._pagination      = False  # désactive la pagination
            self._aff             = _aff
        except Exception:
            self._aff = None
        return self

    def __exit__(self, *args):
        sys.stdout = self._stdout
        sys.stderr = self._stderr
        sys.stdin  = self._stdin

        # Restaurer le fichier trace et la pagination
        if self._aff is not None:
            self._aff._trace_file = self._trace_file
            self._aff._pagination = self._pagination_save


def mesurer(fn, *args, **kwargs):
    """
    Exécute fn(*args, **kwargs) en silence et retourne (résultat, durée_s).
    Utilise time.perf_counter() pour une résolution maximale.
    """
    with _SuppressOutput():
        t0     = time.perf_counter()
        result = fn(*args, **kwargs)
        t1     = time.perf_counter()
    return result, t1 - t0


# ═════════════════════════════════════════════════════════════════════════════
#  BOUCLE PRINCIPALE D'EXPÉRIMENTATION
# ═════════════════════════════════════════════════════════════════════════════

def executer_experience(valeurs_n=None, nb_repetitions=None):
    """
    Pour chaque n dans valeurs_n, génère nb_repetitions instances et mesure :
      - θ_NO(n)  : temps Nord-Ouest seul
      - θ_BH(n)  : temps Balas-Hammer seul
      - t_NO(n)  : temps Marche-Pied (proposition NO)
      - t_BH(n)  : temps Marche-Pied (proposition BH)

    Retourne un dict :
      {
        n: {
          'theta_NO': [t1, t2, ...],   # 100 mesures
          'theta_BH': [t1, t2, ...],
          't_NO':     [t1, t2, ...],
          't_BH':     [t1, t2, ...],
        },
        ...
      }
    """
    if valeurs_n      is None: valeurs_n      = VALEURS_N
    if nb_repetitions is None: nb_repetitions = NB_REPETITIONS

    resultats = {}

    for n in valeurs_n:
        print(f"\n  [n = {n:>6}]  {nb_repetitions} répétitions en cours...")
        theta_NO_list = []
        theta_BH_list = []
        t_NO_list     = []
        t_BH_list     = []

        for rep in range(nb_repetitions):
            # Affichage de progression toutes les 10 itérations
            if (rep + 1) % 10 == 0:
                print(f"             répétition {rep+1:3d}/{nb_repetitions}", end="\r")

            # ── Génération d'une instance ─────────────────────────────────
            n_, m_, couts, provisions, commandes = generer_probleme(n)

            # ── 1. Nord-Ouest seul ────────────────────────────────────────
            (transport_no, _, cases_no), theta_NO = mesurer(
                algo_no.run, n_, m_, couts, provisions, commandes)
            theta_NO_list.append(theta_NO)

            # ── 2. Balas-Hammer seul ──────────────────────────────────────
            (transport_bh, _, cases_bh), theta_BH = mesurer(
                algo_bh.run, n_, m_, couts, provisions, commandes)
            theta_BH_list.append(theta_BH)

            # ── 3. Marche-Pied sur NO ─────────────────────────────────────
            _, t_NO = mesurer(
                algo_mp.run,
                n_, m_, couts, transport_no, cases_no,
                provisions, commandes, algo="Nord-Ouest")
            t_NO_list.append(t_NO)

            # ── 4. Marche-Pied sur BH ─────────────────────────────────────
            _, t_BH = mesurer(
                algo_mp.run,
                n_, m_, couts, transport_bh, cases_bh,
                provisions, commandes, algo="Balas-Hammer")
            t_BH_list.append(t_BH)

        resultats[n] = {
            'theta_NO': theta_NO_list,
            'theta_BH': theta_BH_list,
            't_NO':     t_NO_list,
            't_BH':     t_BH_list,
        }
        print(f"             [OK] n={n}  "
              f"max θ_NO={max(theta_NO_list):.4f}s  "
              f"max θ_BH={max(theta_BH_list):.4f}s  "
              f"max t_NO={max(t_NO_list):.4f}s  "
              f"max t_BH={max(t_BH_list):.4f}s     ")

    return resultats


# ═════════════════════════════════════════════════════════════════════════════
#  SAUVEGARDE CSV
# ═════════════════════════════════════════════════════════════════════════════

def sauvegarder_csv(resultats, chemin=None):
    """
    Sauvegarde toutes les mesures dans un fichier CSV.
    Colonnes : n, repetition, theta_NO, theta_BH, t_NO, t_BH,
               total_NO (theta_NO + t_NO), total_BH (theta_BH + t_BH)
    """
    if chemin is None:
        chemin = FICHIER_CSV

    with open(chemin, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['n', 'repetition',
                         'theta_NO', 'theta_BH',
                         't_NO', 't_BH',
                         'total_NO', 'total_BH'])
        for n, data in sorted(resultats.items()):
            for rep in range(len(data['theta_NO'])):
                tno  = data['theta_NO'][rep]
                tbh  = data['theta_BH'][rep]
                mno  = data['t_NO'][rep]
                mbh  = data['t_BH'][rep]
                writer.writerow([n, rep + 1,
                                 f"{tno:.8f}", f"{tbh:.8f}",
                                 f"{mno:.8f}", f"{mbh:.8f}",
                                 f"{tno+mno:.8f}", f"{tbh+mbh:.8f}"])

    print(f"\n  [CSV] Résultats sauvegardés dans : {chemin}")


# ═════════════════════════════════════════════════════════════════════════════
#  TABLEAU RÉCAPITULATIF (console)
# ═════════════════════════════════════════════════════════════════════════════

def afficher_tableau_recap(resultats):
    """Affiche un tableau des valeurs max par n et par algorithme."""
    print()
    print("  " + "═" * 82)
    print(f"  {'n':>8}  │  {'max θ_NO':>12}  │  {'max θ_BH':>12}  │  "
          f"{'max t_NO':>12}  │  {'max t_BH':>12}")
    print("  " + "─" * 82)
    for n, data in sorted(resultats.items()):
        mno = max(data['theta_NO'])
        mbh = max(data['theta_BH'])
        tno = max(data['t_NO'])
        tbh = max(data['t_BH'])
        print(f"  {n:>8}  │  {mno:>12.6f}  │  {mbh:>12.6f}  │  "
              f"{tno:>12.6f}  │  {tbh:>12.6f}")
    print("  " + "═" * 82)
    print()


# ═════════════════════════════════════════════════════════════════════════════
#  VISUALISATION  (matplotlib)
# ═════════════════════════════════════════════════════════════════════════════

def tracer_graphiques(resultats, dossier=None):
    """
    Trace les 6 figures demandées :
      1. Nuage θ_NO(n)
      2. Nuage θ_BH(n)
      3. Nuage t_NO(n)
      4. Nuage t_BH(n)
      5. Nuage (θ_NO + t_NO)(n)
      6. Nuage (θ_BH + t_BH)(n)
    Pour chaque figure :
      - Nuage de points (100 valeurs par n, en bleu clair)
      - Enveloppe max (en rouge, trait épais)
      - Courbes de référence O(n), O(n log n), O(n²), O(n³) (pointillés)
    """
    try:
        import matplotlib
        matplotlib.use('Agg')   # backend non-interactif pour sauvegarde
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("\n  [AVERT] matplotlib non disponible — graphiques ignorés.")
        print("          Installez-le avec : pip install matplotlib --break-system-packages")
        return

    if dossier is None:
        dossier = DOSSIER_PLOTS
    os.makedirs(dossier, exist_ok=True)

    ns_sorted = sorted(resultats.keys())

    # ── Données brutes et enveloppes max ─────────────────────────────────────
    def extraire(cle):
        """Retourne (xs, ys_tous, ys_max)."""
        xs, ys_tous, ys_max = [], [], []
        for n in ns_sorted:
            vals = resultats[n][cle]
            for v in vals:
                xs.append(n)
                ys_tous.append(v)
            ys_max.append(max(vals))
        return xs, ys_tous, ys_max

    def extraire_somme(cle1, cle2):
        xs, ys_tous, ys_max = [], [], []
        for n in ns_sorted:
            vals = [a + b for a, b in zip(resultats[n][cle1],
                                           resultats[n][cle2])]
            for v in vals:
                xs.append(n)
                ys_tous.append(v)
            ys_max.append(max(vals))
        return xs, ys_tous, ys_max

    # ── Courbes de référence normalisées ──────────────────────────────────────
    def courbes_ref(ax, ns, ys_max):
        """Ajoute O(n), O(n log n), O(n²), O(n³) normalisées sur le max."""
        ns_arr  = np.array(ns, dtype=float)
        ref_val = max(ys_max) if max(ys_max) > 0 else 1.0
        n_ref   = ns_arr[-1]

        styles = [
            ('O(n)',        lambda x: x / n_ref,                    'green',  '--'),
            ('O(n log n)',  lambda x: x * np.log(x) / (n_ref * math.log(n_ref)), 'orange', '-.'),
            ('O(n²)',       lambda x: (x / n_ref) ** 2,             'purple', ':'),
            ('O(n³)',       lambda x: (x / n_ref) ** 3,             'brown',  (0, (3, 5, 1, 5))),
        ]
        for label, fn, color, ls in styles:
            ys_ref = fn(ns_arr) * ref_val
            ax.plot(ns_arr, ys_ref, color=color, linestyle=ls,
                    linewidth=1.2, alpha=0.7, label=label)

    # ── Fonction de tracé ─────────────────────────────────────────────────────
    def tracer_une(xs, ys_tous, ys_max, titre, ylabel, nom_fichier):
        fig, ax = plt.subplots(figsize=(10, 6))

        # Nuage de points
        ax.scatter(xs, ys_tous, color='steelblue', alpha=0.25,
                   s=8, label='Mesures (100/n)', zorder=2)

        # Enveloppe max
        ax.plot(ns_sorted, ys_max, color='red', linewidth=2.5,
                marker='o', markersize=5, label='Max (pire des cas)', zorder=3)

        # Courbes de référence
        courbes_ref(ax, ns_sorted, ys_max)

        ax.set_xlabel('Taille n', fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_title(titre, fontsize=13, fontweight='bold')
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.legend(fontsize=9, loc='upper left')
        ax.grid(True, which='both', linestyle='--', alpha=0.4)

        chemin_fig = os.path.join(dossier, nom_fichier)
        fig.tight_layout()
        fig.savefig(chemin_fig, dpi=150)
        plt.close(fig)
        print(f"  [FIG] {chemin_fig}")

    # ── 6 figures ─────────────────────────────────────────────────────────────
    specs = [
        (extraire('theta_NO'),
         "θ_NO(n) — Nord-Ouest seul",
         "Temps (s)", "fig1_theta_NO.png"),

        (extraire('theta_BH'),
         "θ_BH(n) — Balas-Hammer seul",
         "Temps (s)", "fig2_theta_BH.png"),

        (extraire('t_NO'),
         "t_NO(n) — Marche-Pied sur Nord-Ouest",
         "Temps (s)", "fig3_t_NO.png"),

        (extraire('t_BH'),
         "t_BH(n) — Marche-Pied sur Balas-Hammer",
         "Temps (s)", "fig4_t_BH.png"),

        (extraire_somme('theta_NO', 't_NO'),
         "(θ_NO + t_NO)(n) — Pipeline complet Nord-Ouest",
         "Temps total (s)", "fig5_total_NO.png"),

        (extraire_somme('theta_BH', 't_BH'),
         "(θ_BH + t_BH)(n) — Pipeline complet Balas-Hammer",
         "Temps total (s)", "fig6_total_BH.png"),
    ]

    print(f"\n  Génération des graphiques dans : {dossier}")
    for (xs, ys_tous, ys_max), titre, ylabel, nom in specs:
        tracer_une(xs, ys_tous, ys_max, titre, ylabel, nom)

    # ── Figure 7 : comparaison des ratios (section 3.3.5) ────────────────────
    try:
        import numpy as np
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 6))
        ratio_max = []
        for n in ns_sorted:
            total_no = [a + b for a, b in zip(resultats[n]['theta_NO'],
                                               resultats[n]['t_NO'])]
            total_bh = [a + b for a, b in zip(resultats[n]['theta_BH'],
                                               resultats[n]['t_BH'])]
            r = max(total_no) / max(total_bh) if max(total_bh) > 0 else 0
            ratio_max.append(r)

        ax.plot(ns_sorted, ratio_max, color='darkblue', linewidth=2.5,
                marker='s', markersize=6, label='max(θ_NO + t_NO) / max(θ_BH + t_BH)')
        ax.axhline(y=1.0, color='red', linestyle='--', linewidth=1.2,
                   label='Ratio = 1 (équivalence)')
        ax.set_xlabel('Taille n', fontsize=12)
        ax.set_ylabel('Ratio des pires cas', fontsize=12)
        ax.set_title('Comparaison des pipelines : NO vs BH (pire des cas)',
                     fontsize=13, fontweight='bold')
        ax.set_xscale('log')
        ax.legend(fontsize=10)
        ax.grid(True, which='both', linestyle='--', alpha=0.4)
        fig.tight_layout()
        chemin_ratio = os.path.join(dossier, "fig7_ratio_NO_vs_BH.png")
        fig.savefig(chemin_ratio, dpi=150)
        plt.close(fig)
        print(f"  [FIG] {chemin_ratio}")
    except Exception as e:
        print(f"  [AVERT] Figure ratio ignorée : {e}")


# ═════════════════════════════════════════════════════════════════════════════
#  IDENTIFICATION DE LA CLASSE DE COMPLEXITÉ
# ═════════════════════════════════════════════════════════════════════════════

def identifier_complexite(ns, ys_max):
    """
    Tente d'identifier la classe de complexité des valeurs max
    en calculant le R² d'un ajustement log-log pour chaque modèle.
    Retourne le nom du meilleur modèle.
    """
    try:
        import numpy as np

        log_ns  = np.log(np.array(ns, dtype=float))
        log_ys  = np.log(np.array(ys_max, dtype=float))

        def r2_linreg(x, y):
            A = np.vstack([x, np.ones(len(x))]).T
            m, c = np.linalg.lstsq(A, y, rcond=None)[0]
            y_pred = m * x + c
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            return 1 - ss_res / ss_tot if ss_tot > 0 else 0, m

        # Modèle log-log → pente ≈ k  (O(n^k))
        r2, pente = r2_linreg(log_ns, log_ys)

        if r2 < 0.7:
            return f"Indéterminé (R²={r2:.2f})"
        elif pente < 0.3:
            return f"O(log n)       (pente≈{pente:.2f}, R²={r2:.2f})"
        elif pente < 1.3:
            return f"O(n)           (pente≈{pente:.2f}, R²={r2:.2f})"
        elif pente < 1.7:
            return f"O(n·log n)     (pente≈{pente:.2f}, R²={r2:.2f})"
        elif pente < 2.3:
            return f"O(n²)          (pente≈{pente:.2f}, R²={r2:.2f})"
        elif pente < 3.3:
            return f"O(n³)          (pente≈{pente:.2f}, R²={r2:.2f})"
        else:
            return f"O(n^{pente:.1f}) polynomial (R²={r2:.2f})"
    except Exception:
        return "Identification impossible"


def afficher_complexites(resultats):
    """Affiche l'identification de complexité pour chaque algorithme."""
    ns = sorted(resultats.keys())

    series = {
        'θ_NO  (Nord-Ouest)':            [max(resultats[n]['theta_NO']) for n in ns],
        'θ_BH  (Balas-Hammer)':          [max(resultats[n]['theta_BH']) for n in ns],
        't_NO  (Marche-Pied sur NO)':    [max(resultats[n]['t_NO'])     for n in ns],
        't_BH  (Marche-Pied sur BH)':    [max(resultats[n]['t_BH'])     for n in ns],
        'θ_NO+t_NO (Pipeline NO)': [max(resultats[n]['theta_NO']) +
                                    max(resultats[n]['t_NO'])     for n in ns],
        'θ_BH+t_BH (Pipeline BH)': [max(resultats[n]['theta_BH']) +
                                    max(resultats[n]['t_BH'])     for n in ns],
    }

    print()
    print("  " + "═" * 70)
    print("  IDENTIFICATION DE LA COMPLEXITÉ DANS LE PIRE DES CAS")
    print("  (ajustement log-log sur l'enveloppe maximale)")
    print("  " + "─" * 70)
    for nom, vals in series.items():
        classe = identifier_complexite(ns, vals)
        print(f"  {nom:<30}  →  {classe}")
    print("  " + "═" * 70)
    print()


# ═════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ═════════════════════════════════════════════════════════════════════════════

def main(valeurs_n=None, nb_repetitions=None, avec_graphiques=True):
    """
    Lance l'étude complète de complexité.

    Paramètres :
        valeurs_n        : liste des valeurs de n à tester
                           (défaut : [10, 40, 100, 400, 1000, 4000, 10000])
        nb_repetitions   : nombre d'instances par n  (défaut : 100)
        avec_graphiques  : True pour générer les figures matplotlib
    """
    if valeurs_n      is None: valeurs_n      = VALEURS_N
    if nb_repetitions is None: nb_repetitions = NB_REPETITIONS

    print()
    print("  ╔══════════════════════════════════════════════════════════════╗")
    print("  ║      ANALYSE DE COMPLEXITÉ — ALGORITHMES DE TRANSPORT        ║")
    print("  ║   Nord-Ouest  |  Balas-Hammer  |  Marche-Pied (NO + BH)     ║")
    print("  ╚══════════════════════════════════════════════════════════════╝")
    print()
    print(f"  Valeurs de n testées     : {valeurs_n}")
    print(f"  Répétitions par n        : {nb_repetitions}")
    print(f"  Total d'instances        : {len(valeurs_n) * nb_repetitions}")
    print(f"  Algorithmes mesurés      : θ_NO, θ_BH, t_NO, t_BH")
    print()
    print("  ATTENTION : ne pas utiliser la machine pendant l'exécution.")
    print("              Les mesures doivent être faites sans perturbation.")
    print()

    # ── Expérimentation ───────────────────────────────────────────────────────
    resultats = executer_experience(valeurs_n, nb_repetitions)

    # ── Tableau récapitulatif ─────────────────────────────────────────────────
    print()
    print("  TABLEAU DES VALEURS MAXIMALES (pire des cas par n) :")
    afficher_tableau_recap(resultats)

    # ── Identification de complexité ──────────────────────────────────────────
    afficher_complexites(resultats)

    # ── Sauvegarde CSV ────────────────────────────────────────────────────────
    sauvegarder_csv(resultats)

    # ── Graphiques ────────────────────────────────────────────────────────────
    if avec_graphiques:
        tracer_graphiques(resultats)

    print()
    print("  [FIN]  Analyse de complexité terminée.")
    print()

    return resultats


if __name__ == "__main__":
    # ── Paramètres rapides pour test (modifier selon besoin) ──────────────────
    # Pour un test rapide, réduire les valeurs de n et/ou nb_repetitions :
    #   main(valeurs_n=[10, 40, 100], nb_repetitions=10)
    # Pour l'étude complète :
    #   main()

    import argparse
    parser = argparse.ArgumentParser(
        description="Analyse de complexité des algorithmes de transport")
    parser.add_argument('--n',    nargs='+', type=int,
                        default=VALEURS_N,
                        help="Valeurs de n à tester")
    parser.add_argument('--rep',  type=int,
                        default=NB_REPETITIONS,
                        help="Nombre de répétitions par n")
    parser.add_argument('--no-graphs', action='store_true',
                        help="Désactiver la génération des graphiques")
    args = parser.parse_args()

    main(valeurs_n      = args.n,
         nb_repetitions = args.rep,
         avec_graphiques = not args.no_graphs)