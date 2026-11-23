# Bibliothèque de motifs MLG Alpha

32 888 motifs orientés musique électronique, en texte lisible et modifiable à la main. Après classement et retrait des doublons (`tools/classify.py`), le plugin en embarque 32 163.

| Fichier | Contenu | Nombre |
|---|---|---|
| `fill_drums.txt` | Batteries complètes en 4 temps : rock, metal (double pédale, galop, blast, demi-temps), metal indus, metal prog (kick en 3/5/7 contre la caisse), jazz shuffle, contretemps (one drop, steppers) — avec ghost notes, relances, crashs, roulements | 1 250 |
| `fill_triplets.txt` | Triolets en 4/4 : charleston en triolets (1/8T et 1/16T), rafales trap, arpèges, basses shuffle, roulements, batterie jazz ternaire | 1 002 |
| `fill_four_chords.txt` | Les 4 accords I–IV–V–vi : toutes les combinaisons de 2 à 4 accords, 1 à 4 temps par accord, en nappe, stab ou arpège | 552 |
| `fill_acid.txt` | Nouvelles lignes acid 303 | 1 000 |
| `fill_electro.txt` | Percussions électro, caisses de break à ghost notes, leads électro | 850 |
| `fill_minimal_dub.txt` | Clics minimal, accords dub (m7, m9, m11, sus2, renversements), blips | 900 |
| `fill_trance.txt` | Basses trance roulantes, percussions trance, stabs rave | 433 |
| `fill_light_perc.txt` | Percussions légères : clics, ticks, polymètres doux, textures rythmiques | 500 |
| `tex_ambient.txt` | Drones, nappes polyphoniques avec conduite des voix (4 à 16 mesures), notes flottantes en boucles premières, accords dub | 1 256 |
| `tex_idm.txt` | Drills IDM (ratchets), arpèges glissants en 5/7/9/11, mélodies simples, mélodies et beats façon Boards of Canada | 1 400 |
| `tex_moderat.txt` | Beats demi-temps, sub syncopée, accords mélancoliques, plucks en contretemps | 950 |
| `tex_industrial_techno.txt` | Rhythmic noise, basses grondantes (Perc / Ancient Methods), séquences EBM-techno (Orphx / Adam X) | 900 |
| `tex_swedish.txt` | Techno suédoise en boucles : boucles de toms, ride, stabs d'une note | 461 |
| `tex_noise_rock.txt` | Toms tribaux, basses fuzz (HEALTH) | 200 |
| `tex_dark_electro.txt` | Dark electro façon :wumpscut: : leads gothiques en mineur harmonique (question-réponse), cordes/chœurs, stabs staccato, arpèges sombres | 442 |
| `industrial_bass.txt` | EBM (doubles croches entre les kicks, gate), basses électro-industrielles / dark electro | 900 |
| `industrial_synth.txt` | Riffs chug de rock/metal indus, riffs sur pédale, leads aggrotech | 764 |
| `industrial_perc.txt` | Caisse martiale EBM, kick + caisse de rock indus (dont demi-temps), noise stabs métalliques, « usine » en 3/5/6/7 | 903 |
| `techno_bass.txt` | Techno : basses roulantes qui laissent la place au kick, rumble, contretemps | 1 020 |
| `techno_synth.txt` | Techno : polymètres, euclidiens, accents, courbes de vélocité, lignes atonales/industrielles, question-réponse | 1 970 |
| `techno_perc.txt` | Techno : polymètres et euclidiens de percussions, accents toutes les 3/5/7, courbes de vélocité, relances | 1 430 |
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
| `bass_neuralacid.txt` | Basses NeuralAcid sur 4 mesures, qui suivent une grille d'accords | 8 985 |
| `acid.txt`, `bass.txt`, `melody.txt` | Acid, basses et mélodies écrites à la main | 87 |

**Total : 32 888 motifs.**

## Format

Chaque motif commence par une ligne `@type id=… name="…" genre=… bars=… steps=16`.

- **Batterie** : une ligne par instrument (`BD`, `SN`, `CL`, `RS`, `CH`, `OH`, `CY`, `LT`, `MT`, `HT`, `CB`, `SH`, `PC`, `AC` = accent), un caractère par pas : `x` coup, `r` double coup, `h` coup décalé d'un demi-pas, `.` silence. Mesures séparées par un espace.
- **Triolets** : `steps=12 grid=1/8T` (croches de triolet) ou `steps=24 grid=1/16T` (doubles croches de triolet), toujours en 4/4.
- **Vélocités** (fichiers `gen_*`) : ligne `V` sous chaque ligne `N`, une vélocité par note.
- **Percussions** (`gen_perc.txt`) : dans la ligne `N`, le nom de l'instrument (`RS`, `CH`, `LT`…) au lieu d'un intervalle.
- **Polyphonie** (`tex_*`) : lignes `N`, `N2`, `N3`, `N4` (une par voix) et `V`, `V2`… pour leurs vélocités, à chaque mesure. Champ `voices=` dans l'en-tête.
- **Ratchet** : suffixe `*2`, `*3`, `*4` = note répétée 2, 3 ou 4 fois dans le pas.
- **Acid / basse / mélodie** : `N` puis un jeton par pas = intervalle en demi-tons depuis la tonique (`0`, `3`, `12`, `-2`…), suffixe `a` accent, `s` slide ; `.` silence, `-` note tenue. Tout est transposé dans la tonique choisie.
- **Accords** : `C` puis un degré par mesure (`i`, `VI`, `iv7`, `Imaj7`, `isus2`…), `-` = l'accord continue. `@rhythm` = rythme de jeu des accords.

Pour ajouter tes motifs : copier un bloc, changer l'`id`, le nom et les pas.

## Sources

- `fill_*.txt` : fabriqués par `tools/generate_fill.py` (familles complétées, 4 accords, batteries rock/metal/jazz/mesures impaires).
- `tex_*.txt` : fabriqués par `tools/generate_textures.py` (ambient, IDM, Apparat/Moderat, techno industrielle, techno suédoise, noise rock, dark electro).
- `industrial_*.txt` : fabriqués par `tools/generate_industrial.py` (règles EBM, électro-industriel, aggrotech, rock/metal industriel ; tempo conseillé dans `bpm=`).
- `techno_*.txt` : fabriqués par `tools/generate_techno.py` (règles de production techno : kick libre, rumble, polymètre, euclidien, accents, question-réponse, relances).
- `gen_*.txt` : fabriqués par `tools/generate_patterns.py` (règles : hiérarchie des temps, cellules rythmiques par style, phrasé AAAA'/ABAB'/AABB, tonique sur les temps forts, vélocités accentuées). Relancer le script redonne exactement les mêmes motifs.
- `drums_bardet.txt` : rythmes de René-Pierre Bardet, données JSON de [gvellut/dmp_midi](https://github.com/gvellut/dmp_midi) (`tools/import_bardet.py`).
- `bass_neuralacid.txt` : jeu de données [intrect/neuralacid-basslines](https://huggingface.co/datasets/intrect/neuralacid-basslines) (CC BY 4.0), généré par Electr-o-matic de unohee (`tools/import_neuralacid.py`).
- `drums_groovesteps.txt` : GrooveSteps (groovesteps.com), licence CC0 (`tools/import_groovesteps.py`).
- `chords_drolez.txt` : [ldrolez/free-midi-chords](https://github.com/ldrolez/free-midi-chords), licence MIT (`tools/import_drolez.py`).

- `drums_pocket_operations.txt` : données de [darosh/pocket-patterns](https://github.com/darosh/pocket-patterns) (licence MIT), d'après la collection *Pocket Operations* (Shitty Recording Studio / Paul Wenzel). Import : `tools/import_pocket_operations.py`.
- Tous les autres fichiers : motifs de base des genres écrits pour MLG Alpha (`tools/build_library.py`).
