#pragma once

#include "NetworkManager.h"
#include "ClientFileManager.h"
#include <string>
#include "Protocol.h"

#define UUID_LEN 32
#define PACKET_SIZE (1024*1024) //1MB
#define MAX_RETRIES 4

class RequestManager {
public:
    ///@brief construct initialized the network manager with server details
    explicit RequestManager(const ServerInfo& serverInfo);

    ///@brief connects to the server
    void connect();
    ///@brief disconnect from the server
    void disconnect();

    ///@brief executes registration request (825) and handle the response
    void registerClient();
    ///@brief execute the public key send request(826)
    void sendPublicKey();
    ///@brief execute the reconnect request(827)
    ///@return True if the client reconnect and False if he failed
    bool reconnect();
    ///@brief execute the send file request(828)
    void sendFile(const std::string& filePath);

private:
    ServerInfo m_serverInfo;
    NetworkManager m_network;
    std::string m_aesKey;

    struct ServerResponse {
        ResponseHeader header;
        std::vector<uint8_t> payload;
    };

    ///@brief helper function for safe copy std::string into char array
    template <size_t N>
    static void safeStrCopy(char (&dest)[N], const std::string& src) {
        size_t len = std::min(N-1, src.length());
        std::memcpy(dest, src.c_str(), len);
        dest[len] = '\0';
    }

    ///@brief template function that create header and send the header and the payload of the request
    template <typename PayloadType>
    void sendRequest(const std::string& clientId,RequestCode code,const PayloadType& payload, const std::string& data = "") {
        uint32_t size = sizeof(PayloadType) + data.length();
        RequestHeader header = createHeader(clientId, code,size);

        m_network.sendBytes(reinterpret_cast<const uint8_t*>(&header),sizeof(header));
        m_network.sendBytes(reinterpret_cast<const uint8_t*>(&payload), sizeof(payload));

        if (!data.empty()) {
            m_network.sendBytes(reinterpret_cast<const uint8_t*>(data.data()), data.length());
        }
    }

    ///@brief receive and read server response
    ServerResponse receiveResponse();
    ///@brief helper function that create request header
    static RequestHeader createHeader(const std::string& clientId, RequestCode code, uint32_t payloadSize);
    ///@brief helper function that send the file in packets
    ///@return the rcr response from the server
    uint32_t transferFileInPackets(const std::string& clientId, uint32_t origFileSize, const std::string& fileName, const std::string& encryptedData);

    ///@brief translate UUID bytes into hexa string
    ///@param data is the UUID in bytes
    ///@param len is the length of the bytes
    ///@return the UUID in hexa
    static std::string bytesToHex(const uint8_t* data, size_t len);
    ///@brief translate UUID string into bytes
    ///@param hex is the UUID in hexa string
    ///@param bytes is the UUID in bytes
    static void hexToBytes(const std::string &hex, uint8_t *bytes);
};