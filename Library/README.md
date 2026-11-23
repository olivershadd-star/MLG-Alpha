# Bibliothèque de motifs LINEGEN

332 motifs de base orientés musique électronique, en texte lisible et modifiable à la main.

| Fichier | Contenu | Nombre |
|---|---|---|
| `gen_bass.txt` | Basses fabriquées par règles de groove : contretemps, roulante, galop, sur le temps, syncopée, clairsemée, dub, doubles croches, garage | 1 400 |
| `gen_acid.txt` | Lignes acid fabriquées (accents, slides) | 500 |
| `gen_synth.txt` | Synthés fabriqués : stabs, séquences, arpèges, plucks, gimmicks, drones | 1 100 |
| `gen_perc.txt` | Percussions fabriquées : rim, charleston, toms, shaker, cloche, clap, perc tribale | 900 |
| `drums_bardet.txt` | Batterie : « 200 / 260 Drum Machine Patterns » (funk, disco, pop, rock, reggae, latin…) | 387 |
| `drums_pocket_operations.txt` | Batterie : *Pocket Operations* (house, electro, breaks, DnB, dubstep, UKG, Miami bass…) | 113 |
| `drums_groovesteps.txt` | Grooves de base GrooveSteps | 7 |
| `drums_electronic.txt` | Batterie électronique écrite : techno, minimal, dub techno, hardgroove, industriel, house, EBM, trance… | 76 |
| `chords_drolez.txt` | Grilles d'accords du Free MIDI Chords Pack (majeur, mineur, modal, avec ambiance) | 194 |
| `chords.txt` | Grilles électroniques, 12 nappes sur 8 mesures, 14 rythmes de jeu d'accords | 56 |
| `bass_neuralacid.txt` | Basses NeuralAcid sur 4 mesures, qui suivent une grille d'accords (lot de validation) | 897 |
| `acid.txt`, `bass.txt`, `melody.txt` | Acid, basses et mélodies écrites à la main | 87 |

**Total : 5 717 motifs (1,8 Mo).**

## Format

Chaque motif commence par une ligne `@type id=… name="…" genre=… bars=… steps=16`.

- **Batterie** : une ligne par instrument (`BD`, `SN`, `CL`, `RS`, `CH`, `OH`, `CY`, `LT`, `MT`, `HT`, `CB`, `SH`, `PC`, `AC` = accent), un caractère par pas : `x` coup, `r` double coup, `h` coup décalé d'un demi-pas, `.` silence. Mesures séparées par un espace.
- **Vélocités** (fichiers `gen_*`) : ligne `V` sous chaque ligne `N`, une vélocité par note.
- **Percussions** (`gen_perc.txt`) : dans la ligne `N`, le nom de l'instrument (`RS`, `CH`, `LT`…) au lieu d'un intervalle.
- **Acid / basse / mélodie** : `N` puis un jeton par pas = intervalle en demi-tons depuis la tonique (`0`, `3`, `12`, `-2`…), suffixe `a` accent, `s` slide ; `.` silence, `-` note tenue. Tout est transposé dans la tonique choisie.
- **Accords** : `C` puis un degré par mesure (`i`, `VI`, `iv7`, `Imaj7`, `isus2`…), `-` = l'accord continue. `@rhythm` = rythme de jeu des accords.

Pour ajouter tes motifs : copier un bloc, changer l'`id`, le nom et les pas.

## Sources

- `gen_*.txt` : fabriqués par `tools/generate_patterns.py` (règles : hiérarchie des temps, cellules rythmiques par style, phrasé AAAA'/ABAB'/AABB, tonique sur les temps forts, vélocités accentuées). Relancer le script redonne exactement les mêmes motifs.
- `drums_bardet.txt` : rythmes de René-Pierre Bardet, données JSON de [gvellut/dmp_midi](https://github.com/gvellut/dmp_midi) (`tools/import_bardet.py`).
- `bass_neuralacid.txt` : jeu de données [intrect/neuralacid-basslines](https://huggingface.co/datasets/intrect/neuralacid-basslines) (CC BY 4.0), généré par Electr-o-matic de unohee (`tools/import_neuralacid.py`).
- `drums_groovesteps.txt` : GrooveSteps (groovesteps.com), licence CC0 (`tools/import_groovesteps.py`).
- `chords_drolez.txt` : [ldrolez/free-midi-chords](https://github.com/ldrolez/free-midi-chords), licence MIT (`tools/import_drolez.py`).

- `drums_pocket_operations.txt` : données de [darosh/pocket-patterns](https://github.com/darosh/pocket-patterns) (licence MIT), d'après la collection *Pocket Operations* (Shitty Recording Studio / Paul Wenzel). Import : `tools/import_pocket_operations.py`.
- Tous les autres fichiers : motifs de base des genres écrits pour LINEGEN (`tools/build_library.py`).
