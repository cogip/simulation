/**
 * @file ldlidar_datatype.h
 * @author LDRobot (support@ldrobot.com)
 * @brief  lidar point data structure
 *         This code is only applicable to LDROBOT LiDAR LD19 products sold by Shenzhen LDROBOT Co., LTD
 * @version 0.1
 * @date 2021-11-09
 *
 * @copyright Copyright (c) 2017-2023  SHENZHEN LDROBOT CO., LTD. All rights
 * reserved.
 * Licensed under the MIT License (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License in the file LICENSE
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#pragma once

#include <cstdint>
#include <vector>

#define ANGLE_TO_RADIAN(angle) ((angle) * 3141.59 / 180000)

// Lidar error code definition
#define LIDAR_NO_ERROR 0x00
#define LIDAR_ERROR_BLOCKING 0x01
#define LIDAR_ERROR_OCCLUSION 0x02
#define LIDAR_ERROR_BLOCKING_AND_OCCLUSION 0x03
// End Lidar error code definition

namespace ldlidar {

enum class LidarStatus {
    NORMAL,
    ERROR,
    DATA_TIME_OUT,
    DATA_WAIT,
    STOP,
};

struct PointData {
    // Polar coordinate representation
    float angle;       // Angle ranges from 0 to 359 degrees
    uint16_t distance; // Distance is measured in millimeters
    uint8_t intensity; // Intensity is 0 to 255
    // System time when first range was measured in nanoseconds
    uint64_t stamp;
    // Cartesian coordinate representation
    PointData(float angle, uint16_t distance, uint8_t intensity, uint64_t stamp = 0) {
        this->angle = angle;
        this->distance = distance;
        this->intensity = intensity;
        this->stamp = stamp;
    }
    PointData() {}
};

using Points2D = std::vector<PointData>;

} // namespace ldlidar
