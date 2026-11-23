cmake_minimum_required(VERSION 3.22)
project(MLG_ALPHA VERSION 0.1.0)

include(FetchContent)
FetchContent_Declare(JUCE
    GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG 8.0.4
    GIT_SHALLOW ON)
FetchContent_MakeAvailable(JUCE)

# Instrument VST3 qui ne produit pas de son : il génère des notes MIDI
# envoyées vers une autre piste Ableton (MIDI From -> piste du générateur).
juce_add_plugin(MLGAlpha
    COMPANY_NAME "ANKS Labs"
    IS_SYNTH TRUE
    NEEDS_MIDI_INPUT TRUE
    NEEDS_MIDI_OUTPUT TRUE
    IS_MIDI_EFFECT FALSE
    PLUGIN_MANUFACTURER_CODE Anks
    PLUGIN_CODE Mlga
    VST3_CATEGORIES Instrument Generator
    FORMATS VST3
    BUNDLE_ID com.ankslabs.mlgalpha
    PRODUCT_NAME "MLG Alpha")

# Bibliothèque compilée (tools/classify.py) et dictionnaire (tools/build_dictionary.py), embarqués dans le plugin
juce_add_binary_data(MLGAlphaData SOURCES
    Resources/mlg_library.txt.gz
    Resources/mlg_dictionary.txt)

set(MLG_SOURCES
    Source/Engine.h
    Source/Engine.cpp
    Source/Library.h
    Source/Library.cpp
    Source/Technical.h
    Source/Technical.cpp
    Source/PluginProcessor.h
    Source/PluginProcessor.cpp
    Source/PluginEditor.h
    Source/PluginEditor.cpp)

target_sources(MLGAlpha PRIVATE ${MLG_SOURCES})

target_compile_features(MLGAlpha PRIVATE cxx_std_17)

if(MSVC)
    target_compile_options(MLGAlpha PRIVATE /utf-8)
endif()

target_compile_definitions(MLGAlpha PUBLIC
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0)

target_link_libraries(MLGAlpha
    PRIVATE
        MLGAlphaData
        juce::juce_audio_utils
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_warning_flags)

# Tests (hors plugin) : cmake -DMLGALPHA_TESTS=ON
option(MLGALPHA_TESTS "Construire les tests" OFF)
if(MLGALPHA_TESTS)
    juce_add_console_app(EngineTest PRODUCT_NAME "EngineTest")
    target_sources(EngineTest PRIVATE Tests/EngineTest.cpp Source/Engine.cpp)
    target_compile_definitions(EngineTest PRIVATE JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0)
    target_link_libraries(EngineTest PRIVATE juce::juce_audio_basics)

    juce_add_console_app(LibraryTest PRODUCT_NAME "LibraryTest")
    target_sources(LibraryTest PRIVATE Tests/LibraryTest.cpp Source/Engine.cpp Source/Library.cpp Source/Technical.cpp)
    target_compile_definitions(LibraryTest PRIVATE JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0)
    target_link_libraries(LibraryTest PRIVATE MLGAlphaData juce::juce_audio_basics)

    juce_add_console_app(PlaybackTest PRODUCT_NAME "PlaybackTest")
    target_sources(PlaybackTest PRIVATE Tests/PlaybackTest.cpp ${MLG_SOURCES})
    target_compile_definitions(PlaybackTest PRIVATE JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JucePlugin_Name="MLG Alpha")
    target_link_libraries(PlaybackTest PRIVATE MLGAlphaData juce::juce_audio_utils)

    juce_add_gui_app(Snapshot PRODUCT_NAME "Snapshot")
    target_sources(Snapshot PRIVATE Tests/Snapshot.cpp ${MLG_SOURCES})
    target_compile_definitions(Snapshot PRIVATE JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JucePlugin_Name="MLG Alpha")
    target_link_libraries(Snapshot PRIVATE MLGAlphaData juce::juce_audio_utils)
endif()
