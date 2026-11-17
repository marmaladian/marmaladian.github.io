---
toc: true
toc_depth: 3
---

# Game Tree Search

Game tree search algorithms are at the heart of classical and modern game-playing AI. From the brute-force look-ahead of **alpha-beta pruning** to the simulation-based approach of **Monte Carlo Tree Search**, these methods define how a program decides what move to make.


## Monte Carlo Methods

Monte Carlo methods are a broad family of algorithms that use random sampling to obtain numerical results. The name comes from the Monte Carlo Casino in Monaco — a nod to the role of chance.

The core idea: instead of computing an exact answer analytically, you run many random experiments and aggregate the results. As the number of samples grows, the estimate converges on the true value.

### Applications

Monte Carlo methods appear across many domains:

- **Integration** — estimating areas and volumes by sampling random points
- **Physics simulation** — particle transport, radiation shielding
- **Finance** — pricing derivatives, risk modelling
- **Game playing** — evaluating positions by simulating random play-outs

![Monte Carlo estimation of pi](https://placecats.com/600/350 "side")

### A Simple Example

Estimating π: place a unit circle inside a 2×2 square. Sample random points uniformly in the square. The fraction that fall inside the circle approximates π/4.

```python
import random

def estimate_pi(n):
    inside = 0
    for _ in range(n):
        # extra long lines will cause the code block to extend beyond the width of the centre column. but what if the lines are too long to fit on the page?
        x, y = random.uniform(-1, 1), random.uniform(-1, 1)
        if x**2 + y**2 <= 1:
            inside += 1
    return 4 * inside / n
```

As *n* increases, the estimate improves — but slowly. Monte Carlo converges at O(1/√n), so doubling precision costs four times as many samples.

## Alpha-Beta Pruning

Alpha-beta pruning is an optimisation of the **minimax** algorithm, the classical approach to two-player zero-sum games.

### Minimax

Minimax assumes both players play optimally. The maximising player picks the move leading to the best outcome; the minimising player picks the worst outcome for their opponent. The algorithm explores the full game tree to a fixed depth, then evaluates the leaf nodes with a heuristic.

The problem: the tree is exponential in depth. Chess has a branching factor of roughly 35. At depth 6, that's 35⁶ ≈ 1.8 billion nodes.

![A minimax game tree](https://placecats.com/700/400 "wide")

### Pruning

Alpha-beta pruning avoids exploring branches that cannot influence the final decision.

- **α** — the best value the maximiser is guaranteed so far
- **β** — the best value the minimiser is guaranteed so far

If at any point β ≤ α, we can stop searching the current branch. The subtree is *pruned* — we already know neither player would choose to go there.

```
function alphabeta(node, depth, α, β, maximising):
    if depth == 0 or node is terminal:
        return evaluate(node)
    if maximising:
        value = -∞
        for child in node.children:
            value = max(value, alphabeta(child, depth-1, α, β, false))
            α = max(α, value)
            if β <= α:
                break  # β cutoff
        return value
    else:
        value = +∞
        for child in node.children:
            value = min(value, alphabeta(child, depth-1, α, β, true))
            β = min(β, value)
            if β <= α:
                break  # α cutoff
        return value
```

### Performance

| Move ordering | Nodes explored (depth 6, branching 35) |
|---|---|
| No pruning (pure minimax) | ~1.8 billion |
| Random ordering | ~35³ ≈ 42,000 (average case) |
| Perfect ordering | ~35³ ≈ 42,000 (best case) |

With perfect move ordering, alpha-beta reduces the effective branching factor from *b* to *√b*, doubling the searchable depth for the same compute budget.

Alpha-beta powered the strongest chess programs through the 1990s and 2000s, including Deep Blue.

---

## Monte Carlo Tree Search

Monte Carlo Tree Search (MCTS) takes a different approach. Rather than exploring the tree exhaustively with a heuristic evaluator, it builds the tree *selectively* using random simulations to estimate node values.

MCTS became prominent after its success in Go, where the branching factor (~250) makes alpha-beta impractical and good heuristics are notoriously difficult to design.

![MCTS tree expansion](https://placecats.com/700/450 "full")

### The Four Phases

Each iteration of MCTS has four steps:

1. **Selection** — traverse the tree from the root, choosing nodes using a *tree policy* (usually UCB1) until reaching an unexpanded node
2. **Expansion** — add one or more child nodes to the tree
3. **Simulation** — run a *rollout* (random playout) from the new node to a terminal state
4. **Backpropagation** — propagate the result back up through the ancestors, updating visit counts and value estimates

```
function mcts(root, budget):
    for _ in range(budget):
        node = select(root)         # traverse with UCB1
        child = expand(node)        # add a new child
        result = simulate(child)    # random rollout
        backpropagate(child, result)
    return best_child(root)
```

### The UCB1 Formula

The tree policy balances *exploration* (trying less-visited nodes) against *exploitation* (favouring nodes with high win rates):

> UCB1 = w/n + c · √(ln N / n)

Where:
- *w* = wins from this node
- *n* = visits to this node
- *N* = visits to the parent
- *c* = exploration constant (typically √2)

A node with many visits but a mediocre win rate may lose out to a less-visited node with a higher uncertainty bonus.

### Comparison

MCTS can be stopped at any time and will return the best move found so far. Alpha-beta must search to a fixed depth before it can give a reliable answer.


| Property | Alpha-Beta | MCTS |
|---|---|---|
| Requires heuristic evaluator | Yes | No |
| Handles large branching factors | Poorly | Well |
| Anytime behaviour | No | Yes |
| Deterministic | Yes | No (stochastic) |
| Best suited for | Chess, checkers | Go, general game playing |

---

## Modern Developments

Alpha-beta and MCTS are not mutually exclusive. AlphaGo and AlphaZero combine MCTS with deep neural networks that replace both the rollout policy and the evaluation function. The network guides selection toward promising branches, dramatically reducing the number of simulations needed.

AlphaZero's approach:

- No hand-crafted features or domain knowledge beyond the rules
- A single network outputs both move probabilities and a value estimate
- MCTS uses these to guide search
- Trained entirely by self-play

> "The game of chess is not won by the player who sees the most moves ahead, but by the one who sees the most *relevant* moves ahead." — anon

This is a link to an [external site](https://gray.land) and this is to an [internal anchor](#how-to-do-this-unvisited).

## Further Reading

- Claude Shannon, *Programming a Computer for Playing Chess* (1950)
- Richard Korf, *Depth-First Iterative-Deepening* (1985)
- Rémi Coulom, *Efficient Selectivity and Backup Operators in Monte-Carlo Tree Search* (2006)
- Silver et al., *Mastering the Game of Go with Deep Neural Networks and Tree Search* (2016)
