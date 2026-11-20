# Vision: what this game is

*Written 20 November 2026, at the restart. This is the dream, not the plan: the plan is in [`PROJECT.md`](../PROJECT.md). Ideas here get built in stages, simple first, more realistic later.*

---

## In one paragraph

A **fantasy medieval world** that runs by itself: land shaped by maths, weather and rivers, biomes from deserts to frozen north, and civilisations that farm, mine, fish and trade according to where they live. You play a **wandering trader**: you start alone and on foot in one town's market, and slowly work your way up to a horse, a cart, a caravan, hired traders, a trading company, and perhaps a seat in a city's government. Prices differ from place to place because the world really is different from place to place, and your choices ripple back into it.

**Inspirations:** Dwarf Fortress (a world generated from maths, then a living history on top), RimWorld (a simulation that creates stories), a top-down pixel look.

## Simulation first, game later

*(Decided 20 November 2026.)*

**For a long time this is a simulated world, not a game.** The goal is a realistic world that runs on its own:
- civilisations growing;
- traders doing their own thing;
- people moving and founding colonies;
- an economy that changes.

You leave it running and watch where it goes. **The player comes in near the end**, once the world works without one.

- **PC only**, a program that runs on the computer. No web version for a long time.
- **The whole world is always running.** Something happening on the far side of the world still changes the economy while you watch somewhere else.

---

## 1. The world

**The most important part, and the first thing we build.**

- **Size:** big. The aim is a fantasy country roughly the size of Japan (about 3,000 km long, ~380,000 km² of land), with a few hundred towns and cities and many, many small settlements. **We start with a much smaller test region** and grow it once everything works.
- **Ocean around the edge**, so the land is a country or a continent, with coasts, islands and ports.
- **Height from a formula**: mountains, hills, plains, valleys, all from layers of maths (noise). The formula approach and the noise lessons from September carry over.
- **Climate:**
  - **Temperature**, from how far north or south a place is, and how high it is (mountains are cold).
  - **Rainfall**, from wind carrying sea moisture inland. Mountains wring it out, so the far side of a range is dry (a rain shadow).
  - **Weather**, which changes from day to day and season to season, with bad years: droughts, floods, hard winters.
- **Rivers and lakes**: water runs downhill from the mountains to the sea, collects in lakes, and carves valleys.
- **Fertility**: how good the soil is for growing things, from rain, temperature, rivers and the rock underneath.
- **Biomes from all of that**, so they're never painted by hand:
  - temperate forest, rainforest and bamboo forest
  - grassland, farmland and marsh
  - desert and steppe
  - tundra, taiga and snow
  - mountains

**Real-world example of what we want** (not a real country, just the feel): Japan has a cold north where little grows, a mountainous rice-growing middle, and a hot south with tea and bamboo. Each region makes different things, so each region needs the others.

### Realism over speed: a slow, physical world generator

*(Added 20 November 2026.)* Players of realism games like Dwarf Fortress happily leave the computer for **5–10 minutes** while a world generates. So world generation can **simulate** how land forms, instead of only drawing it from formulas:

- **Erosion:** rivers wear down mountains over a long simulated time, carving realistic branching valleys.
- **Rock hardness:** hard rock resists erosion and soft rock wears away, giving cliffs, plateaus and ragged coasts. Pieces of land can be cut off and become **islands**.
- **Volcanoes**, like Japan's: volcanic mountains and chains of volcanic islands.
- **Islands:** at first simply generated; later, also produced by erosion and volcanoes. **Island peoples have their own economy**: fishing, and selling sea goods while buying what they can't make.
- **Tectonic plates** *(suggested by research)*: plates colliding raise mountain ranges and volcanic arcs, which gives real-looking ranges instead of noise blobs.

### The underground

*(Added 20 November 2026.)* Dwarves and other fantasy creatures need a world **below** the surface:

- natural **caves and caverns**;
- **ore and minerals**, laid down in rock layers that follow real geology;
- **magma** deep down, feeding the volcanoes.

**Built after the surface.** First the land above ground, then the underground generated from it.

Research notes: [`research/2026-11-20-world-generation.md`](research/2026-11-20-world-generation.md).

## 2. Civilisations and species

- **Settlements grow where life is possible**: near water, on fertile flat land, on coasts and rivers, at crossings.
- **What a place makes comes from its surroundings:**
  - a river or a coast gives fishing;
  - a forest gives timber and hunting;
  - plains give grain;
  - a warm wet south gives tea and bamboo;
  - mountains give ore and stone.
- **Fantasy species with their own homes and economies.** The main three:
  - **Humans:** plains, rivers and coasts, farming and trading.
  - **Elves:** the forests.
  - **Dwarves:** the mountains, living in caves or carved halls. They mine, smelt and sell metal goods. They can't grow crops, so they have to buy food, but they do farm mushrooms underground.
  - *Maybe other species later.*
- **Each race has an origin place**, a homeland it starts from, and spreads out by **founding colonies**. Part of the fun is leaving the world running and watching where towns grow and where people decide to settle.
- **Island peoples** live by the sea: fishing, boats, sea trade.
- **Animals:** wild animals for hunters, herds that move with the seasons. A small part of the world, but it gives hunters something real to hunt.
- **Sizes from cities down to hamlets.** A few hundred big towns and cities, plus countless small places: a farmstead by the road, a woodcutter's hut in the forest.
- **Money isn't everywhere.** Cities use coin. Subsistence farmers out in the fields and forests may have no money at all, and only **barter**: your salt for their eggs. *Historically, medieval peasants used some coin, but much rural exchange was barter, credit or payment in kind.*

## 3. The economy

- **Supply and demand differ by place**, because production differs by place. That gap is what makes trade worth doing.
- **The world reacts:**
  - a drought in the grain region raises bread prices everywhere it used to sell;
  - a new mine makes iron cheap nearby.
- **Lessons from the Python prototype, kept from day one:**
  - **Money is conserved:** it only ever moves, and is never created or destroyed by accident.
  - **Do the food maths first:** the world must be able to feed itself.
  - **Every place needs something it sells all the time**, otherwise all the money piles up with whoever sells food. Things that get used up (food, firewood, tools that wear out) give steady demand.
  - **Recipe inputs count as demand,** not only food.
- **Success test:** run for years of game time. Nobody starves, money stays constant, and prices move within a range rather than drifting away. *Prices that move within a range are a working market; prices that drift are a broken one.*

## 4. Things that grow out of the simulation

The ideas that make the world feel alive. None of these are drawn by hand; they come out of the numbers.

- **AI traders** travel between settlements and **find their own paths** across the land.
- **Paths used often become tracks, then roads.** A rich region may pave its busiest road, and faster roads attract more traffic.
- **Fields appear** around settlements, sized by how many mouths there are to feed and how much fertile land is in reach.
- **Industries follow the land:** fishing villages on rivers, mining towns in the hills, logging camps in the forest.
- **Settlements grow, shrink and are founded** as their economies do well or badly.
- **Transport of many kinds**, as in a medieval fantasy world:
  - on foot, horses, carts and caravans;
  - **boats** on rivers, lakes and the sea.
  - Historically, water transport was many times cheaper than land, so rivers, coasts and islands matter a lot.

## 5. The player: a trader (much later)

The game mechanic is trading; the world is the star. **The player is one of the last things built**, after the world runs well on its own (see "Simulation first" at the top).

| Stage | You have | What changes |
|---|---|---|
| 1 | Nothing: on foot, one pack | Slow, small loads, local markets only, barter with farmers |
| 2 | A horse | Faster, reach the next towns |
| 3 | A horse and cart | Bigger loads, bulk goods start to pay |
| 4 | A trading caravan | Cross the whole country, trade between the big cities |
| 5 | Hired traders, a company | Run routes you don't walk yourself |
| 6 | Settle down | Property, influence, maybe a seat in local government |

- **Your choices affect the world.** Flooding a market with cheap grain hurts local farmers; supplying a starving town might save it.
- *Open question:* is the player only a trader, or could you one day play as a settlement? The current answer: **a trader**, which is more personal and more fun.
- *Open question (from September):* if there are ever several players, do they compete for the same goods (drama), or run separate routes?

## 6. Time: the hard design problem

The player lives in **hours and days** (walking a road, haggling in a market). The economy lives in **seasons and years** (a harvest, a drought, a road being paved). Both have to feel right in the same game.

Ideas to think through. **Nothing is decided yet:**

- **Two speeds of time:**
  - when you're in a town, time is slow or paused, and a day of haggling feels like a day;
  - when you're travelling, time runs fast, and a week on the road passes in seconds.
- **Not everything is updated every day:**
  - the economy updates daily or weekly;
  - harvests update each season;
  - population changes yearly.
  - Victoria 3 does this to stay fast.
- **The world keeps running while you travel.** Prices you saw a month ago may be stale when you arrive. That is part of the game: information is a trade good.

## 7. Look and feel

- **Top-down and pixelated**, in the spirit of Dwarf Fortress' map view. Traders are little blocks or sprites moving along roads.
- **The numbers are the truth; the pictures are drawn from them.** That way a zoomed-in town view (houses, market square) can come later without rewriting the simulation.
- **Scale it down until it works, then scale it up.** A small region first, a whole country later.

### Levels of detail

*(Added 20 November 2026.)* Like Dwarf Fortress, where you can zoom right in until one tile is about the size of a person:

| Level | Detail | What you see |
|---|---|---|
| World | ~1 km per cell | Countries, biomes, rivers, roads, towns as dots |
| Region | ~100 m (1 hectare) | Fields, villages, forests, road routes |
| Town | ~1 m, maybe finer | Walking through a town: shops, market stalls, houses, people |

- **Finer levels are generated when they're needed**, at different stages. Nobody needs every street of every town worked out in advance.
- **The whole world keeps simulating while you're zoomed in** on one place. Far away it runs coarsely, in groups and averages; close up it runs in detail.
- This is one of the hard technical problems, so it gets its own design note when we reach it.

## 8. How it's built

- **C# / .NET** for the simulation. It's fast, an AI writes it well, and the owner can read it. Rust is the fallback if we ever need the absolute maximum speed.
- **Claude writes the code; the owner understands it.** Every system starts as a written design note with all its maths and logic. We go through it until it makes sense, and only then is it built. The notes stay, as the explanation of the code.
- **Efficient from the start:**
  - many agents stored as compact arrays;
  - big crowds treated as groups of people rather than one object each, where that's realistic;
  - seeded randomness, so the same seed gives the same world.
- **The development PC:** NVIDIA RTX 3060 Ti (8 GB), AMD Ryzen 5 3600 (6 cores, 12 threads), 32 GB of memory. The simulation should run well on it, using all 12 threads for heavy steps like erosion.

## 9. Local AI: an idea to keep

*(Added 20 November 2026.)* The owner experiments with local AI models (Qwen and others) on the 8 GB graphics card, at around 16 tokens per second.

- **An old idea:** an AI that helps run the world, keeping things realistic and in balance, like a "game master".
- **Current thinking:** the realism should come from **hand-coded realistic systems**, which are fast, repeatable and understood. A local model at 16 tokens a second is far too slow to make decisions every tick.
- **Where a local model could help later:**
  - writing things the simulation has *already decided*: town and character names, a chronicle of the world's history, dialogue with traders;
  - running in the background and saving its results.
- Research notes: [`research/2026-11-20-living-world.md`](research/2026-11-20-living-world.md).
