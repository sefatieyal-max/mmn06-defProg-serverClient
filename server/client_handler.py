import logging

logger = logging.getLogger(__name__)
import os
import socket
import struct
import threading
import uuid

import protocol
from crypto_manager import CryptoManager
from database import Database
from file_manager import FileManager
from protocol import RequestCode, ResponseCode


class ClientHandler(threading.Thread):
    """handles client connection in a separate thread"""

    def __init__(self, conn: socket.socket, addr, db: Database):
        super().__init__()
        self.conn = conn
        self.addr = addr
        self.db = db

    def run(self):
        """handle the client connection - read the header,payload and routs the request"""
        logger.info(f"client connected from {self.addr}")
        try:
            while True:
                # read header
                header_data = self._receive_bytes(protocol.REQUEST_HEADER_SIZE)
                if not header_data:
                    break
                client_id, version, code, payload_size = struct.unpack(protocol.REQUEST_HEADER_FORMAT, header_data)
                logger.info(f"header received Version: {version}, Code: {code}, Payload Size: {payload_size}")

                # read payload
                payload = self._receive_bytes(payload_size) if payload_size > 0 else b''
                if payload_size > protocol.MAX_PAYLOAD_SIZE:
                    logger.warning(f"payload size {payload_size} exceeds max of {protocol.MAX_PAYLOAD_SIZE}")
                    self._send_response(ResponseCode.GeneralError)
                    break

                # route request
                self._route_request(code, client_id, payload)
        except ConnectionError as e:
            logger.warning(f"connection error: {e}")
        except struct.error:
            logger.error(f"failed to receive header from {self.addr}")
        except Exception as e: # noqa: BLE001
            logger.error(f"error handling client {self.addr}: {e}")
        finally:
            self.conn.close()
            logger.info(f"connection closed for {self.addr}")

    def _receive_bytes(self,size: int) -> bytes:
        """helper function to receive exactly size bytes from the socket """
        if size == 0:
            return b''

        bytes_received = 0
        chunks = []
        while bytes_received < size:
            chunk = self.conn.recv(min(size - bytes_received,protocol.CHUNK_SIZE))
            if not chunk:
                raise ConnectionError("connection closed unexpectedly")
            chunks.append(chunk)
            bytes_received += len(chunk)
        return b''.join(chunks)

    def _route_request(self, code: int, client_id: bytes, payload:bytes):
        """route request to their handler method"""
        try:
            req_code: RequestCode = RequestCode(code)
        except ValueError:
            logger.warning(f"invalid code: {code}")
            return
        match req_code:
            case RequestCode.Register:
                self.handle_registration(client_id,payload)
            case RequestCode.SendPublicKey:
                self.handle_public_key(client_id,payload)
            case RequestCode.Reconnect:
                self.handle_reconnect(client_id,payload)
            case RequestCode.SendFile:
                self.handle_send_file(client_id,payload)
            case RequestCode.CRCOK:
                self.handle_crc_ok(client_id, payload)
            case RequestCode.CRCBadResend:
                logger.info(f"client {client_id.hex()} reported mismatch CRC, waiting for resend")
            case RequestCode.CRCBadDone:
                self.handle_crc_abort(client_id, payload)



    def _send_response(self, code: ResponseCode, payload: bytes =b''):
        """helper function for sending a response to the client"""
        try:
            header = struct.pack(protocol.RESPONSE_HEADER_FORMAT, protocol.VERSION, code.value, len(payload))
            self.conn.sendall(header + payload)
            logger.info(f"sent response: Code: {code.value}, Payload Size: {len(payload)}")
        except Exception as e: # noqa: BLE001
            logger.error(f"failed to send response to {self.addr}: {e}")
            raise ConnectionError("failed to send response")

    def handle_registration(self, client_id: bytes, payload: bytes):
        """handle client registration (request 825)"""
        logger.info(f"client registered: {client_id} starting...")
        try:
            name_bytes = payload.split(b'\0',1)[0]
            name = name_bytes.decode('ascii')

            if not name:
                logger.warning("empty name received")
                self._send_response(ResponseCode.RegisterFail)
                return

            if self.db.client_exists(name):
                logger.warning(f"client with name {name} already exists")
                self._send_response(ResponseCode.RegisterFail)
            else:
                # create UUID
                new_client_id = uuid.uuid4().bytes
                self.db.register_client(new_client_id, name)
                logger.info(f"new client {name} registered with UUID: {new_client_id}")
                self._send_response(ResponseCode.RegisterSuccess, new_client_id)
        except UnicodeDecodeError:
            logger.error("failed to decode client name")
            self._send_response(ResponseCode.RegisterFail)
        except Exception as e: # noqa: BLE001
            logger.error(f"failed to register client: {e}")
            self._send_response(ResponseCode.RegisterFail)

    def handle_public_key(self, client_id: bytes, payload: bytes):
        """handle public key request (826)"""
        logger.info(f"processing public key for client {client_id}...")
        try:
            if len(payload) != (Database.PUBLIC_KEY_LEN+Database.NAME_LEN):
                logger.warning(f"invalid payload length: {len(payload)}")
                self._send_response(ResponseCode.GeneralError)
                return

            name_bytes = payload[:Database.NAME_LEN]
            name = name_bytes.split(b'\0',1)[0].decode('ascii')
            public_key_bytes = payload[Database.NAME_LEN:Database.PUBLIC_KEY_LEN+Database.NAME_LEN]

            # generate aes key
            aes_key = CryptoManager.generate_aes_key()

            # save in DB
            if not self.db.update_client_key(client_id, public_key_bytes, aes_key):
                logger.error(f"failed to update '{name}' keys")
                self._send_response(ResponseCode.GeneralError)
                return
            # encrypted aes key
            encrypted_aes_key = CryptoManager.encrypt_aes_key(public_key_bytes, aes_key)
            if not encrypted_aes_key:
                self._send_response(ResponseCode.GeneralError)
                return

            # send response
            res_payload = client_id + encrypted_aes_key
            self._send_response(ResponseCode.PubKeyReceived, res_payload)
            logger.info(f"successfully received public key for client {client_id}")

        except UnicodeDecodeError:
            logger.error("failed to decode client name")
            self._send_response(ResponseCode.GeneralError)
        except Exception as e: # noqa: BLE001
            logger.error(f"error handling public key request for client {client_id}: {e}")
            self._send_response(ResponseCode.GeneralError)

    def handle_reconnect(self, client_id: bytes, payload: bytes):
        """handle reconnect request (827)"""
        logger.info(f"client {client_id} reconnecting...")
        try:
            if len(payload) != Database.NAME_LEN:
                logger.warning(f"invalid payload length: {len(payload)}")
                self._send_response(ResponseCode.GeneralError)
                return

            name = payload.split(b'\0',1)[0].decode('ascii')

            # check if the client exist
            public_key_bytes = self.db.get_client_public_key(client_id)
            if not public_key_bytes:
                logger.warning(f"client {client_id} not found or missing public key")
                self._send_response(ResponseCode.ReconnectReject,client_id)
                return
            # generate aes key
            aes_key = CryptoManager.generate_aes_key()
            self.db.update_client_key(client_id, public_key_bytes, aes_key)
            self.db.update_client_last_seen(client_id)

            # encrypted aes key
            encrypted_aes_key = CryptoManager.encrypt_aes_key(public_key_bytes, aes_key)
            if not encrypted_aes_key:
                self._send_response(ResponseCode.GeneralError)
                return

            # send response
            res_payload = client_id + encrypted_aes_key
            self._send_response(ResponseCode.ReconnectAccept,res_payload)
            logger.info(f"successfully reconnected to client {name}")
        except UnicodeDecodeError:
            logger.error("failed to decode client name in reconnect")
            self._send_response(ResponseCode.GeneralError)
        except Exception as e: # noqa: BLE001
            logger.error(f"failed to reconnect to client {client_id}: {e}")
            self._send_response(ResponseCode.GeneralError)

    def handle_send_file(self, client_id: bytes, payload: bytes):
        """handle transfer file request (828)"""
        handled_payload = FileManager.get_file_payload(payload)
        if not handled_payload:
            self._send_response(ResponseCode.GeneralError)
            return
        _content_size, packet_num, total_packets, file_name, encrypted_data = handled_payload

        try:
            file_path = FileManager.save_chunk(client_id, file_name,packet_num, encrypted_data)
            logger.info(f"packet {packet_num}/{total_packets} for file {file_name} saved")

            if packet_num == total_packets:
                logger.info(f"all packets for file {file_name} saved")

                encrypted_size, crc = FileManager.process_file(client_id, file_name, file_path, self.db)

                res_payload = struct.pack(protocol.RES_FILE_HEADER_FORMAT,client_id, encrypted_size,file_name.encode('ascii'), crc)
                self._send_response(ResponseCode.FileOK,res_payload)
                logger.info(f"file {file_name} successfully transferred")
        except Exception as e: # noqa: BLE001
            logger.error(f"failed to transfer file {file_name}: {e}")
            self._send_response(ResponseCode.GeneralError)

    def handle_crc_ok(self, client_id: bytes, payload: bytes):
        """handle CRC ok massage (900)"""
        if len(payload) < Database.NAME_LEN:
            logger.warning(f"invalid payload length for CRC OK: {len(payload)}")
            self._send_response(ResponseCode.GeneralError)
            return

        file_name = payload[:Database.NAME_LEN].split(b'\0',1)[0].decode('ascii')
        file_name = os.path.basename(file_name)
        logger.info(f"client {client_id.hex()} confirmed CRC for file {file_name}")

        self.db.update_file_verified(client_id, file_name)

        self._send_response(ResponseCode.MessageACK,client_id)

    def handle_crc_abort(self, client_id: bytes, payload: bytes):
        """handle CRC abort message (902)"""
        if len(payload) < Database.NAME_LEN:
            logger.warning(f"invalid payload length for CRC ABORT: {len(payload)}")
            self._send_response(ResponseCode.GeneralError)
            return

        file_name = payload[:Database.NAME_LEN].split(b'\0',1)[0].decode('ascii')
        file_name = os.path.basename(file_name)
        logger.info(f"client {client_id.hex()} aborted transfer file {file_name}")

        self._send_response(ResponseCode.MessageACK,client_id)

