# Savefile scraping
1/5/10 minutes, autosave entire game state checkpoint
analysis tools exist to count and analyse bibites, species, environment

1. on-screen countdown to update
2. extract data for overlay updates
2. add messages to chat, etc


# Static screenshot analysis
screenshot the game window and OCR, extract real-time state
sync action sequence could be:
    pause -> screenshot -> analyse/validate -> execute -> unpause
async: could scrape for additional overlay data on a clock

further ideas: auto zoom level adjustment to best fit live content


# Corpses and Voting
using new alpha build with dead bibites becoming inactive "corpse" for some time, instead of instantly becoming "meat" pellets as before. camera stays on corpse until decay. this works really well for us, and opens up some nice enhancements for twitch actions:

Lay becomes Revive action in-game (give "L"ife) if focused bibite is already dead. as before, this sets the credited twitch user tag, but no longer lays an egg.

Kill on an already-dead corpse just makes the decay instant, so camera will switch to another instead of waiting for natural decay period. allows chat to keep the camera moving - if it's a big old one in the middle of nowehere, this decay can be slow and boring.
