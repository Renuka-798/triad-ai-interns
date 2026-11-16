
import socket
import ssl
import certifi

hosts = [
    "ac-4qwunxf-shard-00-00.rp8rfho.mongodb.net",
    "ac-4qwunxf-shard-00-01.rp8rfho.mongodb.net",
    "ac-4qwunxf-shard-00-02.rp8rfho.mongodb.net"
]

context = ssl.create_default_context(cafile=certifi.where())

for host in hosts:
    print("\nTesting:", host)

    try:
        with socket.create_connection((host, 27017), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as secure_sock:
                print("TLS handshake: SUCCESS")
                print("TLS version:", secure_sock.version())
                print("Cipher:", secure_sock.cipher())

    except Exception as error:
        print("TLS handshake: FAILED")
        print("Error:", error)
