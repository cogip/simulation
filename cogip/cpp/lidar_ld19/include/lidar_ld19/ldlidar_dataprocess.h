/**
 * @file ldlidar_dataprocess.h
 * @author LDRobot (support@ldrobot.com)
 *         David Hu (hmd_hubei_cn@163.com)
 * @brief  LiDAR data protocol processing App
 *         This code is only applicable to LDROBOT LiDAR LD19 products sold by Shenzhen LDROBOT Co., LTD
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
#pragma once

#include "lidar_ld19/ldlidar_protocol.h"
#include "lidar_ld19/tofbf.h"

#include <functional>
#include <mutex>

constexpr size_t NUM_ANGLES = 360;

namespace ldlidar
{

class LdLidarDataProcess
{
public:
    LdLidarDataProcess();

    ~LdLidarDataProcess();

    void setNoiseFilter(bool is_enable);

    void registerTimestampGetFunctional(::std::function<uint64_t(void)> timestamp_handle);

    void commReadCallback(const char *byte, size_t len);

    /**
     * @brief get lidar scan data
     */
    bool getLaserScanData(Points2D &out);

    // Get pointer to internal lidar points
    const uint16_t (&getLidarPoints() const)[NUM_ANGLES][2] { return lidar_points_; }

    /**
     * @brief get Lidar spin speed (Hz)
     */
    double getSpeed(void);

    LidarStatus getLidarStatus(void);

    uint8_t getLidarErrorCode(void);

    bool getLidarPowerOnCommStatus(void);

    void clearDataProcessStatus(void) {
        is_frame_ready_ = false;
        is_poweron_comm_normal_ = false;
        lidar_status_ = LidarStatus::NORMAL;
        lidar_error_code_ = LIDAR_NO_ERROR;
        last_pkg_timestamp_ = 0;
        lidar_scan_data_vec_.clear();
        tmp_lidar_scan_data_vec_.clear();
    }

private:
    int lidar_measure_freq_;
    LidarStatus lidar_status_;
    uint8_t lidar_error_code_;
    bool is_frame_ready_;
    bool is_noise_filter_;
    uint16_t timestamp_;
    double speed_;
    std::function<uint64_t(void)> get_timestamp_;
    bool is_poweron_comm_normal_;
    uint64_t last_pkg_timestamp_;

    LdLidarProtocol *protocol_handle_;
    Points2D lidar_scan_data_vec_;
    Points2D tmp_lidar_scan_data_vec_;
    uint16_t lidar_points_[NUM_ANGLES][2];
    std::mutex mutex_lock1_;
    std::mutex mutex_lock2_;

    bool parse(const uint8_t *data, long len);

    bool assemblePacket(); // combine standard data into data frames and calibrate

    bool isFrameReady(void); // get Lidar data frame ready flag

    void resetFrameReady(void); // reset frame ready flag

    void setFrameReady(void); // set frame ready flag

    void setLaserScanData(Points2D &src);

    void setLidarPoints(Points2D &src);

    Points2D getLaserScanData(void);
};

} // namespace ldlidar
