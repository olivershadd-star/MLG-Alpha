# MLG Alpha — MIDI Line Generator

*par ANKS Labs · VST3 gratuit pour Ableton Live (Lite compris)*

---

## Toi aussi, ça t'arrive ?

Ta boucle tourne depuis vingt minutes. Le kick est bon, la basse aussi, et tu sens bien qu'il manque **une ligne de quelque chose**. Un petit arpège, une nappe, une percu qui claque, n'importe quoi. Et là, rien. Pas une idée. Le vide.

Alors tu fais comme tout le monde : tu poses des notes un peu au hasard dans le piano roll, tu décales, tu effaces, tu recommences. Des fois ça marche. Souvent, non.

**MLG Alpha part de cette idée : « je n'ai pas d'idée, voyons ce qui pourrait tourner ».** Plutôt que de chercher la ligne parfaite, il t'en propose des dizaines. Tu écoutes sur ton propre morceau, tu gardes ce qui colle et tu jettes le reste.

## Un petit calcul pour se faire peur

Prends **une seule mesure de 16 pas** (des doubles croches en 4/4) :

- Rien que pour le rythme, chaque pas est joué ou pas. Ça fait **2¹⁶ = 65 536 rythmes possibles**.
- Ajoute **4 notes différentes** au choix sur chaque pas joué. Chaque pas a alors 5 états (silence ou l'une des 4 notes), soit **5¹⁶ ≈ 152 milliards de lignes**.
- Passe aux **12 notes d'une octave** : **13¹⁶ ≈ 665 millions de milliards**.

Et on n'a pas encore parlé des vélocités, des durées, du swing, ni des lignes sur 2, 4 ou 8 mesures.

Pour écouter les 152 milliards de lignes à 120 BPM (2 secondes par mesure), il te faudrait environ **9 700 ans**, sans pause pipi.

Moralité : le hasard pur, c'est un océan. La grande majorité de ces lignes sonne comme un chat qui marche sur un clavier. Le but de MLG Alpha, c'est de **pêcher dans les coins de l'océan où ça sonne**.

## Comment il s'y prend

### 1. Les potards : ton générateur à toi

Comme tous les générateurs MIDI, MLG Alpha fabrique des lignes à partir de réglages :

- **rythme** aléatoire (densité) ou euclidien (impulsions réparties) ;
- **gamme** et tonique ;
- tessiture de la ligne et écart maximal entre deux notes ;
- **durées** des notes et legato ;
- **vélocités** et accents ;
- **swing**.

Le hasard est guidé par des règles de solfège : les temps forts pèsent plus que les contretemps, et la ligne revient vers la tonique.

Chaque ligne a sa **seed**, un numéro qui permet de la retrouver à l'identique. **MUTER** fait de petites variations. Les **verrous** gardent le rythme pendant que tu changes les notes, ou l'inverse.

Tu crées donc tes propres presets, comme sur n'importe quel générateur.

### 2. La bibliothèque : un peu plus de 30 000 lignes toutes prêtes

En partant de cette logique de probabilités, on a isolé **un peu plus de 30 000 presets MIDI** (32 888 pour être précis) :

- batteries et percussions ;
- basses ;
- lignes acid ;
- mélodies et arpèges ;
- nappes et accords ;
- triolets.

Elles couvrent la techno, la techno industrielle, la minimal et le dub, la house, l'acid, l'EBM et la dark electro, le rock indus, l'electro et le breakbeat, la trance, l'ambient, l'IDM et l'électronique mélodique.

Une partie vient de collections libres (voir les crédits en bas). Le reste a été **fabriqué par des scripts écrits avec une IA**, en appliquant des règles musicales propres à chaque style : où tombent les kicks, comment une basse laisse de la place au kick, comment s'enchaînent les accords d'une nappe, etc.

### 3. Le dictionnaire et l'invite de commande

C'est là que ça devient rigolo. MLG Alpha a une **case de texte** (qui marche aussi avec la dictée Windows, Win+H) où tu tapes ce que tu cherches, avec tes mots :

> *« basse sombre et roulante »*
> *« nappe mélancolique aérée »*
> *« percu sèche et saccadée »*

Un **dictionnaire** d'une centaine de mots (*hypnotique, martelé, sombre, planant, grave, acide*…) traduit ta phrase en critères. MLG Alpha va ensuite **piocher au hasard parmi les lignes qui collent** à ces critères. Ce n'est pas toujours la même : c'est aléatoire, mais orienté. Les mots que tu utilises souvent et les lignes que tu aimes pèsent un peu plus à chaque tirage.

Une deuxième case, **technique**, t'explique ce que tu entends : nombre de mesures, croches ou doubles croches, triolets, groove, vélocités. Les potards se placent sur les réglages équivalents. C'est aussi une façon d'apprendre le langage MIDI en jouant.

Tu peux aussi lui parler technique : *« 2 mesures, division 1/16 »*.

### 4. Ta bibliothèque à toi

- 👍 / 👎 sur les lignes proposées : la bibliothèque apprend tes goûts, sans jamais changer le style d'une ligne.
- **Sauvegarder** : la ligne part dans *ta* bibliothèque perso, avec tes propres mots. Les doublons sont détectés.
- Des **statistiques** montrent les lignes que tu gardes, celles que tu zappes et celles que tu n'as jamais entendues.

## Soyons honnêtes

- **Cette bibliothèque n'a pas encore été vraiment triée ni éprouvée.** Elle a été en grande partie générée par IA. Il y a forcément des perles, des lignes moyennes et quelques casseroles.
- **C'est à toi de la faire grandir.** Chaque utilisateur améliore sa propre bibliothèque en likant, en jetant et en sauvegardant. Elle peut devenir énorme.
- MLG Alpha ne fait **que des notes**. Le son, c'est ton synthé. Une ligne « grasse » sur un piano reste un piano.
- **Version Alpha** : tout est branché, mais rien n'a encore été éprouvé en vrai dans Ableton. Les étiquettes de départ ont été calculées automatiquement sur les notes : elles sont parfois à côté de la plaque, c'est le rôle des J'aime / Bof de les corriger.

## L'esprit

Générer **facilement** toutes sortes de lignes :

- rythmiques ;
- mélodiques ;
- de basse ;
- des nappes.

Le but : quand tu sèches, voir ce qui pourrait coller sur ton morceau et **l'enrichir, tout simplement**. Pas de génie artificiel, pas de morceau fait à ta place. Juste une boîte à idées qui ne se fatigue jamais.

---

## Installation dans Ableton (routage sur 2 pistes)

1. Télécharger le VST3 : onglet **Actions** de ce dépôt, dernier « Build VST3 » en vert, puis l'artefact `MLG-Alpha-VST3-Windows`.
2. Copier `MLG Alpha.vst3` dans `C:\Program Files\Common Files\VST3`, puis rescanner les plugins dans Ableton.
3. **Piste 1** : charger MLG Alpha (il apparaît comme instrument, éditeur ANKS Labs). Il ne fait aucun son.
4. **Piste 2** : charger l'instrument (Serum, Massive, Operator…).
   - *MIDI From* : choisir la piste 1, puis **MLG Alpha** dans le second menu.
   - *Monitor* : **In**.
5. Lancer la lecture : la ligne joue en boucle, calée sur le tempo.

## Mode d'emploi

### Panneau mécanique

- **GÉNÉRER** : nouvelle ligne avec les potards. Ce qui est verrouillé ne change pas.
- **MUTER** : petites variations de la ligne actuelle.
- **Verrou rythme / Verrou hauteurs** : garde l'une des deux couches.
- **Seeds** : identifiants de la ligne. Double-clic pour en saisir une et retrouver une ligne.
- Potards : rythme aléatoire (densité) ou euclidien (impulsions, rotation), division de 1/4 à 1/32 avec triolets, jusqu'à 128 pas (8 mesures), swing, tonique, 13 gammes, notes basse et haute, écart max, durées, legato, vélocités, accent.

### Panneau texte

- **Vocabulaire normal** : tape (ou dicte avec Win+H) ce que tu cherches, puis Entrée ou **CHERCHER**. Exemples : « basse sombre et roulante », « nappe mélancolique aérée », « kick techno très lourd », « arpège triste en triolets, 2 mesures », « pas trop dense façon Boards of Canada ».
  - Le traducteur reconnaît les 100 mots, leurs synonymes, les styles (techno, EBM, acid, IDM, Moderat, NIN…), les rôles (kick, batterie, percu, basse, mélodie, accords, nappe), « très » / « un peu », « pas … », les triolets et le nombre de mesures.
  - **Une autre** : nouveau tirage avec les mêmes mots.
  - S'il n'y a rien qui réunit tout, MLG Alpha prend la ligne la plus proche et le dit.
  - Une basse tirée après un kick évite de tomber sur les coups du kick.
- **Les potards se placent** sur les réglages équivalents de la ligne tirée. Tourner un potard repasse sur le moteur des potards avec ces réglages. La tonique et l'octave, elles, transposent la ligne de la bibliothèque.
- **Vocabulaire technique** : la fiche de la ligne en langage MIDI (mesures, grille, densité, placement sur les temps, durées, vélocités, hauteurs, intervalles, structure). En dessous, tu peux taper des commandes : « 2 mesures », « division 1/16 », « triolets », « densité 40 », « euclidien 5 », « swing 30 », « tonique la », « gamme dorien », « notes C1 à C3 », « legato », « vélocité 80 120 », « durée 50 100 », « écart 4 », « génère », « mute ».
- **J'aime / Bof** : renforce ou affaiblit les étiquettes de la ligne pour les mots que tu as tapés. Le style et le rôle d'une ligne ne changent jamais. Rien n'est obligatoire.
- **Sauvegarder** (sur les deux panneaux) : garde la ligne dans ta bibliothèque perso, avec tes mots. Les doublons sont détectés (même rythme, mêmes notes par rapport à la tonique). Les lignes des potards gardent aussi leurs réglages et leurs seeds.
- **Bilan** : lignes proposées, écartées vite (moins de 4 s), écoutées longtemps (plus de 30 s), aimées, gardées, par style, et ce qui n'a jamais été entendu. Bouton pour remettre l'apprentissage à zéro.

### Lecture

- **Changement de ligne** : immédiat, ou à la mesure suivante.
- **Glisser le clip .mid vers Ableton** : fige la ligne en clip.
- Tes fichiers (bibliothèque perso, apprentissage, statistiques) sont dans `%APPDATA%\ANKS Labs\MLG Alpha\`, en texte lisible.

## La bibliothèque

- `Library/*.txt` : les motifs en texte lisible (voir `Library/README.md`).
- `tools/classify.py` les classe et les compile dans `Resources/mlg_library.txt.gz`, embarqué dans le plugin : 12 familles plus « hors cible », 7 rôles, mesures objectives, 3 à 5 étiquettes parmi les 100 mots avec une confiance de 1 à 9, doublons retirés, lignes de kick extraites des batteries, basses NeuralAcid triées.
- `tools/build_dictionary.py` fabrique `Resources/mlg_dictionary.txt`, le traducteur mots → étiquettes, styles et rôles. Il se modifie à la main.

Après une modification : `python3 tools/build_dictionary.py && python3 tools/classify.py`, puis recompiler.

## Compilation

GitHub Actions compile le VST3 Windows à chaque push : onglet *Actions*, artefact `MLG-Alpha-VST3-Windows`.

Pour compiler les tests (moteur, bibliothèque, lecture) :

```
cmake -B build -DMLGALPHA_TESTS=ON
cmake --build build
```

## Crédits de la bibliothèque

Merci aux collections libres qui ont nourri la bibliothèque :

- [darosh/pocket-patterns](https://github.com/darosh/pocket-patterns) (MIT), d'après *Pocket Operations* de Paul Wenzel ;
- rythmes de René-Pierre Bardet, via [gvellut/dmp_midi](https://github.com/gvellut/dmp_midi) ;
- [intrect/neuralacid-basslines](https://huggingface.co/datasets/intrect/neuralacid-basslines) (CC BY 4.0) ;
- GrooveSteps (groovesteps.com, CC0) ;
- [ldrolez/free-midi-chords](https://github.com/ldrolez/free-midi-chords) (MIT).

Le détail est dans [`Library/README.md`](Library/README.md).

MLG Alpha est libre et gratuit, comme la musique qu'on fait avec.
