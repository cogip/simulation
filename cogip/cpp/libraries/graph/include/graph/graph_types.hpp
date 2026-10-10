// Copyright (C) 2026 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @defgroup    lib_graph Graph module
/// @ingroup     lib
/// @brief       Visibility graph module
///
/// The graph is the discretisation step of path planning: obstacles are grown by the robot radius,
/// candidate nodes are sampled around them, and a node pair becomes an edge when the segment
/// between the two clears every obstacle. Everything it produces lives in trivially copyable
/// structures so it can be mapped into shared memory and drawn by another process.
///
/// @{
/// @file        graph_types.hpp
/// @brief       Declaration of the storage representation of a visibility graph, and of the limits
///              that come with it.
/// @author      Mathis Lécrivain <lecrivain.mathis@gmail.com>

#pragma once

#include "models/coords.hpp"
#include "obstacles_new/obstacle_list.hpp"
#include "obstacles_new/obstacle_types.hpp"

#include <cstddef>
#include <cstdint>
#include <ostream>
#include <type_traits>

namespace cogip {

namespace graph {

/// Most sample points any corner may be given, whatever asks for them.
///
/// The storage bound, and nothing else: every array below is sized from it.
constexpr std::uint8_t GRAPH_SAMPLE_COUNT_MAX = 24;

/// Most sample points per corner a *build* may ask for.
///
/// Below the storage bound, because the two answer different questions. The overshoot of the
/// sampling falls off as 1/cos, so it is already under 1 % at sixteen points per corner of a disc;
/// past that the node count grows, the edge count grows as its square, and the accuracy does not.
/// This is the value a user interface should offer.
constexpr std::uint8_t GRAPH_CORNER_COUNT_MAX = 16;

/// Number of sample points per corner of a displayed outline.
///
/// Deliberately not the corner count of a build, and deliberately finer than one is allowed to be.
/// A displayed outline stands for the **exact** inflated shape, against which the node ring is the
/// visible approximation; drawn at the same resolution the two would say the same thing, and drawn
/// coarsely the exact shape would look like an approximation of itself. Resolution of a drawing is
/// a drawing concern, so it is pinned at the finest the storage allows.
constexpr std::uint8_t GRAPH_DISPLAY_CORNER_COUNT = GRAPH_SAMPLE_COUNT_MAX;

/// Maximum number of nodes a single obstacle can contribute.
constexpr std::size_t GRAPH_OBSTACLE_NODE_COUNT_MAX =
    obstacles_new::OBSTACLE_OUTLINE_SIZE_MAX * GRAPH_SAMPLE_COUNT_MAX;

/// Maximum number of points of a sampled inflated outline.
///
/// One more point per vertex than the node ring: the display polyline includes both ends of each
/// arc, so the straight sections joining two arcs are drawn rather than cut across.
constexpr std::size_t GRAPH_HULL_SIZE_MAX =
    obstacles_new::OBSTACLE_OUTLINE_SIZE_MAX * (GRAPH_SAMPLE_COUNT_MAX + 1);

/// Maximum number of nodes of a graph.
///
/// Sized against a full table: the 2026 set is eighteen obstacles, which sample to 823 nodes at
/// the finest corner count and the smallest inflation that leaves any of them standing. This
/// leaves better than a factor of two on top of that.
constexpr std::size_t GRAPH_NODE_COUNT_MAX = 2048;

/// Maximum number of edges of a graph.
///
/// A complete graph over GRAPH_NODE_COUNT_MAX nodes would hold two million edges, which is not
/// worth reserving for a case obstacles make impossible. The bound instead comes from measuring
/// the worst the 2026 set actually produces — 74 396 edges, at the finest corner count and the
/// smallest useful inflation — and leaving a factor of two above it. Truncating would change the
/// graph rather than merely the picture of it, so the capacity is set where realistic parameters
/// never reach it; Graph::edges_truncated() covers the rest.
constexpr std::size_t GRAPH_EDGE_COUNT_MAX = 131072;

/// Maximum number of sampled inflated outlines.
constexpr std::size_t GRAPH_HULL_COUNT_MAX = obstacles_new::OBSTACLE_LIST_SIZE_MAX;

/// The inputs of a graph build.
///
/// Written by the caller, read by Graph::build(). Kept apart from the outputs so a parameter change
/// and the graph it produced can be published under two different locks.
typedef struct {
    /// Radius added to the corner radius of every obstacle, mm.
    ///
    /// This is the robot shrunk to a point: since (P (+) D(r)) (+) D(rho) = P (+) D(r + rho),
    /// growing an obstacle is this one addition and never an outline offset.
    double inflation_radius;

    /// Distance every node keeps from the inflated shape, mm.
    ///
    /// Not a tuning knob that may be set to zero. Every predicate in the geometry library includes
    /// its boundary, so a node placed exactly on the inflated shape counts as inside it: it would
    /// be discarded, and every edge leaving it rejected at its own endpoint. See the clearance
    /// contract in geometry/README.md.
    double clearance;

    /// Number of sample points per rounded corner.
    ///
    /// Clamped to [1, GRAPH_CORNER_COUNT_MAX] on use, and raised per vertex where a corner sweeps
    /// too wide for that many points. See sample_nodes().
    std::uint8_t corner_count;
} graph_params_t;

/// An undirected edge, as a pair of node indices.
///
/// Indices rather than coordinates: an edge list of pairs is a quarter the size of one of segments,
/// and the display has the node array anyway. Stored once, with first < second.
typedef struct {
    std::uint16_t first;   ///< Index of the first node.
    std::uint16_t second;  ///< Index of the second node.
} edge_t;

/// The nodes of a graph, in absolute mm.
///
/// Laid out as a plain array of coords_t, which is two doubles, so the whole thing is an (n, 2)
/// array of float64 that Python can view without a copy.
typedef struct {
    std::size_t count;                                 ///< Number of valid entries in elems.
    models::coords_t elems[GRAPH_NODE_COUNT_MAX];      ///< Storage. Only the first count are valid.
} node_list_t;

/// The edges of a graph.
typedef struct {
    std::size_t count;                          ///< Number of valid entries in elems.
    edge_t elems[GRAPH_EDGE_COUNT_MAX];         ///< Storage. Only the first count are valid.
} edge_list_t;

/// The sampled boundary of one inflated obstacle.
///
/// For display only: no predicate reads it, because every predicate uses the exact shape. It is
/// published so the process drawing the graph does not have to re-derive the geometry of an
/// obstacle it only wants to show.
typedef struct {
    std::uint32_t obstacle_id;                    ///< Id of the obstacle this outlines.
    std::size_t count;                            ///< Number of valid entries in elems.
    models::coords_t elems[GRAPH_HULL_SIZE_MAX];  ///< Closed polyline, absolute mm, counter-clockwise.
} hull_t;

/// The sampled boundaries of every inflated obstacle.
typedef struct {
    std::size_t count;                       ///< Number of valid entries in elems.
    hull_t elems[GRAPH_HULL_COUNT_MAX];      ///< Storage. Only the first count are valid.
} hull_list_t;

// These structures are meant to be mapped into POSIX shared memory, so they have to stay copyable
// byte by byte and keep a layout both processes agree on. A default member initialiser, a user
// provided constructor or a non trivial member would break that silently.
static_assert(std::is_trivial_v<graph_params_t>);
static_assert(std::is_standard_layout_v<graph_params_t>);
static_assert(std::is_trivially_copyable_v<graph_params_t>);
static_assert(std::is_trivial_v<node_list_t>);
static_assert(std::is_standard_layout_v<node_list_t>);
static_assert(std::is_trivially_copyable_v<node_list_t>);
static_assert(std::is_trivial_v<edge_list_t>);
static_assert(std::is_standard_layout_v<edge_list_t>);
static_assert(std::is_trivially_copyable_v<edge_list_t>);
static_assert(std::is_trivial_v<hull_list_t>);
static_assert(std::is_standard_layout_v<hull_list_t>);
static_assert(std::is_trivially_copyable_v<hull_list_t>);

// A node index has to fit in an edge, and the display views the node array as a contiguous block of
// doubles. Both are properties an upstream change could break quietly.
static_assert(GRAPH_NODE_COUNT_MAX <= UINT16_MAX);
static_assert(sizeof(models::coords_t) == 2 * sizeof(double));

/// Overloads the stream insertion operator for `graph_params_t`.
/// @param os The output stream.
/// @param params The parameters to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const graph_params_t& params) {
    os << "graph_params_t(inflation_radius=" << params.inflation_radius
       << ", clearance=" << params.clearance
       << ", corner_count=" << static_cast<int>(params.corner_count)
       << ")";
    return os;
}

/// Overloads the stream insertion operator for `edge_t`.
/// @param os The output stream.
/// @param edge The edge to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const edge_t& edge) {
    os << "edge_t(" << edge.first << ", " << edge.second << ")";
    return os;
}

} // namespace graph

} // namespace cogip

/// @}
