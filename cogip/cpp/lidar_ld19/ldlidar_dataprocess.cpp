/**
 * @file ldlidar_dataprocess.cpp
 * @author LDRobot (support@ldrobot.com)
 *         David Hu (hmd_hubei_cn@163.com)
 * @brief  LiDAR data protocol processing App
 * @version 1.0
 * @date 2023-03-12
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
#include "lidar_ld19/ldlidar_dataprocess.h"

#include <algorithm>
#include <map>
#include <numeric>

namespace ldlidar {

LdLidarDataProcess::LdLidarDataProcess() :
    lidar_measure_freq_(4500),
    lidar_status_(LidarStatus::NORMAL),
    lidar_error_code_(LIDAR_NO_ERROR),
    is_frame_ready_(false),
    is_noise_filter_(false),
    timestamp_(0),
    speed_(0),
    get_timestamp_(nullptr),
    is_poweron_comm_normal_(false),
    last_pkg_timestamp_(0),
    protocol_handle_(new LdLidarProtocol()) {
}

LdLidarDataProcess::~LdLidarDataProcess() {
    if (protocol_handle_ != nullptr) {
        delete protocol_handle_;
    }
}

void LdLidarDataProcess::setNoiseFilter(bool is_enable) {
    is_noise_filter_ = is_enable;
}

void LdLidarDataProcess::registerTimestampGetFunctional(std::function<uint64_t(void)> timestamp_handle) {
    get_timestamp_ = timestamp_handle;
}

bool LdLidarDataProcess::parse(const uint8_t *data, long len)
{
    for (int i = 0; i < len; i++) {
        uint8_t ret = protocol_handle_->analyzeDataPacket(data[i]);
        if (ret == GET_PKG_PCD) {
            LiDARMeasureDataType datapkg = protocol_handle_->getPCDPacketData();
            is_poweron_comm_normal_ = true;
            speed_ = datapkg.speed;
            timestamp_ = datapkg.timestamp;
            // parse a package is success
            double diff = (datapkg.end_angle / 100 - datapkg.start_angle / 100 + 360) % 360;
            if (diff <= ((double)datapkg.speed * POINT_PER_PACK / lidar_measure_freq_ * 1.5)) {
                if (0 == last_pkg_timestamp_) {
                    last_pkg_timestamp_ = get_timestamp_();
                }
                else {
                    uint64_t current_pack_stamp = get_timestamp_();
                    int pkg_point_number = POINT_PER_PACK;
                    double pack_stamp_point_step =
                        static_cast<double>(current_pack_stamp - last_pkg_timestamp_) / static_cast<double>(pkg_point_number - 1);
                    uint32_t diff = ((uint32_t)datapkg.end_angle + 36000 - (uint32_t)datapkg.start_angle) % 36000;
                    float step = diff / (POINT_PER_PACK - 1) / 100.0;
                    float start = (double)datapkg.start_angle / 100.0;
                    PointData data;
                    for (int i = 0; i < POINT_PER_PACK; i++) {
                        data.distance = datapkg.point[i].distance;
                        data.angle = start + i * step;
                        if (data.angle >= 360.0) {
                            data.angle -= 360.0;
                        }
                        data.intensity = datapkg.point[i].intensity;
                        data.stamp = static_cast<uint64_t>(last_pkg_timestamp_ + (pack_stamp_point_step * i));
                        tmp_lidar_scan_data_vec_.push_back(PointData(data.angle, data.distance, data.intensity, data.stamp));
                    }
                    last_pkg_timestamp_ = current_pack_stamp; // update last pkg timestamp
                }
            }
        }
    }

    return true;
}

bool LdLidarDataProcess::assemblePacket() {
    float last_angle = 0;
    Points2D tmp, data;
    int count = 0;

    if (speed_ <= 0) {
        tmp_lidar_scan_data_vec_.erase(tmp_lidar_scan_data_vec_.begin(), tmp_lidar_scan_data_vec_.end());
        return false;
    }

    for (auto n : tmp_lidar_scan_data_vec_) {
        // wait for enough data, need enough data to show a circle
        // enough data has been obtained
        if ((n.angle < 20.0) && (last_angle > 340.0)) {
            if ((count * getSpeed()) > (lidar_measure_freq_ * 1.4)) {
                if (count >= (int)tmp_lidar_scan_data_vec_.size()) {
                    tmp_lidar_scan_data_vec_.clear();
                }
                else {
                    tmp_lidar_scan_data_vec_.erase(
                        tmp_lidar_scan_data_vec_.begin(),
                        tmp_lidar_scan_data_vec_.begin() + count
                    );
                }
                return false;
            }
            data.insert(data.begin(), tmp_lidar_scan_data_vec_.begin(), tmp_lidar_scan_data_vec_.begin() + count);

            if (is_noise_filter_) {
                Tofbf tofbfLd(speed_);
                tmp = tofbfLd.filter(data); // filter noise point
            }
            else {
                tmp = data;
            }

            std::sort(tmp.begin(), tmp.end(), [](PointData a, PointData b) { return a.stamp < b.stamp; });
            if (tmp.size() > 0) {
                setLaserScanData(tmp);
                setFrameReady();

                if (count >= (int)tmp_lidar_scan_data_vec_.size()) {
                    tmp_lidar_scan_data_vec_.clear();
                }
                else {
                    tmp_lidar_scan_data_vec_.erase(tmp_lidar_scan_data_vec_.begin(), tmp_lidar_scan_data_vec_.begin() + count);
                }
                return true;
            }
        }
        count++;

        if ((count * getSpeed()) > (lidar_measure_freq_ * 2)) {
            if (count >= (int)tmp_lidar_scan_data_vec_.size()) {
                tmp_lidar_scan_data_vec_.clear();
            }
            else {
                tmp_lidar_scan_data_vec_.erase(tmp_lidar_scan_data_vec_.begin(), tmp_lidar_scan_data_vec_.begin() + count);
            }
            return false;
        }

        last_angle = n.angle;
    }

    return false;
}

void LdLidarDataProcess::commReadCallback(const char *byte, size_t len) {
    if (parse((uint8_t *)byte, len)) {
        assemblePacket();
    }
}

bool LdLidarDataProcess::getLaserScanData(Points2D &out) {
    if (isFrameReady()) {
        resetFrameReady();
        out = getLaserScanData();
        return true;
    }
    else {
        return false;
    }
}

double LdLidarDataProcess::getSpeed(void) {
    return (speed_ / 360.0); // unit is Hz
}

LidarStatus LdLidarDataProcess::getLidarStatus(void) {
    return lidar_status_;
}

uint8_t LdLidarDataProcess::getLidarErrorCode(void) {
    return lidar_error_code_;
}

bool LdLidarDataProcess::getLidarPowerOnCommStatus(void) {
    if (is_poweron_comm_normal_) {
        is_poweron_comm_normal_ = false;
        return true;
    }
    else {
        return false;
    }
}

bool LdLidarDataProcess::isFrameReady(void) {
    std::lock_guard<std::mutex> lg(mutex_lock1_);
    return is_frame_ready_;
}

void LdLidarDataProcess::resetFrameReady(void) {
    std::lock_guard<std::mutex> lg(mutex_lock1_);
    is_frame_ready_ = false;
}

void LdLidarDataProcess::setFrameReady(void) {
    std::lock_guard<std::mutex> lg(mutex_lock1_);
    is_frame_ready_ = true;
}

void LdLidarDataProcess::setLaserScanData(Points2D &src) {
    std::lock_guard<std::mutex> lg(mutex_lock2_);
    lidar_scan_data_vec_ = src;
    setLidarPoints(src);
}

// Helper function to find consecutive groups
// Equivalent of Python more_itertools.consecutive_groups
std::vector<std::vector<uint16_t>> consecutive_groups(const std::vector<uint16_t>& angles) {
    std::vector<std::vector<uint16_t>> groups;
    if (angles.empty()) return groups;

    std::vector<uint16_t> current_group;
    current_group.push_back(angles[0]);

    for (size_t i = 1; i < angles.size(); i++) {
        if (angles[i] == angles[i-1] + 1) {
            current_group.push_back(angles[i]);
        }
        else {
            if (!current_group.empty()) {
                groups.push_back(current_group);
                current_group.clear();
            }
            current_group.push_back(angles[i]);
        }
    }
    if (!current_group.empty()) {
        groups.push_back(current_group);
    }
    return groups;
}

void LdLidarDataProcess::setLidarPoints(Points2D &src) {
    uint16_t max_distance = 3000;
    uint8_t min_intensity = 150;
    std::array<uint16_t, NUM_ANGLES> result_distances;
    std::array<uint8_t, NUM_ANGLES> result_intensities;
    std::array<std::vector<uint16_t>, NUM_ANGLES> tmp_distances;
    std::array<std::vector<uint8_t>, NUM_ANGLES> tmp_intensities;

    // Build a list of points for each integer degree
    for (auto & point: src) {
        if (point.intensity < min_intensity) {
            continue;
        }
        uint16_t angle_sym = (uint16_t)std::floor(point.angle);
        uint16_t angle = angle_sym >= 0 ? angle_sym : angle_sym + NUM_ANGLES;
        if (0 <= angle && angle < NUM_ANGLES && point.distance > 0.0) {
            tmp_distances[angle].push_back(point.distance);
            tmp_intensities[angle].push_back(point.intensity);
        }
    }

    // Compute mean of points list for each degree.
    std::vector<uint16_t> empty_angles;
    for (size_t angle = 0; angle < NUM_ANGLES; angle++) {
        auto & distances = tmp_distances[angle];
        auto & intensities = tmp_intensities[angle];
        uint16_t distance = max_distance;
        uint8_t intensity = min_intensity;
        size_t size = distances.size();
        if (size > 0) {
            distance = std::round(std::accumulate(distances.begin(), distances.end(), 0) / size);
            intensity = std::round(std::accumulate(intensities.begin(), intensities.end(), 0) / size);
        }
        else {
            empty_angles.push_back(angle);
        }

        result_distances[angle] = distance;
        result_intensities[angle] = intensity;
    }

    // If a degree has no valid point and is isolated (no other empty angle before and after)
    // it is probably a bad value, so set it to the mean of surrounding degrees.
    // for group in consecutive_groups(empty_angles):
    for (const auto & group: consecutive_groups(empty_angles)) {
        if (group.size() == 1) {
            uint16_t isolated = group[0];
            uint16_t before_distance = result_distances[(isolated - 1 + 360) % 360];
            uint16_t after_distance = result_distances[(isolated + 1) % 360];
            result_distances[isolated] = (uint16_t)std::round((before_distance + after_distance) / 2.0);
            uint8_t before_intensity = result_intensities[(isolated - 1 + 360) % 360];
            uint8_t after_intensity = result_intensities[(isolated + 1) % 360];
            result_intensities[isolated] = (uint8_t)std::round((before_intensity + after_intensity) / 2.0);
        }
    }

    for (size_t angle = 0; angle < NUM_ANGLES; angle++) {
        lidar_points_[angle][0] = result_distances[angle];
        lidar_points_[angle][1] = result_intensities[angle];
    }
}

Points2D LdLidarDataProcess::getLaserScanData(void) {
    std::lock_guard<std::mutex> lg(mutex_lock2_);
    return lidar_scan_data_vec_;
}

} // namespace ldlidar
