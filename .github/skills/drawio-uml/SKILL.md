---
name: drawio-uml
description: "Use when: generation ou correction de diagrammes UML draw.io (classes, activites), regles anti-chevauchement, XML importable sans correction manuelle."
---

# Skill Drawio UML

## Objectif
Produire des diagrammes UML draw.io importables, lisibles et sans chevauchement visuel.

## Regle absolue
- Interdiction des commentaires XML dans les fichiers .drawio livres.
- Interdiction des doubles tirets dans le XML livre.
- Le fichier final doit etre importable dans draw.io sans correction manuelle.

## Structure .drawio minimale
- mxGraphModel complet avec root, cellule id 0 et cellule id 1 parent 0.
- IDs uniques sur tous les elements.
- Enfants d'une classe swimlane : parent = id de la classe.
- Toute relation : mxCell avec edge=1.

## Standard UML classes — 3 compartiments
- Titre : swimlane startSize=35, nom centre, fontStyle=1.
- Attributs : texte aligne gauche, spacingLeft coherent.
- Methodes : texte aligne gauche, signatures explicites.
- Separateur visuel obligatoire entre attributs et methodes.

## Palette UML

Note : les palettes UML et MERISE sont intentionnellement distinctes.
UML modele la structure logicielle (classes, services, composants) ; MERISE modele les donnees metier (entites, associations, flux).
Un element "Entite principale" n'a pas le meme sens dans les deux contextes ; les couleurs differentes signalent ce changement de domaine semantique.
Ne pas tenter d'aligner les deux palettes : la distinction visuelle est un signal delibere pour le lecteur.

| Type | fillColor | strokeColor |
|---|---|---|
| Entite principale | #fff2cc | #d6b656 |
| Service | #e1d5e7 | #9673a6 |
| Entite de donnees | #dae8fc | #6c8ebf |
| DTO | #ffe6cc | #d79b00 |
| Domaine metier | #d5e8d4 | #82b366 |
| Securite | #f8cecc | #b85450 |
| Enumeration | #f5f5f5 | #555555 |

## Relations UML
- Association simple : trait plein, sans fleche.
- Dependance : trait pointille, fleche ouverte, label use.
- Cardinalites visibles et non connectables sur relations critiques.
- Routage manuel par points intermediaires si chevauchement.

## Standard UML activites
- Pool et swimlanes par acteur.
- Noeud initial : cercle plein. Action : rectangle arrondi. Decision : losange. Fork/Join : barre epaisse. Noeud final : double cercle.
- Transitions fleche bloc, gardes explicites.

## Regles de mise en page — Anti-chevauchement (bloquantes)

Ces regles s'appliquent a tous les types UML (classes, activites, sequences, cas d'usage, composants). Leur non-respect produit des elements visuellement fusionnes, des fleches qui traversent des classes ou des labels illisibles.

R1 — Espacement vertical minimum entre classes : 80px
Ne jamais placer deux classes dont les bords se touchent verticalement.
Formule obligatoire : `Y_suivant = Y_precedent + hauteur_precedente + 80`
Valeur minimale du gap : 80px. Applicable entre toute paire de classes sur le meme axe vertical.

R2 — Hauteur de classe calculee avant placement de la classe suivante
Ne jamais fixer la position d'une classe suivante avant d'avoir calcule la hauteur reelle de la classe precedente.
Formule de calcul de hauteur — diagramme de classes :
`hauteur_classe = startSize(35) + hauteur_compartiment_attributs + 8(separateur) + hauteur_compartiment_methodes + 16`
`hauteur_compartiment_attributs = nombre_attributs x 20 + 12`
`hauteur_compartiment_methodes = nombre_methodes x 20 + 12`
Ce calcul est obligatoire avant chaque positionnement vertical.

R3 — Largeur uniforme par colonne de diagramme
Toutes les classes d'une meme colonne verticale ont la meme largeur.
Largeurs standard par type :
- Classe simple (< 5 attributs, < 5 methodes) : 220px
- Classe moyenne (5-10 attributs ou methodes) : 260px
- Classe large (> 10 attributs ou methodes, ou signatures longues) : 300px
- Enumeration : 180px
Interdiction de mixer des largeurs differentes dans une meme colonne.

R4 — Espacement horizontal minimum entre colonnes : 120px
Le gap horizontal entre deux colonnes de classes est de 120px minimum.
Ce gap garantit que les fleches de relation, les labels de cardinalite et les labels de role ne se superposent pas aux classes adjacentes.
Formule : `X_colonne_suivante = X_colonne_courante + largeur_colonne + 120`
Pour les relations bidirectionnelles denses, augmenter ce gap a 160px.

R5 — Les relations sont tracees apres placement de toutes les classes
Ordre de generation obligatoire :
1. Placer toutes les classes et calculer leurs hauteurs reelles.
2. Verifier qu'aucune classe ne chevauche une autre (R6).
3. Tracer les relations (associations, heritages, dependances, realisations).
4. Ajouter les labels de cardinalite et de role en dernier.
Interdiction de tracer une relation vers une classe dont la hauteur finale n'est pas encore calculee.

R6 — Les fleches ne doivent jamais traverser une classe tierce
Avant de valider le trace d'une fleche, verifier que son chemin (source -> target) ne passe pas a l'interieur du rectangle d'une classe non concernee par la relation.
Si c'est le cas : utiliser le routage manuel par points intermediaires pour contourner la classe.
Formule de detour : ajouter un `mxPoint` a gauche ou a droite de la classe obstacle, avec un offset minimum de 30px par rapport au bord de la classe.
Exemple : `<mxPoint x="X_bord_classe - 30" y="Y_milieu_classe" />`

R7 — Verification anti-chevauchement obligatoire avant livraison
Avant de produire le fichier final, verifier pour chaque paire d'elements :
- Vertical : `Y_element_A + hauteur_A + 80 <= Y_element_B` (si B est sous A)
- Horizontal : `X_element_A + largeur_A + 120 <= X_element_B` (si B est a droite de A)
- Fleches : aucune fleche ne passe dans le rectangle d'une classe tierce.
Si une verification echoue : repositionner et recalculer avant de livrer.
Cette verification est bloquante : un fichier avec chevauchement ne peut pas etre livre.

R8 — Labels de cardinalite positionnes hors des rectangles de classe
Les labels `edgeLabel` de cardinalite et de role doivent etre positionnes de facon a ne jamais se superposer au contenu d'une classe.
Positionnement recommande : `x="-0.8"` cote source, `x="0.8"` cote target, `y="1"` pour descendre le label sous la ligne de relation.
Si le label chevauche une classe : ajuster `y` entre -1 et 1 pour le deplacer au-dessus ou en dessous de la relation.

## Erreurs de mise en page interdites

| Erreur | Consequence | Solution |
|---|---|---|
| Hauteur classe fixee avant calcul du contenu | Chevauchement si attributs ou methodes nombreux | Calculer hauteur complete avant tout positionnement suivant |
| Gap vertical < 80px entre classes | Classes visuellement fusionnees | Imposer 80px entre `Y_fin` d'une classe et `Y_debut` de la suivante |
| Gap horizontal < 120px entre colonnes | Relations et labels illisibles | 120px minimum entre colonnes, 160px si relations denses |
| Fleche traversant une classe tierce | Relation attribuee visuellement a une mauvaise classe | Routage manuel avec mxPoint de contournement, offset 30px |
| Relations tracees avant toutes les classes | Position incorrecte si une classe grandit | Placer toutes les classes, valider, puis tracer les relations |
| Largeurs differentes dans une meme colonne | Desalignement visuel, diagramme irregulier | Une seule largeur par colonne definie avant generation |
| Labels de cardinalite sur les classes | Confusion entre attribut et cardinalite | Positionner edgeLabel avec x=-0.8/0.8, ajuster y si superposition |
| Pas de verification anti-chevauchement | Livraison avec elements superposes ou fleches parasites | Checklist R7 obligatoire avant tout fichier final |

## Checklist UML (bloquante)
- [ ] Pas de commentaires XML.
- [ ] Pas de doubles tirets.
- [ ] IDs uniques.
- [ ] Parent/source/target coherents.
- [ ] Cardinalites presentes sur relations critiques.
- [ ] Regles R1 a R8 verifiees : aucun chevauchement, aucune fleche parasite, labels hors des classes.
- [ ] Index doc/DIAGRAMMES/README.md mis a jour.
- [ ] Intervention tracee dans doc/BACKLOG.md.
