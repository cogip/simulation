// Copyright (C) 2026 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @defgroup    lib_geometry Geometry
/// @brief       Geometric predicates over a convex outline dilated by a radius.
/// @details     Free functions over plain arrays. Nothing here knows about obstacles, shared
///              memory or nanobind, which is what makes every predicate testable on its own.
///
///              An obstacle is a convex outline dilated by a radius, so a single primitive
///              answers every question: the distance to the outline. Inside becomes a comparison
///              against the radius, and none of the boolean predicates needs a square root.
///
///              Contact is a collision. Every predicate here includes the boundary, with no way
///              to ask for anything else, which is the conservative direction. It costs nothing
///              provided every point handed to the visibility graph carries a non-zero clearance
///              from every obstacle, which is a contract on the callers rather than on this file:
///              see "The clearance contract" in the README.
/// @{
/// @file        geometry.hpp
/// @brief       Geometric predicates over a convex outline dilated by a radius.
/// @author      Mathis Lécrivain <lecrivain.mathis@gmail.com>

#pragma once

#include "models/coords.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>

namespace cogip {

namespace geometry {

/// Tolerance, in mm².
///
/// Every test below is either the cross product of two vectors in millimetres or a squared
/// distance, so both live in the same unit and one constant covers them. The table spans 0 to
/// 3000 mm, which puts cross products around 9e6 and their rounding noise around 2e-9. This sits
/// three decades above that noise floor, a linear sensitivity of about 3e-10 mm.
///
/// It only ever widens an acceptance, never a rejection: a false positive costs a detour, a false
/// negative costs a collision.
constexpr double EPSILON = 1e-6;

/// Smallest turn angle counted as a real turn, expressed as a squared sine so the test needs no
/// square root. Below it three vertices count as collinear, which a convex polygon may have.
/// Dimensionless, hence independent of the size of the obstacle.
constexpr double COLLINEARITY_EPSILON_SQUARED = 1e-18;

/// A borrowed convex outline, in absolute mm, wound counter-clockwise.
///
/// One vertex describes a point, two a segment, three or more a polygon. None of these is a
/// special case: they are all valid convex sets, and combined with a radius they give a disc, a
/// capsule and a rounded polygon.
struct PolygonView {
    const models::coords_t* points;  ///< First vertex. Not owned.
    std::size_t count;               ///< Number of vertices.
};

/// An axis aligned bounding box, in absolute mm.
struct Aabb {
    double min_x;  ///< Lower bound along X.
    double min_y;  ///< Lower bound along Y.
    double max_x;  ///< Upper bound along X.
    double max_y;  ///< Upper bound along Y.
};

/// Z component of the cross product of two 2D vectors.
inline constexpr double cross(double ux, double uy, double vx, double vy)
{
    return ux * vy - uy * vx;
}

/// Dot product of two 2D vectors.
inline constexpr double dot(double ux, double uy, double vx, double vy)
{
    return ux * vx + uy * vy;
}

/// Squared distance between two points.
///
/// Preferable to the true distance whenever the result is only compared against another distance,
/// since the square root then cancels out on both sides.
inline constexpr double distance_squared(double ax, double ay, double bx, double by)
{
    const double dx = bx - ax;
    const double dy = by - ay;
    return dx * dx + dy * dy;
}

/// Number of edges of an outline.
///
/// A single vertex and a two vertex outline both have one edge, degenerate in the first case. The
/// edge walks below then need no special case.
inline constexpr std::size_t edge_count(PolygonView polygon)
{
    return polygon.count <= 2 ? 1 : polygon.count;
}

/// Bounding box of an outline.
///
/// Meant to be computed once per outline change, not per query.
inline Aabb aabb_of(PolygonView polygon)
{
    if (polygon.count == 0) {
        return Aabb{0.0, 0.0, 0.0, 0.0};
    }

    Aabb box{polygon.points[0].x, polygon.points[0].y, polygon.points[0].x, polygon.points[0].y};

    for (std::size_t i = 1; i < polygon.count; i++) {
        box.min_x = std::min(box.min_x, polygon.points[i].x);
        box.min_y = std::min(box.min_y, polygon.points[i].y);
        box.max_x = std::max(box.max_x, polygon.points[i].x);
        box.max_y = std::max(box.max_y, polygon.points[i].y);
    }

    return box;
}

/// Grow a box outward on every side.
inline Aabb aabb_expanded(const Aabb& box, double margin)
{
    return Aabb{box.min_x - margin, box.min_y - margin, box.max_x + margin, box.max_y + margin};
}

/// Bounding box of an outline dilated by @p radius.
inline Aabb aabb_of_rounded_polygon(PolygonView polygon, double radius)
{
    return aabb_expanded(aabb_of(polygon), radius);
}

/// Check whether a box contains a point.
inline bool aabb_contains_point(const Aabb& box, double x, double y)
{
    return x >= box.min_x && x <= box.max_x && y >= box.min_y && y <= box.max_y;
}

/// Check whether a box may be reached by a segment.
///
/// This compares the box against the bounding box of the segment, not against the segment itself:
/// four comparisons, no multiplication, and it is deliberately loose. A filter does not have to
/// decide, it has to be conservative and free. The only property that matters is the one it does
/// guarantee: it can wrongly answer maybe, never wrongly answer no. Tightening it into a real slab
/// test would buy accuracy nobody uses at the price of the cheapness that is the whole point.
inline bool aabb_overlaps_segment(const Aabb& box, double ax, double ay, double bx, double by)
{
    if (std::max(ax, bx) < box.min_x || std::min(ax, bx) > box.max_x) {
        return false;
    }
    if (std::max(ay, by) < box.min_y || std::min(ay, by) > box.max_y) {
        return false;
    }
    return true;
}

/// Twice the signed area of an outline, computed with the shoelace formula.
///
/// @return Twice the signed area, in mm². Positive counter-clockwise, negative clockwise, zero
///         below three vertices since they bound no area.
inline double signed_area_twice(PolygonView polygon)
{
    if (polygon.count < 3) {
        return 0.0;
    }

    double total = 0.0;

    // previous trails current by one vertex and starts at the last one, so the closing edge needs
    // no special case: the pairs visited are (n-1, 0), (0, 1), ... (n-2, n-1).
    for (std::size_t current = 0, previous = polygon.count - 1;
         current < polygon.count;
         previous = current++) {
        total += polygon.points[previous].x * polygon.points[current].y
               - polygon.points[current].x * polygon.points[previous].y;
    }

    return total;
}

/// Check that an outline turns the same way at every vertex.
///
/// The cross product of two consecutive edges gives the direction of the turn, but its magnitude
/// grows with the size of the obstacle, so an absolute threshold would reject a small polygon and
/// accept a large one. Comparing the squared sine of the turn instead makes the threshold
/// dimensionless, and squaring both sides removes the two square roots it would otherwise need.
///
/// Consistent turns do not prove the outline is simple: a star polygon turns one way throughout
/// while crossing itself. Ruling that out needs the total turning to be a single revolution, which
/// is a far more delicate computation for a shape no caller produces by accident, whereas a
/// concave one is exactly what a caller does produce by accident.
///
/// @return True when every turn goes the same way, or when the outline bounds no area.
inline bool is_convex(PolygonView polygon)
{
    if (polygon.count < 3) {
        // A point or a segment bounds no area, so there is no turn that could go the wrong way.
        return true;
    }

    int turn = 0;

    for (std::size_t current = 0; current < polygon.count; current++) {
        const models::coords_t& a = polygon.points[current];
        const models::coords_t& b = polygon.points[(current + 1) % polygon.count];
        const models::coords_t& c = polygon.points[(current + 2) % polygon.count];

        const double incoming_x = b.x - a.x;
        const double incoming_y = b.y - a.y;
        const double outgoing_x = c.x - b.x;
        const double outgoing_y = c.y - b.y;

        const double turn_sine = cross(incoming_x, incoming_y, outgoing_x, outgoing_y);
        const double lengths_squared = (incoming_x * incoming_x + incoming_y * incoming_y)
                                     * (outgoing_x * outgoing_x + outgoing_y * outgoing_y);

        if (turn_sine * turn_sine <= COLLINEARITY_EPSILON_SQUARED * lengths_squared) {
            // Collinear, or a repeated vertex leaving no direction to compare.
            continue;
        }

        const int sign = turn_sine > 0.0 ? 1 : -1;
        if (turn == 0) {
            turn = sign;
        } else if (sign != turn) {
            return false;
        }
    }

    return true;
}

/// Reorder an outline counter-clockwise, in place.
///
/// Every predicate below reads the sign of a cross product as inside or outside, which only holds
/// for one winding. Paying for this once, when the outline is stored, is what lets the queries
/// stay free of it. It is also a precondition of any offset operation: an outline wound the wrong
/// way inflates inward.
///
/// @return True when the vertices were reversed.
inline bool normalize_winding(models::coords_t* points, std::size_t count)
{
    // Below three vertices there is no area, hence no winding to speak of.
    if (count < 3 || signed_area_twice(PolygonView{points, count}) >= 0.0) {
        return false;
    }

    std::reverse(points, points + count);
    return true;
}

/// Squared distance from a point to a segment.
///
/// The projection ratio is clamped to the segment, so a point beyond an endpoint measures to that
/// endpoint rather than to the supporting line. A zero length segment measures as a point, which
/// is the guard the circle predicates of the previous library lacked.
inline double distance_squared_to_segment(
    double ax, double ay,
    double bx, double by,
    double px, double py
)
{
    const double edge_x = bx - ax;
    const double edge_y = by - ay;
    const double length_squared = edge_x * edge_x + edge_y * edge_y;

    if (length_squared <= 0.0) {
        return distance_squared(ax, ay, px, py);
    }

    double ratio = dot(px - ax, py - ay, edge_x, edge_y) / length_squared;
    ratio = std::clamp(ratio, 0.0, 1.0);

    return distance_squared(ax + ratio * edge_x, ay + ratio * edge_y, px, py);
}

/// Check whether two segments meet, contact included.
///
/// Contact counts as an intersection on purpose: a segment grazing an obstacle is a collision, and
/// widening the test is the direction that fails safely.
inline bool segments_intersect(
    double ax, double ay,
    double bx, double by,
    double cx, double cy,
    double dx, double dy
)
{
    // A degenerate segment has no side, so the orientation tests below say nothing about it.
    if (ax == bx && ay == by) {
        return distance_squared_to_segment(cx, cy, dx, dy, ax, ay) <= EPSILON;
    }
    if (cx == dx && cy == dy) {
        return distance_squared_to_segment(ax, ay, bx, by, cx, cy) <= EPSILON;
    }

    const double a_side = cross(dx - cx, dy - cy, ax - cx, ay - cy);
    const double b_side = cross(dx - cx, dy - cy, bx - cx, by - cy);
    const double c_side = cross(bx - ax, by - ay, cx - ax, cy - ay);
    const double d_side = cross(bx - ax, by - ay, dx - ax, dy - ay);

    // Each segment straddles the supporting line of the other.
    const bool ab_straddles = (a_side > EPSILON && b_side < -EPSILON)
                           || (a_side < -EPSILON && b_side > EPSILON);
    const bool cd_straddles = (c_side > EPSILON && d_side < -EPSILON)
                           || (c_side < -EPSILON && d_side > EPSILON);
    if (ab_straddles && cd_straddles) {
        return true;
    }

    // Collinear or touching: the straddle test above cannot see it, so measure instead. Four
    // point to segment distances also cover a partial overlap of two collinear segments.
    return distance_squared_to_segment(cx, cy, dx, dy, ax, ay) <= EPSILON
        || distance_squared_to_segment(cx, cy, dx, dy, bx, by) <= EPSILON
        || distance_squared_to_segment(ax, ay, bx, by, cx, cy) <= EPSILON
        || distance_squared_to_segment(ax, ay, bx, by, dx, dy) <= EPSILON;
}

/// Squared distance between two segments. Zero when they meet.
inline double distance_squared_between_segments(
    double ax, double ay,
    double bx, double by,
    double cx, double cy,
    double dx, double dy
)
{
    if (cx == dx && cy == dy) {
        return distance_squared_to_segment(ax, ay, bx, by, cx, cy);
    }
    if (ax == bx && ay == by) {
        return distance_squared_to_segment(cx, cy, dx, dy, ax, ay);
    }
    if (segments_intersect(ax, ay, bx, by, cx, cy, dx, dy)) {
        return 0.0;
    }

    // Disjoint convex sets: the closest pair involves an endpoint of one of them.
    return std::min({
        distance_squared_to_segment(cx, cy, dx, dy, ax, ay),
        distance_squared_to_segment(cx, cy, dx, dy, bx, by),
        distance_squared_to_segment(ax, ay, bx, by, cx, cy),
        distance_squared_to_segment(ax, ay, bx, by, dx, dy)
    });
}

/// Check whether a point lies inside a convex outline, boundary included.
///
/// A point is outside as soon as it sits right of one edge, the outline being counter-clockwise.
/// Outlines of one or two vertices bound no area, so being inside them means reaching them.
inline bool point_in_convex_polygon(PolygonView polygon, double x, double y)
{
    if (polygon.count == 0) {
        return false;
    }
    if (polygon.count <= 2) {
        const models::coords_t& a = polygon.points[0];
        const models::coords_t& b = polygon.points[polygon.count - 1];
        return distance_squared_to_segment(a.x, a.y, b.x, b.y, x, y) <= EPSILON;
    }

    for (std::size_t current = 0, previous = polygon.count - 1;
         current < polygon.count;
         previous = current++) {
        const models::coords_t& a = polygon.points[previous];
        const models::coords_t& b = polygon.points[current];
        if (cross(b.x - a.x, b.y - a.y, x - a.x, y - a.y) < -EPSILON) {
            return false;
        }
    }

    return true;
}

/// Check whether a segment meets a convex polygon of at least three vertices.
///
/// Separating axis theorem. Two convex sets are disjoint if and only if a direction exists along
/// which their projections do not overlap, and for a polygon against a segment it is enough to try
/// the edge normals of the polygon plus the one normal of the segment. Nothing here divides, which
/// matters on the Cortex-A72 where a double division costs 15 to 30 cycles against 4 for a
/// pipelined multiply.
///
/// A segment lying entirely inside the polygon is separated by no axis, so it is reported as a
/// hit. Walking the edges instead would miss it and hand back a path straight through the
/// obstacle.
inline bool segment_intersects_convex_polygon(
    PolygonView polygon,
    double ax, double ay,
    double bx, double by
)
{
    if (polygon.count < 3) {
        return false;
    }

    // The polygon lies entirely behind each of its own outward normals, so its extreme projection
    // along one is the edge itself and each axis costs two multiplications rather than a scan.
    for (std::size_t current = 0, previous = polygon.count - 1;
         current < polygon.count;
         previous = current++) {
        const models::coords_t& a = polygon.points[previous];
        const models::coords_t& b = polygon.points[current];
        const double normal_x = b.y - a.y;
        const double normal_y = -(b.x - a.x);
        const double base = dot(normal_x, normal_y, a.x, a.y);
        // A real gap is needed before declaring separation, so contact counts as a hit.
        if (dot(normal_x, normal_y, ax, ay) - base > EPSILON
            && dot(normal_x, normal_y, bx, by) - base > EPSILON) {
            return false;
        }
    }

    // The axis normal to the segment. The segment projects onto a single value there, taken as the
    // origin, so the polygon is separated when all its vertices land on the same side.
    const double normal_x = by - ay;
    const double normal_y = -(bx - ax);
    const double base = dot(normal_x, normal_y, ax, ay);
    double minimum = std::numeric_limits<double>::infinity();
    double maximum = -std::numeric_limits<double>::infinity();

    for (std::size_t i = 0; i < polygon.count; i++) {
        const double projection = dot(normal_x, normal_y, polygon.points[i].x, polygon.points[i].y)
                                - base;
        minimum = std::min(minimum, projection);
        maximum = std::max(maximum, projection);
    }

    return !(minimum > EPSILON || maximum < -EPSILON);
}

/// Nearest point on the boundary of an outline.
///
/// Every edge is projected onto with a clamped ratio, so a query point facing a vertex rather than
/// an edge lands on that vertex. Projecting onto the supporting lines instead would return a point
/// off the outline entirely.
///
/// @return Squared distance to @p closest, or -1.0 when the outline is empty, in which case
///         @p closest is left untouched.
inline double nearest_point_on_polygon_boundary(
    PolygonView polygon,
    double x, double y,
    models::coords_t& closest
)
{
    if (polygon.count == 0) {
        return -1.0;
    }
    if (polygon.count == 1) {
        closest = polygon.points[0];
        return distance_squared(closest.x, closest.y, x, y);
    }

    double best = std::numeric_limits<double>::infinity();
    const std::size_t edges = edge_count(polygon);

    for (std::size_t i = 0; i < edges; i++) {
        const models::coords_t& a = polygon.points[i];
        const models::coords_t& b = polygon.points[(i + 1) % polygon.count];

        const double edge_x = b.x - a.x;
        const double edge_y = b.y - a.y;
        const double length_squared = edge_x * edge_x + edge_y * edge_y;

        double ratio = 0.0;
        if (length_squared > 0.0) {
            ratio = std::clamp(dot(x - a.x, y - a.y, edge_x, edge_y) / length_squared, 0.0, 1.0);
        }

        const models::coords_t candidate{a.x + ratio * edge_x, a.y + ratio * edge_y};
        const double squared = distance_squared(candidate.x, candidate.y, x, y);
        if (squared < best) {
            best = squared;
            closest = candidate;
        }
    }

    return best;
}

/// Squared distance from a point to a convex outline. Zero when the point is on or inside it.
///
/// This is the primitive point_in_rounded_polygon is built on: dilating the outline by a radius
/// turns containment into a comparison against that radius squared.
inline double distance_squared_to_convex_polygon(PolygonView polygon, double x, double y)
{
    if (polygon.count == 0) {
        return std::numeric_limits<double>::infinity();
    }
    if (polygon.count == 1) {
        return distance_squared(polygon.points[0].x, polygon.points[0].y, x, y);
    }
    if (polygon.count == 2) {
        return distance_squared_to_segment(
            polygon.points[0].x, polygon.points[0].y,
            polygon.points[1].x, polygon.points[1].y,
            x, y
        );
    }
    if (point_in_convex_polygon(polygon, x, y)) {
        return 0.0;
    }

    models::coords_t closest;
    return nearest_point_on_polygon_boundary(polygon, x, y, closest);
}

/// Check whether a point lies inside an outline dilated by @p radius, boundary included.
inline bool point_in_rounded_polygon(PolygonView polygon, double radius, double x, double y)
{
    return distance_squared_to_convex_polygon(polygon, x, y) <= radius * radius + EPSILON;
}

/// Check whether a segment meets an outline dilated by @p radius.
///
/// This does not go through distance_squared_to_convex_polygon: it needs to know whether one edge
/// comes within the radius, not which one is nearest, so it returns on the first. That is the
/// function called from the O(V²·N) loop of the visibility graph builder, where the point test is
/// only called O(V·N) times.
inline bool segment_intersects_rounded_polygon(
    PolygonView polygon,
    double radius,
    double ax, double ay,
    double bx, double by
)
{
    if (polygon.count == 0) {
        return false;
    }
    if (polygon.count >= 3 && segment_intersects_convex_polygon(polygon, ax, ay, bx, by)) {
        return true;
    }
    if (radius <= 0.0 && polygon.count >= 3) {
        return false;
    }

    const double limit = radius * radius + EPSILON;
    const std::size_t edges = edge_count(polygon);

    for (std::size_t i = 0; i < edges; i++) {
        const models::coords_t& a = polygon.points[i];
        const models::coords_t& b = polygon.points[(i + 1) % polygon.count];
        if (distance_squared_between_segments(ax, ay, bx, by, a.x, a.y, b.x, b.y) <= limit) {
            return true;
        }
    }

    return false;
}

/// Nearest point on the boundary of an outline dilated by @p radius.
///
/// The result always lies outside the shape, whether the query point started inside or outside,
/// because the only caller that needs it is the one rescuing a robot pose from an obstacle.
/// Returning the nearest vertex instead, as the previous library did, hands back a point that is
/// still inside for anything but a very flat obstacle.
///
/// This is the one function here that costs a square root, and it runs a handful of times per
/// replanning rather than once per graph edge.
///
/// @warning The result lands exactly **on** the boundary of the dilated shape, which every
///          predicate here reports as inside. A caller turning it into a vertex of the visibility
///          graph must therefore pass a radius already grown by a clearance, otherwise the vertex
///          is discarded and every link leaving it is rejected — it touches the obstacle at its own
///          endpoint. Pass the shape radius when you want a point on the shape, and the radius plus
///          a clearance when you want a point the planner can route through.
///
/// @return Squared distance from the query point to @p closest, or -1.0 when the outline is empty.
inline double nearest_point_on_rounded_polygon(
    PolygonView polygon,
    double radius,
    double x, double y,
    models::coords_t& closest
)
{
    models::coords_t on_outline;
    const double squared = nearest_point_on_polygon_boundary(polygon, x, y, on_outline);
    if (squared < 0.0) {
        return -1.0;
    }

    const double distance = std::sqrt(squared);
    double direction_x = 1.0;
    double direction_y = 0.0;

    if (squared > EPSILON) {
        // Outward means away from the outline when the point is outside, and away from the point
        // when it is inside.
        const double sign = point_in_convex_polygon(polygon, x, y) ? -1.0 : 1.0;
        direction_x = sign * (x - on_outline.x) / distance;
        direction_y = sign * (y - on_outline.y) / distance;
    } else if (polygon.count >= 2) {
        // The query point sits on the outline, leaving no direction to read from it. Fall back to
        // the outward normal of the closest edge.
        double best = std::numeric_limits<double>::infinity();
        const std::size_t edges = edge_count(polygon);

        for (std::size_t i = 0; i < edges; i++) {
            const models::coords_t& a = polygon.points[i];
            const models::coords_t& b = polygon.points[(i + 1) % polygon.count];
            const double length = std::hypot(b.x - a.x, b.y - a.y);
            if (length <= 0.0) {
                continue;
            }
            const double edge_distance = distance_squared_to_segment(a.x, a.y, b.x, b.y, x, y);
            if (edge_distance >= best) {
                continue;
            }
            best = edge_distance;
            direction_x = (b.y - a.y) / length;
            direction_y = -(b.x - a.x) / length;
        }
    }
    // A single vertex leaves the +X default, matching what the previous circle did at its centre.

    closest.x = on_outline.x + direction_x * radius;
    closest.y = on_outline.y + direction_y * radius;

    return distance_squared(x, y, closest.x, closest.y);
}

} // namespace geometry

} // namespace cogip

/// @}
