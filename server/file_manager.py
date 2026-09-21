import os
import struct
from cksum import memcrc
from crypto_manager import CryptoManager
from database import Database
import protocol

class FileManager:
    """ class handles file transfer related functions """
    # --------------constant--------------
    UPLOAD_FOLDER = 'uploads'

    @staticmethod
    def get_file_payload(payload: bytes):
        """extract the header and data from the payload"""

        if len(payload) < protocol.REQ_FILE_HEADER_SIZE:
            return None
        header_data = payload[:protocol.REQ_FILE_HEADER_SIZE]
        encrypted_data = payload[protocol.REQ_FILE_HEADER_SIZE:]

        content_size, orig_file_size, packet_num, total_packets, name_bytes = struct.unpack(protocol.REQ_FILE_HEADER_FORMAT, header_data)
        file_name = name_bytes.split(b'\0',1)[0].decode('ascii')
        # clean the file name
        file_name = os.path.basename(file_name)

        return content_size, packet_num, total_packets, file_name, encrypted_data

    @staticmethod
    def save_chunk(client_id: bytes, file_name: str,packet_num: int, encrypted_data: bytes)-> str:
        """save the chunk from the payload into client uploads folder"""
        client_dir = os.path.join(FileManager.UPLOAD_FOLDER, client_id.hex())
        file_path = os.path.join(client_dir, file_name)

        # first packet - created directory
        if packet_num == 1:
            os.makedirs(client_dir, exist_ok=True)
            mode = 'wb'
        else:
            mode = 'ab'
        with open(file_path, mode) as f:
            f.write(encrypted_data)

        return file_path

    @staticmethod
    def process_file(client_id: bytes, file_name: str, file_path: str, db: Database) -> tuple[int, int]:
        """decrypts the file, calculate CRC save to the db and return the encrypted size and CRC"""
        aes_key = db.get_client_aes_key(client_id)
        if not aes_key:
            raise ValueError("No AES key found in the database")

        with open(file_path, 'rb') as f:
            file_encrypted_data = f.read()

        decrypted_data = CryptoManager.decrypt_aes_key(aes_key, file_encrypted_data)
        if not decrypted_data:
            raise ValueError("Decryption failed")

        with open(file_path, 'wb') as f:
            f.write(decrypted_data)

        file_crc = memcrc(decrypted_data)
        db.save_file(client_id, file_name, file_path)

        return len(file_encrypted_data), file_crc