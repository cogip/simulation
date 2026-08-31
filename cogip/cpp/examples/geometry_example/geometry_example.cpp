// Copyright (C) 2026 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "geometry_example/geometry_example.hpp"

#include "geometry/geometry.hpp"

#include <cmath>
#include <cstddef>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>

using cogip::models::coords_t;
using cogip::geometry::Aabb;
using cogip::geometry::PolygonView;

namespace geometry_example {

namespace {

/// Absolute tolerance for the value comparisons, in mm.
constexpr double TOLERANCE = 1e-6;

std::size_t checks_total = 0;
std::size_t checks_failed = 0;

const coords_t DISC[1] = {{1000.0, 800.0}};
const coords_t CAPSULE[2] = {{0.0, 0.0}, {200.0, 0.0}};
const coords_t SQUARE[4] = {{-100.0, -100.0}, {100.0, -100.0}, {100.0, 100.0}, {-100.0, 100.0}};

const PolygonView disc{DISC, 1};
const PolygonView capsule{CAPSULE, 2};
const PolygonView square{SQUARE, 4};

std::string fmt(double value)
{
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(2) << value;
    return oss.str();
}

std::string fmt(double x, double y)
{
    return fmt(x) + " " + fmt(y);
}

void report(const char* name, bool passed, const std::string& actual, const std::string& expected)
{
    checks_total++;
    if (!passed) {
        checks_failed++;
    }
    std::cout << (passed ? "  ok   " : "  FAIL ")
              << std::left << std::setw(32) << name << " "
              << std::setw(24) << actual << " expected " << expected << "\n";
}

void check(const char* name, bool actual, bool expected)
{
    report(name, actual == expected, actual ? "true" : "false", expected ? "true" : "false");
}

void check(const char* name, double actual, double expected)
{
    report(name, std::fabs(actual - expected) < TOLERANCE, fmt(actual), fmt(expected));
}

void check_point(const char* name, const coords_t& actual, double x, double y)
{
    const bool passed = std::fabs(actual.x - x) < TOLERANCE && std::fabs(actual.y - y) < TOLERANCE;
    report(name, passed, fmt(actual.x, actual.y), fmt(x, y));
}

void check_box(const char* name, const Aabb& box,
               double min_x, double min_y, double max_x, double max_y)
{
    const bool passed = std::fabs(box.min_x - min_x) < TOLERANCE
                     && std::fabs(box.min_y - min_y) < TOLERANCE
                     && std::fabs(box.max_x - max_x) < TOLERANCE
                     && std::fabs(box.max_y - max_y) < TOLERANCE;
    report(name, passed,
           fmt(box.min_x, box.min_y) + " " + fmt(box.max_x, box.max_y),
           fmt(min_x, min_y) + " " + fmt(max_x, max_y));
}

void point_on_disc()
{
    std::cout << "\n[point, disc] outline 1000 800, radius 150\n";

    check("centre", cogip::geometry::point_in_rounded_polygon(disc, 150.0, 1000.0, 800.0), true);
    check("on the rim",
          cogip::geometry::point_in_rounded_polygon(disc, 150.0, 1150.0, 800.0), true);
    check("just outside",
          cogip::geometry::point_in_rounded_polygon(disc, 150.0, 1150.001, 800.0), false);
    check("rim along y",
          cogip::geometry::point_in_rounded_polygon(disc, 150.0, 1000.0, 950.0), true);
}

void point_on_capsule()
{
    std::cout << "\n[point, capsule] outline 0 0 to 200 0, radius 50\n";

    check("on the axis",
          cogip::geometry::point_in_rounded_polygon(capsule, 50.0, 100.0, 0.0), true);
    check("on the side",
          cogip::geometry::point_in_rounded_polygon(capsule, 50.0, 100.0, 50.0), true);
    check("past the side",
          cogip::geometry::point_in_rounded_polygon(capsule, 50.0, 100.0, 50.001), false);
    check("on the cap",
          cogip::geometry::point_in_rounded_polygon(capsule, 50.0, -50.0, 0.0), true);
    check("past the cap",
          cogip::geometry::point_in_rounded_polygon(capsule, 50.0, -50.001, 0.0), false);
    check("inside the far cap",
          cogip::geometry::point_in_rounded_polygon(capsule, 50.0, 249.0, 0.0), true);
}

void point_on_square()
{
    std::cout << "\n[point, square] 200 mm side centred on the origin, radius 0\n";

    check("centre",
          cogip::geometry::point_in_rounded_polygon(square, 0.0, 0.0, 0.0), true);
    check("on an edge",
          cogip::geometry::point_in_rounded_polygon(square, 0.0, 100.0, 0.0), true);
    check("on a vertex",
          cogip::geometry::point_in_rounded_polygon(square, 0.0, 100.0, 100.0), true);
    check("just outside",
          cogip::geometry::point_in_rounded_polygon(square, 0.0, 101.0, 0.0), false);
}

void point_on_rounded_square()
{
    std::cout << "\n[point, rounded square] same square, radius 30\n";

    check("beyond the edge",
          cogip::geometry::point_in_rounded_polygon(square, 30.0, 115.0, 0.0), true);
    check("on the boundary",
          cogip::geometry::point_in_rounded_polygon(square, 30.0, 130.0, 0.0), true);
    check("past the boundary",
          cogip::geometry::point_in_rounded_polygon(square, 30.0, 131.0, 0.0), false);

    // The corner is an arc, not a right angle: a square grown to 130 mm would contain 130 130.
    const double corner = 30.0 * std::sqrt(2.0) / 2.0;
    check("corner arc, inside",
          cogip::geometry::point_in_rounded_polygon(square, 30.0,
                                                    100.0 + corner * 0.9, 100.0 + corner * 0.9),
          true);
    check("corner arc, outside",
          cogip::geometry::point_in_rounded_polygon(square, 30.0, 130.0, 130.0), false);
}

void segments()
{
    std::cout << "\n[segment] square radius 0, then disc radius 150\n";

    check("crossing",
          cogip::geometry::segment_intersects_rounded_polygon(
              square, 0.0, -200.0, 0.0, 200.0, 0.0), true);
    check("entirely inside",
          cogip::geometry::segment_intersects_rounded_polygon(
              square, 0.0, -50.0, 0.0, 50.0, 0.0), true);
    check("one endpoint inside",
          cogip::geometry::segment_intersects_rounded_polygon(
              square, 0.0, 0.0, 0.0, 300.0, 0.0), true);
    check("clear",
          cogip::geometry::segment_intersects_rounded_polygon(
              square, 0.0, -200.0, 200.0, 200.0, 200.0), false);
    check("touching a vertex",
          cogip::geometry::segment_intersects_rounded_polygon(
              square, 0.0, 200.0, 200.0, 100.0, 100.0), true);
    check("collinear with an edge",
          cogip::geometry::segment_intersects_rounded_polygon(
              square, 0.0, -50.0, 100.0, 50.0, 100.0), true);
    check("collinear past the edge",
          cogip::geometry::segment_intersects_rounded_polygon(
              square, 0.0, 200.0, 100.0, 300.0, 100.0), false);
    check("zero length inside",
          cogip::geometry::segment_intersects_rounded_polygon(
              square, 0.0, 0.0, 0.0, 0.0, 0.0), true);
    check("zero length outside",
          cogip::geometry::segment_intersects_rounded_polygon(
              square, 0.0, 200.0, 200.0, 200.0, 200.0), false);

    check("tangent to the disc",
          cogip::geometry::segment_intersects_rounded_polygon(
              disc, 150.0, 700.0, 950.0, 1300.0, 950.0), true);
    check("inside the disc",
          cogip::geometry::segment_intersects_rounded_polygon(
              disc, 150.0, 700.0, 949.0, 1300.0, 949.0), true);
    check("clear of the disc",
          cogip::geometry::segment_intersects_rounded_polygon(
              disc, 150.0, 700.0, 951.0, 1300.0, 951.0), false);
}

void distances()
{
    std::cout << "\n[distance] the primitive point_in_rounded_polygon compares against\n";

    check("point outside",
          cogip::geometry::distance_squared_to_convex_polygon(square, 300.0, 0.0), 40000.0);
    check("point inside",
          cogip::geometry::distance_squared_to_convex_polygon(square, 0.0, 0.0), 0.0);
    check("point facing a vertex",
          cogip::geometry::distance_squared_to_convex_polygon(square, 200.0, 200.0), 20000.0);
    check("distance to the disc",
          cogip::geometry::distance_squared_to_convex_polygon(disc, 1400.0, 800.0), 160000.0);
}

void nearest_points()
{
    std::cout << "\n[nearest] projection onto the boundary of the inflated shape\n";

    coords_t closest{0.0, 0.0};

    cogip::geometry::nearest_point_on_rounded_polygon(disc, 150.0, 1400.0, 800.0, closest);
    check_point("outside the disc", closest, 1150.0, 800.0);

    cogip::geometry::nearest_point_on_rounded_polygon(square, 0.0, 300.0, 0.0, closest);
    check_point("outside the square", closest, 100.0, 0.0);

    cogip::geometry::nearest_point_on_rounded_polygon(square, 30.0, 300.0, 0.0, closest);
    check_point("outside the rounded square", closest, 130.0, 0.0);

    cogip::geometry::nearest_point_on_rounded_polygon(square, 30.0, 0.0, 0.0, closest);
    check("from inside, on the boundary",
          std::sqrt(cogip::geometry::distance_squared_to_convex_polygon(
              square, closest.x, closest.y)),
          30.0);

    cogip::geometry::nearest_point_on_rounded_polygon(disc, 150.0, 1000.0, 800.0, closest);
    check_point("at the centre of the disc", closest, 1150.0, 800.0);

    // Facing a vertex, outside the cone of both adjacent edges: projecting onto the supporting
    // lines instead of the clamped edges would land at 200 100 or 100 200.
    cogip::geometry::nearest_point_on_rounded_polygon(square, 0.0, 200.0, 200.0, closest);
    check_point("facing a vertex", closest, 100.0, 100.0);
}

void bounding_boxes()
{
    std::cout << "\n[aabb] boxes and the rejection they allow\n";

    check_box("disc", cogip::geometry::aabb_of_rounded_polygon(disc, 150.0),
              850.0, 650.0, 1150.0, 950.0);
    check_box("rounded square", cogip::geometry::aabb_of_rounded_polygon(square, 30.0),
              -130.0, -130.0, 130.0, 130.0);

    const Aabb box = cogip::geometry::aabb_of_rounded_polygon(square, 0.0);
    check("contains the centre", cogip::geometry::aabb_contains_point(box, 0.0, 0.0), true);
    check("excludes 101 0", cogip::geometry::aabb_contains_point(box, 101.0, 0.0), false);

    check("far above, box", cogip::geometry::aabb_overlaps_segment(box, -300.0, 300.0, 300.0, 300.0),
          false);
    check("far above, shape", cogip::geometry::segment_intersects_rounded_polygon(
              square, 0.0, -300.0, 300.0, 300.0, 300.0), false);
    check("far right, box", cogip::geometry::aabb_overlaps_segment(box, 300.0, -300.0, 300.0, 300.0),
          false);
    check("far right, shape", cogip::geometry::segment_intersects_rounded_polygon(
              square, 0.0, 300.0, -300.0, 300.0, 300.0), false);
    check("through, box", cogip::geometry::aabb_overlaps_segment(box, -300.0, 0.0, 300.0, 0.0),
          true);
    check("through, shape", cogip::geometry::segment_intersects_rounded_polygon(
              square, 0.0, -300.0, 0.0, 300.0, 0.0), true);
    // The box answers maybe and the shape answers no: a filter may over-report, never under-report.
    check("past the corner, box",
          cogip::geometry::aabb_overlaps_segment(box, 0.0, 210.0, 210.0, 0.0), true);
    check("past the corner, shape", cogip::geometry::segment_intersects_rounded_polygon(
              square, 0.0, 0.0, 210.0, 210.0, 0.0), false);
}

void outline_invariants()
{
    std::cout << "\n[convexity] outline invariants\n";

    check("square is convex", cogip::geometry::is_convex(square), true);

    const coords_t chevron[5] = {
        {0.0, 0.0}, {200.0, 0.0}, {200.0, 200.0}, {100.0, 100.0}, {0.0, 200.0}
    };
    check("chevron is convex", cogip::geometry::is_convex(PolygonView{chevron, 5}), false);

    const coords_t collinear[5] = {
        {0.0, 0.0}, {100.0, 0.0}, {200.0, 0.0}, {200.0, 100.0}, {0.0, 100.0}
    };
    check("collinear is convex", cogip::geometry::is_convex(PolygonView{collinear, 5}), true);

    check("counter-clockwise area", cogip::geometry::signed_area_twice(square), 80000.0);

    coords_t clockwise[4] = {
        {-100.0, -100.0}, {-100.0, 100.0}, {100.0, 100.0}, {100.0, -100.0}
    };
    check("clockwise area",
          cogip::geometry::signed_area_twice(PolygonView{clockwise, 4}), -80000.0);
    check("clockwise reversed", cogip::geometry::normalize_winding(clockwise, 4), true);
    check("reversed area",
          cogip::geometry::signed_area_twice(PolygonView{clockwise, 4}), 80000.0);

    coords_t already[4] = {
        {-100.0, -100.0}, {100.0, -100.0}, {100.0, 100.0}, {-100.0, 100.0}
    };
    check("counter-clockwise kept", cogip::geometry::normalize_winding(already, 4), false);
}

} // namespace

void run()
{
    checks_total = 0;
    checks_failed = 0;

    point_on_disc();
    point_on_capsule();
    point_on_square();
    point_on_rounded_square();
    segments();
    distances();
    nearest_points();
    bounding_boxes();
    outline_invariants();

    std::cout << "\n[summary]\n"
              << "  checks " << checks_total << "\n"
              << "  failed " << checks_failed << "\n";
}

} // namespace geometry_example
