#include "RequestManager.h"
#include "AESWrapper.h"
#include "Protocol.h"
#include "RSAWrapper.h"
#include "Base64Wrapper.h"
#include <fstream>
#include <iostream>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <filesystem>

#include "cksum.h"


RequestManager::RequestManager(const ServerInfo &serverInfo)
    : m_serverInfo(serverInfo),m_network(serverInfo.ip,serverInfo.port){
}
void RequestManager::connect() {
    m_network.connect();
}
void RequestManager::disconnect() {
    m_network.disconnect();
}

void RequestManager::registerClient() {
    std::cout << "Starting client registration..." << std::endl;

    //build payload
    PayloadName requestPayload = {};
    std::strncpy(requestPayload.name, m_serverInfo.clientName.c_str(), NAME_LEN-1);

    //send request
    sendRequest("",RequestCode::Register,requestPayload);
    std::cout << "sent registration request (825)." << std::endl;

    //receive response
    ServerResponse response = receiveResponse();

    if (response.header.code == ResponseCode::RegisterFail) {
        throw std::runtime_error("Register failure");
    } else if (response.header.code != ResponseCode::RegisterSuccess) {
        throw std::runtime_error("Unexpected response code");
    }

    //receive the UUID
    if (response.header.payloadSize != CLIENT_ID_SIZE) {
        throw std::runtime_error("invalid UUID size");
    }

    std::string uuidHex = bytesToHex(response.payload.data(), CLIENT_ID_SIZE);
    std::cout <<"registration success, client UUID: " << uuidHex << std::endl;

    //generate RSA
    std::cout << "making 'me.info' ang generating RSA key..." << std::endl;
    RSAPrivateWrapper rsaPrivate;
    std::string newPrivateKey = Base64Wrapper::encode(rsaPrivate.getPrivateKey());

    //create me.info
    ClientInfo newClientInfo = {
        m_serverInfo.clientName,
        uuidHex,
        newPrivateKey,
    };
    ClientFileManager::writeMeInfo(CLIENT_INFO_PATH, newClientInfo);
    ClientFileManager::writePrivFile(newPrivateKey);
    std::cout << "registration complete and '" << CLIENT_INFO_PATH << "' created successfully" << std::endl;

}
void RequestManager::sendPublicKey() {
    std::cout << "starting public key sending request..." << std::endl;

    //read client info
    ClientInfo clientInfo = ClientFileManager::readClientInfo(CLIENT_INFO_PATH);

    // get the private and public key
    std::string privateKey = Base64Wrapper::decode(clientInfo.privateKey);
    RSAPrivateWrapper rsaPrivate(privateKey);
    std::string publicKey = rsaPrivate.getPublicKey();

    if (publicKey.length() != PUBLIC_KEY_SIZE) {
        throw std::runtime_error("invalid public key size");
    }

    // build payload
    PayloadPublicKey reqPayload = {};
    std::strncpy(reqPayload.name, m_serverInfo.clientName.c_str(), NAME_LEN-1);
    std::memcpy(reqPayload.publicKey, publicKey.data(), PUBLIC_KEY_SIZE);

    //send request
    sendRequest(clientInfo.uuid,RequestCode::SendPublicKey,reqPayload);
    std::cout << "sent public key request (826)." << std::endl;


    //receive header response
    ServerResponse response = receiveResponse();
    if (response.header.code != ResponseCode::PubKeyReceived) {
        throw std::runtime_error("invalid response code - the server doesnt accept the public key");
    }

    //receive and decrypt the AES
    size_t aesSize = response.header.payloadSize - CLIENT_ID_SIZE;
    std::string encryptedAes(reinterpret_cast<const char*>(response.payload.data() + CLIENT_ID_SIZE), aesSize);
    m_aesKey = rsaPrivate.decrypt(encryptedAes);

    std::cout << "Public key exchange complete." << std::endl;
}
bool RequestManager::reconnect() {
    std::cout <<"client reconnection..." << std::endl;

    //read client info
    ClientInfo clientInfo = ClientFileManager::readClientInfo(CLIENT_INFO_PATH);
    std::string privateKey = Base64Wrapper::decode(clientInfo.privateKey);
    RSAPrivateWrapper rsaPrivate(privateKey);

    //build payload
    PayloadName reqPayload = {};
    std::memset(reqPayload.name, 0, NAME_LEN);
    std::strncpy(reqPayload.name, m_serverInfo.clientName.c_str(), NAME_LEN-1);

    //send request
    sendRequest(clientInfo.uuid,RequestCode::Reconnect,reqPayload);
    std::cout << "sent reconnecting request (827)." << std::endl;

    //receive response
    ServerResponse response = receiveResponse();

    if (response.header.code == ResponseCode::ReconnectReject) {
        std::cout << "reconnect rejected." << std::endl;
        return false;
    }else if (response.header.code != ResponseCode::ReconnectAccept) {
        throw std::runtime_error("invalid response code for reconnect request");
    }

    //read and decode payload
    size_t aesSize = response.header.payloadSize - CLIENT_ID_SIZE;
    std::string encryptedAes(reinterpret_cast<const char*>(response.payload.data()) + CLIENT_ID_SIZE, aesSize);
    m_aesKey = rsaPrivate.decrypt(encryptedAes);

    std::cout << "reconnect complete." << std::endl;
    return true;
}

void RequestManager::sendFile(const std::string &filePath) {
    std::cout <<"starting file transfer request for: " << filePath << std::endl;

    // read file
    std::string fileContent = ClientFileManager::readFile(filePath);

    // encrypt file
    AESWrapper aes(m_aesKey);
    std::string encryptedContent = aes.encrypt(fileContent.c_str(), fileContent.length());
    std::string fileName = std::filesystem::path(filePath).filename().string();

    // calculate CRC
    uint32_t myCRC = CRCCalculator::calculateCRC(fileContent);

    ClientInfo clientInfo = ClientFileManager::readClientInfo(CLIENT_INFO_PATH);
    //prepare CRC payload
    PayloadCRC crcPayload = {};
    std::strncpy(crcPayload.name, fileName.c_str(), NAME_LEN-1);

    // send file in number of tries
    bool success = false;
    for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
        std::cout << "transfer attempt " << attempt <<"/" << MAX_RETRIES << std::endl;
        uint32_t serverCRC = transferFileInPackets(clientInfo.uuid,fileContent.length(),fileName,encryptedContent);

        //check CRC
        if (serverCRC == myCRC) {
            std::cout << "CRC matched, sending confirmation (900)" << std::endl;
            sendRequest(clientInfo.uuid, RequestCode::CRCOK,crcPayload);
            receiveResponse();
            success = true;
            break;
        }
        if (attempt < MAX_RETRIES) {
            std::cout << "CRC mismatch, resend file and retry request (901)" << std::endl;
            sendRequest(clientInfo.uuid, RequestCode::CRCBadResend,crcPayload);
        }
    }
    if (!success) {
        std::cout <<"CRC mismatch " << MAX_RETRIES << " times, send abort (902)" << std::endl;
        sendRequest(clientInfo.uuid, RequestCode::CRCBadDone,crcPayload);
        throw std::runtime_error("file transfer failed");
    }
    std::cout <<"file transfer completed" << std::endl;
}


RequestManager::ServerResponse RequestManager::receiveResponse() {
    // read header
    auto headerBytes = m_network.receiveBytes(sizeof(ResponseHeader));
    ResponseHeader header = {};
    std::memcpy(&header, headerBytes.data(), sizeof(ResponseHeader));

    // read payload if needed
    std::vector<uint8_t> payload;
    if (header.payloadSize > 0) {
        payload = m_network.receiveBytes(header.payloadSize);
    }
    return ServerResponse{header, payload};
}
RequestHeader RequestManager::createHeader(const std::string &clientId, RequestCode code, uint32_t payloadSize) {
    RequestHeader header = {};
    header.version = VERSION;
    header.code = code;
    header.payloadSize = payloadSize;
    hexToBytes(clientId, header.clientID);

    return header;
}

uint32_t RequestManager::transferFileInPackets(const std::string &clientId, uint32_t origFileSize, const std::string &fileName,const std::string& encryptedData) {
    uint16_t totalPackets = static_cast<uint16_t>((encryptedData.length()+PACKET_SIZE-1)/PACKET_SIZE);
    if (totalPackets == 0) totalPackets = 1;

    for (uint16_t packetNum = 1; packetNum <= totalPackets; packetNum++) {
        // calculate offset and packet size/data
        uint32_t offset = (packetNum-1) * PACKET_SIZE;
        uint32_t packetSize = std::min(static_cast<uint32_t>(PACKET_SIZE), static_cast<uint32_t>(encryptedData.length()-offset));
        std::string packetData = encryptedData.substr(offset, packetSize);

        // build payload
        PayloadFile reqPayload = {};
        reqPayload.contentSize = encryptedData.length();
        reqPayload.origFileSize = origFileSize;
        reqPayload.packetNumber = packetNum;
        reqPayload.totalPackets = totalPackets;
        std::strncpy(reqPayload.fileName, fileName.c_str(), NAME_LEN-1);

        //send request
        sendRequest(clientId,RequestCode::SendFile,reqPayload,packetData);
        std::cout << "sent packet " << packetNum << "/" << totalPackets << std::endl;
    }

    // receive response
    ServerResponse response = receiveResponse();
    if (response.header.code != ResponseCode::FileOK) {
        throw std::runtime_error("the server doesnt received the file successfully");
    }
    if (response.payload.size() < sizeof(ResponsePayloadFileOK)) {
        throw std::runtime_error("invalid payload size received for response code 1603");
    }
    const auto* payload = reinterpret_cast<const ResponsePayloadFileOK*>(response.payload.data());
    return payload->Cksum;
}

std::string RequestManager::bytesToHex(const uint8_t* data, size_t len) {
    std::ostringstream oss;
    for (size_t i = 0; i < len; i++) {
        oss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(data[i]);
    }
    return oss.str();
}
void RequestManager::hexToBytes(const std::string &hex, uint8_t *bytes) const {
    for (size_t i = 0; i < hex.length() && i < UUID_LEN; i +=2) {
        std::string bytesString = hex.substr(i, 2);
        bytes[i/2] = static_cast<uint8_t>(std::strtol(bytesString.c_str(), nullptr, 16));
    }
}