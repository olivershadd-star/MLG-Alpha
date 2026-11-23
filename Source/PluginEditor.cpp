#include "PluginEditor.h"

using midilines::fr;

namespace colours
{
const juce::Colour background { 0xff121418 };
const juce::Colour panel      { 0xff1b1f26 };
const juce::Colour cell       { 0xff242a33 };
const juce::Colour cellBeat   { 0xff2c3440 };
const juce::Colour accent     { 0xff35d0ba };
const juce::Colour accent2    { 0xffff8a3d };
const juce::Colour text       { 0xffd8dee9 };
const juce::Colour dim        { 0xff7a8494 };
}

// ---------------------------------------------------------------------------

void StepView::paint (juce::Graphics& g)
{
    const auto& pat = proc.getDisplayPattern();
    const int n = juce::jmax (1, pat.numSteps);
    const int lo = juce::jmin ((int) proc.apvts.getRawParameterValue ("lowNote")->load(),
                               (int) proc.apvts.getRawParameterValue ("highNote")->load());
    const int hi = juce::jmax ((int) proc.apvts.getRawParameterValue ("lowNote")->load(),
                               (int) proc.apvts.getRawParameterValue ("highNote")->load());
    const int current = proc.getCurrentStep();

    auto bounds = getLocalBounds().toFloat();
    g.setColour (colours::panel);
    g.fillRoundedRectangle (bounds, 6.0f);

    const auto inner = bounds.reduced (6.0f);
    const float w = inner.getWidth() / (float) n;

    for (int i = 0; i < n; ++i)
    {
        auto r = juce::Rectangle<float> (inner.getX() + i * w, inner.getY(), w, inner.getHeight()).reduced (1.0f, 0.0f);
        g.setColour ((i % 4) == 0 ? colours::cellBeat : colours::cell);
        g.fillRoundedRectangle (r, 2.0f);

        const auto& st = pat.steps[(size_t) i];
        if (st.on)
        {
            const float frac = hi > lo ? (float) (st.pitch - lo) / (float) (hi - lo) : 0.5f;
            const float h = juce::jmax (6.0f, (0.12f + 0.80f * frac) * (r.getHeight() - 16.0f));
            auto bar = r.withTop (r.getBottom() - h).reduced (1.0f, 0.0f);
            g.setColour (colours::accent.withAlpha (0.35f + 0.65f * (float) st.velocity / 127.0f));
            g.fillRoundedRectangle (bar, 2.0f);

            if (w >= 24.0f)
            {
                g.setColour (colours::text);
                g.setFont (juce::FontOptions (10.0f));
                g.drawText (midilines::noteName (st.pitch), r.withHeight (14.0f), juce::Justification::centred);
            }
        }

        if (i == current)
        {
            g.setColour (colours::accent2);
            g.drawRoundedRectangle (r, 2.0f, 2.0f);
        }
    }
}

// ---------------------------------------------------------------------------

void MidiDragZone::paint (juce::Graphics& g)
{
    auto r = getLocalBounds().toFloat().reduced (1.0f);
    g.setColour (dragging ? colours::accent.withAlpha (0.25f) : colours::panel);
    g.fillRoundedRectangle (r, 6.0f);
    g.setColour (colours::accent);
    g.drawRoundedRectangle (r, 6.0f, 1.5f);
    g.setFont (juce::FontOptions (13.0f));
    g.drawFittedText (fr ("Glisser le clip .mid"), getLocalBounds(), juce::Justification::centred, 2);
}

void MidiDragZone::mouseDrag (const juce::MouseEvent& e)
{
    if (dragging || e.getDistanceFromDragStart() < 4 || ! makeFile)
        return;

    dragging = true;
    repaint();
    const auto file = makeFile();
    if (file.existsAsFile())
        juce::DragAndDropContainer::performExternalDragDropOfFiles ({ file.getFullPathName() }, false, this,
                                                                    [this] { dragging = false; repaint(); });
}

// ---------------------------------------------------------------------------

MidiLinesEditor::MidiLinesEditor (MidiLinesProcessor& p)
    : AudioProcessorEditor (&p), proc (p), stepView (p)
{
    laf.setColour (juce::Slider::rotarySliderFillColourId, colours::accent);
    laf.setColour (juce::Slider::rotarySliderOutlineColourId, colours::cell);
    laf.setColour (juce::Slider::thumbColourId, colours::accent);
    laf.setColour (juce::Slider::textBoxTextColourId, colours::text);
    laf.setColour (juce::Slider::textBoxOutlineColourId, juce::Colours::transparentBlack);
    laf.setColour (juce::Label::textColourId, colours::text);
    laf.setColour (juce::ComboBox::backgroundColourId, colours::cell);
    laf.setColour (juce::ComboBox::outlineColourId, colours::cellBeat);
    laf.setColour (juce::ComboBox::textColourId, colours::text);
    laf.setColour (juce::PopupMenu::backgroundColourId, colours::panel);
    laf.setColour (juce::TextButton::buttonColourId, colours::cell);
    laf.setColour (juce::TextButton::textColourOffId, colours::text);
    laf.setColour (juce::ToggleButton::textColourId, colours::text);
    laf.setColour (juce::ToggleButton::tickColourId, colours::accent);
    setLookAndFeel (&laf);

    addAndMakeVisible (stepView);

    dragZone.makeFile = [this] { return proc.writeMidiFile(); };
    addAndMakeVisible (dragZone);

    generateButton.setButtonText (fr ("GÉNÉRER"));
    generateButton.setColour (juce::TextButton::buttonColourId, colours::accent.darker (0.4f));
    generateButton.onClick = [this] { proc.generateNew(); };
    addAndMakeVisible (generateButton);

    mutateButton.setButtonText (fr ("MUTER"));
    mutateButton.onClick = [this] { proc.mutate(); };
    addAndMakeVisible (mutateButton);

    lockRhythmButton.setButtonText (fr ("Verrou rythme"));
    lockRhythmButton.setToggleState (proc.isRhythmLocked(), juce::dontSendNotification);
    lockRhythmButton.onClick = [this] { proc.setRhythmLocked (lockRhythmButton.getToggleState()); };
    addAndMakeVisible (lockRhythmButton);

    lockPitchButton.setButtonText (fr ("Verrou hauteurs"));
    lockPitchButton.setToggleState (proc.isPitchLocked(), juce::dontSendNotification);
    lockPitchButton.onClick = [this] { proc.setPitchLocked (lockPitchButton.getToggleState()); };
    addAndMakeVisible (lockPitchButton);

    for (auto* l : { &seedRhythmLabel, &seedPitchLabel })
    {
        l->setColour (juce::Label::textColourId, colours::dim);
        l->setFont (juce::FontOptions (11.0f));
        addAndMakeVisible (*l);
    }
    seedRhythmLabel.setText (fr ("Seed rythme"), juce::dontSendNotification);
    seedPitchLabel.setText (fr ("Seed hauteurs"), juce::dontSendNotification);

    for (auto* l : { &seedRhythmValue, &seedPitchValue })
    {
        l->setEditable (false, true, false);
        l->setColour (juce::Label::backgroundColourId, colours::cell);
        l->setFont (juce::FontOptions (12.0f));
        l->setJustificationType (juce::Justification::centred);
        l->setTooltip (fr ("Double-clic pour saisir une seed"));
        addAndMakeVisible (*l);
    }
    const auto applySeeds = [this]
    {
        const auto r = (juce::uint32) seedRhythmValue.getText().getLargeIntValue();
        const auto pp = (juce::uint32) seedPitchValue.getText().getLargeIntValue();
        proc.setSeeds (r, pp);
    };
    seedRhythmValue.onTextChange = applySeeds;
    seedPitchValue.onTextChange = applySeeds;

    // Rythme
    addChoice ("rhythmMode", fr ("Moteur"));
    addKnob ("steps", fr ("Pas"));
    addChoice ("division", fr ("Division"));
    addKnob ("density", fr ("Densité"));
    addKnob ("pulses", fr ("Impulsions"));
    addKnob ("rotation", fr ("Rotation"));
    addKnob ("swing", fr ("Swing"));

    // Hauteurs
    addChoice ("root", fr ("Tonique"));
    addChoice ("scale", fr ("Gamme"));
    addKnob ("lowNote", fr ("Note basse"));
    addKnob ("highNote", fr ("Note haute"));
    addKnob ("maxJump", fr ("Écart max"));

    // Notes
    addKnob ("lenMin", fr ("Durée min"));
    addKnob ("lenMax", fr ("Durée max"));
    addKnob ("velMin", fr ("Vél. min"));
    addKnob ("velMax", fr ("Vél. max"));
    addKnob ("accent", fr ("Accent"));
    legatoButton.setButtonText ("Legato");
    legatoAttachment = std::make_unique<juce::AudioProcessorValueTreeState::ButtonAttachment> (proc.apvts, "legato", legatoButton);
    addAndMakeVisible (legatoButton);

    refreshSeedLabels();
    setSize (980, 560);
    startTimerHz (30);
}

MidiLinesEditor::~MidiLinesEditor()
{
    stopTimer();
    setLookAndFeel (nullptr);
}

MidiLinesEditor::Knob& MidiLinesEditor::addKnob (const char* paramId, const juce::String& text)
{
    auto k = std::make_unique<Knob>();
    k->slider.setSliderStyle (juce::Slider::RotaryHorizontalVerticalDrag);
    k->slider.setTextBoxStyle (juce::Slider::TextBoxBelow, false, 64, 16);
    k->label.setText (text, juce::dontSendNotification);
    k->label.setJustificationType (juce::Justification::centred);
    k->label.setFont (juce::FontOptions (12.0f));
    k->attachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment> (proc.apvts, paramId, k->slider);
    addAndMakeVisible (k->slider);
    addAndMakeVisible (k->label);
    auto& ref = *k;
    knobs[paramId] = std::move (k);
    return ref;
}

MidiLinesEditor::Choice& MidiLinesEditor::addChoice (const char* paramId, const juce::String& text)
{
    auto c = std::make_unique<Choice>();
    if (auto* param = dynamic_cast<juce::AudioParameterChoice*> (proc.apvts.getParameter (paramId)))
        c->box.addItemList (param->choices, 1);
    c->label.setText (text, juce::dontSendNotification);
    c->label.setJustificationType (juce::Justification::centred);
    c->label.setFont (juce::FontOptions (12.0f));
    c->attachment = std::make_unique<juce::AudioProcessorValueTreeState::ComboBoxAttachment> (proc.apvts, paramId, c->box);
    addAndMakeVisible (c->box);
    addAndMakeVisible (c->label);
    auto& ref = *c;
    choices[paramId] = std::move (c);
    return ref;
}

void MidiLinesEditor::refreshSeedLabels()
{
    const auto& s = proc.getSeeds();
    seedRhythmValue.setText (juce::String (s.rhythm), juce::dontSendNotification);
    seedPitchValue.setText (juce::String (s.pitch), juce::dontSendNotification);
}

void MidiLinesEditor::timerCallback()
{
    // Réglages propres au moteur rythmique choisi
    const bool euclid = proc.apvts.getRawParameterValue ("rhythmMode")->load() > 0.5f;
    knobs["density"]->slider.setEnabled (! euclid);
    knobs["pulses"]->slider.setEnabled (euclid);
    knobs["rotation"]->slider.setEnabled (euclid);

    if (proc.getPatternVersion() != lastVersion)
    {
        lastVersion = proc.getPatternVersion();
        if (! seedRhythmValue.isBeingEdited() && ! seedPitchValue.isBeingEdited())
            refreshSeedLabels();
        stepView.repaint();
    }

    if (proc.getCurrentStep() != lastStep)
    {
        lastStep = proc.getCurrentStep();
        stepView.repaint();
    }
}

void MidiLinesEditor::paint (juce::Graphics& g)
{
    g.fillAll (colours::background);

    g.setColour (colours::accent);
    g.setFont (juce::FontOptions (22.0f, juce::Font::bold));
    g.drawText ("MIDI LINES", 16, 10, 140, 30, juce::Justification::centredLeft);
    g.setColour (colours::dim);
    g.setFont (juce::FontOptions (11.0f));
    g.drawText ("ANKS Labs", 16, 36, 140, 14, juce::Justification::centredLeft);

    const auto drawSection = [&g] (juce::Rectangle<int> r, const juce::String& title)
    {
        g.setColour (colours::panel);
        g.fillRoundedRectangle (r.toFloat(), 6.0f);
        g.setColour (colours::accent2);
        g.setFont (juce::FontOptions (12.0f, juce::Font::bold));
        g.drawText (title, r.removeFromTop (22).reduced (10, 0), juce::Justification::centredLeft);
    };
    drawSection (rhythmArea, fr ("RYTHME"));
    drawSection (pitchArea, fr ("HAUTEURS"));
    drawSection (notesArea, fr ("NOTES"));
}

void MidiLinesEditor::resized()
{
    auto r = getLocalBounds().reduced (12);

    // Barre du haut
    auto top = r.removeFromTop (46);
    top.removeFromLeft (150);
    generateButton.setBounds (top.removeFromLeft (120).reduced (2, 6));
    mutateButton.setBounds (top.removeFromLeft (100).reduced (2, 6));
    top.removeFromLeft (10);
    lockRhythmButton.setBounds (top.removeFromLeft (120).reduced (2, 8));
    lockPitchButton.setBounds (top.removeFromLeft (130).reduced (2, 8));
    dragZone.setBounds (top.removeFromRight (150).reduced (2, 4));
    top.removeFromRight (8);
    auto seedsArea = top;
    auto sr = seedsArea.removeFromLeft (seedsArea.getWidth() / 2).reduced (4, 2);
    seedRhythmLabel.setBounds (sr.removeFromTop (14));
    seedRhythmValue.setBounds (sr.reduced (0, 1));
    auto spa = seedsArea.reduced (4, 2);
    seedPitchLabel.setBounds (spa.removeFromTop (14));
    seedPitchValue.setBounds (spa.reduced (0, 1));

    r.removeFromTop (8);
    stepView.setBounds (r.removeFromTop (170));
    r.removeFromTop (10);

    const int w = r.getWidth();
    rhythmArea = r.removeFromLeft (w * 4 / 10);
    r.removeFromLeft (8);
    pitchArea = r.removeFromLeft (r.getWidth() / 2 - 4);
    r.removeFromLeft (8);
    notesArea = r;

    // Chaque case = étiquette + contrôle ; 2 rangées par section.
    enum class Kind { knob, combo, toggle, empty };
    struct Slot { Kind kind; juce::Component* label; juce::Component* widget; };

    const auto layout = [] (juce::Rectangle<int> area, int cols, const std::vector<Slot>& slots)
    {
        area.removeFromTop (22);
        area = area.reduced (6, 4);
        const int cw = area.getWidth() / cols;
        const int rh = area.getHeight() / 2;
        for (int i = 0; i < (int) slots.size(); ++i)
        {
            const auto& s = slots[(size_t) i];
            auto cell = juce::Rectangle<int> (area.getX() + (i % cols) * cw, area.getY() + (i / cols) * rh, cw, rh).reduced (2);
            switch (s.kind)
            {
                case Kind::knob:   s.label->setBounds (cell.removeFromTop (16)); s.widget->setBounds (cell); break;
                case Kind::combo:  s.label->setBounds (cell.removeFromTop (16)); s.widget->setBounds (cell.withSizeKeepingCentre (cell.getWidth() - 4, 24)); break;
                case Kind::toggle: s.widget->setBounds (cell.withSizeKeepingCentre (cell.getWidth() - 8, 24)); break;
                case Kind::empty:  break;
            }
        }
    };

    const auto k = [this] (const char* id) { return Slot { Kind::knob, &knobs[id]->label, &knobs[id]->slider }; };
    const auto c = [this] (const char* id) { return Slot { Kind::combo, &choices[id]->label, &choices[id]->box }; };
    const Slot none { Kind::empty, nullptr, nullptr };

    layout (rhythmArea, 4, { c ("rhythmMode"), c ("division"), k ("steps"), k ("swing"),
                             k ("density"), k ("pulses"), k ("rotation"), none });
    layout (pitchArea, 3, { c ("root"), c ("scale"), k ("maxJump"),
                            k ("lowNote"), k ("highNote"), none });
    layout (notesArea, 3, { k ("lenMin"), k ("lenMax"), Slot { Kind::toggle, nullptr, &legatoButton },
                            k ("velMin"), k ("velMax"), k ("accent") });
}
