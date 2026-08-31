// Copyright (C) 2026 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "geometry/geometry.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/stl/pair.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>

#include <sstream>
#include <vector>

namespace nb = nanobind;
using namespace nb::literals;

namespace cogip {

namespace geometry {

namespace {

using point_list_t = std::vector<std::pair<double, double>>;

/// Convert a list of (x, y) tuples into the storage a PolygonView borrows.
///
/// coords_t has no bound constructor in the models module, so a list of tuples is the only shape a
/// Python caller can produce. The vector must outlive the view, hence the two step call at each
/// binding site.
std::vector<models::coords_t> to_outline(const point_list_t& points)
{
    std::vector<models::coords_t> outline;
    outline.reserve(points.size());
    for (const auto& point : points) {
        outline.push_back(models::coords_t{point.first, point.second});
    }
    return outline;
}

PolygonView view_of(const std::vector<models::coords_t>& outline)
{
    return PolygonView{outline.data(), outline.size()};
}

} // namespace

NB_MODULE(geometry, m) {
    m.doc() = "Geometric predicates over a convex outline dilated by a radius";

    m.attr("EPSILON") = EPSILON;

    nb::class_<Aabb>(m, "Aabb", "An axis aligned bounding box, in absolute mm")
        .def_ro("min_x", &Aabb::min_x, "Lower bound along X")
        .def_ro("min_y", &Aabb::min_y, "Lower bound along Y")
        .def_ro("max_x", &Aabb::max_x, "Upper bound along X")
        .def_ro("max_y", &Aabb::max_y, "Upper bound along Y")
        .def("__repr__", [](const Aabb& box) {
            std::ostringstream oss;
            oss << "Aabb(min_x=" << box.min_x << ", min_y=" << box.min_y
                << ", max_x=" << box.max_x << ", max_y=" << box.max_y << ")";
            return oss.str();
        });

    m.def(
        "signed_area_twice",
        [](const point_list_t& points) {
            const auto outline = to_outline(points);
            return signed_area_twice(view_of(outline));
        },
        "points"_a,
        "Twice the signed area of an outline. Positive counter-clockwise"
    );

    m.def(
        "is_convex",
        [](const point_list_t& points) {
            const auto outline = to_outline(points);
            return is_convex(view_of(outline));
        },
        "points"_a,
        "Check that an outline turns the same way at every vertex"
    );

    m.def(
        "normalize_winding",
        [](const point_list_t& points) {
            auto outline = to_outline(points);
            normalize_winding(outline.data(), outline.size());
            point_list_t result;
            result.reserve(outline.size());
            for (const auto& point : outline) {
                result.emplace_back(point.x, point.y);
            }
            return result;
        },
        "points"_a,
        "Return the outline wound counter-clockwise"
    );

    m.def(
        "aabb_of_rounded_polygon",
        [](const point_list_t& points, double radius) {
            const auto outline = to_outline(points);
            return aabb_of_rounded_polygon(view_of(outline), radius);
        },
        "points"_a, "radius"_a,
        "Bounding box of an outline dilated by a radius"
    );

    m.def(
        "aabb_contains_point",
        &aabb_contains_point,
        "box"_a, "x"_a, "y"_a,
        "Check whether a box contains a point"
    );

    m.def(
        "aabb_overlaps_segment",
        &aabb_overlaps_segment,
        "box"_a, "ax"_a, "ay"_a, "bx"_a, "by"_a,
        "Check whether a box may be reached by a segment. Conservative, never wrongly negative"
    );

    m.def(
        "point_in_rounded_polygon",
        [](const point_list_t& points, double radius, double x, double y) {
            const auto outline = to_outline(points);
            return point_in_rounded_polygon(view_of(outline), radius, x, y);
        },
        "points"_a, "radius"_a, "x"_a, "y"_a,
        "Check whether a point lies inside an outline dilated by a radius, boundary included"
    );

    m.def(
        "segment_intersects_rounded_polygon",
        [](const point_list_t& points, double radius,
           double ax, double ay, double bx, double by) {
            const auto outline = to_outline(points);
            return segment_intersects_rounded_polygon(
                view_of(outline), radius, ax, ay, bx, by
            );
        },
        "points"_a, "radius"_a, "ax"_a, "ay"_a, "bx"_a, "by"_a,
        "Check whether a segment meets an outline dilated by a radius, boundary included"
    );

    m.def(
        "nearest_point_on_rounded_polygon",
        [](const point_list_t& points, double radius, double x, double y) {
            const auto outline = to_outline(points);
            models::coords_t closest{0.0, 0.0};
            nearest_point_on_rounded_polygon(view_of(outline), radius, x, y, closest);
            return std::pair<double, double>{closest.x, closest.y};
        },
        "points"_a, "radius"_a, "x"_a, "y"_a,
        "Nearest point on the boundary of an outline dilated by a radius, always outside it"
    );
}

} // namespace geometry

} // namespace cogip
