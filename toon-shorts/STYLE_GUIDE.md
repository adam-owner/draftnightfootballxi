# Style guide: the reference shorts

Taken from 7 reference clips: five ~60 s stories (gold mine, space-station toilet,
prison bank vault, roadside tree, army camp with cannonballs), one 25 s story (backyard
fireworks), and one 13 s comic-over-gameplay clip that is a different format and was
left out. All are 576x1024 at 30 fps, vertical 9:16.

## 1. The look: flat characters in a 3D world

The style rests on one contrast: **flat 2D cartoon characters placed inside rich,
cinematically lit 3D environments.**

**Environments**
- Stylized 3D, like an indie game or a diorama: chunky proportions, hand-made props,
  painterly textures. Not photoreal, not low-poly.
- Strong practical lighting sets the mood of each scene: lantern-lit mine, blue-night
  snow with paper lanterns, moonlit army camp with campfires, neon mission control,
  sunny farm road, then rain at night for the dark turn.
- Lots of props that tell the story (candle crates, $20.67 gold-price boards, a
  "SURE THING MINE" sign, a giant vault door, "DON'T HIT THIS TREE" marquee arrow).
- Atmosphere: haze, dust, snow, sparks, rain, smoke.

**Characters** (one design system for the whole cast)
- A big, perfectly round white head with a thick dark-brown outline and no neck.
- A minimal face: dot eyes or half-lidded line eyes, simple brows, a tiny mouth.
  Expressions are exaggerated for beats: a wide grin, a screaming open mouth, a sweat
  drop, sunglasses, squinted ^^ eyes.
- **The hat or hair is the character's identity**: beanie, top hat, bowler, cowboy hat,
  sheriff hat, prison headlamp, samurai jingasa, astronaut cap. Give every character a
  hat or hairstyle you could recognise in silhouette.
- The torso is a rounded bean or capsule shape that *is* the outfit: one flat colour,
  simple details (buttons, suspenders, stripes, a scarf).
- Stick-thin dark arms and legs with small round hands.
- Cel-shaded flat, with a soft contact shadow on the 3D ground so they sit in the world.

## 2. Camera and shot grammar

- A cut or a strong camera move every **~3-6 s**. Hard-cut counts were low (2-15 per
  minute) because many "shots" are one continuous 3D camera move: a fly-through, an
  orbit, a crane.
- Cycle through: **establishing wide** -> **medium on the character** -> **close-up
  reaction** -> **insert of the key prop** (gold nugget, vault dial, speed sign, valve)
  -> **POV** (gun sights, steering wheel, climbing).
- Signature moves: a slow push-in on a deadpan face, an FPV fly-through of the set, a
  top-down view, a cutaway diagram (the cross-section of the town above the vault, the
  "target fixation" vignette in the tree story).
- Characters face camera often, talking-head style, even mid-action.

## 3. Animation

- The characters move like 2D puppets: bouncy walks, snappy poses, face swaps on the
  beat, squash and stretch on big moments.
- The world moves continuously: flicker, drifting particles, smoke, swaying grass.
- Big visual payoffs at the turns: an explosion, a flood, fireworks, a car crash.

## 4. Sound

- **One narrator throughout**: calm, deadpan, dry wit, a storyteller pace of about
  2.5-3 words per second. Third person, present tense.
- **A continuous bed under the voice.** The audio never drops below -50 dB until the
  outro, so there is always music or ambience. Keep it low and duck it under speech.
- Sound effects on the payoffs (whoosh, boom, splash) help.
- Final loudness of about -17 LUFS integrated. The pipeline normalises to -16.

## 5. Writing: the story formula

The scripts are short, absurd, slightly dark "clever schemer" stories, written as if
true:

1. **Hook (0-3 s): one line that sets up an odd premise.** "A man sells umbrellas in the
   driest town in America." It often uses a number or price ($20.67, 10,000, 15 mph).
2. **Setup (3-15 s):** the world and the rule ("it hasn't rained in 41 years"). Short
   declarative sentences, one per shot.
3. **The scheme (15-40 s):** the character finds a loophole and exploits it. Escalate
   with repetition ("He does it again on Tuesday. And Wednesday.").
4. **Complication (40-50 s):** authority notices (a sheriff, a guard, mission control,
   a commander).
5. **Twist/punchline (last 5-10 s):** the scheme backfires or pays off ironically. End on
   a short line and a reaction close-up.

Style rules:
- One sentence (or a fragment) per shot. A cut on every line.
- Present tense: "he watches", "he knows", "they attack".
- Rhetorical questions as pivots: "Why?", "What's happening?"
- Concrete numbers and props over adjectives.
- 150-180 words for 60 s (the OCR'd reference scripts run 152-179).

## 6. Captions

The references burn in one word at a time (white bold sans with a dark outline, at
about 70% of the frame height). **Our output has no captions, by request.** The prompts
also tell the image and video models not to draw any text.

## 7. How the pipeline maps onto this

| Element of the style | Where it lives |
| --- | --- |
| World + character look | `scripts/style.py` -> `WORLD`, `CHARACTER` |
| Consistent cast | `characters.py` makes reference sheets, and `keyframes.py` conditions every character shot on them |
| Shot grammar | `shot_size` + `camera` vocab in `style.py` |
| Puppet-like motion | `style.motion_prompt()` |
| Narrator + bed | `voiceover.py` (MiniMax TTS + Suno instrumental on MuAPI) |
| Voice-driven edit, ducking, loudness | `assemble.py` |
| Story formula | `story.example.json` follows sec. 5 |
