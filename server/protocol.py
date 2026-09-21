import struct
from enum import IntEnum


class RequestCode(IntEnum):
    Register = 825
    SendPublicKey = 826
    Reconnect = 827
    SendFile = 828
    CRCOK = 900
    CRCBadResend = 901
    CRCBadDone = 902

class ResponseCode(IntEnum):
    RegisterSuccess = 1600
    RegisterFail = 1601
    PubKeyReceived = 1602
    FileOK = 1603
    MessageACK = 1604
    ReconnectAccept = 1605
    ReconnectReject = 1606
    GeneralError = 1607

# --------------constant--------------
CHUNK_SIZE = 4096
VERSION = 3
MAX_PAYLOAD_SIZE = 50 * 1024 * 1024
REQUEST_HEADER_FORMAT = '<16s B H I'
REQUEST_HEADER_SIZE = struct.calcsize(REQUEST_HEADER_FORMAT)
RESPONSE_HEADER_FORMAT = '< B H I'
RESPONSE_HEADER_SIZE = struct.calcsize(RESPONSE_HEADER_FORMAT)

REQ_FILE_HEADER_FORMAT = '<I I H H 255s'
REQ_FILE_HEADER_SIZE = struct.calcsize(REQ_FILE_HEADER_FORMAT)
RES_FILE_HEADER_FORMAT = '<16s I 255s I'
