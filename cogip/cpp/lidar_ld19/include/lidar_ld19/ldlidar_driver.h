/**
 * @file ldlidar_driver.h
 * @author LDRobot (support@ldrobot.com)
 * @brief  ldlidar sdk interface
 *         This code is only applicable to LDROBOT LiDAR LD19 products sold by Shenzhen LDROBOT Co., LTD
 * @version 0.1
 * @date 2021-05-12
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

#include "lidar_ld19/ldlidar_datatype.h"
#include "lidar_ld19/ldlidar_dataprocess.h"

#include <libserial/SerialPort.h>

#include <atomic>
#include <chrono>
#include <functional>
#include <thread>

#define MAX_ACK_BUF_LEN (4096 / 8)

namespace ldlidar {

uint64_t getSystemTimeStamp(void);

class LDLidarDriver {
public:
    LDLidarDriver();

    ~LDLidarDriver();

    /**
     * @brief Get running status.
     */
    static bool ok() { return is_ok_; };

    /**
     * @brief Set running status.
     */
    static void setLidarDriverStatus(bool status) { is_ok_ = status; };

    /**
     * @brief Communication port open and assert initialization param
     * @param serial_port_name
     *        serial device system path, eg: "/dev/ttyUSB0"
     * @param serial_baudrate
     *       serial communication baudrate value(> 0), unit is bit/s.
     * @retval value is true, start is success;
     *   value is false, start is failed.
     */
    bool connect(
        const std::string &serial_port_name,
        LibSerial::BaudRate serial_baudrate = LibSerial::BaudRate::BAUD_230400
    );

    bool disconnect(void);

    void enablePointCloudDataFilter(bool is_enable);

    /**
     * @brief Whether the connection of the communication channel is normal after the lidar is powered on
     * @param[in]
     * *@param timeout:  Wait timeout, in milliseconds
     * @retval if times >= 1000, return false, communication connection is fail;
     *   if "times < 1000", return true, communication connection is successful.
     */
    bool waitLidarComm(int64_t timeout);

    /**
     * @brief get lidar laser scan point cloud data
     * @param [output]
     * *@param dst: type is ldlidar::Point2D, value is laser scan point cloud data
     * @param [in]
     * *@param timeout: Wait timeout, in milliseconds
     * @retval value is ldlidar::LidarStatus Enum Type, definition in "include/ldlidar_datatype.h", value is:
     *  ldlidar::LidarStatus::NORMAL
     *  ldlidar::LidarStatus::ERROR
     *  ....
     */
    LidarStatus getLaserScanData(Points2D &dst, int64_t timeout);

    // Get pointer to internal lidar points
    const uint16_t (&getLidarPoints() const)[NUM_ANGLES][2] {
        return comm_pkg_->getLidarPoints();
    }

    /**
     * @brief get lidar scan frequency
     * @param [output]
     * *@param spin_hz: value is lidar scan frequency, unit is Hz
     * @retval value is true, get success;
     */
    bool getLidarScanFreq(double &spin_hz);

    /**
     * @brief register get timestamp handle functional.
     * @param [input]
     * *@param get_timestamp_handle: type is `uint64_t (*)(void)`, value is pointer get timestamp fuction.
     * @retval none
     */
    void registerGetTimestampFunctional(std::function<uint64_t(void)> get_timestamp_handle);

    /**
     * @brief When the lidar is in an error state, get the error code fed back by the lidar
     * @param none
     * @retval errcode
     */
    uint8_t getLidarErrorCode(void) const;

    /**
     * @brief Start lidar driver node
     * @param none
     * @retval value is true, start is success;
     *   value is false, start is failed.
     */
    bool start(void);

    /**
     * @brief Stop lidar driver node
     * @param none
     * @retval value is true, stop is success;
     *  value is false, stop is failed.
     */
    bool stop(void);

    void rxThreadProc();

protected:
    bool is_start_flag_;
    bool is_connect_flag_;

private:
    static bool is_ok_;
    LdLidarDataProcess *comm_pkg_;
    LibSerial::SerialPort *comm_serial_;
    std::function<uint64_t(void)> register_get_timestamp_handle_;
    std::chrono::_V2::steady_clock::time_point last_pubdata_times_;
    std::atomic<bool> rx_thread_exit_flag_;
    std::thread *rx_thread_;
};

} // namespace ldlidar
