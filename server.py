import socket
import threading
from cryptography.fernet import Fernet
from datetime import datetime, timezone
import subprocess

#Killing anython on port 5555 because the server doesn't close itself lol
import subprocess

cmd = r"""netstat -ano | Select-String ':5555\s' | Where-Object { $_ -match 'LISTENING' } | ForEach-Object { Stop-Process -Id ($_.Line.Trim() -split '\s+')[-1] -Force }"""

result = subprocess.run(
    ["powershell", "-NoProfile", "-Command", cmd],
)

HOST = "127.0.0.1"
PORT = 5555

with open("secret.key", "rb") as f:
    fernet = Fernet(f.read())

clients = {}
clients_lock = threading.Lock()


def handle_client(conn, addr):
    display_name = fernet.decrypt(conn.recv(1024)).decode().strip()
    with clients_lock:
        if display_name in clients:
            conn.sendall(fernet.encrypt(b"User already connected to server."))
            conn.close()
            return
        clients[display_name] = conn
    print(f"{display_name} connected from {addr}")
    while True:
        data = conn.recv(1024)
        if not data:
            break
        text = fernet.decrypt(data).decode().strip()
        #list command
        if text == "list":
            with clients_lock:
                names = ", ".join(clients.keys())
            conn.sendall(fernet.encrypt(names.encode()))
        #msg command
        elif text.startswith("msg "):
            _, target, message = text.split(" ", 2)
            with clients_lock:
                target_conn = clients.get(target)
            if target_conn:
                #print("Test2")
                target_conn.sendall(fernet.encrypt(f"{display_name}: {message}".encode()))
                with open("log.txt", "a") as f:
                    f.write(f"User {target} received a message from user {display_name} at {datetime.now(timezone.utc).isoformat()}\n")
                    #f.write("Test\n")
                    #print("Test")
        #Removes user from server
        elif text == "logout":
            del clients[display_name]
            print(f"{display_name} disconnected from {addr}")


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
