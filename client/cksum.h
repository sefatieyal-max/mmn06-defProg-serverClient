#pragma once
#include <string>
#include <cstdint>

class CRCCalculator {
public:
    ///@brief the function calculate CRC from a given content
    static uint32_t calculateCRC(const std::string& content);
};