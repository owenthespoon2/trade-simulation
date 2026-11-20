# Research: evolving neural-network agents and emergent behaviour

*20 November 2026. A web research scout (Sonnet) looked for case studies of agents with small neural networks that **evolve** (weights inherited with mutation, natural selection by survival) in simulated worlds, what emerged, the lessons, the tools, and a small test project. **(F)** = found in a source, **(O)** = opinion or background knowledge not checked this session.*

## 1. Case studies

| Project | Method | What emerged | Lesson |
|---|---|---|---|
| **Polyworld** (Larry Yaeger) | evolving networks in a 3D ecology; agents see coloured pixels | predators, mimicry, grazing, swarming, some communication, stable "species"; brains grew richer over time (F) | **survival alone**, with no hand-written goal, gave rich behaviour. [Paper](https://shinyverse.org/larryy/Yaeger.ALife3.pdf) |
| **The Bibites** | creatures with empty starting brains that evolve (NEAT-like) | herding, a host–parasite relationship (mostly player reports) (F) | very close to what we want. [Wiki](https://the-bibites.fandom.com/wiki/Bibites) |
| **Avida / Tierra** | digital evolution of programs (not neural networks) | rich diversity, then it petered out; parasites kept complexity rising (F) | a static world goes stale; **other living things** keep evolution going. [Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC4267771) |
| **NEAT / rtNEAT / NERO** (Ken Stanley) | networks that start simple and grow, with "species" protecting new ideas (F) | NERO: soldiers trained by the player in real time | the standard method for evolving network shapes. [Thesis](http://nn.cs.utexas.edu/downloads/papers/stanley.phd04.pdf) |
| **Neural MMO** (OpenAI, then MIT) | reinforcement learning, not evolution | populations spread into different regions; more populations → more specialisation; a later version added professions and exchange (F) | [OpenAI](https://openai.com/index/neural-mmo), [specialisation paper](https://mlanthology.org/iclrw/2022/suarez2022iclrw-specialization) |
| **Hide-and-seek** (OpenAI) | reinforcement learning | six phases of strategy: shelters, ramps, an arms race (F) | competition creates arms races, but it took ~500 million games. [Paper](https://arxiv.org/pdf/1909.07528) |
| **Social dilemmas** (DeepMind) | reinforcement learning | whether agents cooperate depends on the world's structure (F) | [Paper](https://arxiv.org/pdf/1702.03037) |
| **Emergent bartering** (Johanson et al., DeepMind, 2022) | reinforcement learning | agents produced, traded and consumed; prices followed supply and demand; with fruit growing in different regions, **price regions** appeared and some agents became **traders carrying fruit between them** (F) | the **closest example to our goal**. [Paper](https://arxiv.org/abs/2205.06760), [blog](https://deepmind.google/blog/emergent-bartering-behaviour-in-multi-agent-reinforcement-learning/) |
| **Sugarscape** (Epstein and Axtell, 1996) | simple rules, no learning | with trade: a market, bigger populations, more unequal wealth, prices near equilibrium (F) | the **world's structure** (two goods, different needs) does most of the work. [Book](https://www.brookings.edu/books/growing-artificial-societies) |
| **Evolved signalling** | evolved networks | communication evolved, sometimes without being pushed (F) | [Paper](https://www.biorxiv.org/content/10.1101/2022.08.16.504071.full.pdf) |

**Not found:** an example where **trade emerged from neuroevolution alone**. (O) Probably a real gap: treat it as research, not a safe bet. That also makes it exciting.

## 2. Lessons and pitfalls

- **Diversity shrinks** as evolution optimises (F). Remedies: gentle selection, extinction events, other populations to compete with. [Slides](https://www.cs.utexas.edu/~risto/cs378ne/private/slides/9.1_Openended-4up.pdf)
- **Interacting populations** (parasites, rivals) drive complexity and specialisation (F).
- Rules of thumb (O):
  - fitness = **survival and reproduction only**;
  - **make specialisation pay**: two resources in different places, a need for both, carrying limits and travel costs, so nobody can do everything alone;
  - 200–1,000 agents; mutate ~5–10% of weights by small random amounts, with rare big jumps;
  - children copy one parent first; mixing two parents later;
  - expect **thousands of generations**; tiny networks and a few hundred agents run fast on one core;
  - repeatable: seeded randomness, fixed update order; use the 12 threads by running **one world per thread**;
  - **measure**: population, average energy, diversity of weights, counts of each behaviour, inequality (Gini), trades per tick, exchange ratios (a stand-in for prices); log to CSV and chart;
  - **always run a control**: the same world with trading switched off.

## 3. Tools

- **SharpNEAT** (C#, version 4.1.0 for .NET 8) (F) exists but suits "score a network against a test" more than a living world where agents are born and die (O). Borrow ideas from it, not the whole library.
- **Hand-written is simpler (O):** a small network is ~50 lines of C#; evolution = copy the parent's weights and add small random noise. Growing network shapes (NEAT) can come later.
- **Reading:** Stanley's NEAT thesis; Lehman and Stanley, "Abandoning Objectives: Evolution through the Search for Novelty Alone" (2011); *Why Greatness Cannot Be Planned* (Stanley and Lehman, 2015; a book, many free talks about it); Yaeger's Polyworld papers.

## 4. A suggested toy world

64 × 64 grid, 300–600 agents, each with a small network (~12 inputs, 8 hidden, 6 outputs). Inputs: food nearby, own energy, own inventory. Outputs: move, eat, gather, give. Energy 0 → death. Enough energy → a child with mutated weights.

1. **Survival:** one resource. Evolved agents should beat random wandering; same seed → same result. Chart population and energy.
2. **Two resources:** A and B grow in separate zones; agents need both; travel costs and carrying limits. Look for zone preferences, migration and different strategies.
3. **Exchange:** add "give to a neighbour". Measure gifts returned, trades, specialisation, exchange ratios, against a no-giving control. (O) The hard step; if it fails, add memory or recognising individuals.
