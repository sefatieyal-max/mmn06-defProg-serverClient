
```markdown
# Secure File Transfer Client-Server System (Maman 06)

A secure Client-Server communication system built as part of the "Defensive Systems Programming" course. The system allows C++20 clients to register with a Python 3.12 server, perform encrypted key exchanges, and securely transfer binary files with integrity verification (CRC) and failure retry controls.

---

## 🚀 Key Features

* **Binary TCP Architecture:** Strict protocol implementation over TCP, ensuring **Little-Endian** data representation and fixed-size headers (23-byte header).
* **Advanced Hybrid Encryption:**
  * **Asymmetric (RSA-1024 / PKCS1_OAEP):** For secure initial key exchange between client and server.
  * **Symmetric (AES-256-CBC):** For fast encryption of file contents split into chunks.
* **File Integrity Verification (POSIX CRC):** Utilizing the Linux `cksum` algorithm on both ends for absolute file content verification, including an automatic retry mechanism (up to 3 attempts).
* **Persistence & Recovery:** Integration of an **SQLite** database (`defensive.db`) on the server side for client management, file tracking, and full recovery support after server crashes.
* **Defensive Programming:** Strict input validation, mitigation against vulnerabilities (such as Path Traversal in filenames), and automatic resource management via **RAII** on the client side.

---

## 🛠️ Tech Stack

* **Server Side:** Python 3.12, PyCryptodome, SQLite3, Sockets, Threading.
* **Client Side:** C++20, Boost.Asio (Networking), Crypto++ (Encryption), STL, MSVC.
* **Version Control:** Git / GitHub.

---

## 💻 How to Run the Project (Execution Guide)

### 1. Server Setup (Python)
1. Navigate to the `server/` directory.
2. *(Optional)* Create a `port.info` file containing the desired port number (e.g., `1265`). If the file is missing or contains invalid data, the server will default to port `1369`.
3. Run the server:
   ```bash
   python server.py

```

4. The server will automatically generate the `defensive.db` (SQLite database) and an `uploads/` directory for incoming files upon receiving active client connections.

### 2. Client Setup (C++)

1. Navigate to the client executable's directory (e.g., `cmake-build-debug` or `Release`).
2. Create a configuration file named `transfer.json` in the same directory with the following structure:
```json
{
  "server": {
    "ip": "127.0.0.1",
    "port": 1265,
    "client": "MyComputer",
    "file": "test.txt"
  }
}

```


3. Place the target file you wish to transfer (e.g., `test.txt`) in this exact same directory.
4. Compile the project using C++20 (via CMake or Visual Studio 2026).
5. Execute the compiled client application:
```bash
client.exe

```



### 3. Expected Behavior (Batch Mode)

* **First Run:** The client reads `transfer.json`, connects to the server, registers as a new user, exchanges RSA and AES keys, generates `me.info` and `priv.key`, encrypts the target file, and securely transfers it.
* **Subsequent Runs (Reconnection):** The client detects the existing `me.info` file, skips the registration process, successfully requests a new AES key from the server (Reconnect request 827), and proceeds directly to the file transfer.

📂 Project Architecture
mmn06/
│
├── server/
│   ├── server.py           # Main entry point and socket listener
│   ├── client_handler.py   # Client request routing in dedicated threads
│   ├── database.py         # SQLite interface (Clients and Files tables)
│   ├── crypto_manager.py   # AES decryption and PKCS#7 unpadding
│   ├── file_manager.py     # User directories and chunk management
│   └── cksum.py            # POSIX-compliant CRC calculation
│
└── client/
    ├── main.cpp            # Entry point and client lifecycle management
    ├── RequestManager.*    # Protocol logic implementation (825 to 902)
    ├── NetworkManager.*    # TCP networking wrapper using Boost.Asio
    ├── ClientFileManager.* # JSON configuration parsing and me.info handling
    └── Protocol.h          # Packed memory data structures (#pragma pack)
