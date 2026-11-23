#include "../Source/PluginProcessor.h"
#include "../Source/PluginEditor.h"
int main()
{
    juce::ScopedJuceInitialiser_GUI init;
    MLGAlphaProcessor proc;
    while (! proc.libraryReady()) juce::Thread::sleep (20);
    proc.drawFromText (juce::String::fromUTF8 ("basse sombre roulante"));
    std::unique_ptr<juce::AudioProcessorEditor> ed (proc.createEditor());
    auto img = ed->createComponentSnapshot (ed->getLocalBounds(), true, 1.0f);
    juce::File out (juce::File::getCurrentWorkingDirectory().getChildFile ("snapshot.png")); out.deleteFile();
    juce::FileOutputStream os (out); juce::PNGImageFormat().writeImageToStream (img, os);
    return 0;
}
