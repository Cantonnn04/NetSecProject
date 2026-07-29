import socket
import threading

HOST = "127.0.0.1"
PORT = 5555

clients = {}  
clients_lock = threading.Lock()


def handle_client(conn, addr):
    display_name = conn.recv(1024).decode().strip()
    with clients_lock:
        clients[display_name] = conn
    print(f"{display_name} connected from {addr}")
    while True:
        data = conn.recv(1024)
        if not data:
            break
        text = data.decode().strip()
        #list command
        if text == "list":
            with clients_lock:
                names = ", ".join(clients.keys())
            conn.sendall(names.encode())
        #msg command
        elif text.startswith("msg "):
            _, target, message = text.split(" ", 2)
            with clients_lock:
                target_conn = clients.get(target)
            if target_conn:
                target_conn.sendall(f"{display_name}: {message}".encode())


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server listening on {HOST}:{PORT}")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
