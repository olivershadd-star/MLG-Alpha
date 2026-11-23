#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include "PluginProcessor.h"
#include <map>

// Piano roll de la ligne en cours (toutes voix), avec la tête de lecture.
class ClipView : public juce::Component
{
public:
    explicit ClipView (MLGAlphaProcessor& p) : proc (p) {}
    void paint (juce::Graphics&) override;

private:
    MLGAlphaProcessor& proc;
};

// Zone à glisser vers une piste Ableton : crée un fichier .mid de la ligne.
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

// Écran de bilan (statistiques d'usage, remise à zéro de l'apprentissage).
class BilanView : public juce::Component
{
public:
    explicit BilanView (MLGAlphaProcessor&);
    void refresh();
    void paint (juce::Graphics&) override;
    void resized() override;

private:
    MLGAlphaProcessor& proc;
    juce::TextEditor text;
    juce::TextButton closeButton, resetButton;
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
    Choice& addChoice (const char* paramId, const juce::String& text, const juce::StringArray& items = {});
    void timerCallback() override;
    void refreshSeedLabels();
    void refreshLine();
    void search (bool again);
    void runTechnical();
    void askWordsAndKeep();
    void setMessage (const juce::String&);

    MLGAlphaProcessor& proc;
    juce::LookAndFeel_V4 laf;

    // Panneau mécanique
    juce::TextButton generateButton, mutateButton, keepMecaButton;
    juce::ToggleButton lockRhythmButton, lockPitchButton, legatoButton;
    std::unique_ptr<juce::AudioProcessorValueTreeState::ButtonAttachment> legatoAttachment;
    juce::Label seedRhythmLabel, seedPitchLabel, seedRhythmValue, seedPitchValue;
    std::map<juce::String, std::unique_ptr<Knob>> knobs;
    std::map<juce::String, std::unique_ptr<Choice>> choices;

    // Panneau texte
    juce::Label normalTitle, techTitle, understood, lineTitle, libraryStatus, techFeedback;
    juce::TextEditor normalInput, techText, techInput;
    juce::TextButton searchButton, againButton, likeButton, dislikeButton, keepButton, bilanButton, techButton;

    ClipView clipView;
    MidiDragZone dragZone;
    BilanView bilan;

    juce::Rectangle<int> mecaArea, textArea, rhythmArea, pitchArea, notesArea;
    int lastVersion = -1;
    bool lastReady = false;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (MLGAlphaEditor)
};
