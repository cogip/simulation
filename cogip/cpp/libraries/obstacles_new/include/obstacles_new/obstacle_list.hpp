// Copyright (C) 2026 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

/// @ingroup     lib_obstacles_new
/// @{
/// @file        obstacle_list.hpp
/// @brief       Declaration of obstacle_list_t, a fixed capacity array of obstacles.
/// @author      Mathis Lécrivain <lecrivain.mathis@gmail.com>

#pragma once

#include "obstacles_new/obstacle_types.hpp"

#include <cstddef>
#include <ostream>
#include <type_traits>

namespace cogip {

namespace obstacles_new {

/// Maximum number of obstacles a list can hold.
///
/// The whole point of the list is to be mapped into shared memory, so its capacity is part of the
/// layout and cannot grow at run time. Sized for what a table holds at once: the fixed obstacles
/// plus the robots seen by the detector.
constexpr std::size_t OBSTACLE_LIST_SIZE_MAX = 32;

/// A fixed capacity array of obstacles.
///
/// Only the first @ref count entries are valid; the rest is untouched storage rather than a
/// sentinel, so appending never has to clear anything.
typedef struct {
    std::size_t count;                             ///< Number of valid entries in elems.
    obstacle_t elems[OBSTACLE_LIST_SIZE_MAX];      ///< Storage. Only the first count are valid.
} obstacle_list_t;

// Same reasoning as obstacle_t: this lives in POSIX shared memory, so it has to stay copyable byte
// by byte with a layout both processes agree on.
static_assert(std::is_trivial_v<obstacle_list_t>);
static_assert(std::is_standard_layout_v<obstacle_list_t>);
static_assert(std::is_trivially_copyable_v<obstacle_list_t>);

/// Overloads the stream insertion operator for `obstacle_list_t`.
/// @param os The output stream.
/// @param list The obstacle list to print.
/// @return A reference to the output stream.
inline std::ostream& operator<<(std::ostream& os, const obstacle_list_t& list) {
    os << "obstacle_list_t(count=" << list.count << ", obstacles=[";
    for (std::size_t i = 0; i < list.count; i++) {
        if (i > 0) os << ", ";
        os << list.elems[i];
    }
    os << "])";
    return os;
}

} // namespace obstacles_new

} // namespace cogip

/// @}
