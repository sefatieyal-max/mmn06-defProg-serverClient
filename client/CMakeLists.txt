cmake_minimum_required(VERSION 3.10)

project(client)

set(CMAKE_CXX_STANDARD 20)

find_package(Boost REQUIRED)
find_package(cryptopp CONFIG REQUIRED)

add_executable(client
        main.cpp
        ClientFileManager.h
        ClientFileManager.cpp
        RSAWrapper.h
        RSAWrapper.cpp
        AESWrapper.h
        AESWrapper.cpp
        Base64Wrapper.h
        Base64Wrapper.cpp
        Protocol.h
        NetworkManager.h
        NetworkManager.cpp
        RequestManager.h
        RequestManager.cpp
        cksum.h
        cksum.cpp
)

target_link_libraries(client PRIVATE
        Boost::boost
        cryptopp::cryptopp
        ws2_32
)