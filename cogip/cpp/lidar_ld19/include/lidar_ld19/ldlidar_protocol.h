/**
 * @file         ldlidar_protocol.h
 * @author       LDRobot (support@ldrobot.com)
 *               David Hu(hmd_hubei_cn@163.com)
 * @brief
 * @version      1.0
 * @date         2023.3.11
 * @note
 * @copyright    Copyright (c) 2017-2023  SHENZHEN LDROBOT CO., LTD. All rights reserved.
 * Licensed under the MIT License (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License in the file LICENSE
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 **/

#pragma once

#include <cstdint>

namespace ldlidar {

#define PKG_HEADER 0x54
#define DATA_PKG_INFO 0x2C
#define POINT_PER_PACK 12
#define HEALTH_PKG_INFO 0xE0
#define MANUFACT_PKG_INF 0x0F

#define GET_PKG_PCD 1
#define GET_PKG_HEALTH 2
#define GET_PKG_MANUFACT 3
#define GET_PKG_ERROR 0

typedef struct __attribute__((packed)) {
    uint8_t header;
    uint8_t information;
    uint16_t speed;
    uint16_t product_version;
    uint32_t sn_high;
    uint32_t sn_low;
    uint32_t hardware_version;
    uint32_t firmware_version;
    uint8_t crc8;
} LiDARManufactureInfoType;

typedef struct __attribute__((packed)) {
    uint16_t distance;
    uint8_t intensity;
} LidarPointStructType;

typedef struct __attribute__((packed)) {
    uint8_t header;
    uint8_t ver_len;
    uint16_t speed;
    uint16_t start_angle;
    LidarPointStructType point[POINT_PER_PACK];
    uint16_t end_angle;
    uint16_t timestamp;
    uint8_t crc8;
} LiDARMeasureDataType;

typedef struct __attribute__((packed)) {
    uint8_t header;
    uint8_t information;
    uint8_t error_code;
    uint8_t crc8;
} LiDARHealthInfoType;

class LdLidarProtocol {
public:
    LdLidarProtocol();
    ~LdLidarProtocol();

    /**
     * @brief Analyze data packet.
     * @param[in]
     * * @param byte: input serial byte data.
     * @retval
     *   If the return value is GET_PKG_PCD macro, the lidar point cloud data is obtained.
     *   If the return value is GET_PKG_HEALTH macro, the lidar health information is obtained.
     *   If the return value is GET_PKG_MANUFACT macro, the lidar manufacture information is obtained.
     */
    uint8_t analyzeDataPacket(uint8_t byte);

    /**
     * @brief get point cloud data.
     */
    LiDARMeasureDataType &getPCDPacketData(void);

private:
    LiDARMeasureDataType pcdpkg_data_;
    LiDARHealthInfoType healthpkg_data_;
    LiDARManufactureInfoType manufacinfpkg_data_;
};

uint8_t calCRC8(const uint8_t *data, uint16_t data_len);

} // namespace ldlidar
