
import logging
import socket
from database import Database
from client_handler import ClientHandler

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
                    logging.info(f"setting port to '{port_int}'")
                    return port_int
                else:
                    logging.warning(f"'{port_int}' is not a valid port, setting port to '{self.DEFAULT_PORT}'")
                    return self.DEFAULT_PORT
        except FileNotFoundError:
            logging.warning(f"'{self.PORT_INFO_FILE}' does not exist, setting port to default port '{self.DEFAULT_PORT}'")
            return self.DEFAULT_PORT
        except ValueError:
            logging.warning(f"invalid content in '{self.PORT_INFO_FILE}', setting port to '{self.DEFAULT_PORT}'")
            return self.DEFAULT_PORT
        except Exception as e:
            logging.warning(f"error reading '{self.PORT_INFO_FILE}': {e}, setting port to '{self.DEFAULT_PORT}'")
            return self.DEFAULT_PORT
    def start(self):
        """starts the server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('', self.port))
            server_socket.listen()
            logging.info(f"server starting and listening on port {self.port}")

            while True:
                conn, addr = server_socket.accept()
                handler = ClientHandler(conn, addr, self.db)
                handler.start()
        except KeyboardInterrupt:
            logging.info("server stopped")
        except Exception as e:
            logging.critical(f"error starting server: {e}")
        finally:
            server_socket.close()


# ----------------main-------------------
if __name__ == '__main__':
    try:
        server = Server()
        server.start()
    except KeyboardInterrupt:
        logging.info("server stopped")
    except Exception as e:
        logging.critical(f"error starting server: {e}")
