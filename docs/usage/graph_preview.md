# graph_preview

Development tool. Shows the visibility graph the C++ [`graph`](../developers/developers.md) library
builds: the obstacles as they are, the shapes they become once grown, and the graph laid over them.

It owns its own shared memory segment and seeds it with this year's table — the fixed obstacles,
the collection areas and the pantries, taken from the planner's `GameContext` — plus one disc
standing for a robot, which the mouse drags. Nothing else has to be running.

## What is on screen

| | |
|---|---|
| grey shape | the obstacle, exact, arcs included |
| orange disc | the robot. Drag it |
| violet dashed line | the obstacle grown by `rho`, **exact**, and around the table the boundary the grown walls leave |
| green ring | the circumscribed polygon the nodes sit on, at the current corner count |
| green dot | a node the build kept |
| blue line | an edge |

The two sliders answer two different questions, and it is worth knowing which is which:

- **`rho`** grows every obstacle. Since an obstacle is a convex outline dilated by a radius, this
  is one addition and not an outline offset — the violet line stays at a constant distance from the
  grey shape however far it is pushed.
- **`N`** moves the **green ring**, not the violet line. The violet line is the exact grown shape
  and owes nothing to `N`; the ring is the approximation the graph is actually built on. At a low
  `N` it stands well clear of the violet line, and it tightens onto it as `N` rises. Corners that
  sweep wide are given more points than asked for, so a disc never drops below six.

Three things to look for:

1. **No edge crosses a violet region.** The collision test is exact, so one that did would be a
   bug, not a rounding artefact.
2. **Nodes sit outside, never on.** That is the clearance contract, made visible.
3. **Edges that graze an obstacle survive.** This is what the circumscribed ring buys: with the
   nodes on the grown boundary instead, every edge following an obstacle would be rejected and the
   graph would come apart.

While the robot is being dragged the edges are hidden, because they are the expensive layer and the
least useful mid-drag. They come back when the mouse is released.

## Usage

Use `--help` to show available options:

```bash
cogip-graph-preview --help
```

| Option | Default | |
|---|---|---|
| `-n, --corners` | 6 | Sample points per rounded corner |
| `-r, --inflation-radius` | 150 | Radius added to every obstacle, mm |
| `-c, --clearance` | 10 | Distance every node keeps from the grown shape, mm. Never zero |
| `-t, --table` | Game | Table to lay the obstacles on |
| `-i, --id` | 1 | Robot ID: decides which obstacles are on the table |
| `--table-margin` | 0 | Margin taken off the table limits, mm |
| `--shm-name` | cogip_graph_preview | Segment to create |
| `-d, --debug` | off | Debug messages, C++ included |

The segment layout is part of `shared_data_t`, so a segment left behind by an older build no longer
matches and has to be removed:

```bash
rm -f /dev/shm/cogip_graph_preview /dev/shm/sem.cogip_graph_preview*
```
