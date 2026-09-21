
import logging

logger = logging.getLogger(__name__)
import socket

from client_handler import ClientHandler
from database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class Server:
    """main server class responsible for configuring up the server"""
    # --------------constant--------------
    PORT_INFO_FILE = 'port.info'
    DEFAULT_PORT = 1369
    MIN_PORT = 0
    MAX_PORT = 65535


    def __init__(self):
        self.port = self._load_port()
        self.db = Database()

    def _load_port(self) -> int:
        """load port info from file or set to default port """
        try:
            with open(self.PORT_INFO_FILE, 'r') as file:
                port_str = file.read().strip()
                port_int = int(port_str)
                if self.MIN_PORT <= port_int <= self.MAX_PORT:
                    logger.info(f"setting port to '{port_int}'")
                    return port_int
                else:
                    logger.warning(f"'{port_int}' is not a valid port, setting port to '{self.DEFAULT_PORT}'")
                    return self.DEFAULT_PORT
        except FileNotFoundError:
            logger.warning(f"'{self.PORT_INFO_FILE}' does not exist, setting port to default port '{self.DEFAULT_PORT}'")
            return self.DEFAULT_PORT
        except ValueError:
            logger.warning(f"invalid content in '{self.PORT_INFO_FILE}', setting port to '{self.DEFAULT_PORT}'")
            return self.DEFAULT_PORT
        except Exception as e: # noqa: BLE001
            logger.warning(f"error reading '{self.PORT_INFO_FILE}': {e}, setting port to '{self.DEFAULT_PORT}'")
            return self.DEFAULT_PORT
    def start(self):
        """starts the server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('', self.port))
            server_socket.listen()
            logger.info(f"server starting and listening on port {self.port}")

            while True:
                try:
                    conn, addr = server_socket.accept()
                except OSError as e:
                    logger.error(f"error connecting to server: {e}")
                    continue
                try:
                    handler = ClientHandler(conn, addr, self.db)
                    handler.start()
                except RuntimeError as e:
                    logger.error(f"error starting client: {e}")
                    continue
        except KeyboardInterrupt:
            logger.info("server stopped")
        except Exception as e: # noqa: BLE001
            logger.critical(f"error starting server: {e}")
        finally:
            server_socket.close()


# ----------------main-------------------
if __name__ == '__main__':
    try:
        server = Server()
        server.start()
    except KeyboardInterrupt:
        logger.info("server stopped")
    except Exception as e: # noqa: BLE001
        logger.critical(f"error starting server: {e}")
