# Monte Carlo Tree Search

Monte Carlo Tree Search is a method that uses the results of randomly simulated
games to find a good move or action to take in an actual game. The basic algorithm is
applicable to games like noughts-and-crosses, chess and go.

## Practical and Historical Context

<!-- need something here -->

### Two-player, Zero-sum Games
Noughts-and-crosses is a zero-sum game, which means that one player's gain is the other's loss — if one player wins the other must lose.[^positive-sum-game] We can represent the outcome of such a game with a 1 for a win, -1 for a loss and 0 for a draw.

[^positive-sum-game]: The alternative is a _positive-sum game_, or win-win game, where the total gains and losses can be more than zero.

## Game Trees
If you are playing noughts-and-crosses and thinking about which move you should make, you might think ahead about what options that leaves your opponent, and what moves they can make in response. We can **represent** this as a _game tree_.

<!-- game state diagram. show player turn, turn (ply) number, game board, actions, outcome -->

**An example game tree** &middot; The nodes of the tree are game states, the branches are actions. From the starting state, an empty board, Player A has 9 moves available, 9 different squares in which to place their X. Each of these gives Player B a set of 8 moves in response, and so on down the tree. When a game state has three Xs or three Os in a row, then that is a terminal node and is either a win, loss or draw. We consider these from the perspective of the player whose turn it is at the root node of the tree.

If we draw the whole tree, we can see which paths lead to wins, losses or draws. (We can also sum up the scores below a node... what does this tell us?) 

### When Game Trees Get Large

Alpha-beta pruning.

## Monte Carlo Search

### Bandits

## Monte Carlo Tree Search

### Things to look out for
1. Don't confuse the simulations with the actual playing of the game. We run many simulations, then based on what we learn from those, we make a single move. When it's time to make our next move, we run more simulations.
2. You need to account for the fact that what's good for one player is bad for the other. So, when propagating wins up the tree, you'll need to flip them every second step to make them losses. Or you can adjust the way UCB1 is calculated and do the flipping there.
3. Calculating the constant.

<!-- add history/invention of MCTS -->

### Extensions
#### Tree Re-use

#### Games With More Than Two Players

## Applications

## Further Reading