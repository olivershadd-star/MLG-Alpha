#include "PluginEditor.h"

using mlg::fr;

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

void ClipView::paint (juce::Graphics& g)
{
    const auto& c = proc.getDisplayClip();
    auto bounds = getLocalBounds().toFloat();
    g.setColour (colours::panel);
    g.fillRoundedRectangle (bounds, 6.0f);
    const auto inner = bounds.reduced (8.0f);
    const double L = juce::jmax (0.25, c.lengthPpq);
    const auto xOf = [&] (double ppq) { return inner.getX() + (float) (ppq / L) * inner.getWidth(); };

    // grille : pas, temps, mesures
    const int steps = juce::jmax (1, (int) std::round (L / c.stepPpq));
    for (int s = 0; s <= steps; ++s)
    {
        const double t = s * c.stepPpq;
        const bool bar = std::abs (std::fmod (t + 1e-6, 4.0)) < 1e-3;
        const bool beat = std::abs (std::fmod (t + 1e-6, 1.0)) < 1e-3;
        if (! beat && steps > 64) continue;
        g.setColour (bar ? colours::dim.withAlpha (0.6f) : beat ? colours::cellBeat.brighter (0.2f) : colours::cell);
        g.drawVerticalLine ((int) xOf (t), inner.getY(), inner.getBottom());
    }

    if (c.notes.empty()) return;
    int lo = 127, hi = 0;
    for (auto& n : c.notes) { lo = juce::jmin (lo, n.pitch); hi = juce::jmax (hi, n.pitch); }
    lo -= 1; hi += 1;
    const float rowH = inner.getHeight() / (float) (hi - lo + 1);

    for (auto& n : c.notes)
    {
        const float x = xOf (n.start), w = juce::jmax (2.0f, xOf (juce::jmin (L, n.start + n.length)) - x - 1.0f);
        const float y = inner.getBottom() - (float) (n.pitch - lo + 1) * rowH;
        g.setColour ((c.drums ? colours::accent2 : colours::accent).withAlpha (0.35f + 0.65f * (float) n.velocity / 127.0f));
        g.fillRoundedRectangle (x, y, w, juce::jmax (2.0f, rowH - 1.0f), 2.0f);
    }

    g.setColour (colours::dim);
    g.setFont (juce::FontOptions (10.0f));
    g.drawText (c.drums ? juce::String ("GM ") + juce::String (lo + 1) : mlg::noteName (lo + 1), inner.withTop (inner.getBottom() - 12).withWidth (60), juce::Justification::left);

    const double pos = proc.getPlayPosition();
    if (pos >= 0.0)
    {
        g.setColour (colours::accent2);
        g.drawVerticalLine ((int) xOf (std::fmod (pos, L)), inner.getY(), inner.getBottom());
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
    g.drawFittedText (fr ("Glisser le clip .mid\nvers Ableton"), getLocalBounds(), juce::Justification::centred, 2);
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

BilanView::BilanView (MLGAlphaProcessor& p) : proc (p)
{
    text.setMultiLine (true);
    text.setReadOnly (true);
    text.setFont (juce::FontOptions (juce::Font::getDefaultMonospacedFontName(), 13.0f, juce::Font::plain));
    text.setColour (juce::TextEditor::backgroundColourId, colours::panel);
    text.setColour (juce::TextEditor::textColourId, colours::text);
    addAndMakeVisible (text);

    closeButton.setButtonText ("Fermer");
    closeButton.onClick = [this] { setVisible (false); };
    addAndMakeVisible (closeButton);

    resetButton.setButtonText (fr ("Remettre l'apprentissage à zéro"));
    resetButton.onClick = [this]
    {
        auto opts = juce::MessageBoxOptions().withIconType (juce::MessageBoxIconType::QuestionIcon)
                        .withTitle (fr ("Remettre à zéro"))
                        .withMessage (fr ("Effacer tous les J'aime / Bof ? La bibliothèque perso et les statistiques d'écoute sont gardées."))
                        .withButton ("Effacer").withButton ("Annuler").withAssociatedComponent (this);
        juce::AlertWindow::showAsync (opts, [this] (int r) { if (r == 1) { proc.resetLearning(); refresh(); } });
    };
    addAndMakeVisible (resetButton);
}

void BilanView::refresh() { text.setText (proc.learningReport(), false); }

void BilanView::paint (juce::Graphics& g) { g.fillAll (colours::background.withAlpha (0.96f)); }

void BilanView::resized()
{
    auto r = getLocalBounds().reduced (30);
    auto bottom = r.removeFromBottom (36);
    closeButton.setBounds (bottom.removeFromRight (120).reduced (2));
    resetButton.setBounds (bottom.removeFromLeft (260).reduced (2));
    r.removeFromBottom (8);
    text.setBounds (r);
}

// ---------------------------------------------------------------------------

namespace
{
void styleButton (juce::TextButton& b, const juce::String& t, juce::Colour c = colours::cell)
{
    b.setButtonText (t);
    b.setColour (juce::TextButton::buttonColourId, c);
}

void styleEditor (juce::TextEditor& e, bool multi)
{
    e.setMultiLine (multi, true);
    e.setReturnKeyStartsNewLine (false);
    e.setColour (juce::TextEditor::backgroundColourId, colours::cell);
    e.setColour (juce::TextEditor::textColourId, colours::text);
    e.setColour (juce::TextEditor::outlineColourId, colours::cellBeat);
    e.setColour (juce::TextEditor::focusedOutlineColourId, colours::accent);
    e.setFont (juce::FontOptions (14.0f));
}

void styleLabel (juce::Label& l, const juce::String& t, float size, juce::Colour c, bool bold = false)
{
    l.setText (t, juce::dontSendNotification);
    l.setFont (juce::FontOptions (size, bold ? juce::Font::bold : juce::Font::plain));
    l.setColour (juce::Label::textColourId, c);
    l.setJustificationType (juce::Justification::topLeft);
}
} // namespace

MLGAlphaEditor::MLGAlphaEditor (MLGAlphaProcessor& p)
    : AudioProcessorEditor (&p), proc (p), clipView (p), bilan (p)
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
    laf.setColour (juce::AlertWindow::backgroundColourId, colours::panel);
    laf.setColour (juce::AlertWindow::textColourId, colours::text);
    setLookAndFeel (&laf);

    // ---------- Panneau mécanique ----------
    styleButton (generateButton, fr ("GÉNÉRER"), colours::accent.darker (0.4f));
    generateButton.onClick = [this] { proc.generateNew(); };
    styleButton (mutateButton, fr ("MUTER"));
    mutateButton.onClick = [this] { proc.mutate(); };
    styleButton (keepMecaButton, fr ("Sauvegarder"));
    keepMecaButton.onClick = [this] { askWordsAndKeep(); };
    for (auto* b : { &generateButton, &mutateButton, &keepMecaButton }) addAndMakeVisible (*b);

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

    addChoice ("rhythmMode", fr ("Moteur"));
    addKnob ("steps", fr ("Pas"));
    addChoice ("division", fr ("Division"));
    addKnob ("density", fr ("Densité"));
    addKnob ("pulses", fr ("Impulsions"));
    addKnob ("rotation", fr ("Rotation"));
    addKnob ("swing", fr ("Swing"));
    addChoice ("root", fr ("Tonique"));
    addChoice ("scale", fr ("Gamme"));
    addKnob ("lowNote", fr ("Note basse"));
    addKnob ("highNote", fr ("Note haute"));
    addKnob ("maxJump", fr ("Écart max"));
    addKnob ("lenMin", fr ("Durée min"));
    addKnob ("lenMax", fr ("Durée max"));
    addKnob ("velMin", fr ("Vél. min"));
    addKnob ("velMax", fr ("Vél. max"));
    addKnob ("accent", fr ("Accent"));
    addChoice ("octave", fr ("Octave"), { "-3", "-2", "-1", "0", "+1", "+2", "+3" });
    addChoice ("switchAt", fr ("Changement de ligne"));
    legatoButton.setButtonText ("Legato");
    legatoAttachment = std::make_unique<juce::AudioProcessorValueTreeState::ButtonAttachment> (proc.apvts, "legato", legatoButton);
    addAndMakeVisible (legatoButton);

    // ---------- Panneau texte ----------
    styleLabel (lineTitle, {}, 15.0f, colours::text, true);
    styleLabel (libraryStatus, {}, 11.0f, colours::dim);
    libraryStatus.setJustificationType (juce::Justification::topRight);
    styleLabel (normalTitle, fr ("VOCABULAIRE NORMAL — décris ce qui manque à ton morceau (Win+H pour dicter)"), 12.0f, colours::accent2, true);
    styleLabel (techTitle, fr ("VOCABULAIRE TECHNIQUE — la ligne en langage MIDI"), 12.0f, colours::accent2, true);
    styleLabel (understood, fr ("Exemples : « basse sombre et roulante », « nappe mélancolique aérée », « percu sèche ebm », "
                                "« kick techno lourd », « arpège triste en triolets, 2 mesures »."), 13.0f, colours::text);
    styleLabel (techFeedback, {}, 12.0f, colours::dim);
    for (auto* l : { &lineTitle, &libraryStatus, &normalTitle, &techTitle, &understood, &techFeedback }) addAndMakeVisible (*l);

    styleEditor (normalInput, false);
    normalInput.setTextToShowWhenEmpty (fr ("basse sombre roulante…"), colours::dim);
    normalInput.onReturnKey = [this] { search (false); };
    addAndMakeVisible (normalInput);

    styleEditor (techText, true);
    techText.setReadOnly (true);
    techText.setFont (juce::FontOptions (13.0f));
    techText.setColour (juce::TextEditor::backgroundColourId, colours::panel);
    addAndMakeVisible (techText);

    styleEditor (techInput, false);
    techInput.setTextToShowWhenEmpty (fr ("2 mesures, division 1/16, tonique la…"), colours::dim);
    techInput.onReturnKey = [this] { runTechnical(); };
    addAndMakeVisible (techInput);

    styleButton (searchButton, fr ("CHERCHER"), colours::accent.darker (0.4f));
    searchButton.onClick = [this] { search (false); };
    styleButton (againButton, fr ("Une autre"));
    againButton.onClick = [this] { search (true); };
    styleButton (likeButton, fr ("J'aime"));
    likeButton.onClick = [this] { setMessage (proc.like (true)); };
    styleButton (dislikeButton, "Bof");
    dislikeButton.onClick = [this] { setMessage (proc.like (false)); };
    styleButton (keepButton, fr ("Sauvegarder"));
    keepButton.onClick = [this] { askWordsAndKeep(); };
    styleButton (bilanButton, "Bilan");
    bilanButton.onClick = [this] { bilan.refresh(); bilan.setVisible (true); bilan.toFront (true); };
    styleButton (techButton, "OK");
    techButton.onClick = [this] { runTechnical(); };
    for (auto* b : { &searchButton, &againButton, &likeButton, &dislikeButton, &keepButton, &bilanButton, &techButton })
        addAndMakeVisible (*b);

    addAndMakeVisible (clipView);
    dragZone.makeFile = [this] { return proc.writeMidiFile(); };
    addAndMakeVisible (dragZone);

    addChildComponent (bilan);

    refreshSeedLabels();
    refreshLine();
    setSize (1240, 800);
    startTimerHz (30);
}

MLGAlphaEditor::~MLGAlphaEditor()
{
    stopTimer();
    setLookAndFeel (nullptr);
}

MLGAlphaEditor::Knob& MLGAlphaEditor::addKnob (const char* paramId, const juce::String& text)
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

MLGAlphaEditor::Choice& MLGAlphaEditor::addChoice (const char* paramId, const juce::String& text, const juce::StringArray& items)
{
    auto c = std::make_unique<Choice>();
    if (! items.isEmpty())
        c->box.addItemList (items, 1);
    else if (auto* param = dynamic_cast<juce::AudioParameterChoice*> (proc.apvts.getParameter (paramId)))
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

void MLGAlphaEditor::refreshSeedLabels()
{
    const auto& s = proc.getSeeds();
    seedRhythmValue.setText (juce::String (s.rhythm), juce::dontSendNotification);
    seedPitchValue.setText (juce::String (s.pitch), juce::dontSendNotification);
}

void MLGAlphaEditor::refreshLine()
{
    const auto& i = proc.getLineInfo();
    juce::String t = i.source;
    if (i.name.isNotEmpty()) t << fr (" : ") << i.name;
    if (i.role >= 0) t << fr ("   —   ") << mlg::roleNames()[i.role] << fr (" · ") << mlg::familyNames()[juce::jmax (0, i.family)];
    lineTitle.setText (t, juce::dontSendNotification);
    techText.setText (proc.getTechnicalText(), false);
    const bool lib = proc.isLibraryLine();
    likeButton.setEnabled (lib);
    dislikeButton.setEnabled (lib);
}

void MLGAlphaEditor::setMessage (const juce::String& m) { understood.setText (m, juce::dontSendNotification); }

void MLGAlphaEditor::search (bool again)
{
    setMessage (again ? proc.drawAgain() : proc.drawFromText (normalInput.getText()));
}

void MLGAlphaEditor::runTechnical()
{
    techFeedback.setText (proc.applyTechnical (techInput.getText()), juce::dontSendNotification);
    techInput.clear();
}

void MLGAlphaEditor::askWordsAndKeep()
{
    auto* w = new juce::AlertWindow (fr ("Garder cette ligne"),
                                     fr ("Avec tes propres mots (ils serviront à la retrouver) :"),
                                     juce::MessageBoxIconType::NoIcon, this);
    w->addTextEditor ("words", normalInput.getText());
    w->addButton ("Garder", 1, juce::KeyPress (juce::KeyPress::returnKey));
    w->addButton ("Annuler", 0, juce::KeyPress (juce::KeyPress::escapeKey));
    juce::Component::SafePointer<MLGAlphaEditor> safe (this);
    w->enterModalState (true, juce::ModalCallbackFunction::create ([safe, w] (int r)
    {
        if (r == 1 && safe != nullptr)
            safe->setMessage (safe->proc.keep (w->getTextEditorContents ("words")));
    }), true);
}

void MLGAlphaEditor::timerCallback()
{
    const bool euclid = proc.apvts.getRawParameterValue ("rhythmMode")->load() > 0.5f;
    knobs["density"]->slider.setEnabled (! euclid);
    knobs["pulses"]->slider.setEnabled (euclid);
    knobs["rotation"]->slider.setEnabled (euclid);

    if (proc.getVersion() != lastVersion)
    {
        lastVersion = proc.getVersion();
        if (! seedRhythmValue.isBeingEdited() && ! seedPitchValue.isBeingEdited())
            refreshSeedLabels();
        refreshLine();
    }

    if (proc.libraryReady() != lastReady || ! lastReady)
    {
        lastReady = proc.libraryReady();
        libraryStatus.setText (lastReady ? fr ("Bibliothèque : ") + juce::String (proc.librarySize()) + fr (" lignes")
                                         : fr ("Bibliothèque : chargement…"), juce::dontSendNotification);
    }
    clipView.repaint();
}

void MLGAlphaEditor::paint (juce::Graphics& g)
{
    g.fillAll (colours::background);

    g.setColour (colours::accent);
    g.setFont (juce::FontOptions (22.0f, juce::Font::bold));
    g.drawText ("MLG Alpha", 16, 8, 160, 28, juce::Justification::centredLeft);
    g.setColour (colours::dim);
    g.setFont (juce::FontOptions (11.0f));
    g.drawText (fr ("MIDI Line Generator · ANKS Labs"), 16, 34, 220, 14, juce::Justification::centredLeft);

    const auto drawPanel = [&g] (juce::Rectangle<int> r, const juce::String& title, juce::Colour c, float size)
    {
        g.setColour (colours::panel.withAlpha (0.6f));
        g.fillRoundedRectangle (r.toFloat(), 8.0f);
        g.setColour (c);
        g.setFont (juce::FontOptions (size, juce::Font::bold));
        g.drawText (title, r.removeFromTop (24).reduced (10, 0), juce::Justification::centredLeft);
    };
    drawPanel (mecaArea, fr ("PANNEAU MÉCANIQUE"), colours::accent, 13.0f);
    drawPanel (textArea, fr ("PANNEAU TEXTE"), colours::accent, 13.0f);

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

void MLGAlphaEditor::resized()
{
    auto r = getLocalBounds().reduced (12);
    bilan.setBounds (getLocalBounds());

    // Barre du haut : nom de la ligne en cours
    auto top = r.removeFromTop (44);
    top.removeFromLeft (240);
    libraryStatus.setBounds (top.removeFromRight (200).withTrimmedTop (4));
    lineTitle.setBounds (top.withTrimmedTop (10));
    r.removeFromTop (6);

    // Bas : piano roll + glisser
    auto bottom = r.removeFromBottom (150);
    auto right = bottom.removeFromRight (190);
    dragZone.setBounds (right.removeFromBottom (70).reduced (4, 2));
    auto sw = right.removeFromTop (52).reduced (4, 0);
    choices["switchAt"]->label.setBounds (sw.removeFromTop (16));
    choices["switchAt"]->box.setBounds (sw.withSizeKeepingCentre (sw.getWidth(), 24));
    bottom.removeFromRight (8);
    clipView.setBounds (bottom);
    r.removeFromBottom (10);

    // Deux panneaux
    mecaArea = r.removeFromLeft (r.getWidth() / 2 - 6);
    r.removeFromLeft (12);
    textArea = r;

    // ---------- Mécanique ----------
    auto m = mecaArea.reduced (8);
    m.removeFromTop (24);
    auto buttons = m.removeFromTop (32);
    generateButton.setBounds (buttons.removeFromLeft (110).reduced (2));
    mutateButton.setBounds (buttons.removeFromLeft (90).reduced (2));
    keepMecaButton.setBounds (buttons.removeFromRight (120).reduced (2));
    lockRhythmButton.setBounds (buttons.removeFromLeft (125).reduced (2));
    lockPitchButton.setBounds (buttons.removeFromLeft (135).reduced (2));
    auto seedsRow = m.removeFromTop (34);
    auto sr = seedsRow.removeFromLeft (seedsRow.getWidth() / 2).reduced (4, 0);
    seedRhythmLabel.setBounds (sr.removeFromLeft (80));
    seedRhythmValue.setBounds (sr.reduced (0, 6));
    auto spa = seedsRow.reduced (4, 0);
    seedPitchLabel.setBounds (spa.removeFromLeft (84));
    seedPitchValue.setBounds (spa.reduced (0, 6));
    m.removeFromTop (4);

    const int h = m.getHeight();
    rhythmArea = m.removeFromTop (h * 44 / 100);
    m.removeFromTop (6);
    pitchArea = m.removeFromTop (m.getHeight() / 2 - 3);
    m.removeFromTop (6);
    notesArea = m;

    enum class Kind { knob, combo, toggle, empty };
    struct Slot { Kind kind; juce::Component* label; juce::Component* widget; };

    const auto layout = [] (juce::Rectangle<int> area, int cols, int rows, const std::vector<Slot>& slots)
    {
        area.removeFromTop (22);
        area = area.reduced (6, 2);
        const int cw = area.getWidth() / cols;
        const int rh = area.getHeight() / rows;
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

    layout (rhythmArea, 4, 2, { c ("rhythmMode"), c ("division"), k ("steps"), k ("swing"),
                                k ("density"), k ("pulses"), k ("rotation"), c ("octave") });
    layout (pitchArea, 5, 1, { c ("root"), c ("scale"), k ("lowNote"), k ("highNote"), k ("maxJump") });
    layout (notesArea, 6, 1, { k ("lenMin"), k ("lenMax"), k ("velMin"), k ("velMax"), k ("accent"),
                               Slot { Kind::toggle, nullptr, &legatoButton } });

    // ---------- Texte ----------
    auto t = textArea.reduced (10);
    t.removeFromTop (24);
    normalTitle.setBounds (t.removeFromTop (18));
    auto in = t.removeFromTop (34);
    againButton.setBounds (in.removeFromRight (100).reduced (2));
    searchButton.setBounds (in.removeFromRight (100).reduced (2));
    normalInput.setBounds (in.reduced (0, 2));
    t.removeFromTop (4);
    understood.setBounds (t.removeFromTop (54));
    auto actions = t.removeFromTop (32);
    const int bw = actions.getWidth() / 4;
    likeButton.setBounds (actions.removeFromLeft (bw).reduced (2));
    dislikeButton.setBounds (actions.removeFromLeft (bw).reduced (2));
    keepButton.setBounds (actions.removeFromLeft (bw).reduced (2));
    bilanButton.setBounds (actions.reduced (2));
    t.removeFromTop (10);
    techTitle.setBounds (t.removeFromTop (18));
    auto cmd = t.removeFromBottom (54);
    techFeedback.setBounds (cmd.removeFromBottom (18));
    techButton.setBounds (cmd.removeFromRight (60).reduced (2));
    techInput.setBounds (cmd.reduced (0, 2));
    t.removeFromBottom (4);
    techText.setBounds (t);
}
