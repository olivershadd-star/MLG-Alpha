#pragma once

#include "Library.h"

// Vocabulaire technique : fiche de la ligne en cours, réglages équivalents des potards,
// et commandes tapées (« 2 mesures, division 1/16 »).
namespace mlg
{
struct LineInfo
{
    juce::String source;     // « Potards », « Bibliothèque », « Bibliothèque perso »
    juce::String id, name;
    int role = -1, family = -1;
    std::vector<std::pair<int, int>> tags;
};

juce::String describe (const Clip&, const LineInfo&, int root);

// Réglages des potards qui donnent une ligne du même genre (valeurs « réelles » des paramètres).
std::map<juce::String, float> equivalentSettings (const Clip&, int root);

struct Command
{
    std::map<juce::String, float> params;
    juce::StringArray done, unknown;
    bool generate = false, mutate = false;
};

// stepsPerBar : pas par mesure de la division actuelle (pour « 2 mesures »)
Command parseTechnical (const juce::String& text, int currentDivision);

int parseNoteName (const juce::String& token);   // « c3 », « la2 », « f#1 » -> note MIDI (C3 = 60), -1 sinon
} // namespace mlg
