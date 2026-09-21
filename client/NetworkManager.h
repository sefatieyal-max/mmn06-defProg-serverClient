#pragma once

#include <string>
#include <vector>
#include <boost/asio.hpp>


class NetworkManager {
public:
        ///@brief constructor for the network with ip and port
        NetworkManager(std::string  ip, uint16_t port);

        NetworkManager(const NetworkManager&) = delete;
        NetworkManager& operator=(const NetworkManager&) = delete;
        ///@brief destructor that disconnect the client from the network
        ~NetworkManager();

        ///@brief connect to the network
        void connect();
        ///@brief disconnect from the network
        void disconnect();
        ///@brief send a sequence of bytes
        ///@param data is the data of bytes we send
        ///@param len is the length of the message
        void sendBytes(const uint8_t* data, size_t len);
        ///@brief receive a sequence of bytes
        ///@param len is the length of the message
        ///@return the bytes we received
        std::vector<uint8_t> receiveBytes(size_t len);
private:
        std::string m_ip;
        uint16_t m_port;
        boost::asio::io_context m_io;
        boost::asio::ip::tcp::socket m_socket;
};