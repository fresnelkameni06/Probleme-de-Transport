═══════════════════════════════════════════════════════════════
  PROGRAMME DE TRANSPORT — GUIDE D'UTILISATION
═══════════════════════════════════════════════════════════════

STRUCTURE DES FICHIERS
──────────────────────
  Project_RO/
  ├── main.py           ← Point d'entrée  (lancer celui-ci)
  ├── affichage.py      ← Affichage des tableaux (Unicode)
  ├── lecture.py        ← Lecture des fichiers .txt
  ├── nord_ouest.py     ← Algorithme Nord-Ouest
  ├── balas_hammer.py   ← Algorithme Balas-Hammer
  ├── README.txt        ← Ce fichier
  └── tableaux/         ← Dossier de vos fichiers problèmes
      ├── probleme1.txt
      ├── probleme2.txt
      ├── ...
      └── probleme12.txt

MISE EN PLACE
─────────────
  1. Créez un dossier "tableaux/" dans le même dossier que main.py
  2. Placez-y vos 12 fichiers :  probleme1.txt, probleme2.txt, ..., probleme12.txt
  3. Lancez le programme : python main.py

FORMAT DES FICHIERS .TXT
─────────────────────────
  Ligne 1      : n  m          (nombre de fournisseurs, nombre de clients)
  Lignes 2..n+1: a_{i,1} a_{i,2} ... a_{i,m}  P_i   (coûts + provision)
  Ligne n+2    : C_1  C_2  ...  C_m             (commandes)

  Exemple (4 fournisseurs, 3 clients) :
      4 3
      30 20 20 450
      10 50 20 250
      50 40 30 250
      30 20 30 450
      500 600 300

UTILISATION
───────────
  1. Lancer :  python main.py
  2. Choisir le numéro du problème à traiter  (1 à 12)
  3. Choisir l'algorithme :
        [1] Nord-Ouest
        [2] Balas-Hammer
  4. La trace complète s'affiche dans le terminal
  5. À la fin, choisir de traiter un autre problème ou quitter

ALGORITHMES DISPONIBLES
────────────────────────
  Nord-Ouest   : méthode du coin Nord-Ouest (remplissage diagonal)
  Balas-Hammer : méthode des pénalités de Vogel (choix optimal)
═══════════════════════════════════════════════════════════════
