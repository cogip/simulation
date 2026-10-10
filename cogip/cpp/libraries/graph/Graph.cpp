// Copyright (C) 2026 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "graph/Graph.hpp"

#include "utils/trigonometry.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace cogip {

namespace graph {

namespace {

/// Smallest turn counted as a real corner, radians.
///
/// Matches the collinearity threshold of the geometry library, whose squared sine of 1e-18 is a
/// sine of 1e-9. Below it the two edges meeting at a vertex are the same edge, and the vertex gets
/// a single sample instead of a fan of coincident ones.
constexpr double MIN_TURN = 1e-9;

/// The exterior arc swept by the boundary of an inflated obstacle at one outline vertex.
struct arc_t {
    double start;  ///< Angle of the outward normal of the incoming edge, radians.
    double sweep;  ///< Turn angle, radians. In [0, pi) for a convex outline, 2*pi for a disc.
};

/// Return the exterior arc at one vertex of an outline.
///
/// The outward normal of an edge of a counter-clockwise outline is its direction turned clockwise,
/// so `u = (ux, uy)` gives `(uy, -ux)`. Turning both edge directions the same way leaves the angle
/// between them unchanged, which is why the sweep is read off the directions rather than off the
/// normals. Neither value needs a normalised input: atan2 is insensitive to a common positive
/// scale.
arc_t arc_at(const models::coords_t* points, std::size_t count, std::size_t index)
{
    if (count == 1) {
        // A disc has no edge to take a normal from, and its whole boundary is a single arc. The
        // starting angle is then arbitrary rather than undefined.
        return arc_t{0.0, 2.0 * M_PI};
    }

    // With two vertices the previous and the next are the same one, and this yields a sweep of pi
    // per end: the two ends of a capsule, with no special case.
    const std::size_t previous = (index + count - 1) % count;
    const std::size_t next = (index + 1) % count;

    const double ux = points[index].x - points[previous].x;
    const double uy = points[index].y - points[previous].y;
    const double vx = points[next].x - points[index].x;
    const double vy = points[next].y - points[index].y;

    return arc_t{
        std::atan2(-ux, uy),
        std::atan2(geometry::cross(ux, uy, vx, vy), geometry::dot(ux, uy, vx, vy))
    };
}

/// Widest subdivision any corner is allowed, radians.
///
/// A subdivision of `step` puts the ring at `1 / cos(step / 2)` of where the shape is, so this
/// angle *is* the worst overshoot the sampling may produce: at `pi / 3` it is 15 %, the figure
/// geometry/README.md quotes for the current defaults. The cosine also vanishes at `step = pi` and
/// turns negative past it, so some bound is required for the formula to be total at all — but the
/// bound is set by the accuracy one is willing to accept, not by that singularity.
///
/// What it means in practice, since a corner's sweep is fixed by the outline: a disc is never
/// sampled below six points, each end of a capsule below three, and a right angle below two.
constexpr double MAX_STEP = M_PI / 3.0;

/// Relative slack on MAX_STEP, so a sweep that divides into it exactly rounds down rather than up.
///
/// Not cosmetic. An angle that lands on the bound exactly — and a corner of `pi / 3`, or a sweep
/// read back through an atan2, does — comes out a rounding step either side of it depending on the
/// orientation of the obstacle, so a bare `ceil` would give the same shape a different sample count
/// at a different angle. Nothing breaks either way, an extra sample only costing a node, but the
/// node count would stop being a function of the geometry, which is the first thing one checks when
/// reading a graph. Widening the bound by a rounding step costs nothing: it is a threshold on
/// accuracy, not an identity.
constexpr double MAX_STEP_TOLERANCE = 1e-9;

/// Number of subdivisions of an arc.
///
/// The requested count, raised wherever it would leave the corner coarser than MAX_STEP allows.
/// Since a sweep never exceeds a full turn the raised value never exceeds six, so the result always
/// stays within GRAPH_SAMPLE_COUNT_MAX.
std::size_t sample_count(double sweep, std::uint8_t corner_count)
{
    if (sweep < MIN_TURN) {
        // A flat vertex, redundant in a convex outline. One sample, not a fan of identical ones.
        return 1;
    }

    // Clamped to the storage bound, not to the build bound: the display asks for more than a
    // build is allowed to, and both go through here.
    const std::size_t requested = std::clamp<std::size_t>(
        corner_count, 1, GRAPH_SAMPLE_COUNT_MAX
    );
    const std::size_t required = static_cast<std::size_t>(
        std::ceil(sweep / MAX_STEP - MAX_STEP_TOLERANCE)
    );

    return std::max(requested, required);
}

} // namespace

std::size_t sample_nodes(
    const obstacles_new::obstacle_t& obstacle,
    const graph_params_t& params,
    models::coords_t* out,
    std::size_t out_max
)
{
    const double radius = obstacle.corner_radius + params.inflation_radius + params.clearance;
    std::size_t written = 0;

    for (std::size_t i = 0; i < obstacle.outline_count; i++) {
        const arc_t arc = arc_at(obstacle.outline, obstacle.outline_count, i);
        const std::size_t count = sample_count(arc.sweep, params.corner_count);
        const double step = arc.sweep / static_cast<double>(count);

        // The circumscribed radius: pushing the points out by this much is what makes the chords
        // between them tangent to the inflated shape instead of secant to it.
        const double distance = radius / std::cos(step / 2.0);

        for (std::size_t k = 0; k < count; k++) {
            if (written >= out_max) {
                return 0;
            }
            // Mid-angle of the subdivision, which is where the chord touches the shape.
            const double angle = arc.start + (static_cast<double>(k) + 0.5) * step;
            out[written].x = obstacle.outline[i].x + distance * std::cos(angle);
            out[written].y = obstacle.outline[i].y + distance * std::sin(angle);
            written++;
        }
    }

    return written;
}

std::size_t sample_inflated_outline(
    const obstacles_new::obstacle_t& obstacle,
    double inflation_radius,
    std::uint8_t corner_count,
    models::coords_t* out,
    std::size_t out_max
)
{
    const double radius = obstacle.corner_radius + inflation_radius;

    // A disc is one arc that closes on itself, so emitting its far end would repeat its near one.
    // Any other outline needs both ends of every arc, otherwise the polyline cuts the corner
    // instead of following the straight section that joins two arcs.
    const bool closed_arc = obstacle.outline_count == 1;
    std::size_t written = 0;

    for (std::size_t i = 0; i < obstacle.outline_count; i++) {
        const arc_t arc = arc_at(obstacle.outline, obstacle.outline_count, i);
        const std::size_t count = sample_count(arc.sweep, corner_count);
        const double step = arc.sweep / static_cast<double>(count);
        const std::size_t points = closed_arc ? count : count + 1;

        for (std::size_t k = 0; k < points; k++) {
            if (written >= out_max) {
                return 0;
            }
            // On the boundary, not beyond it: this traces the shape rather than enclosing it.
            const double angle = arc.start + static_cast<double>(k) * step;
            out[written].x = obstacle.outline[i].x + radius * std::cos(angle);
            out[written].y = obstacle.outline[i].y + radius * std::sin(angle);
            written++;
        }
    }

    return written;
}

Graph::Graph(
    const obstacles_new::obstacle_list_t* obstacles,
    const graph_params_t* params,
    node_list_t* nodes,
    edge_list_t* edges,
    hull_list_t* hulls
):
    obstacles_(obstacles),
    params_(params),
    nodes_(nodes),
    edges_(edges),
    hulls_(hulls),
    effective_limits_{0.0, 0.0, 0.0, 0.0},
    nodes_truncated_(false),
    edges_truncated_(false)
{
    if (!obstacles_ || !params_ || !nodes_ || !edges_ || !hulls_) {
        throw std::runtime_error("graph structures must all be provided");
    }
}

void Graph::build(const geometry::Aabb& limits)
{
    nodes_->count = 0;
    edges_->count = 0;
    hulls_->count = 0;
    nodes_truncated_ = false;
    edges_truncated_ = false;

    // The walls, grown the same way everything else is. A negative margin, because growing a
    // boundary shrinks what is inside it.
    effective_limits_ = geometry::aabb_expanded(
        limits, -(params_->inflation_radius + params_->clearance)
    );

    /// One obstacle, resolved once: its outline, the radius the predicates test against, and the
    /// box that filters a segment before they run.
    struct inflated_t {
        const obstacles_new::obstacle_t* obstacle;
        geometry::PolygonView view;
        double radius;
        geometry::Aabb box;
    };

    inflated_t inflated[obstacles_new::OBSTACLE_LIST_SIZE_MAX];
    std::size_t inflated_count = 0;

    // A count read from shared memory is data, not a promise.
    const std::size_t obstacle_count = std::min(
        obstacles_->count, obstacles_new::OBSTACLE_LIST_SIZE_MAX
    );

    // Pass one: resolve every obstacle, and publish the outlines the display asks for. The
    // bounding box is built here, once per obstacle, rather than inside the pair loop below where
    // it would be rebuilt for every candidate edge.
    for (std::size_t i = 0; i < obstacle_count; i++) {
        const obstacles_new::obstacle_t& obstacle = obstacles_->elems[i];
        if (!obstacle.enabled) {
            continue;
        }

        const geometry::PolygonView view{obstacle.outline, obstacle.outline_count};
        const double radius = obstacle.corner_radius + params_->inflation_radius;

        inflated[inflated_count++] = inflated_t{
            &obstacle, view, radius, geometry::aabb_of_rounded_polygon(view, radius)
        };

        if (hulls_->count < GRAPH_HULL_COUNT_MAX) {
            hull_t& hull = hulls_->elems[hulls_->count];
            hull.obstacle_id = obstacle.id;
            hull.count = sample_inflated_outline(
                obstacle, params_->inflation_radius, GRAPH_DISPLAY_CORNER_COUNT,
                hull.elems, GRAPH_HULL_SIZE_MAX
            );
            hulls_->count++;
        }
    }

    // Pass two: the candidate nodes, and the two reasons to drop one.
    models::coords_t candidates[GRAPH_OBSTACLE_NODE_COUNT_MAX];

    for (std::size_t i = 0; i < inflated_count && !nodes_truncated_; i++) {
        const std::size_t candidate_count = sample_nodes(
            *inflated[i].obstacle, *params_, candidates, GRAPH_OBSTACLE_NODE_COUNT_MAX
        );

        for (std::size_t k = 0; k < candidate_count; k++) {
            const double x = candidates[k].x;
            const double y = candidates[k].y;

            if (!geometry::aabb_contains_point(effective_limits_, x, y)) {
                continue;
            }

            bool inside = false;
            for (std::size_t j = 0; j < inflated_count; j++) {
                if (geometry::point_in_rounded_polygon(
                        inflated[j].view, inflated[j].radius, x, y)) {
                    inside = true;
                    break;
                }
            }
            if (inside) {
                continue;
            }

            if (nodes_->count >= GRAPH_NODE_COUNT_MAX) {
                nodes_truncated_ = true;
                break;
            }
            nodes_->elems[nodes_->count++] = candidates[k];
        }
    }

    // Pass three: every pair once, kept when nothing stands between the two.
    for (std::size_t i = 0; i < nodes_->count; i++) {
        const double ax = nodes_->elems[i].x;
        const double ay = nodes_->elems[i].y;

        for (std::size_t j = i + 1; j < nodes_->count; j++) {
            const double bx = nodes_->elems[j].x;
            const double by = nodes_->elems[j].y;

            bool blocked = false;
            for (std::size_t k = 0; k < inflated_count; k++) {
                if (!geometry::aabb_overlaps_segment(inflated[k].box, ax, ay, bx, by)) {
                    continue;
                }
                if (geometry::segment_intersects_rounded_polygon(
                        inflated[k].view, inflated[k].radius, ax, ay, bx, by)) {
                    blocked = true;
                    break;
                }
            }
            if (blocked) {
                continue;
            }

            if (edges_->count >= GRAPH_EDGE_COUNT_MAX) {
                edges_truncated_ = true;
                return;
            }
            edges_->elems[edges_->count++] = edge_t{
                static_cast<std::uint16_t>(i), static_cast<std::uint16_t>(j)
            };
        }
    }
}

} // namespace graph

} // namespace cogip
