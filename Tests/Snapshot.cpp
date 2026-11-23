#include "../Source/PluginProcessor.h"
#include "../Source/PluginEditor.h"
int main()
{
    juce::ScopedJuceInitialiser_GUI init;
    MLGAlphaProcessor proc; proc.setSeeds (42u, 99u);
    std::unique_ptr<juce::AudioProcessorEditor> ed (proc.createEditor());
    auto img = ed->createComponentSnapshot (ed->getLocalBounds(), true, 1.0f);
    juce::File out ("/home/claude/MIDI-LINES/build/snapshot.png"); out.deleteFile();
    juce::FileOutputStream os (out); juce::PNGImageFormat().writeImageToStream (img, os);
    return 0;
}
