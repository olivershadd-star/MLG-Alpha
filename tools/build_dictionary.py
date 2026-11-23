"""Fabrique Resources/mlg_dictionary.txt : le traducteur mots -> étiquettes, familles, rôles.

Le fichier produit est du texte simple, modifiable à la main :
    tag <étiquette>[,<étiquette>…] = forme, forme, expression en plusieurs mots…
    family <famille>[,…] = …
    role <rôle>[,…] = …
    mod <poids> = …          (intensité : « très » = 2, « un peu » = 0.5)
    neg = …                  (négation : « pas », « sans »…)
    tech <clé> = …           (mots techniques reconnus dans les deux cases)
Le plugin ignore les accents et les majuscules. Usage : python3 tools/build_dictionary.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "Resources", "mlg_dictionary.txt")


def forms(w):
    """Masculin, féminin, pluriels."""
    out = {w}
    if w.endswith("eux"):
        b = w[:-3]
        out |= {b + "euse", b + "euses"}
    elif w.endswith("if"):
        b = w[:-2]
        out |= {w + "s", b + "ive", b + "ives"}
    elif w.endswith("el"):
        out |= {w + "s", w + "le", w + "les"}
    elif w.endswith("e"):
        out |= {w + "s"}
    elif w.endswith(("s", "x")):
        out |= {w + "e", w + "es"}
    elif w.endswith("al"):
        out |= {w[:-2] + "aux", w + "e", w + "es"}
    else:
        out |= {w + "s", w + "e", w + "es"}
    return out


# étiquette -> synonymes (les formes fléchies sont ajoutées automatiquement pour les mots simples)
TAGS = {
    # mouvement
    "rectiligne": ["rectiligne", "droit", "linéaire", "tout droit", "carré"],
    "hypnotique": ["hypnotique", "hypnotisant", "envoûtant", "transe", "en boucle"],
    "roulant": ["roulant", "qui roule", "rolling", "déroulé"],
    "martelé": ["martelé", "martèle", "qui martèle", "tapé", "pilonné", "pounding"],
    "haché": ["haché", "hachuré", "découpé", "coupé"],
    "saccadé": ["saccadé", "par à-coups", "heurté", "stop and go"],
    "syncopé": ["syncopé", "syncope", "syncopes", "décalé", "à contretemps", "contretemps", "off beat", "offbeat"],
    "bancal": ["bancal", "branlant", "titubant", "ivre", "bourré", "drunk", "de travers"],
    "boiteux": ["boiteux", "qui boite", "claudicant", "irrégulier"],
    "cassé": ["cassé", "brisé", "broken", "déstructuré", "concassé"],
    "régulier": ["régulier", "stable", "constant", "carré", "métronomique", "sur le temps"],
    "mécanique": ["mécanique", "robotique", "robot", "machine", "automatique", "industriel"],
    "galopant": ["galopant", "galop", "qui galope", "cavalcade"],
    "sautillant": ["sautillant", "rebondissant", "bondissant", "bouncy", "qui rebondit", "joueur"],
    "lancinant": ["lancinant", "entêtant", "qui tourne en rond"],
    "obsédant": ["obsédant", "obsessionnel", "obsession", "qui reste en tête"],
    "répétitif": ["répétitif", "répétition", "qui se répète", "en boucle", "boucle"],
    "pulsé": ["pulsé", "pulsation", "pulsant", "qui pulse", "pompe", "pumping"],
    "chaloupé": ["chaloupé", "balancé", "swingué", "swing", "swingant", "ondulant", "souple"],
    "groovy": ["groovy", "groove", "groovant", "funky", "qui groove", "dansant", "dansante"],
    # énergie
    "calme": ["calme", "tranquille", "doux", "paisible", "zen", "relax", "chill"],
    "posé": ["posé", "tranquille", "pépère", "serein"],
    "lent": ["lent", "lentement", "doucement", "slow", "mou", "langoureux"],
    "tendu": ["tendu", "tension", "sous tension", "crispé"],
    "nerveux": ["nerveux", "vif", "rapide", "vite", "speed", "pressé", "agité", "fébrile"],
    "agressif": ["agressif", "énervé", "vénère", "hargneux", "rageur", "violent", "méchant", "véner"],
    "brutal": ["brutal", "brut", "bourrin", "sauvage", "barbare", "violent"],
    "explosif": ["explosif", "qui explose", "qui pète", "percutant", "punchy", "pêchu", "patate"],
    "frénétique": ["frénétique", "effréné", "fou", "dingue", "endiablé", "hystérique", "à fond"],
    "puissant": ["puissant", "fort", "costaud", "énorme", "massif", "imposant", "patate"],
    "lourd": ["lourd", "pesant", "massif", "heavy", "plombé"],
    "léger": ["léger", "aérien", "délicat", "fin", "subtil", "discret"],
    "retenu": ["retenu", "contenu", "sobre", "pudique", "en retenue"],
    "montant": ["montant", "qui monte", "montée", "build up", "buildup", "crescendo", "progressif"],
    # humeur
    "sombre": ["sombre", "noir", "dark", "obscur", "ténébreux", "sinistre", "lugubre"],
    "mélancolique": ["mélancolique", "mélancolie", "mélanco", "spleen", "à fleur de peau"],
    "triste": ["triste", "tristesse", "peine", "chagrin", "émouvant", "émotion"],
    "déprimé": ["déprimé", "déprimant", "dépressif", "désespéré", "plombant"],
    "nostalgique": ["nostalgique", "nostalgie", "vintage", "rétro", "souvenir", "enfance", "vhs"],
    "inquiétant": ["inquiétant", "étrange", "bizarre", "malsain", "glauque", "creepy", "flippant"],
    "menaçant": ["menaçant", "menace", "dangereux", "hostile"],
    "angoissant": ["angoissant", "angoisse", "anxiogène", "stressant", "stress", "panique"],
    "oppressant": ["oppressant", "étouffant", "écrasant", "claustrophobe"],
    "glacial": ["glacial", "glacé", "gelé", "polaire", "de glace"],
    "froid": ["froid", "clinique", "distant", "métallique froid", "cold"],
    "mystérieux": ["mystérieux", "mystère", "énigmatique", "secret", "occulte", "mystique"],
    "solennel": ["solennel", "grandiose", "majestueux", "épique", "cérémonial", "religieux", "sacré"],
    "martial": ["martial", "militaire", "marche", "guerrier", "soldat"],
    "rêveur": ["rêveur", "rêve", "onirique", "songeur", "dreamy", "contemplatif"],
    "apaisé": ["apaisé", "apaisant", "reposant", "relaxant", "doux", "sérénité"],
    "lumineux": ["lumineux", "lumière", "clair", "solaire", "joyeux", "joie", "gai", "heureux", "positif"],
    "euphorique": ["euphorique", "euphorie", "extatique", "festif", "fête", "hymne", "anthem", "joyeux"],
    # couleur harmonique
    "mineur": ["mineur", "en mineur", "minor"],
    "majeur": ["majeur", "en majeur", "major"],
    "dissonant": ["dissonant", "dissonance", "faux", "qui frotte", "grinçant harmonique"],
    "consonant": ["consonant", "harmonieux", "juste", "propre"],
    "tendu-h": ["triton", "harmonie tendue", "accord tendu", "tension harmonique"],
    "suspendu": ["suspendu", "sus", "sus2", "sus4", "en suspens", "irrésolu"],
    "modal": ["modal", "dorien", "phrygien", "lydien", "mixolydien", "mode"],
    "exotique": ["exotique", "oriental", "arabe", "hijaz", "lointain", "ethnique"],
    "chromatique": ["chromatique", "chromatisme", "demi-tons"],
    "atonal": ["atonal", "sans tonalité", "bruitiste", "bruit", "noise", "expérimental"],
    "ouvert": ["ouvert", "quintes", "large harmonie"],
    "épuré": ["épuré", "simple", "simplissime", "basique", "une note", "deux notes", "sobre"],
    # densité / espace
    "dense": ["dense", "plein", "beaucoup de notes", "touffu", "busy"],
    "chargé": ["chargé", "surchargé", "lourd en notes", "blindé"],
    "rempli": ["rempli", "plein", "complet", "nourri"],
    "aéré": ["aéré", "espacé", "respire", "qui respire", "de l'air", "spacieux"],
    "clairsemé": ["clairsemé", "épars", "rare", "peu de notes", "quelques notes", "sparse"],
    "minimal": ["minimal", "minimaliste", "mini"],
    "dépouillé": ["dépouillé", "nu", "squelettique", "à l'os"],
    "vide": ["vide", "vidé", "silence", "silencieux", "désert"],
    "ample": ["ample", "large", "vaste", "grand", "immense", "spacieux"],
    "planant": ["planant", "plane", "qui plane", "spatial", "cosmique", "space", "atmosphérique", "atmosphère"],
    "flottant": ["flottant", "qui flotte", "en apesanteur", "apesanteur", "vaporeux", "brumeux"],
    "suspendu-t": ["figé", "arrêté", "en suspension", "temps suspendu", "immobile", "statique"],
    "étiré": ["étiré", "long", "longues notes", "tenu", "notes tenues", "étendu"],
    "serré": ["serré", "court", "notes courtes", "staccato", "piqué", "tight"],
    # registre
    "grave": ["grave", "bas", "dans les graves", "graves"],
    "sub": ["sub", "subbass", "sub bass", "infra", "infrabasse", "rumble"],
    "médium": ["médium", "medium", "milieu", "mediums"],
    "aigu": ["aigu", "haut", "dans les aigus", "aigus"],
    "profond": ["profond", "profondeur", "deep", "abyssal", "caverneux"],
    "perché": ["perché", "très haut", "stratosphérique", "cristallin"],
    # son et matière (tendances : le son dépend du synthé)
    "gras": ["gras", "grasse", "fat", "gros", "grosse", "dodu"],
    "épais": ["épais", "épaisse", "chunky", "consistant"],
    "sec": ["sec", "sèche", "sèches", "dry", "mat"],
    "claquant": ["claquant", "qui claque", "claque", "snappy", "punchy"],
    "distordu": ["distordu", "distorsion", "disto", "fuzz", "overdrive"],
    "saturé": ["saturé", "saturation", "satu", "écrasé"],
    "grinçant": ["grinçant", "qui grince", "strident", "crissant"],
    "métallique": ["métallique", "métal", "ferraille", "acier", "tôle", "cloche"],
    "étouffé": ["étouffé", "sourd", "filtré", "muffled", "feutré", "lointain"],
    "feutré": ["feutré", "ouaté", "velours", "moelleux", "cotonneux"],
    "sale": ["sale", "dirty", "lo-fi", "lofi", "crasseux"],
    "crade": ["crade", "cradingue", "dégueu", "pourri", "trash"],
    "rugueux": ["rugueux", "râpeux", "granuleux", "grain", "abrasif"],
    "chaud": ["chaud", "chaleureux", "analogique", "vintage chaud", "warm"],
    "brillant": ["brillant", "scintillant", "étincelant", "bright", "cristallin"],
    "acide": ["acide", "acid", "303", "tb303", "tb-303", "squelchy", "qui couine"],
}
SIMPLE_INFLECT = set(TAGS)  # les mots simples reçoivent leurs formes fléchies

FAMILIES = {
    "techno": ["techno", "techno classique", "detroit", "drumcode", "adam beyer", "cari lekebusch", "lekebusch",
               "hardgroove", "peak time", "minimal techno"],
    "techno-dure": ["techno dure", "hard techno", "techno indus", "techno industrielle", "industrial techno",
                    "techno suédoise", "suédoise", "swedish techno", "berghain", "perc trax", "ancient methods",
                    "sonic groove", "adam x", "orphx", "orphex", "sigha", "rhythmic noise", "schranz"],
    "minimal-dub": ["minimal", "minimale", "dub", "dub techno", "basic channel", "chain reaction", "deep dub", "microhouse"],
    "house": ["house", "tech house", "deep house", "garage", "ukg", "disco", "funk", "funky house", "french touch"],
    "acid": ["acid", "acide", "acid house", "acid techno", "303", "tb303"],
    "ebm": ["ebm", "électro indus", "électro industriel", "electro industrial", "dark electro", "aggrotech",
            "industriel", "indus", "wumpscut", "skinny puppy", "suicide commando", "front 242", "nitzer ebb",
            "dark wave", "darkwave", "body music"],
    "rock-indus": ["rock indus", "rock industriel", "metal indus", "métal indus", "industrial rock", "industrial metal",
                   "nin", "nine inch nails", "ministry", "rammstein", "noise rock", "health", "rock", "métal", "metal",
                   "prog metal", "metal prog"],
    "electro-breaks": ["electro", "électro", "breaks", "breakbeat", "break", "miami bass", "drum and bass", "dnb",
                       "jungle", "uk bass", "trap", "dubstep", "hip hop", "hiphop", "footwork", "drexciya"],
    "trance-rave": ["trance", "rave", "psytrance", "psy", "goa", "hard trance", "progressive", "hardcore", "hymne rave"],
    "ambient": ["ambient", "ambiant", "soundscape", "textures ambient"],
    "idm": ["idm", "boards of canada", "boc", "aphex", "aphex twin", "autechre", "warp", "leftfield", "glitch"],
    "melodique": ["moderat", "apparat", "modeselektor", "électronique mélodique", "mélodique", "melodic techno",
                  "synthwave", "berlin school", "école de berlin", "pop", "quatre accords", "4 accords"],
    "hors-cible": ["jazz", "reggae", "ska", "samba", "bossa", "latin", "latino", "cha cha", "rnb", "ballade",
                   "afro cubain", "marche militaire"],
}
ROLES = {
    "kick": ["kick", "kicks", "grosse caisse", "bass drum", "bd", "boum", "pied"],
    "drums": ["batterie", "batteries", "drums", "beat", "beats", "rythmique", "rythme complet", "boucle de batterie",
              "drum", "breakbeat", "groove de batterie"],
    "perc": ["percu", "percus", "percussion", "percussions", "perc", "hats", "charley", "charleston", "hi hat",
             "hihat", "shaker", "clap", "claps", "rim", "rimshot", "toms", "tom", "cloche", "cowbell", "clic", "clics",
             "ride", "caisse claire", "snare"],
    "bass": ["basse", "basses", "bass", "bassline", "ligne de basse", "sub bass", "303", "rumble"],
    "lead": ["mélodie", "mélodies", "lead", "leads", "ligne", "riff", "riffs", "arpège", "arpèges", "arp", "arpeggio",
             "séquence", "séquences", "sequence", "gimmick", "hook", "pluck", "plucks", "motif", "thème", "solo", "blip", "blips"],
    "chords": ["accord", "accords", "stab", "stabs", "chords", "grille", "grille d'accords", "progression", "piano"],
    "pad": ["nappe", "nappes", "pad", "pads", "drone", "drones", "tenue", "tapis", "strings", "cordes", "chœurs", "choeurs"],
}
MODS = {"2": ["très", "vraiment", "super", "hyper", "ultra", "trop", "carrément", "bien", "extrêmement", "méga"],
        "1.5": ["assez", "plutôt bien"],
        "0.5": ["un peu", "légèrement", "plutôt", "un brin", "à peine", "pas trop", "un poil"]}
NEG = ["pas", "sans", "non", "jamais", "pas de", "pas du tout", "aucun", "aucune", "évite", "éviter"]
TECH = {
    "triplet": ["triolet", "triolets", "ternaire", "en triolets", "12/8"],
    "binary": ["binaire", "doubles croches", "double croche", "croches", "16 pas"],
    "next": ["au hasard", "autre", "encore", "suivant", "une autre", "next"],
}


def main():
    lines = ["# Dictionnaire de MLG Alpha — fabriqué par tools/build_dictionary.py, modifiable à la main.",
             "# Format : <type> <cible>[,<cible>] = forme, forme…   (accents et majuscules ignorés)",
             "# Une même forme peut viser plusieurs étiquettes : « violent » = agressif + brutal.", ""]
    for tag, syns in TAGS.items():
        fs = []
        for s in syns:
            fs += sorted(forms(s)) if " " not in s and "-" not in s and s.isalpha() else [s]
        seen = []
        for f in fs:
            if f not in seen:
                seen.append(f)
        lines.append(f"tag {tag} = " + ", ".join(seen))
    lines.append("")
    for fam, syns in FAMILIES.items():
        lines.append(f"family {fam} = " + ", ".join(syns))
    lines.append("")
    for r, syns in ROLES.items():
        lines.append(f"role {r} = " + ", ".join(syns))
    lines.append("")
    for w, syns in MODS.items():
        lines.append(f"mod {w} = " + ", ".join(syns))
    lines.append("neg = " + ", ".join(NEG))
    for k, syns in TECH.items():
        lines.append(f"tech {k} = " + ", ".join(syns))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(OUT, len(lines), "lignes")


if __name__ == "__main__":
    main()
