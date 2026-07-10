---
name: drawio-merise
description: "Use when: generation ou correction de diagrammes MERISE draw.io (MCD, MLD, MCT, MOT), regles anti-chevauchement, XML importable sans correction manuelle."
---

# Skill Drawio MERISE

## Objectif
Produire des diagrammes MERISE draw.io importables, lisibles et conformes (MCD/MLD/MCT/MOT).

## Regles absolues
- Interdiction des commentaires XML et des doubles tirets dans le XML livre.
- Le fichier final doit etre importable dans draw.io.

## Standards MERISE
### MCD
- Entite: 2 compartiments (en-tete + attributs).
- Identifiant souligne obligatoirement.
- Association nommee avec un verbe explicite.
- Association porteuse: attributs affiches dans l'association.
- Cardinalites lisibles: 0,1 ; 1,1 ; 0,N ; 1,N.

### MLD
- Chaque entite devient une table.
- PK: prefixe # ou annotation PK.
- FK: prefixe * ou annotation FK.
- 1,N -> FK ; N,N -> table de jonction.
- Fleches ER: ERone, ERmany, ERmandOne, ERzeroToOne, ERzeroToMany.

### MCT
- Evenement: ovale.
- Operation: rectangle.
- Synchronisation: barre.
- Regle d'emission: texte sous operation.
- Flux directionnels.

### MOT
- Swimlanes par acteur.
- Tache manuelle: rectangle simple.
- Tache automatique: double bordure.
- Tache interactive: arrondi.
- Decisions avec gardes.
- Transitions lisibles entre couloirs.

## Palette MERISE

Note : voir justification de la separation des palettes UML/MERISE dans le skill drawio-uml.

- Entite principale: #dae8fc / #6c8ebf
- Entite faible: #e1f0ff / #4a7ab5
- Association binaire: #fff2cc / #d6b656
- Association ternaire: #ffe6cc / #d79b00
- Association porteuse: #d5e8d4 / #82b366
- Evenement MCT/MOT: #f8cecc / #b85450
- Tache MOT systeme: #dae8fc / #6c8ebf
- Tache MOT gestionnaire: #d5e8d4 / #82b366

## Regles anti-chevauchement (bloquantes)

Ces regles s'appliquent a tous les types MERISE (MCD, MLD, MCT, MOT). Leur non-respect produit des elements visuellement fusionnes ou illisibles.

R1 — Espacement vertical minimum entre entites : 80px
Ne jamais placer deux entites dont les bords se touchent verticalement.
Formule obligatoire : `Y_suivant = Y_precedent + hauteur_precedente + 80`
Valeur minimale du gap : 80px. Ne jamais descendre en dessous, meme si le diagramme semble compact.

R2 — Hauteur d'entite calculee avant placement de l'entite suivante
Ne jamais fixer la position d'une entite suivante avant d'avoir calcule la hauteur reelle de l'entite precedente.
Formule de calcul de hauteur : `hauteur_entite = startSize + (nombre_attributs x 22) + 16`
Ce calcul est obligatoire avant chaque positionnement vertical.

R3 — Largeur uniforme par colonne de diagramme
Toutes les entites d'une meme colonne verticale ont la meme largeur.
Largeur standard : 240px pour entites simples, 300px pour entites avec associations porteuses.
Interdiction de mixer des largeurs differentes dans une meme colonne.

R4 — Espacement horizontal minimum entre colonnes : 120px
Le gap horizontal entre deux colonnes d'entites est de 120px minimum (pas 60px).
Ce gap est necessaire pour que les liens et leurs cardinalites soient lisibles sans chevauchement.
Formule : `X_colonne_suivante = X_colonne_courante + largeur_colonne + 120`

R5 — Les associations sont positionnees en dernier
Ordre de generation obligatoire :
1. Placer toutes les entites et calculer leurs hauteurs reelles.
2. Calculer les centres geometriques des entites a relier.
3. Positionner les rectangles d'association au centre geometrique entre les entites concernees.
Interdiction de positionner une association avant de connaitre la hauteur finale de toutes les entites.
Centre geometrique horizontal : `X_assoc = (X_entite_A + largeur_A/2 + X_entite_B - largeur_B/2) / 2 - largeur_assoc/2`
Centre geometrique vertical : `Y_assoc = (Y_entite_A + hauteur_A/2 + Y_entite_B + hauteur_B/2) / 2 - hauteur_assoc/2`

R6 — Verification anti-chevauchement obligatoire avant livraison
Avant de produire le fichier final, verifier pour chaque paire d'elements :
- Vertical : `Y_element_A + hauteur_A + 80 <= Y_element_B` (si B est sous A)
- Horizontal : `X_element_A + largeur_A + 120 <= X_element_B` (si B est a droite de A)
Si une verification echoue : repositionner et recalculer avant de livrer.
Cette verification est bloquante : un fichier avec chevauchement ne peut pas etre livre.

## Erreurs de mise en page interdites

| Erreur | Consequence | Solution |
|---|---|---|
| Hauteur cellule fixee avant calcul du contenu | Chevauchement si un attribut est long | Calculer `startSize + (N x 22) + 16` avant tout positionnement suivant |
| Gap vertical < 80px entre entites | Tables visuellement fusionnees | Imposer 80px entre `Y_fin` d'une entite et `Y_debut` de la suivante |
| Gap horizontal < 120px entre colonnes | Liens et cardinalites illisibles | 120px minimum entre colonnes |
| Association positionnee avant les entites | Position incorrecte si entite grandit | Positionner les associations en dernier, au centre geometrique calcule |
| Largeurs differentes dans une meme colonne | Desalignement visuel | Une seule largeur par colonne, definie avant generation |
| Pas de verification anti-chevauchement | Livraison avec elements superposes | Checklist R6 obligatoire avant tout fichier final |

## Checklist de sortie
- [ ] Pas de commentaires XML ni doubles tirets.
- [ ] IDs uniques, parent/source/target coherents.
- [ ] Notation conforme au type (MCD/MLD/MCT/MOT).
- [ ] Cardinalites presentes sur tous les liens MCD critiques.
- [ ] Identifiant souligne dans MCD.
- [ ] PK et FK marquees dans MLD.
- [ ] Taches MOT dans le bon couloir.
- [ ] Regles R1-R6 verifiees : aucun chevauchement detecte.
- [ ] Index doc/DIAGRAMMES/README.md mis a jour.
- [ ] Intervention tracee dans doc/BACKLOG.md.
