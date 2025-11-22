# Session 6 twitch enhancements

1. bot CTA & updates
twitch_bot:
outgoing - currently just initial announce on going live

desired:
every minute, only if no recent votes, very simple call to action
on opening vote cast, announce "voting opened by <user>: <vote>."
on vote close, announce outcome.
(ah shit, the state may not be available directly here. might need more planning)

2. Commands
plumb chat commands:
- "+", "-": zoom (already in game_controller + admin_panel)
- "1", "2", "3", "4", "h": forward keystroke (1, 2, 3, 4, or h) to game (not yet in controller, easy to add)
I may come regret this, but no rate limit for now. maybe a placeholder or reminder to add later.


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


# Rules (update 2025-11-22)

Voting
timer shown, but not counting down until first vote of the round comes in
timer length is variable 30-120s, depending only on current vote ratios

ratios
L X K timer
0 0 1 30s
0 1 1 60s
1 0 1 60s
1 1 1 90s
1 2+ 1 120s

flow:
- voting opens, only k/l available (x is n/a)
- countdown shows 30sec but *not* yet counting down ("waiting for votes")
- first user votes, triggers countdown to begin with appropriate value for 1:0 ratio
- second user votes
    - if same as first, no affect on countdown
    - if different, ratio changes to 50%, timer jumps +30s
- more votes come in, even between k/l with only a few x, countdown len hovers ~60s (while still counting down the whole time)
- at any point when countdown hits zero, voting closes and round completes
    - if neither k/l are > 33% (meaning x is >33%), round ends without action
    - if k/l tied -> tie break event
    - actions executed as reqd

each tick, add a brief "+/-X" animation over countdown when changed due to ratio swings

ideas to consider:
x votes expire after 30s, can be refreshed by user re-voting same (track last only), no cummulative effect
other votes never expire, last vote remains locked until changed or round ends
repeated voting k/l *toggles* that vote, so spamming (in the limit) == 50% chance of vote actually being counted, vs single valid vote == 100%
alternate: multiple votes from same user all tracked, with each diluting the value of that user's 1 vote (e.g. 1 == 100%, each additional: -5% weight)
simple majority wins between k/l when timer expires. tie break - next vote wins, and if that is l, they steal naming rights. if tie unbroken, round ends without action


