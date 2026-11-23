#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include <atomic>
#include "Engine.h"
#include "Library.h"
#include "Technical.h"

// MLG Alpha : se charge comme un instrument dans Ableton, ne produit aucun son
// et envoie ses notes en MIDI. Sur une 2e piste : MIDI From = piste MLG Alpha.
//
// Deux sources de lignes :
//   - les potards (moteur paramétrique, seeds) ;
//   - la bibliothèque (motifs classés, tirés au hasard d'après les mots tapés).
class MLGAlphaProcessor : public juce::AudioProcessor,
                         private juce::AudioProcessorValueTreeState::Listener,
                         private juce::Timer
{
public:
    MLGAlphaProcessor();
    ~MLGAlphaProcessor() override;

    void prepareToPlay (double sampleRate, int samplesPerBlock) override;
    void releaseResources() override {}
    bool isBusesLayoutSupported (const BusesLayout&) const override;
    void processBlock (juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    using AudioProcessor::processBlock;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }

    const juce::String getName() const override { return JucePlugin_Name; }
    bool acceptsMidi() const override { return true; }
    bool producesMidi() const override { return true; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 0.0; }

    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram (int) override {}
    const juce::String getProgramName (int) override { return {}; }
    void changeProgramName (int, const juce::String&) override {}

    void getStateInformation (juce::MemoryBlock&) override;
    void setStateInformation (const void*, int) override;

    juce::AudioProcessorValueTreeState apvts;

    // --- Panneau mécanique (thread principal) ---
    void generateNew();
    void mutate();
    void setRhythmLocked (bool);
    void setPitchLocked (bool);
    bool isRhythmLocked() const { return lockRhythm; }
    bool isPitchLocked() const { return lockPitch; }
    void setSeeds (juce::uint32 rhythmSeed, juce::uint32 pitchSeed);
    const mlg::Seeds& getSeeds() const { return seeds; }

    // --- Panneau texte ---
    juce::String drawFromText (const juce::String& words);   // renvoie ce qui a été compris
    juce::String drawAgain();
    juce::String applyTechnical (const juce::String& command);
    juce::String like (bool up);
    juce::String keep (const juce::String& words);
    juce::String learningReport() const { return library->report(); }
    void resetLearning() { library->resetLearning(); }
    bool libraryReady() const { return library->isReady(); }
    int librarySize() const { return (int) library->patterns().size(); }

    // --- Affichage ---
    const mlg::Clip& getDisplayClip() const { return displayClip; }
    const mlg::LineInfo& getLineInfo() const { return info; }
    juce::String getTechnicalText() const;
    int getVersion() const { return version; }
    double getPlayPosition() const { return playPos.load(); }   // en noires dans le clip, -1 à l'arrêt
    bool isLibraryLine() const { return fromLibrary; }
    int currentRoot() const { return (int) raw ("root"); }
    juce::File writeMidiFile();

    // pour les tests
    std::function<void()> onLineChanged;

private:
    static juce::AudioProcessorValueTreeState::ParameterLayout createLayout();
    void parameterChanged (const juce::String&, float) override;
    void timerCallback() override;
    void rebuild();
    void setLibraryLine (int index);
    void refreshLibraryClip();
    void publish (const mlg::Clip&);
    void placeKnobs (const mlg::Clip&);
    void setParam (const juce::String& id, float value);
    void closeListening();
    void fallbackFromTags (const mlg::Query&);
    juce::String settingsString() const;
    mlg::Settings readSettings() const;
    float raw (const char* id) const { return apvts.getRawParameterValue (id)->load(); }

    juce::SharedResourcePointer<mlg::Library> library;

    // État (thread principal)
    mlg::Seeds seeds;
    bool lockRhythm = false, lockPitch = false;
    bool fromLibrary = false, placing = false;
    int libIndex = -1;
    juce::String pendingLibId;
    mlg::Clip displayClip, kickCompanion;
    bool hasKick = false;
    mlg::LineInfo info;
    mlg::Query lastQuery;
    int version = 0;
    std::atomic<bool> dirty { true }, libDirty { false };
    juce::Random rng;
    double shownSince = 0.0;

    // Passage du clip vers le thread audio
    juce::SpinLock clipLock;
    mlg::Clip pendingClip;
    std::atomic<bool> hasPending { false };

    // Thread audio
    void render (const mlg::Clip&, double from, double to, double blockPpq, double ppqPerSample, int numSamples, juce::MidiBuffer&);
    void releaseDue (double t, double blockPpq, double ppqPerSample, int numSamples, juce::MidiBuffer&);
    void allNotesOff (juce::MidiBuffer&);
    mlg::Clip playClip, queuedClip;
    bool hasQueued = false;
    double currentSampleRate = 44100.0;
    bool wasPlaying = false;
    double expectedPpq = 0.0;
    struct Active { int pitch; double end; };
    std::vector<Active> active;
    std::atomic<double> playPos { -1.0 };

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (MLGAlphaProcessor)
};
