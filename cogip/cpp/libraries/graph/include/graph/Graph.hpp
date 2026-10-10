// Copyright (C) 2026 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_graph
/// @{
/// @file        Graph.hpp
/// @brief       Visibility graph construction over a list of obstacles.
/// @details     The sampling is the only place in the whole obstacle stack where a shape is
///              approximated, so it lives on its own, as free functions over plain structures that
///              can be checked against the formula they implement.
/// @author      Mathis Lécrivain <lecrivain.mathis@gmail.com>

#pragma once

#include "graph/graph_types.hpp"

#include "geometry/geometry.hpp"
#include "models/coords.hpp"
#include "obstacles_new/obstacle_list.hpp"
#include "obstacles_new/obstacle_types.hpp"

#include <cstddef>

namespace cogip {

namespace graph {

/// Sample the ring of candidate nodes around an inflated obstacle.
///
/// @par Why the ring is circumscribed and not inscribed
/// The predicates use the exact shape, so a node placed *on* the inflated boundary leaves every
/// chord between two neighbours dipping inside it, and the graph loses exactly the edges that
/// follow an obstacle — the ones a path needs to get around it. The nodes therefore sit on the
/// circumscribed polygon, whose edges are tangent to the shape rather than secant to it.
///
/// @par The sampling
/// The boundary of `P (+) D(R)` alternates straight sections, offset from the edges of `P`, and
/// circular arcs of radius `R` centred on its vertices. Only the arcs need sampling. At vertex `i`
/// the arc runs from the outward normal of the incoming edge to the outward normal of the outgoing
/// one, sweeping the turn angle
///
///     delta_i = atan2(cross(u, v), dot(u, v))
///
/// of the two edge directions, which is in `[0, pi)` for a convex outline. A single vertex outline,
/// a disc, has no edge to take a normal from and sweeps a full turn instead.
///
/// The arc then takes
///
///     N_i   = max(corner_count, ceil(delta_i / MAX_STEP))
///     step  = delta_i / N_i
///     rho_i = (R + clearance) / cos(step / 2)
///
/// and places `N_i` points at the mid-angle of each subdivision. The `max()` bounds the overshoot:
/// `1 / cos(step / 2)` is how far outside the shape the ring sits, so capping `step` caps that, and
/// a corner whose sweep is wide enough gets more points than were asked for — six on a disc, three
/// per end of a capsule, two on a right angle. It is also what keeps the formula total, since
/// `cos(step / 2)` vanishes at `step = pi` and turns negative past it.
///
/// @par What the sides get for free
/// The last point of the arc at vertex `i` and the first of the arc at vertex `i + 1` both sit at a
/// perpendicular distance `rho * cos(step / 2) = R + clearance` from the edge joining the two, so
/// the whole segment between them does too. The straight sections need no samples of their own.
///
/// For a disc this reduces to `rho = (R + clearance) / cos(pi / N)`, the formula in
/// geometry/README.md.
///
/// @return Number of points written, or 0 if @p out_max cannot hold them all.
std::size_t sample_nodes(
    const obstacles_new::obstacle_t& obstacle,  ///< [in] Obstacle to sample around.
    const graph_params_t& params,               ///< [in] Inflation, clearance and corner count.
    models::coords_t* out,                      ///< [out] Destination. Not owned.
    std::size_t out_max                         ///< [in] Capacity of @p out.
);

/// Sample the boundary of an inflated obstacle, for display.
///
/// Same subdivision as sample_nodes(), but the points sit *on* the boundary, at radius `R`, and
/// both ends of every arc are emitted so the straight sections between arcs are drawn instead of
/// being cut across. Never use the result as a graph node: it is on the boundary by construction,
/// which every predicate counts as inside.
///
/// Takes its resolution as an argument rather than reading it off graph_params_t, because it is not
/// the same quantity: the corner count of a build says how coarsely the graph is allowed to
/// approximate an obstacle, while this one says how finely the obstacle is drawn. Passing an
/// inflation radius of zero also makes this the raw shape of the obstacle, which is what a display
/// needs to put next to the grown one.
///
/// @return Number of points written, or 0 if @p out_max cannot hold them all.
std::size_t sample_inflated_outline(
    const obstacles_new::obstacle_t& obstacle,  ///< [in] Obstacle to outline.
    double inflation_radius,                    ///< [in] Radius added to the corner radius, mm.
    std::uint8_t corner_count,                  ///< [in] Sample points per corner.
    models::coords_t* out,                      ///< [out] Destination. Not owned.
    std::size_t out_max                         ///< [in] Capacity of @p out.
);

/// @class Graph
/// @brief Builds a visibility graph over a list of obstacles.
///
/// @par Ownership
/// Every structure is borrowed, typically from a shared memory segment, and none is owned. This
/// class holds no geometry of its own: rebuilding is what the obstacles and the parameters say it
/// is, at the moment build() is called.
///
/// @par Why it does not know about shared memory
/// It takes pointers, not a segment name. That keeps the whole algorithm testable on stack
/// allocated structures, and leaves it to the caller — the binding, in practice — to decide where
/// the memory comes from.
class Graph final {
public:
    /// Constructor.
    /// @throws std::runtime_error if any pointer is null.
    Graph(
        const obstacles_new::obstacle_list_t* obstacles,  ///< [in] Obstacles to route around. Not owned.
        const graph_params_t* params,                     ///< [in] Build parameters. Not owned.
        node_list_t* nodes,                               ///< [out] Node storage. Not owned.
        edge_list_t* edges,                               ///< [out] Edge storage. Not owned.
        hull_list_t* hulls                                ///< [out] Display outline storage. Not owned.
    );

    /// Rebuild the graph from the current obstacles and parameters.
    ///
    /// Nodes come from sample_nodes() around every enabled obstacle, and are kept only when they
    /// lie inside effective_limits() and outside every inflated obstacle. That second test is run
    /// against *all* obstacles, the sampled one included, rather than against the others only: a
    /// node is at `clearance` from its own obstacle by construction, so the test passes whenever
    /// the clearance contract holds — and fails visibly when it does not, instead of quietly
    /// seeding the graph with boundary nodes.
    ///
    /// An edge joins two nodes when the segment between them clears every obstacle. The bounding
    /// box of each inflated obstacle is computed once here, not once per candidate edge, and
    /// filters the segment before the exact test runs.
    ///
    /// Costs `O(V^2 * M)` exact segment tests in the worst case, for `V` nodes and `M` obstacles,
    /// which is why the bounding box filter is worth its four comparisons.
    void build(
        const geometry::Aabb& limits  ///< [in] The table itself, walls included.
    );

    /// The box nodes were actually kept inside, after the walls were grown.
    ///
    /// The walls are a boundary, not something to route around, so growing them is shrinking the
    /// free region rather than adding four obstacles: a robot reduced to a point has to stay its
    /// own radius away from a wall exactly as it does from an obstacle. Done here rather than left
    /// to the caller because the amount to shrink by is `inflation_radius + clearance`, which is
    /// this class's own parameters — a caller doing it would be duplicating the clearance contract
    /// and would eventually get it wrong. Only meaningful once build() has run.
    const geometry::Aabb& effective_limits() const { return effective_limits_; };

    /// Return true if the node capacity was reached and the graph is incomplete.
    bool nodes_truncated() const { return nodes_truncated_; };

    /// Return true if the edge capacity was reached and the graph is incomplete.
    bool edges_truncated() const { return edges_truncated_; };

    /// Return the borrowed node list.
    const node_list_t* nodes() const { return nodes_; };

    /// Return the borrowed edge list.
    const edge_list_t* edges() const { return edges_; };

    /// Return the borrowed display outline list.
    const hull_list_t* hulls() const { return hulls_; };

private:
    const obstacles_new::obstacle_list_t* obstacles_;  ///< Obstacles to route around. Not owned.
    const graph_params_t* params_;                     ///< Build parameters. Not owned.
    node_list_t* nodes_;                               ///< Node storage. Not owned.
    edge_list_t* edges_;                               ///< Edge storage. Not owned.
    hull_list_t* hulls_;                               ///< Display outline storage. Not owned.
    geometry::Aabb effective_limits_;                  ///< Table limits, shrunk by the last build.
    bool nodes_truncated_;                             ///< Node capacity was reached.
    bool edges_truncated_;                             ///< Edge capacity was reached.
};

} // namespace graph

} // namespace cogip

/// @}
