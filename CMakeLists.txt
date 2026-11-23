cmake_minimum_required(VERSION 3.22)
project(LINEGEN VERSION 0.1.0)

include(FetchContent)
FetchContent_Declare(JUCE
    GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG 8.0.4
    GIT_SHALLOW ON)
FetchContent_MakeAvailable(JUCE)

# Instrument VST3 qui ne produit pas de son : il génère des notes MIDI
# envoyées vers une autre piste Ableton (MIDI From -> piste du générateur).
juce_add_plugin(LINEGEN
    COMPANY_NAME "ANKS Labs"
    IS_SYNTH TRUE
    NEEDS_MIDI_INPUT TRUE
    NEEDS_MIDI_OUTPUT TRUE
    IS_MIDI_EFFECT FALSE
    PLUGIN_MANUFACTURER_CODE Anks
    PLUGIN_CODE Lgn1
    VST3_CATEGORIES Instrument Generator
    FORMATS VST3
    PRODUCT_NAME "LINEGEN")

target_sources(LINEGEN PRIVATE
    Source/Engine.h
    Source/Engine.cpp
    Source/PluginProcessor.h
    Source/PluginProcessor.cpp
    Source/PluginEditor.h
    Source/PluginEditor.cpp)

target_compile_features(LINEGEN PRIVATE cxx_std_17)

if(MSVC)
    target_compile_options(LINEGEN PRIVATE /utf-8)
endif()

target_compile_definitions(LINEGEN PUBLIC
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0)

target_link_libraries(LINEGEN
    PRIVATE
        juce::juce_audio_utils
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_warning_flags)

# Test du moteur (hors plugin) : cmake -DLINEGEN_TESTS=ON
option(LINEGEN_TESTS "Construire le test du moteur" OFF)
if(LINEGEN_TESTS)
    juce_add_console_app(EngineTest PRODUCT_NAME "EngineTest")
    target_sources(EngineTest PRIVATE Tests/EngineTest.cpp Source/Engine.cpp)
    target_compile_definitions(EngineTest PRIVATE JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0)
    target_link_libraries(EngineTest PRIVATE juce::juce_audio_basics)
endif()

if(LINEGEN_TESTS)
    juce_add_console_app(PlaybackTest PRODUCT_NAME "PlaybackTest")
    target_sources(PlaybackTest PRIVATE Tests/PlaybackTest.cpp Source/Engine.cpp
        Source/PluginProcessor.cpp Source/PluginEditor.cpp)
    target_compile_definitions(PlaybackTest PRIVATE JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0
        JucePlugin_Name="LINEGEN")
    target_link_libraries(PlaybackTest PRIVATE juce::juce_audio_utils)
endif()

if(LINEGEN_TESTS)
    juce_add_gui_app(Snapshot PRODUCT_NAME "Snapshot")
    target_sources(Snapshot PRIVATE Tests/Snapshot.cpp Source/Engine.cpp Source/PluginProcessor.cpp Source/PluginEditor.cpp)
    target_compile_definitions(Snapshot PRIVATE JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JucePlugin_Name="LINEGEN")
    target_link_libraries(Snapshot PRIVATE juce::juce_audio_utils)
endif()
