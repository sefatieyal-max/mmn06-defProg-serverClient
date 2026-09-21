#include "NetworkManager.h"
#include <stdexcept>
#include <iostream>
#include <utility>


NetworkManager::NetworkManager(std::string ip, uint16_t port) :
    m_ip(std::move(ip)), m_port(port), m_socket(m_io){

}

NetworkManager::~NetworkManager() {
    disconnect();
}

void NetworkManager::connect() {
    try {
        boost::asio::ip::tcp::resolver resolver(m_io);
        auto endpoints = resolver.resolve(m_ip, std::to_string(m_port));

        boost::asio::connect(m_socket, endpoints);
        std::cout << "Connected to server: " << m_ip << ":" << m_port << std::endl;
    }catch (const boost::system::system_error& e) {
        throw std::runtime_error("Connection failed: " + std::string(e.what()));
    }
}

void NetworkManager::disconnect() {
    if (m_socket.is_open()) {
        boost::system::error_code ec;
        m_socket.shutdown(boost::asio::ip::tcp::socket::shutdown_both, ec);
        m_socket.close(ec);
    }
}

void NetworkManager::sendBytes(const uint8_t *data, size_t len) {
    try {
        boost::asio::write(m_socket, boost::asio::buffer(data, len));
    }catch (const boost::system::system_error& e) {
        throw std::runtime_error("Data send failed: " + std::string(e.what()));
    }
}

std::vector<uint8_t> NetworkManager::receiveBytes(size_t len) {
    std::vector<uint8_t> buffer(len);
    try {
        boost::asio::read(m_socket, boost::asio::buffer(buffer, len));
    }catch (const boost::system::system_error& e) {
        throw std::runtime_error("Data receive failed: " + std::string(e.what()));
    }
    return buffer;
}