// Copyright (C) 2026 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_obstacles_new
/// @{
/// @file        ObstacleList.hpp
/// @brief       ObstacleList class declaration.
/// @details     Thin wrapper over an obstacle_list_t, adding the append operations that establish
///              the outline invariants of a slot in place.
/// @author      Mathis Lécrivain <lecrivain.mathis@gmail.com>

#pragma once

#include "obstacles_new/Obstacle.hpp"
#include "obstacles_new/obstacle_list.hpp"

#include "models/List.hpp"

#include <cstddef>
#include <ostream>
#include <stdexcept>

namespace cogip {

namespace obstacles_new {

/// @class ObstacleList
/// @brief A fixed capacity list of obstacles, borrowed or owned.
///
/// @par Why append goes through the factories
/// An obstacle carries invariants its storage cannot express: the outline is counter-clockwise and
/// convex. Writing an obstacle_t field by field into a slot would bypass them. Each append below
/// therefore hands the slot to the matching Obstacle factory, which normalises the winding and
/// rejects a concave outline before the count moves. Nothing in the list can be half constructed:
/// the count is incremented only once the factory has returned.
class ObstacleList: public models::List<obstacle_t, Obstacle, obstacle_list_t, OBSTACLE_LIST_SIZE_MAX> {
public:
    /// Constructor.
    ObstacleList(
        obstacle_list_t* list=nullptr  ///< [in] Pointer to an existing data structure.
                                       ///<      If nullptr, will allocate one internally.
    ) : List(list) {};

    /// Append a disc.
    /// @return The index of the new obstacle.
    /// @throws std::runtime_error if the list is full.
    std::size_t append_circle(
        double x,       ///< [in] X coordinate of the centre, mm.
        double y,       ///< [in] Y coordinate of the centre, mm.
        double radius   ///< [in] Radius, mm.
    ) {
        obstacle_t* slot = reserve();
        Obstacle::make_circle(x, y, radius, slot);
        return commit();
    };

    /// Append a rectangle.
    /// @return The index of the new obstacle.
    /// @throws std::runtime_error if the list is full.
    std::size_t append_rectangle(
        double x,         ///< [in] X coordinate of the centre, mm.
        double y,         ///< [in] Y coordinate of the centre, mm.
        double angle,     ///< [in] Orientation angle, in degrees.
        double length_x,  ///< [in] Length along the local X axis, mm.
        double length_y   ///< [in] Length along the local Y axis, mm.
    ) {
        obstacle_t* slot = reserve();
        Obstacle::make_rectangle(x, y, angle, length_x, length_y, slot);
        return commit();
    };

    /// Append an arbitrary convex polygon.
    ///
    /// The factory throws on a non convex or oversized outline, and it does so before commit(), so
    /// a rejected outline leaves the list exactly as it was.
    ///
    /// @return The index of the new obstacle.
    /// @throws std::runtime_error if the list is full, or if the outline is not storable.
    std::size_t append_polygon(
        const models::coords_t* points,  ///< [in] Vertices, absolute mm. Not owned.
        std::size_t count                ///< [in] Number of vertices.
    ) {
        obstacle_t* slot = reserve();
        Obstacle::make_polygon(points, count, slot);
        return commit();
    };

private:
    /// Return the slot past the last valid entry, without claiming it.
    /// @throws std::runtime_error if the list is full.
    obstacle_t* reserve()
    {
        if (list_->count >= OBSTACLE_LIST_SIZE_MAX) {
            throw std::runtime_error("obstacle list is full");
        }
        return &list_->elems[list_->count];
    };

    /// Claim the reserved slot.
    /// @return The index of the claimed slot.
    std::size_t commit() { return list_->count++; };
};

/// Overloads the stream insertion operator for `ObstacleList`.
/// @param os The output stream.
/// @param list The ObstacleList to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, ObstacleList& list) {
    os << "ObstacleList(count=" << list.size() << ", obstacles=[";
    for (std::size_t i = 0; i < list.size(); i++) {
        if (i > 0) os << ", ";
        os << list.get(i);
    }
    os << "])";
    return os;
}

} // namespace obstacles_new

} // namespace cogip

/// @}
