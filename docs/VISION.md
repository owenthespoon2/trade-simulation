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

### Still to add to the world generator

*(Listed 20 November 2026, as a checklist so nothing is forgotten.)*

1. **Seasons in the climate:**
   - monthly temperature and rain, not just yearly averages;
   - snow cover, frozen rivers, mountain passes closing in winter;
   - wet and dry seasons.
   - Trade depends on all of this.
2. **Other resources than ore:**
   - building stone and clay;
   - salt, a vital medieval trade good;
   - peat, sand;
   - rich flood-plain soil along big rivers, like the Nile's.
3. **Water details:**
   - **which rivers boats can use** (wide and deep enough);
   - **fords and crossing points**, where towns and bridges appear;
   - **natural harbours** (sheltered bays) for ports;
   - springs.
4. **The sea:**
   - fish stocks, richest in shallow coastal water;
   - reefs and dangerous coasts;
   - winds and currents that help or hinder sailing.
5. **Natural disasters:** floods, earthquakes, eruptions, wildfires, droughts.
6. **Kinds of forest and plants:**
   - tree species chosen by **biome and temperature**: oak and beech in temperate forest, pine and spruce in the cold north, bamboo in the warm wet south, and so on;
   - each species has its own timber, uses and regrowth time, and some can be **coppiced**;
   - wild food plants.
7. **Fantasy elements:** **yes, there will be magic** (decided 20 Nov), but added later; see [section 11](#11-magic-later-but-planned-for-now). The world generator should leave room for a **magic layer**: where magic is strong or weak, magical materials, dangerous wild regions.
8. **Names** for places, rivers and mountains (later; a local AI could help here).

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

### Factions, kingdoms and politics

*(Added 20 November 2026.)* As the history runs, the peoples organise themselves:

- **Groups of towns form factions.** Grow big enough and they become **small kingdoms**.
- **Big kingdoms have smaller powers underneath them**: lords, provinces, vassal towns. A hierarchy, so there are **politics**.
- **One currency for now.** Different currencies per kingdom would be realistic, but much harder; maybe much later.
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
- **Travel speed depends on the land:**
  - plains are fast and forests are slow; hills and marshes are slower still;
  - a road is faster than open country;
  - a big kingdom might **cut a road through a forest**.

### People change the world

*(Added 20 November 2026.)* The people in the simulation don't just trade; they **reshape the land**, because that's what real people did:

- **Construction:**
  - fields, houses, town halls and markets;
  - ports, bridges and dams;
  - way stations, trade stops and **taverns along the routes**, as there were in real history.
  - Kept **simple**: this must not turn into a colony builder. But towns have these things, and a town that lacks them should suffer for it.
- **Using the land up and putting it back:**
  - a town by a forest can have a timber industry, cutting the forest down and replanting it;
  - farms replace forest;
  - rivers get dammed.
- **What drives them:** every agent (a family, a trader, a town) is always striving for something: food, safety, wealth, status. Their choices add up to the changes we see.

### Forests, regrowth and running out

*(Added 20 November 2026.)* Time matters here: trees take years to decades to grow back. A big world won't run out of resources overall, but **local shortages** are realistic and interesting.

**It really happened.** These figures are approximate, from general history knowledge:
- **England** was mostly forest after the Ice Age. By the Domesday Book (1086) only about 15% was woodland, and later even less, because forest became fields.
- **Iron smelting** burned huge amounts of charcoal and used up woods.
- **Ship timber** (big oaks) was in short supply in later centuries.
- **Coppicing** was the medieval answer: cutting trees to the stump every 7–20 years so they regrow as many poles. It's a renewable wood supply, but no good for big timber. A big oak for beams or ships takes 80–150 years.

That gives a natural mechanic: **managed woodland** (coppice) gives a steady supply of firewood and charcoal; **old forest** gives rare, slow-to-replace big timber.

### Lessons from real history

*(Added 20 November 2026.)* Real examples to borrow from:

- **Rome and Egypt:** Rome was fed by grain shipped from Egypt across the Mediterranean. Cheap sea transport let a city grow far bigger than its own land could feed.
- **The Silk Road:** a long overland route carrying goods **and ideas**. Paper, techniques and new crops spread along trade routes.
- **Ideas and discoveries travel with traders.** A new technique (a better plough, a new crop) could spread from town to town along the routes, faster along busy ones.
- **Taverns, inns and way stations** grew up a day's travel apart along busy roads.

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
- **A headless mode** *(added 20 Nov)*: the simulation runs with **no window**, just the console, at full speed, and can be asked questions (prices over time, populations, trades). Much faster than with graphics, and the main way to test the simulation. **The simulation never depends on the graphics**; the graphics only read the numbers.
- **The base is built in a separate test project first** *(added 20 Nov)*: [`evolution-sandbox`](https://github.com/owenthespoon2/evolution-sandbox), which chooses the engine and graphics and builds the foundation this project then sits on.
- **The foundation, agreed 21 Nov** ([evolution-sandbox note 0](https://github.com/owenthespoon2/evolution-sandbox/blob/main/docs/design/0-foundation.md)):
  - **MonoGame** for drawing, **Dear ImGui** for developer panels and live charts, **Myra or our own UI** for the game's menus and windows.
  - **One simulation library** that never references graphics; a headless console and a window on top. Outside changes are **commands applied between ticks**; **save/load** from day one.
  - **Repeatable:** our own seeded random generator, a fixed tick order, a checksum test. **Parallel steps inside a tick** (read anything, write only your own slot) use the CPU's cores for this one big world.
  - **Data:** common actions counted, **every trade** and other meaningful events in **Parquet + DuckDB**, and agents' **reasons** for decisions logged, so "why are they trading this?" can be answered. **Python** makes reports and does analysis.
  - The shared **Foundation** library comes into this repository as a **git submodule**.
  - Only what's on screen is drawn: a few thousand moving figures at most; the map is drawn once into a picture and updated where it changes.
- **The development PC:** NVIDIA RTX 3060 Ti (8 GB), AMD Ryzen 5 3600 (6 cores, 12 threads), 32 GB of memory. The simulation should run well on it, using all 12 threads for heavy steps like erosion.

## 9. Local AI: an idea to keep

*(Added 20 November 2026.)* The owner experiments with local AI models (Qwen and others) on the 8 GB graphics card, at around 16 tokens per second.

- **An old idea:** an AI that helps run the world, keeping things realistic and in balance, like a "game master".
- **Current thinking:** the realism should come from **hand-coded realistic systems**, which are fast, repeatable and understood. A local model at 16 tokens a second is far too slow to make decisions every tick.
- **Where a local model could help later:**
  - writing things the simulation has *already decided*: town and character names, a chronicle of the world's history, dialogue with traders;
  - running in the background and saving its results.
- **Softened on 20 Nov (agents brainstorm):** never for the masses, but **maybe for a handful of notable people's big decisions** (a lord deciding on war once a year), with every answer recorded in the save so the world stays repeatable. See [section 13](#13-agents-and-the-economy).
- Research notes: [`research/2026-11-20-living-world.md`](research/2026-11-20-living-world.md).

## 10. The layers of the simulation (draft, for discussion)

*(Sketched 20 November 2026.)* The world generator makes the stage; the simulation is the play. It's several layers stacked on each other. Each layer reads the ones below it and changes shared things (the land, stocks of goods, prices), never another layer's insides.

| # | Layer | What it holds | What changes it | Updates roughly |
|---|---|---|---|---|
| 1 | **Land** | Height, rivers, soil, biomes, plus changes people made | World generation; then people: fields, felled forest, roads, dams | rarely |
| 2 | **Nature** | Forests and their regrowth, animals, fish, soil fertility, seasons and weather | Growth, seasons, weather; hunting, fishing, felling | monthly / seasonally |
| 3 | **People** | Groups of people per settlement (pops): race, job, age, health, needs | Births, deaths, hunger, migration, founding new settlements | monthly |
| 4 | **Work and production** | Jobs, recipes, what each place makes from its land | Pops choosing work; resources available | daily / weekly |
| 5 | **Economy** | Markets, stocks, prices, money, barter and credit | Supply and demand, trade arriving | daily / weekly |
| 6 | **Transport** | Traders, caravans, boats, routes, roads, travel times | Traders' decisions; terrain; roads built | daily |
| 7 | **Building** | Houses, fields, markets, town halls, ports, bridges, taverns | Towns investing when they need and can afford it | monthly |
| 8 | **Society and politics** | Factions, kingdoms, lords and vassals, taxes, laws | Growth, wealth, alliances, conflict | yearly |
| 9 | **Knowledge** | Which techniques and crops each place knows | Ideas spreading along trade routes | yearly |
| 10 | **History** | The record of what happened | Everything above; at world generation, layers 3–9 run coarsely for centuries | — |

**The open questions for this part of the design:**
- What does each kind of agent (a family, a trader, a town, a lord) strive for, and how do they choose?
- How much is simulated as groups, and how much as individuals?
- How fast does each layer run, and how do they stay in step (the time-scale problem)?

## 11. Magic: later, but planned for now

*(Added 20 November 2026.)* **There will be magic.** It makes the world far more interesting. But it comes **after** the world and the economy work. It's a third system on top of the world simulation and the economic simulation.

### What the owner likes

- **Mushoku Tensei:**
  - magic is something you **grow from childhood by using it**;
  - talent varies, and a gifted child grows fast;
  - mages are ranked by skill.
- **Frieren:**
  - long-lived elf mages;
  - magic is **knowledge that is researched**, and spreads over decades until a once-rare spell is common.

### Ideas so far

- **Everyone is born with aptitudes:**
  - each person has natural talents (magic among them) that grow with use;
  - race shapes them, e.g. **elves** good at forest and healing magic.
- **Humans:** maybe no special affinity, but the best at **research and education** (universities), so they push magic forward fastest.
- **Long-lived species** (elves) remember and know more, but change more slowly.
- **Magical trade goods by region:**
  - **dwarves forge swords** and other enchanted metalwork;
  - **elves cultivate herbs**;
  - **humans brew potions** or sell research.
- **Magic develops over history:** techniques are discovered and spread along routes, just like other knowledge (simulation layer 9).
- **A full, "scientific" magic system, not Skyrim's.**
  - In Skyrim, magic is mostly one person's fighting tool.
  - Here it's a whole field of knowledge, like Mushoku Tensei's: researched, taught, ranked, with **magic runes** and **magic items** that can be made, sold and traded.
  - It has limits, but it touches everything: crafts, healing, disasters, trade.
- **Limits that keep it from breaking the world.** For example, if casting tires the caster, a mage can't grow crops all day every day, but can stop a flood or a fire once in a while. That helps the world without replacing farming.
- **No general flight magic**, so transport isn't broken. Flying belongs only to particular creatures or races. For example, **giant falcons that live in the mountains**, which are very rare and hard to catch or tame. A tamed one would be an extraordinary, valuable way to carry things.
- **Creatures in the caves:** the underground will have its own life and dangers.

### The risk

Magic can **break things**, especially the economy. If a spell grows food or heals for free, farming and medicine stop mattering. So magic needs **limits and costs**:
- rare talent;
- years of training;
- materials that have to be gathered and traded;
- tiredness.

Research: [`research/2026-11-20-magic-systems.md`](research/2026-11-20-magic-systems.md). Its recommendation fits the ideas above almost exactly:
1. a **talent** number per person, adjusted by race;
2. **capacity that grows with use** up to a ceiling set by talent (Mushoku Tensei);
3. **spells as world knowledge** that spreads over decades, with elves as long-lived researchers (Frieren);
4. **a material cost per use**, so magic creates trade in reagents.

All of it is cheap: a few numbers per person, plus one record per spell.

### When to add it: the decision

**Proposed: leave hooks for it now, build the system later.** It costs almost nothing to leave room for it:

| Hook, built in from the start | Why it costs little now |
|---|---|
| People have a **table of aptitudes and skills**, not fixed jobs | Magic later is just more skills in the same table |
| Goods and recipes are **data, not code** | Magical herbs, reagents and enchanted swords are new rows of data |
| Races are **data**: lifespan, aptitudes, favourite lands | Elves' long lives and affinities are numbers to fill in |
| The world generator can add **one more map layer** | A "magic strength" map is one more 1 km grid, cheap |
| **Knowledge spreads** as its own layer | Spells spread through the same mechanism as better ploughs |

Then, when the world and the economy run well, we design the magic system itself with its own design note.

## 12. Individuals and groups

*(Added 20 November 2026.)* **Can we store hundreds of thousands of individual people with their own skills? Yes, easily.**

| | Rough size |
|---|---|
| One person: race, age, health, home, job, ~32 skill values and a few links | ~100–150 bytes |
| 1,000,000 people | ~100–150 MB |
| This PC's memory | 32 GB, so a million people use under 1% of it |

- **Storage isn't the hard part.** Updating a million simple records once a month takes a fraction of a second on 12 threads.
- **The expensive part is decisions:** finding paths, choosing what to do, matching buyers and sellers. Those are what levels of detail and groups are for.

**The plan: a hybrid, as Dwarf Fortress does.**
- **The masses as groups** (pops). For example: "Riverford: 340 human farmers, 12 smiths, average skills such and such, 3% with magic talent".
- **Notable people as individuals**, each with their own skills, life story and choices: lords, master smiths, mages, traders, founders. Dwarf Fortress does this with its "historical figures", individuals who appear in its generated legends. It has tens to hundreds of thousands of them.
- **A person can step out of the group** when they become notable: the farmer's child with rare magic talent, the trader who gets rich.

### Is this getting too detailed?

**Computing power is not the limit.**
- Dwarf Fortress is mostly single-threaded, and it's slow because it simulates every item, worm and wall tile at 1 m scale around your fort, not because of its world.
- We have 12 threads and design for speed from the start.

**The real limit is our time and understanding**, and the Python lesson: **too many systems switched on at once can't be debugged.** So the rule is:

> **Design wide, build narrow.** Plan room for everything (hooks), but build and switch on one system at a time, and only add the next once the last one works.

## 13. Agents and the economy

*(Brainstormed 20 November 2026. Full detail, worked examples and history in [`design/4.0-agents-brainstorm.md`](design/4.0-agents-brainstorm.md).)*

### Who decides

- **Agents** are whatever makes choices; **things** (land, goods, buildings) don't. The two are separate systems: a family lives in a house, but the house isn't part of the family.
- **Every person is stored** with a name, race, birth year, parents and skills, so everyone has a **family tree**. **Children are born and grow up**, and **marriages** join families and link villages; **royal weddings** link faraway capitals and help trade.
- **The family is the agent** that decides (work, food, buying and selling, moving). Pops are just totals of families.
- **Notable people** (lords, mages, founders, every trader) decide for themselves. **Every trader is tracked individually**: traders are the heart of the game.
- Also agents: **settlements** (villages run by their lord; towns can buy a charter and run themselves), **lords**, **factions and kingdoms**, **guilds**, **monasteries and temples**, and **bandits**. Bandits come from hard times (a village ruined by disaster) and can **go straight**, founding a village or being hired as guards.
- **Races organise differently:** dwarves in **clans**, elves under **councils of elders**, humans in **feudal** lords and vassals. Inheritance rules differ by race too.
- **Only humans, elves and dwarves at first.** Later perhaps merfolk, gnomes, giants and our own **tree-folk** (inspired by Tolkien's Ents). **No orcs, no lizardfolk.** **Monsters** changed by magic, carrying valuable magic stones as in *Mushoku Tensei*.
- **Religion** will be its own layer, like magic: religions develop and spread, shaped by race and land. **Serfdom: not for now** (too realistic for this fantasy world; maybe a future "super-realistic" mode).

### How they decide

- **A ladder of needs:** food → warmth and shelter → safety → comfort → standing and the future. The lowest unmet need comes first.
- **Two modes:**
  1. **Scoring** (*utility AI*): score every option from the needs, weighted by **personality**, with **habit** so people don't change their lives lightly. Built first, as the baseline.
  2. **Evolving neural networks** (*neuroevolution*): each family's small network is **inherited from its parents with small mutations**, and families that survive and prosper pass theirs on. **The owner's favourite idea**, and a genuine research question: nobody seems to have shown trade emerging from evolution alone.
  3. *(Added 21 Nov, later.)* **Reinforcement learning:** networks that learn during their lives from a reward that describes what people want (being fed, comfortable, secure). Likely the best fit for agents that "act like people". **Imitation learning** can give them a head start by copying the scoring AI first. Order: see whether trade emerges by evolution in `evolution-sandbox` first, then try RL.
- **Every family has a personality**, inherited by its children; races have tendencies.
- **Limited knowledge:** agents only know news that has reached them, so traders must travel to learn prices. **Memories** (famines, robberies) nudge choices for years.
- **Local language models** only for a handful of notable people's big decisions, with every answer recorded so the world stays repeatable.

### The economy emerges

- **Nobody writes the prices.** Each agent **believes** what goods are worth (a range, coloured by local prices); buyers and sellers bid and ask on **market days**, trade halfway, and learn. **Wages** form the same way.
- **Market days** are chosen by each town's lord or council, so traders move between towns; yearly **fairs**; hamlets barter any time.
- **Money is minted from silver and gold, and at first only the dwarves mine and mint it.** They grow rich, but coin is their main export and they must buy food. From that: minting profit, trusted clan coins with **clan marks**, **debasement** by greedy kings, coins flowing outward so faraway hamlets **barter**, food embargoes and minting strikes as politics, coins wearing out, and later other minters and counterfeiters.
- **Banks** for merchants and kings (bills of exchange make long journeys safer; kings who don't repay ruin them). Peasants use credit with neighbours.
- **Track everything:** every trade is recorded, with **statistics viewers** for prices, amounts of goods and trades over time.
- **Watch for real economics emerging:** prices evening out along routes, von Thünen's rings of fields around towns, market towns a day apart, boom-and-bust harvest cycles, the Malthusian trap, wages rising after plagues, inflation after a silver strike.

### Still to brainstorm

Goods and recipes; how agents change the world; keeping it cheap to run; how lords appear; towns buying freedom; religion; war; disease; law and taxes; health and lifespans; culture and language. The checklist is in the design note.
