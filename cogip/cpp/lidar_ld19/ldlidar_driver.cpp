/**
 * @file ldlidar_driver.cpp
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
#include "lidar_ld19/ldlidar_driver.h"

#include <libserial/SerialPortConstants.h>

#include <unistd.h>

#include <iostream>

namespace ldlidar {

uint64_t getSystemTimeStamp(void) {
    std::chrono::time_point<std::chrono::system_clock, std::chrono::nanoseconds> tp =
        std::chrono::time_point_cast<std::chrono::nanoseconds>(std::chrono::system_clock::now());
    auto tmp = std::chrono::duration_cast<std::chrono::nanoseconds>(tp.time_since_epoch());
    return ((uint64_t)tmp.count());
}

bool LDLidarDriver::is_ok_ = false;

LDLidarDriver::LDLidarDriver() : is_start_flag_(false),
                                 is_connect_flag_(false),
                                 comm_pkg_(new LdLidarDataProcess()),
                                //  comm_serial_(new SerialInterfaceLinux()) {
                                 comm_serial_(new LibSerial::SerialPort()) {
    last_pubdata_times_ = std::chrono::steady_clock::now();
    registerGetTimestampFunctional(std::bind(getSystemTimeStamp));
}

LDLidarDriver::~LDLidarDriver() {
    if (comm_pkg_ != nullptr) {
        delete comm_pkg_;
    }

    if (comm_serial_ != nullptr) {
        delete comm_serial_;
    }
}

bool LDLidarDriver::connect(const std::string &serial_port_name, LibSerial::BaudRate serial_baudrate) {
    if (is_connect_flag_) {
        return true;
    }

    if (serial_port_name.empty()) {
        std::cerr << "Input <serial_port_name> is empty." << std::endl;
        return false;
    }

    if (register_get_timestamp_handle_ == nullptr) {
        std::cerr << "Get timestamp function is not registered." << std::endl;
        return false;
    }

    comm_pkg_->clearDataProcessStatus();
    comm_pkg_->registerTimestampGetFunctional(register_get_timestamp_handle_);

    comm_serial_->Open(serial_port_name);
    if (!comm_serial_->IsOpen()) {
        std::cerr << "Serial is not opened: " << serial_port_name << std::endl;
        return false;
    }
    comm_serial_->SetBaudRate(serial_baudrate);

    is_connect_flag_ = true;

    rx_thread_exit_flag_ = false;
    rx_thread_ = new std::thread(&LDLidarDriver::rxThreadProc, this);

    setLidarDriverStatus(true);

    return true;
}

bool LDLidarDriver::disconnect(void) {
    if (!is_connect_flag_) {
        return true;
    }

    rx_thread_exit_flag_ = true;

    setLidarDriverStatus(false);

    is_connect_flag_ = false;
    if ((rx_thread_ != nullptr) && rx_thread_->joinable()) {
        rx_thread_->join();
        delete rx_thread_;
        rx_thread_ = nullptr;
    }

    comm_serial_->Close();

    return true;
}

void LDLidarDriver::rxThreadProc() {
    std::string rx_buf;
    while (!this->rx_thread_exit_flag_.load()) {
        this->comm_serial_->Read(rx_buf, MAX_ACK_BUF_LEN);
        this->comm_pkg_->commReadCallback(rx_buf.c_str(), MAX_ACK_BUF_LEN);
   }
}

void LDLidarDriver::enablePointCloudDataFilter(bool is_enable) {
    comm_pkg_->setNoiseFilter(is_enable);
}

bool LDLidarDriver::waitLidarComm(int64_t timeout) {
    auto last_time = std::chrono::steady_clock::now();

    bool is_recvflag = false;
    do {
        if (comm_pkg_->getLidarPowerOnCommStatus()) {
            is_recvflag = true;
        }
        usleep(1000);
    } while (!is_recvflag && (std::chrono::duration_cast<std::chrono::milliseconds>(
                                    std::chrono::steady_clock::now() - last_time)
                                    .count() < timeout));

    if (is_recvflag) {
        setLidarDriverStatus(true);
        return true;
    }
    else {
        setLidarDriverStatus(false);
        return false;
    }
}

LidarStatus LDLidarDriver::getLaserScanData(Points2D &dst, int64_t timeout) {
    if (!is_start_flag_) {
        return LidarStatus::STOP;
    }

    LidarStatus status = comm_pkg_->getLidarStatus();
    if (LidarStatus::NORMAL == status) {
        if (comm_pkg_->getLaserScanData(dst)) {
            last_pubdata_times_ = std::chrono::steady_clock::now();
            return LidarStatus::NORMAL;
        }

        if (std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::steady_clock::now() - last_pubdata_times_)
                .count() > timeout) {
            return LidarStatus::DATA_TIME_OUT;
        }
        else {
            return LidarStatus::DATA_WAIT;
        }
    }
    else {
        last_pubdata_times_ = std::chrono::steady_clock::now();
        return status;
    }
}

bool LDLidarDriver::getLidarScanFreq(double &spin_hz) {
    if (!is_start_flag_) {
        return false;
    }
    spin_hz = comm_pkg_->getSpeed();
    return true;
}

void LDLidarDriver::registerGetTimestampFunctional(std::function<uint64_t(void)> get_timestamp_handle) {
    register_get_timestamp_handle_ = get_timestamp_handle;
}

uint8_t LDLidarDriver::getLidarErrorCode(void) const {
    if (!is_start_flag_) {
        return LIDAR_NO_ERROR;
    }

    uint8_t errcode = comm_pkg_->getLidarErrorCode();
    return errcode;
}

bool LDLidarDriver::start(void) {
    if (is_start_flag_) {
        return true;
    }

    if (!is_connect_flag_) {
        return false;
    }

    is_start_flag_ = true;

    last_pubdata_times_ = std::chrono::steady_clock::now();

    setLidarDriverStatus(true);

    return true;
}

bool LDLidarDriver::stop(void) {
    if (!is_start_flag_) {
        return true;
    }

    setLidarDriverStatus(false);

    is_start_flag_ = false;

    return true;
}

} // namespace ldlidar
