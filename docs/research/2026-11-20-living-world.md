# Research: simulating a living world

*20 November 2026. A web research scout (Sonnet) looked at how games keep a whole world running, how civilisations spread, medieval economies, animals, and local AI models. **(F)** = found in a source, **(O)** = opinion. It read search snippets only.*

## 1. Simulating everywhere at once (level of detail)

- **Dwarf Fortress (F):**
  - history keeps running after world generation, while you play, but slowly;
  - generation time grows with the number of civilisations and sites, so both are capped.
  - Sources: [World activities](https://dwarffortresswiki.org/World%20activities), [World gen](https://dwarffortresswiki.org/index.php/DF2014:World_gen)
- **Victoria 3 (F):**
  - not everything runs every tick: there are yearly, monthly, weekly and daily jobs;
  - people are simulated as **pops** (groups), and pops are merged to keep it fast.
  - Source: [dev diary 76](https://www.paradoxinteractive.com/games/victoria-3/news/dev-diary-76-performance)
- **Songs of Syx (F):** 5,000–12,000 individual citizens run smoothly, but that's one town; pathfinding was the main cost. [Store page](https://store.steampowered.com/app/1162750)
- **The usual pattern (O):**
  - groups and averages everywhere;
  - individuals only near where you're looking;
  - "promoted" to individuals when you arrive, "demoted" back when you leave.

## 2. Where civilisations start and how they spread

- **DF (F):** terrain first, then sites appear as history runs, with roads, towns and cities forming over time.
- *Not confirmed:* the common claim that DF puts dwarves in mountains, elves in forests and humans on grassland.
- **Real settlement factors (O, standard geography):**
  - fresh water and fertile soil;
  - defensible ground;
  - river crossings, river mouths and harbours;
  - meeting points of routes.
  - Score every cell on these, then weight the scores differently for each race.
- **History (O):** run founding, expansion and collapse as **events per civilisation per year**, rather than simulating every person.

## 3. Medieval economy

- **Coin was short (F):** everyday trade used small silver coins, but there were never enough of them. People used barter, foreign coin and especially **credit between neighbours**. Barter worked best in small communities. Sources: [LSE](https://researchonline.lse.ac.uk/id/eprint/79742/1/blogs.lse.ac.uk-How%20a%20shortage%20of%20coins%20precipitated%20a%20depression%20in%2015th%20century%20England.pdf), [Dyer](https://ideas.repec.org/h/pal/psitcp/978-3-319-90251-7_1.html)
- **Transport costs, sea : river : land (F):**
  - figures vary by source: about 1 : 3 : 4 for Roman Britain, 1 : 4 : 8 for 14th-century England;
  - the famous 1 : 4 : 28 is not confirmed;
  - one Roman estimate: carrying wheat 100 miles by land cost 55% of its value, but only 1.3% by sea.
  - Sources: [Scheidel/ORBIS](https://www.ancientportsantiques.com/wp-content/uploads/Documents/ETUDESarchivees/MedNavigationRoutes/ORBISprices-Scheidel2013.pdf), [Watkins](https://sjsu.edu/faculty/watkins/rome.htm)
  - **Water transport is many times cheaper than land.**
- **Doran and Parberry, "Emergent Economies for Role Playing Games" (F):** a cheap way to update prices from supply and demand, grounded in economic theory. [Paper](https://ianparberry.com/pubs/econ.pdf) (not read in detail yet)

## 4. Animals

- **Research models (F):** animal numbers stored per grid cell, with herd movement and hunting pressure. [Serengeti model](https://pmc.ncbi.nlm.nih.gov/articles/PMC3026817/figure/pone-0016370-g004)
- **The simplest version (F):** each population grows towards what the land can support, minus what's hunted ("logistic growth"). [USGS](https://www.usgs.gov/data/hunter-and-prey-linked-population-models)
- **Cheap approach (O):**
  - a herd count per region;
  - herds migrate with the seasons;
  - hunting subtracts from the count;
  - individual animals appear only near where you're looking.

## 5. Local AI models

- **Size (F):** a 3–4 billion-parameter model, compressed to about 4 bits, fits a 6 GB graphics card for NPC dialogue. *(This PC actually has an 8 GB RTX 3060 Ti, which fits roughly 7–8 billion-parameter models at 4 bits.)* [Guide](https://bestllmfor.com/verticals/local-llm-for-game-dev/)
- **What works (F):** small models do well when given **structured facts** to write about; free invention without grounding doesn't work well yet. [Ember Quest](https://emberquest.kimmoi.people.aws.dev/), [llmnpc](https://git.mitjafelicijan.com/llmnpc/about/), [arXiv 2511.10277](https://arxiv.org/html/2511.10277v1)
- **Speed (O):**
  - at ~16 tokens per second, a 60-word line takes about 5 seconds;
  - fine for dialogue, chronicles and names written in the background;
  - far too slow to make simulation decisions every tick.
  - **Keep all decisions rule-based; use the AI only to describe what the simulation already decided.**

## What to copy (scout's top six)

1. Generate the land, then run **years of coarse history** (founding, trade, expansion), with caps on sites and years.
2. **Tiered tick rates:** towns monthly, trade seasonally, individuals only when watched.
3. **Pops:** people grouped by trade and age per settlement, made individual only near the viewer.
4. **A transport-cost network** with adjustable sea, river and land costs; roads emerge from counting trade along each link.
5. **Barter and credit in hamlets, coin in towns**, with a shortage of small change as a mechanic; prices updated from supply and demand.
6. **Animals as per-cell populations** with seasonal migration and hunting. Local AI optional: background flavour text from structured facts.
