# Bibliothèque de motifs LINEGEN

332 motifs de base orientés musique électronique, en texte lisible et modifiable à la main.

| Fichier | Contenu | Nombre |
|---|---|---|
| `drums_electronic.txt` | Batterie : techno, minimal, dub techno, hardgroove, hard techno, industriel, house, deep, tech house, electro, EBM, synthwave, trance, breaks, DnB, trap, gqom… + breaks de fin | 76 |
| `drums_pocket_operations.txt` | Batterie : familles électroniques de *Pocket Operations* (house, electro, breaks, DnB, dubstep, UK garage, Miami bass, hip hop, dub, roulements) | 113 |
| `acid.txt` | Lignes acid façon TB-303 (accents, slides) | 32 |
| `bass.txt` | Basses : contretemps, roulante, galop, EBM, octave house, sub, electro, reese… | 30 |
| `melody.txt` | Arpèges, riffs, stabs, séquences, phrases de 2 et 4 mesures | 25 |
| `chords.txt` | 30 grilles d'accords, 12 nappes sur 8 mesures, 14 rythmes de jeu d'accords | 56 |

## Format

Chaque motif commence par une ligne `@type id=… name="…" genre=… bars=… steps=16`.

- **Batterie** : une ligne par instrument (`BD`, `SN`, `CL`, `RS`, `CH`, `OH`, `CY`, `LT`, `MT`, `HT`, `CB`, `SH`, `PC`, `AC` = accent), un caractère par pas : `x` coup, `r` double coup, `h` coup décalé d'un demi-pas, `.` silence. Mesures séparées par un espace.
- **Acid / basse / mélodie** : `N` puis un jeton par pas = intervalle en demi-tons depuis la tonique (`0`, `3`, `12`, `-2`…), suffixe `a` accent, `s` slide ; `.` silence, `-` note tenue. Tout est transposé dans la tonique choisie.
- **Accords** : `C` puis un degré par mesure (`i`, `VI`, `iv7`, `Imaj7`, `isus2`…), `-` = l'accord continue. `@rhythm` = rythme de jeu des accords.

Pour ajouter tes motifs : copier un bloc, changer l'`id`, le nom et les pas.

## Sources

- `drums_pocket_operations.txt` : données de [darosh/pocket-patterns](https://github.com/darosh/pocket-patterns) (licence MIT), d'après la collection *Pocket Operations* (Shitty Recording Studio / Paul Wenzel). Import : `tools/import_pocket_operations.py`.
- Tous les autres fichiers : motifs de base des genres écrits pour LINEGEN (`tools/build_library.py`).
