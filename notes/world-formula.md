# The world formula: learning notes

*Started 19 September 2026. These notes follow the layer plan in [`PROJECT.md`](../PROJECT.md#the-formula), and grow as we go.*

The world is one function: give it a position (x, y) in km, and it gives back the height of the ground there in metres. Sea level is 0 m. The function is built from layers added together, each understood before the next.

---

## Layer 1: the big shape ✅

```
height(x, y) = plain(y) + hills(y) − lakeDip(x, y)

plain(y)    = 1 × (y + 80)                     rises 1 m per km north; coast at y = −80
hills(y)    = 1500 × smoothstep(15, 200, y)    starts at y = 15, peaks off the map at y = 200
lakeDip     = 63 × (1 − smoothstep(0, 20, r))  r = √(x² + y²), distance from the centre
```

### Smoothstep

On its own, for t between 0 and 1:

```
s(t) = 3t² − 2t³   ( = t × t × (3 − 2t) )
```

| Property | Why it matters |
|---|---|
| s(0) = 0 and s(1) = 1 | It goes from "none" to "all" |
| s′(t) = 6t − 6t² = 6t(1 − t), so s′(0) = s′(1) = 0 | It starts and ends **flat**, so there are no sharp creases where it joins other land |
| s(0.5) = 0.5, and s(1 − t) = 1 − s(t) | Symmetric about the middle |

It's the simplest polynomial that does all of that: the one cubic with those four conditions (start value, end value, start slope, end slope).

To use it between any two values a and b, first turn the position into a fraction, then clamp it:

```
smoothstep(a, b, v):   t = (v − a) / (b − a), kept between 0 and 1;   result = s(t)
```

### Why the lake is where it is

A lake fills its dip until the water spills over the **lowest point of the rim**. Because the land tilts south, that point is on the south side, which is exactly where River 2 leaves. A lake only forms if the dip is deeper than slope × radius: here 63 m against 1 × 20 = 20 m. The result is a lake surface at about 60 m, about 44 m deep and about 28 km across.

### Why the hills "peak off the map"

`smoothstep(15, 200, y)` reaches its top at y = 200, but the map ends at y = 100. So on the map we only see the lower half of the S-curve, hills getting steeper towards the north, and the mountains are out beyond the edge. A formula doesn't stop at the map's edge.

---

## Layer 2: noise (in progress)

**What we need:** randomness that is **smooth** (neighbours have similar heights), **repeatable** (the same point always gives the same answer, so the world stays a formula), and **controllable in size**.

### The hash: a random number that belongs to a position

`Math.random()` gives a different answer every call, which is no good. A hash scrambles its inputs into a number that looks random but is always the same for the same inputs:

```ts
function hash(i: number, j: number, seed: number): number {
  let h = (Math.imul(i, 374761393) + Math.imul(j, 668265263) + Math.imul(seed, 1442695041)) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;   // between 0 and 1
}
```

It multiplies by big odd numbers and mixes the bits with XOR and shifts (`^`, `>>>`). `Math.imul` is whole-number multiplication that wraps around at 32 bits. You don't need to understand the particular constants; they're simply known to scramble well. Change the seed and you get a different world.

**White noise** is a hash value for every square kilometre. Neighbours have nothing to do with each other, so it looks like TV static: useless as land, but it's the raw material.

### Value noise in 1D, worked through

Grid points every `size` km, each with a random height from the hash. For any position x:

```
i = floor(x / size)       the grid point to the left
t = x / size − i          how far towards the next grid point: 0 at the left one, 1 at the right one
a = hash(i),  b = hash(i + 1)
height = a + (b − a) × s(t)
```

**How t moves between the points.** Say `size` = 20 km, a = 0 and b = 10, with grid points at x = 40 and x = 60. As x walks from 40 to 60, x / size walks from 2 to 3, i stays at 2, and t = x / 20 − 2 walks steadily from 0 to 1. t is just "the fraction of the way across". Smoothstep then bends that steady walk into an S-curve:

| x (km) | t | s(t) | height = 0 + (10 − 0) × s(t) | straight line (no smoothstep) |
|---|---|---|---|---|
| 40 | 0 | 0 | 0 | 0 |
| 45 | 0.25 | 0.156 | 1.56 | 2.5 |
| 50 | 0.5 | 0.5 | 5 | 5 |
| 55 | 0.75 | 0.844 | 8.44 | 7.5 |
| 60 | 1 | 1 | 10 | 10 |

At x = 60, t jumps back to 0: i becomes 3, a becomes the old b, and a new b comes from hash(4). The curve carries on into the next segment.

⚠ **Brackets matter:** `a + (b − a) × s(t)`. Without them, `a + b − a × s(t)` means something different.

**Why there are no creases: the derivative.** By the chain rule:

```
d(height)/dx = (b − a) × s′(t) × (1 / size)
```

s′ is 0 at t = 0 and t = 1, so the slope is exactly 0 arriving at every grid point from the left, and 0 leaving it to the right. The slope is continuous, so the land is smooth. With a straight line instead, the slope is (b − a)/size on one side and (c − b)/size on the other: it jumps, and that jump is a crease in the land.

**The side effect:** the slope is 0 at *every* grid point, so every grid point is a small flat spot (a top, a bottom or a shelf). That's part of why value noise looks lined up with its grid, and one reason Perlin noise exists.

### Value noise in 2D (next)

Each point sits in a square of four grid points. Blend along x across the bottom pair and across the top pair, then blend those two results along y:

```
i = floor(x / size),  j = floor(y / size)
u = s(x / size − i),  v = s(y / size − j)
bottom = lerp(hash(i, j),     hash(i + 1, j),     u)
top    = lerp(hash(i, j + 1), hash(i + 1, j + 1), u)
height = lerp(bottom, top, v)                      lerp(a, b, w) = a + (b − a) × w
```

### Octaves (fBm) (next)

Several layers of noise added together, each **half the size** and **"roughness" times as strong** (usually 0.5) as the one before, then divided by the total strength so the result stays between −1 and 1:

```
fBm(x, y) = Σ  roughnessᵒ × noise(x, y, size / 2ᵒ, seedₒ)   ÷   Σ roughnessᵒ      for o = 0, 1, 2, …
```

### Perlin and simplex (after that)

- **Perlin** gives each grid point a random *slope direction* instead of a random height, which hides the grid much better.
- **Simplex** is Perlin's faster successor and uses triangles instead of squares.
- The plan is to understand value noise fully, then use simplex for the real world.

### Then: noise in our world

```
height = Layer 1 + roughness(x, y) × fBm(x, y)
```

Roughness is a few metres on the lowlands and hundreds of metres in the hills. The coast and lake shore wiggle by themselves. Noise can dig ponds, breach the lake's rim or bump the river's path, which is why rivers (Layer 3) get carved afterwards.

---

## Where we stopped

**19 September, 1am.**
- **Understood:** the hash, white noise, and the idea of value noise and octaves. Worked through the 1D blend with a = 0, b = 10.
- **Next session, one step at a time:**
  1. The 1D blend and smoothstep's derivative, if anything is still unclear
  2. Value noise in 2D
  3. Octaves
  4. Perlin and simplex
  5. Adding noise to our map, choosing roughness for the lowlands and the hills
- The interactive explorers (Layer 1 map, noise explorer) are in the chat of 19 September. In a new session, ask Claude to rebuild them.
