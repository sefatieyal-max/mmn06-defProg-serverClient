#pragma once

#include <string>


class AESWrapper
{
public:
	static constexpr unsigned int DEFAULT_KEY_LENGTH = 32;
private:
	unsigned char _key[DEFAULT_KEY_LENGTH]{};
public:
	static unsigned char* GenerateKey(unsigned char* buffer, unsigned int length);

	AESWrapper();
	AESWrapper(const unsigned char* key, unsigned int size);
	explicit AESWrapper(const std::string& key);
	~AESWrapper();

	[[nodiscard]] const unsigned char* getKey() const;

	std::string encrypt(const char* plain, unsigned int length);
	std::string decrypt(const char* cipher, unsigned int length);
};