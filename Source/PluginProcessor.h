#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include <atomic>
#include "Engine.h"

// MLG Alpha : se charge comme un instrument dans Ableton, ne produit aucun son
// et envoie ses notes en MIDI. Sur une 2e piste : MIDI From = piste MLG Alpha.
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

    // --- Appelés depuis l'interface (thread principal) ---
    void generateNew();
    void mutate();
    void setRhythmLocked (bool);
    void setPitchLocked (bool);
    bool isRhythmLocked() const { return lockRhythm; }
    bool isPitchLocked() const { return lockPitch; }
    void setSeeds (juce::uint32 rhythmSeed, juce::uint32 pitchSeed);
    const mlg::Seeds& getSeeds() const { return seeds; }

    const mlg::Pattern& getDisplayPattern() const { return displayPattern; }
    int getPatternVersion() const { return patternVersion; }
    int getCurrentStep() const { return currentStep.load(); }
    juce::File writeMidiFile() const;

private:
    static juce::AudioProcessorValueTreeState::ParameterLayout createLayout();
    void parameterChanged (const juce::String&, float) override;
    void timerCallback() override;
    void rebuild();
    mlg::Settings readSettings() const;
    float raw (const char* id) const { return apvts.getRawParameterValue (id)->load(); }

    // État de génération (thread principal)
    mlg::Seeds seeds;
    bool lockRhythm = false, lockPitch = false;
    mlg::Pattern displayPattern;
    int patternVersion = 0;
    std::atomic<bool> dirty { true };
    juce::Random seedSource;

    // Passage du motif vers le thread audio
    juce::SpinLock patternLock;
    mlg::Pattern pendingPattern;
    std::atomic<bool> hasPending { false };

    // Thread audio
    mlg::Pattern playPattern;
    double currentSampleRate = 44100.0;
    bool wasPlaying = false;
    double expectedPpq = 0.0;
    bool noteActive = false;
    int activePitch = 0;
    double activeEndPpq = 0.0;
    std::atomic<int> currentStep { -1 };

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (MLGAlphaProcessor)
};
