# Research: neural networks and local AI for agent decisions

*20 November 2026. A web research scout (Sonnet) looked at whether neural networks or local language models could drive agents' decisions as an optional second "mode" next to scoring (utility AI). **(F)** = found in a source, **(O)** = opinion. Several results were secondary summaries; full papers weren't read unless stated.*

## 1. What's been tried

- **Creatures (F):** its creatures ("norns") had neural-network brains with simulated body chemistry. One analysis puts it at ~952 neurons and ~5,000 connections, learning by experience. Its creator said they could learn and generalise but not "think". [Wikipedia](https://en.wikipedia.org/wiki/Creatures_(video_game_series)), [Zucconi](https://www.alanzucconi.com/2020/07/27/the-ai-of-creatures/)
- **Black & White (F):** an early game that used a neural network for its creature.
- **NERO (F):** agents trained by the player through real-time **neuroevolution** (networks bred and mutated). [Paper](https://www.cse.unr.edu/~bdbryant/papers/stanley-2005-cig.pdf)
- **Developers hesitate (F):** evolved NPC behaviour can be too unpredictable. [Paper](https://core.ac.uk/download/81666697.pdf)
- **Stanford "Generative Agents" (F):** 25 language-model agents with memories, reflection and plans; take any part away and they seemed less believable. [Paper](https://arxiv.org/pdf/2304.03442v2)
- **Project Sid (F):** 500–1,000 language-model agents in Minecraft; professions, voting on laws and spreading religion emerged. But small flaws in single agents snowballed into society-wide problems, and runs differed from each other. [Paper](https://arxiv.org/abs/2411.00114)
- **Salesforce AI Economist (F):** reinforcement learning for tax policy; worked, but only with ~10 agents, was unstable, and the agents **gamed the rules** (timing a house sale around tax rates). [Paper](https://arxiv.org/pdf/2004.13332)
- **(O)** Every success is small: tens to about 1,000 agents. None is a repeatable, balanced economy of 200,000.

## 2. Cost of a small network

- **(O)** A small network (20 inputs, 32 hidden, 10 outputs) is ~960 multiply-adds per decision; 200,000 families ≈ 0.2 billion per monthly round: **well under a second on one thread**. No graphics card needed.
- **(O)** Hand-written (an array of weights and a loop) is simpler than ML.NET, ONNX Runtime or TorchSharp, and keeps results repeatable. Heavy libraries only for training, outside the simulation.

## 3. Training it

- **Reinforcement learning (F):** needs a reward, and agents exploit whatever the reward misses.
- **Neuroevolution (O):** fits families well: weights inherited with mutation, "fitness" = the family survives and prospers. No reward engineering. Weakness: you can't easily see **why** a network chose something, which clashes with "the owner must understand everything".
- **Imitation (O):** train the network to copy the scoring AI. Safest, adds nothing new, but a good first test.
- **Repeatability (O):** fine if the weights are fixed and the maths is done in a fixed order; learning *during* play makes it much harder.

## 4. Local language models

- **Speed (F, estimate):** an 8-billion-parameter model, compressed, on a 3060 Ti: roughly 40–60 tokens per second (to be measured on this PC). [Estimate](https://willitrunai.com/can-run/hf-nousresearch--hermes-2-pro-llama-3-8b-gguf-on-rtx-3060-ti-8gb)
- **(O)** ~2–3 seconds per decision → ~1,200–1,800 decisions an hour. One monthly round for 200,000 families would take **110–170 hours**. Impossible for the masses.
- **(O)** Fine for **a few notable characters**: a lord deciding on war once a year, short reflections, flavour text. Dozens of calls per game year.
- **Not repeatable (F):** even at "temperature 0" the same prompt can give different answers (one test: 80 different outputs in 1,000 runs). [Article](https://hidekazu-konishi.com/entry/reproducible_llm_inference.html)
- **(O)** Fix: **record every answer** in the save file, keyed by seed, day and agent. Replays read the record instead of asking the model again.

## 5. Recommendation (O)

- **A hybrid is feasible.** Scoring stays the default and the only source of truth for the masses.
- **Cheapest real experiment:** a small hand-written network "mode" behind the same decision interface, with the same inputs as the scores.
  1. imitation: train it to copy the scoring AI and check the world's statistics stay similar;
  2. neuroevolution: weights inherited across family generations, fitness = survival and wealth;
  3. compare the two modes: outcomes, speed, repeatability (same seed → same world).
- **Separately:** try a local model for a handful of lords, recording prompts and answers; about 20 decisions will show whether it's worth it.
