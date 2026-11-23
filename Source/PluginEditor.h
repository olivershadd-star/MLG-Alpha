#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include "PluginProcessor.h"
#include <map>

// Affichage des pas : une colonne par pas, hauteur = note, intensité = vélocité.
class StepView : public juce::Component
{
public:
    explicit StepView (MLGAlphaProcessor& p) : proc (p) {}
    void paint (juce::Graphics&) override;

private:
    MLGAlphaProcessor& proc;
};

// Zone à glisser vers une piste Ableton : crée un fichier .mid du cycle.
class MidiDragZone : public juce::Component
{
public:
    std::function<juce::File()> makeFile;
    void paint (juce::Graphics&) override;
    void mouseDrag (const juce::MouseEvent&) override;
    void mouseUp (const juce::MouseEvent&) override { dragging = false; repaint(); }

private:
    bool dragging = false;
};

class MLGAlphaEditor : public juce::AudioProcessorEditor, private juce::Timer
{
public:
    explicit MLGAlphaEditor (MLGAlphaProcessor&);
    ~MLGAlphaEditor() override;

    void paint (juce::Graphics&) override;
    void resized() override;

private:
    struct Knob
    {
        juce::Slider slider;
        juce::Label label;
        std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> attachment;
    };

    struct Choice
    {
        juce::ComboBox box;
        juce::Label label;
        std::unique_ptr<juce::AudioProcessorValueTreeState::ComboBoxAttachment> attachment;
    };

    Knob& addKnob (const char* paramId, const juce::String& text);
    Choice& addChoice (const char* paramId, const juce::String& text);
    void timerCallback() override;
    void refreshSeedLabels();

    MLGAlphaProcessor& proc;
    juce::LookAndFeel_V4 laf;

    StepView stepView;
    MidiDragZone dragZone;
    juce::TextButton generateButton, mutateButton;
    juce::ToggleButton lockRhythmButton, lockPitchButton, legatoButton;
    std::unique_ptr<juce::AudioProcessorValueTreeState::ButtonAttachment> legatoAttachment;
    juce::Label seedRhythmLabel, seedPitchLabel, seedRhythmValue, seedPitchValue;

    std::map<juce::String, std::unique_ptr<Knob>> knobs;
    std::map<juce::String, std::unique_ptr<Choice>> choices;

    juce::Rectangle<int> rhythmArea, pitchArea, notesArea;
    int lastVersion = -1, lastStep = -2;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (MLGAlphaEditor)
};
