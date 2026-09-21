#include <filesystem>

#include "ClientFileManager.h"
#include "NetworkManager.h"
#include "RequestManager.h"
#include <iostream>
#include <fstream>

#define PROGRAM_ERROR (-1)
#define OK (0)



int main() {
    try {
        //----------------connection----------------------

        // read json file
        ServerInfo serverInfo = ClientFileManager::readServerInfo(SERVER_INFO_PATH);
        std::cout << "Server Info:" << std::endl;
        std::cout << "- Server IP:" << serverInfo.ip << std::endl;
        std::cout << "- Server Port:" << serverInfo.port << std::endl;
        std::cout << "- Client Name:" << serverInfo.clientName << std::endl;

        //connect into the server
        RequestManager requestManager(serverInfo);
        requestManager.connect();

        //----------------registration----------------------

        // check if me.info exist
        std::ifstream checkMeInfo(CLIENT_INFO_PATH);
        if (!checkMeInfo.is_open()) {
            //new client - register and exchange keys
            requestManager.registerClient();
            requestManager.sendPublicKey();
        }else {
            checkMeInfo.close();
            //existing client - reconnect
            if (!requestManager.reconnect()) {
                std::cerr << "Failed to reconnect to the server" << std::endl;
                std::filesystem::remove(CLIENT_INFO_PATH);

                //act like new client
                requestManager.registerClient();
                requestManager.sendPublicKey();
            }
        }

        //--------------------send files-------------------
        requestManager.sendFile(serverInfo.filePath);

        //--------------------disconnect-------------------
        requestManager.disconnect();

    }catch (std::exception &e) {
        std::cout << "Error:" << e.what() << std::endl;
        return PROGRAM_ERROR;
    }
    return OK;
}