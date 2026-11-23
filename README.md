# MLG Alpha — MIDI Line Generator

*par ANKS Labs · appareil Max for Live gratuit pour Ableton Live*

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

## Installation : l'appareil Max for Live

MLG Alpha est un **effet MIDI Max for Live**. Il se pose sur la piste MIDI, juste devant ton synthé :

**[MLG Alpha] → [ton synthé]**

Une seule piste, pas de routage. Il faut Live avec Max for Live (Suite, ou Standard avec Max for Live).

1. Télécharger l'appareil : onglet **Actions** de ce dépôt, dernier « Max for Live » en vert, artefact `MLG-Alpha-Max-for-Live`.
2. Dézipper. Le dossier `MLG Alpha` contient l'appareil, quatre scripts et la bibliothèque. **Ils doivent rester ensemble dans le même dossier.**
3. Copier ce dossier dans ta User Library d'Ableton, par exemple `Documents\Ableton\User Library\Presets\MIDI Effects\Max MIDI Effect\MLG Alpha\`.
4. Dans Live, glisser `MLG Alpha.amxd` sur une piste MIDI, devant l'instrument.
5. Lancer la lecture : la ligne joue en boucle, calée sur le tempo. Les notes jouées au clavier passent à travers.

Si l'appareil reste vide ou affiche « Bibliothèque : chargement… », ouvre l'éditeur Max (bouton crayon de l'appareil) et regarde la fenêtre Max (console) : le message d'erreur dit quel fichier manque.

**Secours** : si Live refuse le fichier `.amxd`, glisse un « Max MIDI Effect » vide sur la piste, ouvre son éditeur, ouvre `MLG Alpha.maxpat` dans Max, sélectionne tout, copie, colle dans l'appareil vide, puis enregistre-le dans le dossier `MLG Alpha` sous le nom `MLG Alpha.amxd`.

### Comment l'appareil est construit (pour bidouiller dans Max)

En ouvrant l'éditeur Max, tu trouves trois zones titrées :

1. **CŒUR** : `node.script mlg_core.js`. Tout le cerveau est là : générateur, bibliothèque, traducteur, tirage, fiche technique, apprentissage. Il reçoit des messages simples (`param density 40`, `words basse sombre`, `generate`…) et en renvoie (`clip …`, `place p_density 40`, `understood …`). Un `[route]` les distribue.
2. **LECTURE** : `js mlg_player.js`. Il lit la position du transport de Live (`[metro]` → `[transport]`), joue la ligne vers `[midiformat]` → `[midiout]`, et écrit la ligne dans un clip quand on le lui demande.
3. **INTERFACE** : les potards (`live.dial`, `live.menu`), les boutons (`live.text`), les cases de texte (`textedit`), le piano roll (`jsui mlg_roll.js`) et les zones de texte (`jsui mlg_text.js`). En mode présentation, c'est ce que tu vois dans Live.

Le patch n'est pas dessiné à la main : il est fabriqué par `tools/build_device.py`. Pour une modification durable, c'est ce script qu'il faut changer, puis relancer `python3 tools/build_device.py`.

## Mode d'emploi

L'appareil fait 1 180 pixels de large, en trois zones.

### Panneau mécanique (à gauche)

- **GÉNÉRER** : nouvelle ligne avec les potards. Ce qui est verrouillé ne change pas.
- **MUTER** : petites variations de la ligne actuelle.
- **Verrou rythme / Verrou hauteurs** : garde l'une des deux couches.
- **Garder** : garde la ligne dans ta bibliothèque perso, avec les mots tapés dans la case de texte.
- **Seeds** : identifiants de la ligne. Tape un nombre puis Entrée pour retrouver une ligne.
- **Menus** : moteur (aléatoire ou euclidien), division (1/4 à 1/32, triolets compris), tonique, gamme (13), octave, changement de ligne (immédiat ou à la mesure suivante), legato.
- **Potards** : pas (jusqu'à 128, soit 8 mesures), densité, impulsions, rotation, swing, note basse, note haute, écart max, accent, durées min et max, vélocités min et max. Tous automatisables et mappables dans Live.

### Panneau texte (au milieu)

- **Case de texte** : tape (ou dicte avec Win+H) ce que tu cherches, puis Entrée ou **CHERCHER**. Exemples : « basse sombre et roulante », « nappe mélancolique aérée », « kick techno très lourd », « arpège triste en triolets, 2 mesures », « pas trop dense façon Boards of Canada ».
  - Le traducteur reconnaît les 100 mots, leurs synonymes, les styles (techno, EBM, acid, IDM, Moderat, NIN…), les rôles (kick, batterie, percu, basse, mélodie, accords, nappe), « très » / « un peu », « pas … », les triolets et le nombre de mesures.
  - En dessous s'affiche ce qui a été compris. S'il n'y a rien qui réunit tout, MLG Alpha prend la ligne la plus proche et le dit.
  - Une basse tirée après un kick évite de tomber sur les coups du kick.
- **Une autre** : nouveau tirage avec les mêmes mots.
- **Les potards se placent** sur les réglages équivalents de la ligne tirée. Tourner un potard repasse sur le moteur des potards avec ces réglages. La tonique et l'octave transposent la ligne de la bibliothèque.
- **J'aime / Bof** : renforce ou affaiblit les étiquettes de la ligne pour les mots que tu as tapés. Le style et le rôle d'une ligne ne changent jamais. Rien n'est obligatoire.
- **Garder** : comme à gauche.
- **Fiche** : ouvre une fenêtre avec la fiche de la ligne en langage MIDI (mesures, grille, densité, placement sur les temps, durées, vélocités, hauteurs, intervalles, structure).
- **Bilan** : ouvre une fenêtre avec les statistiques (proposées, écartées vite, écoutées longtemps, aimées, gardées, par style, jamais entendues) et un bouton pour effacer les J'aime / Bof.
- **Commande technique** : « 2 mesures », « division 1/16 », « triolets », « densité 40 », « euclidien 5 », « swing 30 », « tonique la », « gamme dorien », « notes C1 à C3 », « legato », « vélocité 80 120 », « durée 50 100 », « écart 4 », « génère », « mute ».

### Ligne en cours (à droite)

- Le nom de la ligne, son rôle et son style, et le piano roll avec la tête de lecture.
- **→ Écrire dans un clip** : écrit la ligne dans la case sélectionnée de la piste (vue Session), ou dans la première case libre. C'est la façon de la garder dans ton morceau.
- Tes fichiers (bibliothèque perso, apprentissage, statistiques) sont dans `%APPDATA%\ANKS Labs\MLG Alpha\`, en texte lisible. Ce sont les mêmes que ceux de la version VST.

### Et le VST3 ?

Le VST3 (dossier `Source/`) marche, mais dans Ableton il ne peut pas se placer devant un instrument : il faut deux pistes et un routage MIDI. La version Max for Live est la version principale. Le VST3 reste compilé à chaque push (artefact `MLG-Alpha-VST3-Windows`) pour d'autres logiciels.

## La bibliothèque

- `Library/*.txt` : les motifs en texte lisible (voir `Library/README.md`).
- `tools/classify.py` les classe et les compile dans `Resources/mlg_library.txt.gz`, embarqué dans le plugin : 12 familles plus « hors cible », 7 rôles, mesures objectives, 3 à 5 étiquettes parmi les 100 mots avec une confiance de 1 à 9, doublons retirés, lignes de kick extraites des batteries, basses NeuralAcid triées.
- `tools/build_dictionary.py` fabrique `Resources/mlg_dictionary.txt`, le traducteur mots → étiquettes, styles et rôles. Il se modifie à la main.

Après une modification : `python3 tools/build_dictionary.py && python3 tools/classify.py`, puis recompiler.

## Compilation

Les tests de l'appareil Max tournent avec Node : `node max/tests/test_core.js`, `node max/tests/test_player.js`, `node max/tests/test_maxapi.js`. GitHub Actions les lance, puis fabrique l'appareil (artefact `MLG-Alpha-Max-for-Live`).


GitHub Actions compile le VST3 Windows à chaque push : onglet *Actions*, artefact `MLG-Alpha-VST3-Windows`.

Pour compiler les tests du VST3 (moteur, bibliothèque, lecture) :

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
