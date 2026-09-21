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
