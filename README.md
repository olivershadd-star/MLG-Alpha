# LINEGEN — générateur de lignes MIDI (ANKS Labs)

VST3 qui génère des lignes MIDI à partir de réglages (pas d'IA) et les joue en direct sur n'importe quel instrument d'Ableton.

## Installation dans Ableton (routage sur 2 pistes)

1. Copier `LINEGEN.vst3` dans `C:\Program Files\Common Files\VST3`, puis rescanner les plugins dans Ableton.
2. **Piste 1** : charger LINEGEN (il apparaît comme instrument, éditeur ANKS Labs). Il ne fait aucun son.
3. **Piste 2** : charger l'instrument (Serum, Massive…).
   - *MIDI From* : piste 1, puis choisir **LINEGEN** dans le second menu.
   - *Monitor* : **In**.
4. Lancer la lecture : la ligne joue en boucle, synchronisée sur le tempo.

## Commandes

- **GÉNÉRER** : nouvelle ligne (ce qui est verrouillé ne change pas).
- **MUTER** : petites variations de la ligne actuelle.
- **Verrou rythme / Verrou hauteurs** : garder l'une des deux couches.
- **Seeds** : identifiants de la ligne ; double-clic pour en saisir une et retrouver une ligne.
- **Glisser le clip .mid** : glisser vers une piste d'Ableton pour figer la ligne en clip.

Tous les réglages agissent en direct sur la ligne en cours.

## Moteurs v1

- Rythme **Aléatoire** (densité) ou **Euclidien** (pas, impulsions, rotation).
- Hauteurs **Aléatoire contraint** : tonique, gamme (13 gammes), note basse / haute, écart max (en degrés de gamme).
- Notes : durée min / max (en % d'un pas), legato (glide si le synthé est en mono), vélocité min / max, accent sur les temps forts, swing.
- Cycle jusqu'à 64 pas ; divisions 1/4 à 1/32, triolets compris.

## Compilation

GitHub Actions compile le VST3 Windows à chaque push (onglet *Actions* → artefact `LINEGEN-VST3-Windows`).

Tests du moteur et de la lecture : `cmake -B build -DLINEGEN_TESTS=ON && cmake --build build`.
