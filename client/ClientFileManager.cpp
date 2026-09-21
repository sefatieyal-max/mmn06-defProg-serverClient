#include "ClientFileManager.h"
#include <fstream>
#include <stdexcept>
#include <iostream>

std::string extractJsonValue(const std::string& jsonTxt,const std::string& key) {
    size_t keyPos = jsonTxt.find("\"" + key + "\"");
    if (keyPos == std::string::npos) {
        throw std::runtime_error(" key not found: " + key);
    }

    //find the start of the requested value (first colon after the key)
    size_t colonPos = jsonTxt.find(':',keyPos);
    if (colonPos == std::string::npos) return "";

    //find the first value char
    size_t startPos = jsonTxt.find_first_not_of(" \t\r\n", colonPos + 1);
    if (startPos == std::string::npos) return "";

    std::string value;
    if (jsonTxt[startPos] == '\"') {
        //deal with a string
        size_t endPos = jsonTxt.find('\"', startPos + 1);
        if (endPos == std::string::npos) throw std::runtime_error(" crooked JSON string for key: " + key);
        value = jsonTxt.substr(startPos + 1, endPos - startPos - 1);
    }else {
        //deal with number
        size_t endPos = jsonTxt.find_first_of(",}", startPos);
        if (endPos == std::string::npos) endPos = jsonTxt.length();
        value = jsonTxt.substr(startPos, endPos - startPos);

        //clean extra spaces
        value.erase(value.find_last_not_of(" \t\r\n") + 1);
    }
    return value;
};


// ----------ClientFileManager functions-------------

ServerInfo ClientFileManager::readServerInfo(const std::string &filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        throw std::runtime_error("Error: cannot open: " + filename);
    }
    //read all the file
    std::string content((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());

    ServerInfo serverInfo;
    try {
        serverInfo.ip = extractJsonValue(content, "ip");
        serverInfo.port = static_cast<uint16_t>(std::stoi(extractJsonValue(content, "port")));
        serverInfo.clientName = extractJsonValue(content, "client");
        serverInfo.filePath = extractJsonValue(content, "file");
    }catch (const std::exception &e) {
        throw std::runtime_error("Error: reading the server info file" + std::string(e.what()));
    }
    return serverInfo;
}

ClientInfo ClientFileManager::readClientInfo(const std::string &filename) {
    ClientInfo clientInfo;
    std::ifstream file(filename);

    if (!file.is_open()) {
        return clientInfo;
    }

    auto cleanLine = [](std::string& line) {
        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }
    };

    std::getline(file,clientInfo.name);
    cleanLine(clientInfo.name);
    std::getline(file, clientInfo.uuid);
    cleanLine(clientInfo.uuid);
    std::getline(file,clientInfo.privateKey);
    cleanLine(clientInfo.privateKey);

    return clientInfo;
}

void ClientFileManager::writeMeInfo(const std::string& filename, const ClientInfo& clientInfo) {
    std::ofstream file(filename);
    if (!file.is_open()) {
        throw std::runtime_error("Error: cannot open: " + filename);
    }
    file << clientInfo.name << "\n";
    file << clientInfo.uuid << "\n";
    file << clientInfo.privateKey << "\n";

    std::cout << "successfully create " << filename <<" for client: " << clientInfo.name << std::endl;
}

void ClientFileManager::writePrivFile(const std::string &privateKey) {
    std::ofstream privFile(PRIVATE_KEY_PATH);
    if (!privFile.is_open()) {
        throw std::runtime_error("Error: cannot open: " + static_cast<std::string>(PRIVATE_KEY_PATH));
    }
    privFile << privateKey;
    privFile.close();
}

std::string ClientFileManager::readFile(const std::string &filePath) {
    std::ifstream file(filePath, std::ios::binary);
    if (!file.is_open()) throw std::runtime_error("failed to open file");
    std::string fileContent((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
    file.close();
    return fileContent;
}
