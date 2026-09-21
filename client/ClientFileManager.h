#pragma once
#include <cstdint>
#include <string>


#define SERVER_INFO_PATH "transfer.json"
#define CLIENT_INFO_PATH "me.info"
#define PRIVATE_KEY_PATH "priv.key"

///@brief hold the server info read from "transfer.json"
struct ServerInfo {
    std::string ip;
    uint16_t port;
    std::string clientName;
    std::string filePath;
};

///@brief hold the client info read from the "me.info"
struct ClientInfo {
    std::string name;
    std::string uuid;
    std::string privateKey;
};


class ClientFileManager {
    public:
    ///@brief extract server data from the server info file
    ///@param filename is the name of the file we are extracting from
    ///@return ServerInfo structured hold the server info
    static ServerInfo readServerInfo(const std::string& filename = SERVER_INFO_PATH);

    ///@brief extract client data from the client info file
    ///@param filename is the name of the file we are extracting form
    ///@return ClientInfo structured hold the client info or empty if we need to crate me.info
    static ClientInfo readClientInfo(const std::string& filename = CLIENT_INFO_PATH);

    ///@brief create me.info
    ///@param filename is the name of the file we are creating
    ///@param clientInfo is the struct that hold the client info
    static void writeMeInfo(const std::string& filename, const ClientInfo& clientInfo);
    ///@brief create priv.key for the client
    ///@param privateKey is the client private key
    static void writePrivFile(const std::string& privateKey);
    ///@brief read and return a file content
    static std::string readFile(const std::string& filePath);
};