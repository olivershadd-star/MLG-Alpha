// Vérifie la bibliothèque, le traducteur, le tirage, les empreintes et la fiche technique.
#include "../Source/Library.h"
#include "../Source/Technical.h"
#include <iostream>

using namespace mlg;

static int failures = 0;
#define CHECK(cond) do { if (! (cond)) { std::cerr << "ECHEC: " #cond " (ligne " << __LINE__ << ")\n"; ++failures; } } while (0)

int main()
{
    Library lib;
    const auto t0 = juce::Time::getMillisecondCounterHiRes();
    while (! lib.isReady()) juce::Thread::sleep (20);
    std::cout << "Chargement : " << (int) lib.patterns().size() << " motifs en "
              << (int) (juce::Time::getMillisecondCounterHiRes() - t0) << " ms\n";
    CHECK (lib.patterns().size() > 30000);

    // Empreintes cohérentes : un motif converti en clip retrouve sa propre empreinte
    int same = 0, tested = 0;
    for (size_t i = 0; i < lib.patterns().size(); i += 97)
    {
        const auto& p = lib.patterns()[i];
        const int root = (int) (i % 12);
        const auto clip = lib.toClip (p, root, Library::defaultCentre (p.role));
        ++tested;
        same += Library::fingerprintOf (clip, root) == p.fingerprint ? 1 : 0;
    }
    std::cout << "Empreintes retrouvees : " << same << " / " << tested << "\n";
    CHECK (same >= tested * 95 / 100);

    // Traducteur
    const auto& tr = lib.translator();
    const char* phrases[] = { "basse sombre et roulante", "nappe mélancolique aérée", "percu sèche EBM",
                              "kick techno très lourd", "arpège triste en triolets, 2 mesures",
                              "une ligne pas trop dense façon boards of canada", "truc vénère et saturé style nine inch nails",
                              "accords dub chauds", "mélodie lumineuse trance" };
    juce::Random rng (42);
    for (auto* ph : phrases)
    {
        const auto q = tr.parse (juce::String::fromUTF8 (ph));
        CHECK (! q.empty());
        std::cout << "\n« " << ph << " »\n  " << q.summary() << "\n";
        for (int k = 0; k < 3; ++k)
        {
            const int idx = lib.draw (q, nullptr, rng);
            if (idx < 0) { std::cout << "  -> rien (" << lib.lastDrawNote() << ")\n"; break; }
            const auto& p = lib.patterns()[(size_t) idx];
            juce::StringArray tags;
            for (auto& [t, c] : p.tags) tags.add (tagKeys()[t]);
            std::cout << "  -> " << p.name << " [" << roleKeys()[p.role] << ", " << familyKeys()[p.family] << "] "
                      << tags.joinIntoString (",") << "\n";
            if (! q.roles.empty()) CHECK (q.roles.count (p.role) == 1);
            if (q.triplet) CHECK (p.steps == 12 || p.steps == 24);
            lib.noteProposed (p.id);
        }
    }

    // Tirage sans mots : jamais hors cible
    {
        Query q;
        for (int k = 0; k < 200; ++k)
        {
            const int idx = lib.draw (q, nullptr, rng);
            CHECK (idx >= 0);
            if (idx >= 0) CHECK (lib.patterns()[(size_t) idx].family != familyIndex ("hors-cible") || lib.patterns()[(size_t) idx].personal);
        }
    }

    // Fiche technique et réglages équivalents
    {
        auto q = tr.parse ("basse acid");
        const int idx = lib.draw (q, nullptr, rng);
        CHECK (idx >= 0);
        const auto& p = lib.patterns()[(size_t) idx];
        const auto clip = lib.toClip (p, 9, Library::defaultCentre (p.role));
        LineInfo info { "Bibliothèque", p.id, p.name, p.role, p.family, p.tags };
        std::cout << "\n" << describe (clip, info, 9) << "\n";
        const auto s = equivalentSettings (clip, 9);
        CHECK (s.count ("steps") && s.count ("density") && s.count ("lowNote"));
        juce::StringArray kv;
        for (auto& [k, v] : s) kv.add (k + "=" + juce::String (v));
        std::cout << "Potards : " << kv.joinIntoString (" ") << "\n";
    }

    // Commandes techniques
    {
        auto c = parseTechnical (juce::String::fromUTF8 ("2 mesures, division 1/16, tonique la, gamme dorien, notes C1 à C3, legato, euclidien 5"), 3);
        std::cout << "\nCommande : " << c.done.joinIntoString (" | ") << "  inconnus : " << c.unknown.joinIntoString (" ") << "\n";
        CHECK (c.params["steps"] == 32.0f);
        CHECK (c.params["root"] == 9.0f);
        CHECK (c.params["scale"] == 2.0f);
        CHECK (c.params["lowNote"] == 36.0f && c.params["highNote"] == 60.0f);
        CHECK (c.params["legato"] == 1.0f);
        CHECK (c.params["pulses"] == 5.0f && c.params["rhythmMode"] == 1.0f);
        auto t = parseTechnical ("triolets 4 mesures", 3);
        CHECK (t.params["division"] == 4.0f && t.params["steps"] == 96.0f);
    }

    // Sauvegarde perso : doublon détecté
    {
        const auto& p = lib.patterns()[100];
        const auto clip = lib.toClip (p, 2, Library::defaultCentre (p.role));
        CHECK (lib.findDuplicate (Library::fingerprintOf (clip, 2)) != nullptr);
    }

    std::cout << "\n" << lib.report().substring (0, 600) << "\n";
    std::cout << (failures == 0 ? "OK bibliotheque\n" : "ECHECS bibliotheque\n");
    return failures ? 1 : 0;
}
