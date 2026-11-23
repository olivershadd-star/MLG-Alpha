#include "PluginProcessor.h"
#include "PluginEditor.h"

using midilines::fr;

namespace
{
const char* const kParamIds[] = { "rhythmMode", "steps", "division", "density", "pulses", "rotation", "swing",
                                  "root", "scale", "lowNote", "highNote", "maxJump",
                                  "lenMin", "lenMax", "legato", "velMin", "velMax", "accent" };
}

MidiLinesProcessor::MidiLinesProcessor()
    : AudioProcessor (BusesProperties().withOutput ("Output", juce::AudioChannelSet::stereo(), true)),
      apvts (*this, nullptr, "MIDILINES", createLayout())
{
    for (auto* id : kParamIds)
        apvts.addParameterListener (id, this);

    seeds.rhythm = (juce::uint32) juce::Random::getSystemRandom().nextInt();
    seeds.pitch = (juce::uint32) juce::Random::getSystemRandom().nextInt();
    rebuild();
    startTimerHz (30);
}

MidiLinesProcessor::~MidiLinesProcessor()
{
    stopTimer();
    for (auto* id : kParamIds)
        apvts.removeParameterListener (id, this);
}

juce::AudioProcessorValueTreeState::ParameterLayout MidiLinesProcessor::createLayout()
{
    using namespace juce;
    std::vector<std::unique_ptr<RangedAudioParameter>> p;

    auto pct = AudioParameterFloatAttributes().withStringFromValueFunction ([] (float v, int) { return String (roundToInt (v)) + " %"; });
    auto note = AudioParameterIntAttributes().withStringFromValueFunction ([] (int v, int) { return midilines::noteName (v); });

    // Rythme
    p.push_back (std::make_unique<AudioParameterChoice> (ParameterID { "rhythmMode", 1 }, fr ("Mode rythme"),
                                                         StringArray { fr ("Aléatoire"), fr ("Euclidien") }, 0));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "steps", 1 }, fr ("Pas"), 1, midilines::kMaxSteps, 16));
    p.push_back (std::make_unique<AudioParameterChoice> (ParameterID { "division", 1 }, fr ("Division"), midilines::divisionNames(), 3));
    p.push_back (std::make_unique<AudioParameterFloat> (ParameterID { "density", 1 }, fr ("Densité"), NormalisableRange<float> (0.0f, 100.0f, 1.0f), 50.0f, pct));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "pulses", 1 }, fr ("Impulsions"), 0, midilines::kMaxSteps, 5));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "rotation", 1 }, fr ("Rotation"), 0, midilines::kMaxSteps - 1, 0));
    p.push_back (std::make_unique<AudioParameterFloat> (ParameterID { "swing", 1 }, fr ("Swing"), NormalisableRange<float> (0.0f, 100.0f, 1.0f), 0.0f, pct));

    // Hauteurs
    p.push_back (std::make_unique<AudioParameterChoice> (ParameterID { "root", 1 }, fr ("Tonique"), midilines::rootNames(), 0));
    p.push_back (std::make_unique<AudioParameterChoice> (ParameterID { "scale", 1 }, fr ("Gamme"), midilines::scaleNames(), 1));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "lowNote", 1 }, fr ("Note basse"), 24, 108, 48, note));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "highNote", 1 }, fr ("Note haute"), 24, 108, 67, note));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "maxJump", 1 }, fr ("Écart max"), 0, 12, 3));

    // Notes
    p.push_back (std::make_unique<AudioParameterFloat> (ParameterID { "lenMin", 1 }, fr ("Durée min"), NormalisableRange<float> (5.0f, 400.0f, 1.0f), 50.0f, pct));
    p.push_back (std::make_unique<AudioParameterFloat> (ParameterID { "lenMax", 1 }, fr ("Durée max"), NormalisableRange<float> (5.0f, 400.0f, 1.0f), 100.0f, pct));
    p.push_back (std::make_unique<AudioParameterBool> (ParameterID { "legato", 1 }, fr ("Legato"), false));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "velMin", 1 }, fr ("Vélocité min"), 1, 127, 80));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "velMax", 1 }, fr ("Vélocité max"), 1, 127, 110));
    p.push_back (std::make_unique<AudioParameterInt> (ParameterID { "accent", 1 }, fr ("Accent"), 0, 40, 15));

    return { p.begin(), p.end() };
}

bool MidiLinesProcessor::isBusesLayoutSupported (const BusesLayout& layouts) const
{
    const auto out = layouts.getMainOutputChannelSet();
    return out == juce::AudioChannelSet::stereo() || out == juce::AudioChannelSet::mono();
}

void MidiLinesProcessor::prepareToPlay (double sampleRate, int)
{
    currentSampleRate = sampleRate > 0.0 ? sampleRate : 44100.0;
    wasPlaying = false;
    noteActive = false;
}

// ---------------------------------------------------------------------------
// Génération (thread principal)

midilines::Settings MidiLinesProcessor::readSettings() const
{
    midilines::Settings s;
    s.rhythmMode = (int) raw ("rhythmMode") == 1 ? midilines::RhythmMode::euclidean : midilines::RhythmMode::random;
    s.numSteps = (int) raw ("steps");
    s.division = (int) raw ("division");
    s.density = raw ("density") / 100.0;
    s.pulses = (int) raw ("pulses");
    s.rotation = (int) raw ("rotation");
    s.swing = raw ("swing") / 100.0;
    s.root = (int) raw ("root");
    s.scale = (int) raw ("scale");
    s.lowNote = (int) raw ("lowNote");
    s.highNote = (int) raw ("highNote");
    s.maxJump = (int) raw ("maxJump");
    s.lenMin = raw ("lenMin") / 100.0;
    s.lenMax = raw ("lenMax") / 100.0;
    s.legato = raw ("legato") > 0.5f;
    s.velMin = (int) raw ("velMin");
    s.velMax = (int) raw ("velMax");
    s.accent = (int) raw ("accent");
    return s;
}

void MidiLinesProcessor::rebuild()
{
    const auto p = midilines::generate (readSettings(), seeds);
    displayPattern = p;
    ++patternVersion;

    {
        const juce::SpinLock::ScopedLockType lock (patternLock);
        pendingPattern = p;
        hasPending.store (true);
    }
}

void MidiLinesProcessor::parameterChanged (const juce::String&, float) { dirty.store (true); }

void MidiLinesProcessor::timerCallback()
{
    if (dirty.exchange (false))
        rebuild();
}

void MidiLinesProcessor::generateNew()
{
    if (! lockRhythm) { seeds.rhythm = (juce::uint32) seedSource.nextInt(); seeds.rhythmMutations = 0; }
    if (! lockPitch)  { seeds.pitch = (juce::uint32) seedSource.nextInt();  seeds.pitchMutations = 0; }
    rebuild();
}

void MidiLinesProcessor::mutate()
{
    if (! lockRhythm) ++seeds.rhythmMutations;
    if (! lockPitch)  ++seeds.pitchMutations;
    rebuild();
}

void MidiLinesProcessor::setRhythmLocked (bool b) { lockRhythm = b; }
void MidiLinesProcessor::setPitchLocked (bool b) { lockPitch = b; }

void MidiLinesProcessor::setSeeds (juce::uint32 r, juce::uint32 p)
{
    if (r != seeds.rhythm) { seeds.rhythm = r; seeds.rhythmMutations = 0; }
    if (p != seeds.pitch)  { seeds.pitch = p;  seeds.pitchMutations = 0; }
    rebuild();
}

juce::File MidiLinesProcessor::writeMidiFile() const
{
    auto dir = juce::File::getSpecialLocation (juce::File::tempDirectory).getChildFile ("MIDI LINES");
    dir.createDirectory();
    auto file = dir.getChildFile ("MIDI_LINES_" + juce::String (seeds.rhythm) + "-" + juce::String (seeds.rhythmMutations)
                                  + "_" + juce::String (seeds.pitch) + "-" + juce::String (seeds.pitchMutations) + ".mid");
    file.deleteFile();

    juce::FileOutputStream os (file);
    if (os.openedOk())
    {
        midilines::toMidiFile (displayPattern).writeTo (os);
        os.flush();
    }
    return file;
}

// ---------------------------------------------------------------------------
// Lecture (thread audio)

void MidiLinesProcessor::processBlock (juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midi)
{
    juce::ScopedNoDenormals noDenormals;
    buffer.clear();   // aucun son : seulement du MIDI

    if (hasPending.load())
    {
        const juce::SpinLock::ScopedTryLockType lock (patternLock);
        if (lock.isLocked())
        {
            playPattern = pendingPattern;
            hasPending.store (false);
        }
    }

    const int numSamples = buffer.getNumSamples();
    juce::MidiBuffer out;
    for (const auto m : midi)            // les notes jouées au clavier passent à travers
        out.addEvent (m.getMessage(), m.samplePosition);

    bool playing = false;
    double ppq = 0.0, bpm = 120.0;
    if (auto* ph = getPlayHead())
        if (auto pos = ph->getPosition())
        {
            playing = pos->getIsPlaying();
            if (auto v = pos->getPpqPosition()) ppq = *v;
            if (auto b = pos->getBpm()) bpm = *b;
        }

    const auto noteOff = [] (int pitch) { return juce::MidiMessage::noteOff (midilines::kMidiChannel, pitch); };

    if (! playing || numSamples <= 0 || bpm <= 0.0)
    {
        if (noteActive) { out.addEvent (noteOff (activePitch), 0); noteActive = false; }
        wasPlaying = false;
        currentStep.store (-1);
        midi.swapWith (out);
        return;
    }

    const double ppqPerSample = bpm / (60.0 * currentSampleRate);
    const double endPpq = ppq + numSamples * ppqPerSample;

    // Saut de lecture (boucle, déplacement du curseur) : on coupe la note en cours.
    const bool contiguous = wasPlaying && std::abs (ppq - expectedPpq) < 0.05;
    if (! contiguous && noteActive) { out.addEvent (noteOff (activePitch), 0); noteActive = false; }
    const double scanStart = contiguous ? expectedPpq : ppq;
    wasPlaying = true;
    expectedPpq = endPpq;

    const auto& pat = playPattern;
    const int n = juce::jmax (1, pat.numSteps);
    const double sp = pat.stepPpq;

    const auto toSample = [&] (double t) { return juce::jlimit (0, numSamples - 1, (int) std::floor ((t - ppq) / ppqPerSample)); };
    const auto releaseIfDue = [&] (double t)
    {
        if (noteActive && activeEndPpq <= t)
        {
            out.addEvent (noteOff (activePitch), toSample (activeEndPpq));
            noteActive = false;
        }
    };

    const auto first = (juce::int64) std::floor (scanStart / sp) - 1;
    const auto last = (juce::int64) std::floor (endPpq / sp);

    for (auto a = first; a <= last; ++a)
    {
        const int s = (int) (((a % n) + n) % n);
        const double t = (double) (a - s) * sp + pat.stepStartPpq (s);   // début du cycle + position du pas
        if (t < scanStart || t >= endPpq) continue;

        const auto& st = pat.steps[(size_t) s];
        if (! st.on) continue;

        releaseIfDue (t);
        const int smp = toSample (t);
        const auto on = juce::MidiMessage::noteOn (midilines::kMidiChannel, st.pitch, (juce::uint8) st.velocity);

        if (noteActive)
        {
            if (pat.legato && activePitch != st.pitch)
            {
                out.addEvent (on, smp);                    // nouvelle note d'abord -> glide
                out.addEvent (noteOff (activePitch), smp);
            }
            else
            {
                out.addEvent (noteOff (activePitch), smp);
                out.addEvent (on, smp);
            }
        }
        else
        {
            out.addEvent (on, smp);
        }

        noteActive = true;
        activePitch = st.pitch;
        activeEndPpq = t + st.lengthSteps * sp;
    }

    releaseIfDue (endPpq);

    const auto stepNow = (juce::int64) std::floor (endPpq / sp);
    currentStep.store ((int) (((stepNow % n) + n) % n));

    midi.swapWith (out);
}

// ---------------------------------------------------------------------------
// Sauvegarde

void MidiLinesProcessor::getStateInformation (juce::MemoryBlock& dest)
{
    auto state = apvts.copyState();
    state.setProperty ("seedRhythm", (juce::int64) seeds.rhythm, nullptr);
    state.setProperty ("seedPitch", (juce::int64) seeds.pitch, nullptr);
    state.setProperty ("mutRhythm", seeds.rhythmMutations, nullptr);
    state.setProperty ("mutPitch", seeds.pitchMutations, nullptr);
    state.setProperty ("lockRhythm", lockRhythm, nullptr);
    state.setProperty ("lockPitch", lockPitch, nullptr);

    if (auto xml = state.createXml())
        copyXmlToBinary (*xml, dest);
}

void MidiLinesProcessor::setStateInformation (const void* data, int size)
{
    auto xml = getXmlFromBinary (data, size);
    if (xml == nullptr || ! xml->hasTagName (apvts.state.getType()))
        return;

    auto state = juce::ValueTree::fromXml (*xml);
    seeds.rhythm = (juce::uint32) (juce::int64) state.getProperty ("seedRhythm", (juce::int64) seeds.rhythm);
    seeds.pitch = (juce::uint32) (juce::int64) state.getProperty ("seedPitch", (juce::int64) seeds.pitch);
    seeds.rhythmMutations = state.getProperty ("mutRhythm", 0);
    seeds.pitchMutations = state.getProperty ("mutPitch", 0);
    lockRhythm = state.getProperty ("lockRhythm", false);
    lockPitch = state.getProperty ("lockPitch", false);

    apvts.replaceState (state);
    dirty.store (true);
}

juce::AudioProcessorEditor* MidiLinesProcessor::createEditor() { return new MidiLinesEditor (*this); }

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() { return new MidiLinesProcessor(); }
