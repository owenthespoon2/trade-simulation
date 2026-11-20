# Research: magic systems for a simulated world

*20 November 2026. A web research scout (Sonnet) compared fantasy magic systems and how to keep magic from breaking an economy. **(F)** = found in a source, **(M)** = the scout's memory (not verified), **(O)** = opinion. Several wiki pages were blocked, so some details come from search summaries.*

## Systems compared

| System | How it works | Limits and costs | Fits a simulated economy? |
|---|---|---|---|
| **Mushoku Tensei** | Inborn affinity plus a mana pool; seven spell tiers (Beginner, Intermediate, Advanced, Saint, King, Emperor, God); chants trigger spells (F) | Higher tiers need far more mana; overuse causes fainting, damage or death (F) | **Yes:** a talent number plus a pool that grows with use |
| **Frieren** | Magic is researched, learned and spread; mages graded by an association (F) | Raw mana isn't everything; new spells take years of research (F) | **Yes:** knowledge spreading is the key mechanic |
| **Mistborn** (Allomancy) | Burn swallowed metals for fixed powers; inherited (M) | The metal is used up: every use has a material cost (M) | **Very good:** the cost is a tradable good |
| **Wheel of Time** | Channel a limited power; strength varies by person (F, M) | A built-in cost and weakness (F) | Moderate: rare, varying talent is easy to model |
| **Earthsea** (true names) | Knowing a thing's true name gives power over it (M) | Knowledge and balance (M) | Poor: hard to turn into numbers |
| **Kingkiller** (sympathy) | Link two objects and move energy between them; energy is conserved (M) | Energy conservation; mental strain (M) | Good: conservation is a useful economic rule |
| **D&D spell slots** | Prepare spells into slots; a spell is used up when cast (F) | Slots per day; rest restores them | Easy to count, but made for a game, not a world |
| **Dwarf Fortress** | Necromancers and "source" slabs now; procedural magic planned, not released (F) | — | Reference only |

## Brandon Sanderson's laws of magic (F)

[Lecture notes](https://www.brandonsanderson.com/)
1. **Understanding equals power:** the reader can only be impressed by magic whose rules they know.
2. **Limits matter more than powers.**
3. **Expand what exists before adding new things.**

Hard magic (clear rules) and soft magic (deliberately mysterious) are a spectrum. **A simulation is hard magic by nature**: the computer needs explicit rules.

## Mushoku Tensei's rules (F, mostly from wiki summaries)

- **Rank by difficulty.** A mage's rank is the strongest spell they can cast:
  - Saint-tier spells can change the weather;
  - Emperor-tier spells cover whole regions;
  - God-tier spells reach continents.
- **Capacity can grow:**
  - it was long thought fixed at birth;
  - Rudeus showed that **using up and rebuilding mana in childhood enlarges the pool**;
  - inborn talent sets the potential, not the result.
- **No unit for mana** in the series.
- **Chants trigger spells.** Experts shorten them; silent casting is rare.
- **The elements** (fire, water, wind, earth) can be combined.

Sources: [Game Rant](https://gamerant.com/mushoku-tensei-magic-spells-explained/), the Mushoku Tensei wiki (Mana, Magic).

## Frieren's rules (F)

- **Zoltraak, a spell spreading through history:**
  - a demon invented it, and nothing could stop it;
  - he was sealed away for about 80 years;
  - meanwhile, humans studied the spell, adapted it and invented shields against it;
  - it ended up as a standard spell for apprentices.
- **Long life:** the elf Frieren followed and guided that research across generations. Short human lives drive steady, cumulative progress.
- **Grading:** the Continental Magic Association grades mages. The first-class exam runs every three years, and only about 45 first-class mages exist.
- **Concealment:** mages sense each other's mana, and can hide their own.

Sources: [mystiqora](https://mystiqora.com/?p=2506), [MetaFilter Fanfare](https://fanfare.metafilter.com/23922/Frieren-Beyond-Journeys-End-First-Class-Mage-Exam).

## Keeping magic from breaking the economy (O, common worldbuilding advice)

Sources: [LegendKeeper](https://www.legendkeeper.com/), [EN World](https://www.enworld.org/).

1. **Rare talent:** few can cast at all, so most of magic's effect comes from a small elite.
2. **Physical ingredients:** reagents cost money, so magic has a supply chain and regions have something to trade.
3. **Cost per use:** mana pools, tiredness and recovery time limit what one mage can do in a day.
4. **Long training:** capacity grows only over years, so magic can't flood the world overnight.
5. **Institutions:** guilds, academies and licences ration access. Guild secrets are medieval intellectual property.
6. **Monopolies:** supply can be held back even when something isn't rare.
7. **Services, not vending machines:** healing and enchanting are paid, often licensed, services.
8. **Slow spread:** spells spread slowly, and the best versions stay secret, as with Zoltraak.

## Long-lived species (O, mostly fan discussion)

- Usually **fewer children**, though writers disagree.
- Elves become **keepers of history and knowledge**, but short-lived humans may out-innovate them.
- **Slow political and cultural change**, and a risk of overconfidence.
- Elf lifespans range from 300 to over 1,000 years across settings. Pick one and keep it.

## Cheap or expensive to simulate (O)

- **Cheap (a few numbers per person):**
  - talent, fixed at birth;
  - capacity that grows with use;
  - a rank worked out from capacity;
  - a daily mana budget that refills.
- **Cheap (stored once for the whole world):** the set of known spells, with when each was discovered and how fast it spreads in each region.
- **Expensive:**
  - a list of spells for every person;
  - simulating every single casting;
  - true-name or energy-link physics;
  - inventing new spells procedurally.

## Recommended traits for a simulation-friendly magic system (O)

1. **A talent number** (inherited or random, adjusted by race) that decides whether someone can cast at all.
2. **Capacity that grows with use and age, up to a ceiling set by talent.** The Mushoku Tensei mechanic, costing one number per person.
3. **Spells as world knowledge that spreads over decades**, with long-lived elves as researchers who keep it going. The Frieren mechanic, costing one record per spell, not per person.
4. **A material or time cost per use**, so magic creates demand for reagents and labour, and regions have something to trade.
5. *(Optional)* **Ranks** from capacity thresholds, for guild and licence rules. No extra data per person.
