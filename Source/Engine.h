#pragma once

#include <juce_core/juce_core.h>
#include <juce_audio_basics/juce_audio_basics.h>
#include <array>

// Moteur de génération LINEGEN.
// Deux couches indépendantes :
//   - rythme  : quand une note joue (moteur Aléatoire ou Euclidien)
//   - hauteurs : quelle note joue (moteur Aléatoire contraint)
// La génération est déterministe : mêmes réglages + mêmes seeds = même ligne.

namespace linegen
{
inline juce::String fr (const char* utf8) { return juce::String::fromUTF8 (utf8); }

constexpr int kMaxSteps = 64;
constexpr int kMidiChannel = 1;

struct Step
{
    bool on = false;
    int pitch = 60;
    int velocity = 100;
    double lengthSteps = 1.0;   // durée exprimée en pas
};

struct Pattern
{
    int numSteps = 16;
    double stepPpq = 0.25;      // durée d'un pas en noires (1/16 = 0.25)
    double swing = 0.0;         // 0..1 : les pas impairs sont retardés de swing * 1/2 pas
    bool legato = false;
    std::array<Step, kMaxSteps> steps {};

    double stepStartPpq (int s) const { return s * stepPpq + ((s & 1) ? swing * 0.5 * stepPpq : 0.0); }
    double cyclePpq() const { return numSteps * stepPpq; }
};

enum class RhythmMode { random = 0, euclidean = 1 };

struct Settings
{
    RhythmMode rhythmMode = RhythmMode::random;
    int numSteps = 16;
    int division = 3;
    double density = 0.5;       // 0..1
    int pulses = 5;
    int rotation = 0;
    double swing = 0.0;         // 0..1

    int root = 0;               // 0 = C
    int scale = 1;
    int lowNote = 48;
    int highNote = 67;
    int maxJump = 3;            // en degrés de gamme

    double lenMin = 0.5;        // en pas
    double lenMax = 1.0;
    bool legato = false;
    int velMin = 80;
    int velMax = 110;
    int accent = 15;
};

struct Seeds
{
    juce::uint32 rhythm = 1;
    juce::uint32 pitch = 1;
    int rhythmMutations = 0;
    int pitchMutations = 0;
};

juce::StringArray scaleNames();
juce::StringArray divisionNames();
juce::StringArray rootNames();
double divisionToPpq (int division);
juce::String noteName (int midiNote);      // convention Ableton : 60 = C3

Pattern generate (const Settings&, const Seeds&);
juce::MidiFile toMidiFile (const Pattern&);
} // namespace linegen
