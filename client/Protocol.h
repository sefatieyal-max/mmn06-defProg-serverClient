#pragma once

#include <string>
#include <cstdint>

#pragma pack(push,1)


//----------------constants----------------
constexpr uint8_t VERSION = 3;
constexpr size_t CLIENT_ID_SIZE = 16;
constexpr size_t NAME_LEN = 255;
constexpr size_t PUBLIC_KEY_SIZE = 160;

///@brief class represent the request codes
enum class RequestCode: uint16_t {
    Register = 825,
    SendPublicKey = 826,
    Reconnect = 827,
    SendFile = 828,
    CRCOK = 900,
    CRCBadResend = 901,
    CRCBadDone = 902,
};
///@brief class represent the response codes
enum class ResponseCode: uint16_t {
    RegisterSuccess = 1600,
    RegisterFail = 1601,
    PubKeyReceived = 1602,
    FileOK = 1603,
    MassageACK = 1604,
    ReconnectAccept = 1605,
    ReconnectReject = 1606,
    GeneralError = 1607,
};

///@brief struct represent the request header
struct RequestHeader {
    uint8_t clientID[CLIENT_ID_SIZE];
    uint8_t version;
    RequestCode code;
    uint32_t payloadSize;
};
///@brief struct response the request header
struct ResponseHeader {
    uint8_t version;
    ResponseCode code;
    uint32_t payloadSize;
};

//-------------request payloads---------------------------
///@brief request payload for request codes 825|827 and crc
struct PayloadName {
    char name[NAME_LEN];
};
using PayloadRequestName = PayloadName;
using PayloadCRC = PayloadName;

///@brief request payload for request code 826
struct PayloadPublicKey {
    char name[NAME_LEN];
    uint8_t publicKey[PUBLIC_KEY_SIZE];
};
///@brief request payload for request code 828
struct PayloadFile {
    uint32_t contentSize;
    uint32_t origFileSize;
    uint16_t packetNumber;
    uint16_t totalPackets;
    char fileName[NAME_LEN];
};

//-------------response payloads---------------------------
///@brief response payload for response code 1603
struct ResponsePayloadFileOK {
    uint8_t clientID[CLIENT_ID_SIZE];
    uint32_t contentSize;
    char fileName[NAME_LEN];
    uint32_t Cksum;
};

#pragma pack (pop)