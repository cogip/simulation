// Copyright (C) 2026 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "graph/Graph.hpp"

#include "obstacles_new/Obstacle.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/pair.h>
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>

#include <cstdint>
#include <sstream>
#include <stdexcept>
#include <tuple>
#include <utility>
#include <vector>

namespace nb = nanobind;
using namespace nb::literals;

namespace cogip {

namespace graph {

NB_MODULE(graph, m) {
    nb::module_::import_("cogip.cpp.libraries.obstacles_new");

    m.doc() = "Visibility graph construction over a list of obstacles";

    m.attr("GRAPH_SAMPLE_COUNT_MAX") = GRAPH_SAMPLE_COUNT_MAX;
    m.attr("GRAPH_CORNER_COUNT_MAX") = GRAPH_CORNER_COUNT_MAX;
    m.attr("GRAPH_NODE_COUNT_MAX") = GRAPH_NODE_COUNT_MAX;
    m.attr("GRAPH_EDGE_COUNT_MAX") = GRAPH_EDGE_COUNT_MAX;
    m.attr("GRAPH_HULL_COUNT_MAX") = GRAPH_HULL_COUNT_MAX;
    m.attr("GRAPH_DISPLAY_CORNER_COUNT") = GRAPH_DISPLAY_CORNER_COUNT;

    nb::class_<graph_params_t>(m, "GraphParams", "The inputs of a graph build")
        .def(nb::init<>(), "Default constructor for graph_params_t")
        .def_rw(
            "inflation_radius", &graph_params_t::inflation_radius,
            "Radius added to the corner radius of every obstacle, mm")
        .def_rw(
            "clearance", &graph_params_t::clearance,
            "Distance every node keeps from the inflated shape, mm. Never zero")
        .def_rw(
            "corner_count", &graph_params_t::corner_count,
            "Number of sample points per rounded corner")
        .def("__repr__", [](const graph_params_t& params) {
            std::ostringstream oss;
            oss << params;
            return oss.str();
        });

    // The three output structures are opaque on purpose: they are only ever handed back to Graph,
    // which is where the zero copy views below read them from. Exposing their fields would invite
    // a Python side loop over an array that numpy can already address in one go.
    nb::class_<node_list_t>(m, "NodeList", "Graph node storage, read through Graph.get_nodes()")
        .def(nb::init<>(), "Default constructor for node_list_t");
    nb::class_<edge_list_t>(m, "EdgeList", "Graph edge storage, read through Graph.get_edges()")
        .def(nb::init<>(), "Default constructor for edge_list_t");
    nb::class_<hull_list_t>(m, "HullList", "Display outline storage, read through Graph.get_hull()")
        .def(nb::init<>(), "Default constructor for hull_list_t");

    m.def(
        "sample_inflated_outline",
        [](const obstacles_new::Obstacle& obstacle, double inflation_radius,
           std::uint8_t corner_count) {
            models::coords_t out[GRAPH_HULL_SIZE_MAX];
            const std::size_t count = sample_inflated_outline(
                *obstacle.data(), inflation_radius, corner_count, out, GRAPH_HULL_SIZE_MAX
            );
            std::vector<std::pair<double, double>> result;
            result.reserve(count);
            for (std::size_t i = 0; i < count; i++) {
                result.emplace_back(out[i].x, out[i].y);
            }
            return result;
        },
        "obstacle"_a, "inflation_radius"_a, "corner_count"_a = GRAPH_DISPLAY_CORNER_COUNT,
        "Closed polyline tracing the boundary of an obstacle grown by a radius, as (x, y) tuples. "
        "An inflation radius of zero traces the raw shape, arcs included"
    );

    m.def(
        "sample_nodes",
        [](const obstacles_new::Obstacle& obstacle, const graph_params_t& params) {
            models::coords_t out[GRAPH_OBSTACLE_NODE_COUNT_MAX];
            const std::size_t count = sample_nodes(
                *obstacle.data(), params, out, GRAPH_OBSTACLE_NODE_COUNT_MAX
            );
            std::vector<std::pair<double, double>> result;
            result.reserve(count);
            for (std::size_t i = 0; i < count; i++) {
                result.emplace_back(out[i].x, out[i].y);
            }
            return result;
        },
        "obstacle"_a, "params"_a,
        "Ring of candidate nodes around an inflated obstacle, as (x, y) tuples, in order. "
        "Returns a copy rather than a view: the ring is a pure function of the obstacle and the "
        "parameters, so it is derived on demand instead of being published alongside the graph"
    );

    nb::class_<Graph>(m, "Graph", "Builds a visibility graph over a list of obstacles")
        // Every structure is borrowed, so all five have to outlive the Graph. In practice they are
        // slots of a shared memory segment, whose owner outlives everything.
        .def(
            nb::init<
                const obstacles_new::obstacle_list_t*, const graph_params_t*,
                node_list_t*, edge_list_t*, hull_list_t*
            >(),
            "Borrow the obstacles, the parameters and the three output structures",
            "obstacles"_a, "params"_a, "nodes"_a, "edges"_a, "hulls"_a,
            nb::keep_alive<1, 2>(), nb::keep_alive<1, 3>(), nb::keep_alive<1, 4>(),
            nb::keep_alive<1, 5>(), nb::keep_alive<1, 6>())
        .def(
            "build",
            [](Graph& self, double min_x, double min_y, double max_x, double max_y) {
                self.build(geometry::Aabb{min_x, min_y, max_x, max_y});
            },
            "Rebuild the graph over the given table, walls included",
            "min_x"_a, "min_y"_a, "max_x"_a, "max_y"_a)
        .def_prop_ro(
            "effective_limits",
            [](const Graph& self) {
                const geometry::Aabb& box = self.effective_limits();
                return std::make_tuple(box.min_x, box.min_y, box.max_x, box.max_y);
            },
            "The table, shrunk by the grown walls, as (min_x, min_y, max_x, max_y) in mm")
        .def_prop_ro(
            "nodes_truncated", &Graph::nodes_truncated,
            "True if the node capacity was reached and the graph is incomplete")
        .def_prop_ro(
            "edges_truncated", &Graph::edges_truncated,
            "True if the edge capacity was reached and the graph is incomplete")
        .def_prop_ro(
            "hull_count",
            [](const Graph& self) { return self.hulls()->count; },
            "Number of sampled inflated outlines")
        // coords_t is two doubles, so a run of them is already an (n, 2) float64 array and numpy
        // can address it in place. No copy, and no tuple marshalling per node either — which is
        // the whole reason the graph is published in shared memory rather than returned.
        .def(
            "get_nodes",
            [](const Graph& self) {
                const node_list_t* nodes = self.nodes();
                return nb::ndarray<const double, nb::numpy, nb::shape<-1, 2>>(
                    nodes->elems, {nodes->count, 2}
                );
            },
            "Nodes as an (n, 2) float64 view of shared memory, already trimmed to the node count",
            nb::rv_policy::reference_internal)
        .def(
            "get_edges",
            [](const Graph& self) {
                const edge_list_t* edges = self.edges();
                return nb::ndarray<const std::uint16_t, nb::numpy, nb::shape<-1, 2>>(
                    edges->elems, {edges->count, 2}
                );
            },
            "Edges as an (m, 2) uint16 view of node indices, already trimmed to the edge count",
            nb::rv_policy::reference_internal)
        .def(
            "get_hull",
            [](const Graph& self, std::size_t index) {
                const hull_list_t* hulls = self.hulls();
                if (index >= hulls->count) {
                    throw std::runtime_error("index out of range");
                }
                const hull_t& hull = hulls->elems[index];
                return nb::ndarray<const double, nb::numpy, nb::shape<-1, 2>>(
                    hull.elems, {hull.count, 2}
                );
            },
            "Sampled boundary of one inflated obstacle, as an (n, 2) float64 view",
            "index"_a,
            nb::rv_policy::reference_internal)
        .def(
            "get_hull_obstacle_id",
            [](const Graph& self, std::size_t index) {
                const hull_list_t* hulls = self.hulls();
                if (index >= hulls->count) {
                    throw std::runtime_error("index out of range");
                }
                return hulls->elems[index].obstacle_id;
            },
            "Id of the obstacle the outline at this index belongs to",
            "index"_a)
        .def("__repr__", [](const Graph& self) {
            std::ostringstream oss;
            oss << "Graph(nodes=" << self.nodes()->count
                << ", edges=" << self.edges()->count
                << ", hulls=" << self.hulls()->count << ")";
            return oss.str();
        });
}

} // namespace graph

} // namespace cogip
