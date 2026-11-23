#pragma once

#include "Engine.h"
#include <atomic>
#include <map>
#include <set>
#include <vector>

// Bibliothèque de MLG Alpha : motifs classés (tools/classify.py), bibliothèque perso,
// apprentissage par likes et statistiques d'usage.
namespace mlg
{
enum Role { roleKick, roleDrums, rolePerc, roleBass, roleLead, roleChords, rolePad, numRoles };
const juce::StringArray& roleKeys();     // kick, drums…
const juce::StringArray& roleNames();    // en français
const juce::StringArray& familyKeys();   // techno, techno-dure… hors-cible
const juce::StringArray& familyNames();
const juce::StringArray& tagKeys();      // les 100 étiquettes (clés)
juce::String tagLabel (const juce::String& key);   // « tendu-h » -> « tendu (harmonie) »
int familyIndex (const juce::String& key);

struct LibEvent { int t, l, p, v; };     // t et l en 1/12 de pas ; p = intervalle depuis la tonique ou note GM

struct LibPattern
{
    juce::String id, name, words;        // words : mots de l'utilisateur (bibliothèque perso)
    int role = roleLead, family = 0, bars = 1, steps = 16;
    bool drums = false, personal = false;
    std::vector<std::pair<int, int>> tags;   // (index d'étiquette, confiance 1..9)
    std::vector<LibEvent> events;
    juce::String settings;               // réglages des potards + seeds (lignes gardées depuis les potards)
    juce::uint64 fingerprint = 0;
    float meanPitch = 0.0f;
};

// Ce que le traducteur a compris d'une phrase.
struct Query
{
    std::map<int, float> tags;           // étiquette -> poids (négatif = « pas … »)
    std::set<int> families, roles;
    bool triplet = false, binary = false;
    int bars = 0;                         // 0 = indifférent
    juce::StringArray understood, unknown;
    bool empty() const { return tags.empty() && families.empty() && roles.empty() && ! triplet && ! binary && bars == 0; }
    juce::String summary() const;
};

class Translator
{
public:
    void load (const juce::String& dictionaryText);
    Query parse (const juce::String& text) const;
    static juce::String normalise (const juce::String&);   // minuscules, sans accents ni ponctuation

private:
    std::map<juce::String, std::vector<std::pair<juce::String, juce::String>>> phrases;   // forme -> (type, cible)
    int maxWords = 1;
};

struct Stats { int proposed = 0, skipped = 0, listened = 0, liked = 0, disliked = 0, kept = 0; };

class Library
{
public:
    Library();
    ~Library();

    bool isReady() const { return ready.load(); }
    const std::vector<LibPattern>& patterns() const { return all; }
    const Translator& translator() const { return dict; }

    // Tirage : renvoie l'index du motif choisi, ou -1 si rien ne correspond.
    int draw (const Query&, const Clip* kickToAnswer, juce::Random&);
    juce::String lastDrawNote() const { return lastNote; }   // explication si le tirage a dû élargir la recherche

    // Conversion en clip jouable : tonique 0..11, centre de registre (note MIDI)
    Clip toClip (const LibPattern&, int root, int registerCentre) const;
    static int defaultCentre (int role);

    // Empreinte (rythme + notes relatives à la tonique, octave ramenée) et recherche de doublon
    static juce::uint64 fingerprintOf (const Clip&, int root);
    const LibPattern* findDuplicate (juce::uint64 fp) const;

    // Bibliothèque perso
    juce::String savePersonal (const Clip&, int root, const juce::String& words, const Query& wordsMeaning,
                               int role, int family, const juce::String& settings);

    // Apprentissage
    void like (const juce::String& id, const Query& context, bool up);
    void resetLearning();
    float tagDelta (const juce::String& id, int tag) const;

    // Statistiques
    void noteProposed (const juce::String& id);
    void noteListenTime (const juce::String& id, double seconds);
    void noteKept (const juce::String& id);
    juce::String report() const;
    const Stats* statsFor (const juce::String& id) const;

    static juce::File dataFolder();

private:
    void loadAll();
    void parseCompiled (const juce::String& text, bool personal);
    void loadLearning();
    void saveLearning() const;
    void saveStats() const;
    void index (LibPattern&);

    std::vector<LibPattern> all;
    std::map<juce::uint64, int> byFingerprint;
    std::map<juce::String, int> byId;
    Translator dict;
    std::atomic<bool> ready { false };
    std::unique_ptr<juce::Thread> loader;

    std::map<juce::String, std::map<int, float>> deltas;   // id -> étiquette -> renfort
    std::map<juce::String, int> likeScore;                  // id -> likes - dislikes
    std::map<juce::String, Stats> stats;
    std::vector<juce::String> recent;
    juce::String lastNote;
    juce::CriticalSection lock;
};
} // namespace mlg
