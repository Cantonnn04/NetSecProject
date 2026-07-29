import time
import json
import re
import uuid
import getpass
from datetime import datetime, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import socket
import threading
from cryptography.fernet import Fernet

USERS_FILE = "users.json"
SHADOWS_FILE = "shadows.txt"
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5555

ph = PasswordHasher()

with open("secret.key", "rb") as f:
    fernet = Fernet(f.read())

#Function to load users
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

#Function to save users
def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def main():
    print("1. Login")
    print("2. Register")

    choice = input("Choose an option (1 or 2): ")

    if choice == "1": #Login
        accountTries = 0 #Used for account lockout
        #General anti-bruteforce
        tries = 0
        while True:
            tries += 1
            if tries > 3:
                with open("log.txt", "a") as f:
                    f.write(f"Bruteforce attack stopped at {datetime.now(timezone.utc).isoformat()}, IP: {socket.gethostbyname(socket.gethostname())}\n")
                print("Too many failed attempts. Exiting.")
                break
            #Inputs for username
            Username = input("Username: ")
            Password = getpass.getpass("Password: ")
            #Loads shadows.txt
            shadows = {}
            try:
                with open(SHADOWS_FILE, "r") as f:
                    for line in f:
                        shadow_username, hashed_password = line.strip().split(":", 1)
                        shadows[shadow_username] = hashed_password
            except FileNotFoundError:
                pass
            #Checks if username is in shadows.txt
            if Username not in shadows:
                with open("log.txt", "a") as f:
                    f.write(f"Log on attempt for non-existent username at {datetime.now(timezone.utc).isoformat()}, IP: {socket.gethostbyname(socket.gethostname())}\n")
                time.sleep(5) #Brute force mitigation
                print("Invalid username or password.")
                continue
            #Checks if account is disabled
            users = load_users()
            if any(user["username"] == Username and user.get("disabled") for user in users):
                with open("log.txt", "a") as f:
                    f.write(f"Disabled account logon attempt for: {Username} at {datetime.now(timezone.utc).isoformat()}, IP: {socket.gethostbyname(socket.gethostname())}\n")
                print("Account locked. Please contact administrator.")
                break
            #Checks if password is correct
            try:
                ph.verify(shadows[Username], Password)
            except VerifyMismatchError:
                accountTries += 1
                if accountTries >= 3:
                    #Marks user as disabled
                    users = load_users()
                    for user in users:
                        if user["username"] == Username:
                            user["disabled"] = True
                            break
                    save_users(users)
                    with open("log.txt", "a") as f:
                        f.write(f"Account locked for: {Username} at {datetime.now(timezone.utc).isoformat()}, IP: {socket.gethostbyname(socket.gethostname())}\n")
                    print("Too many failed attempts. Account locked. Please contact administrator.")
                    break
                time.sleep(5)
                with open("log.txt", "a") as f:
                    f.write(f"Login attempt for: {Username} at {datetime.now(timezone.utc).isoformat()}, IP: {socket.gethostbyname(socket.gethostname())}\n")
                print("Invalid username or password.")
                continue

            #Once password check is done, updates last login time
            users = load_users()
            for user in users:
                if user["username"] == Username:
                    user["last_login"] = datetime.now(timezone.utc).isoformat()
                    break
            save_users(users)
            with open("log.txt", "a") as f:
                f.write(f"Account logged in: {Username} at {datetime.now(timezone.utc).isoformat()}, IP: {socket.gethostbyname(socket.gethostname())}\n")

            print("Login successful!")
            #Connect to the server
            Display_Name = next((user["display_name"] for user in users if user["username"] == Username), Username)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((SERVER_HOST, SERVER_PORT))
                sock.sendall(fernet.encrypt(Display_Name.encode()))
                print(f"Connected to chat server as {Display_Name}.")
                print(f"List of commands:\nlogout\nlist\nmsg <username> <message>\n------------------------")

                #Thread to print anything the server sends (list replies, incoming messages)
                def receive():
                    while True:
                        data = sock.recv(1024)
                        if not data:
                            break
                        print(fernet.decrypt(data).decode())
                threading.Thread(target=receive, daemon=True).start()

                #Loop for commands the user will send
                while True:
                    command = input()
                    if command == "logout":
                        break
                    sock.sendall(fernet.encrypt(command.encode()))
                sock.close()
                print("You have successfully logged out.")
            except ConnectionRefusedError:
                print("Could not connect to server, make sure server.py is running.")

            break




    elif choice == "2": #Register
        Username = input("Choose a username: ")

        while True:
            Password = getpass.getpass("Choose a password: ")
            #Checking password requirements
            if (len(Password) >= 14
                    and re.search(r"[A-Z]", Password)
                    and re.search(r"[0-9]", Password)
                    and re.search(r"[^A-Za-z0-9]", Password)):
                break
            print("Password must be at least 14 characters, include an uppercase letter, number, and a special character.")

        Display_Name = input("Choose a display name: ") #This is not used for login

        #Load users.json
        users = load_users()
        #Username check
        if any(user["username"] == Username for user in users):
                    print("That username is already taken.")
        #Displayname check
        elif any(user["display_name"] == Display_Name for user in users):
                    print("That display name is already taken.")
        else:
            #Creating array for user
            new_user = {
                "username": Username,
                "user_id": str(uuid.uuid4()), #This library *should* make a unique ID
                "display_name": Display_Name,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_login": datetime.now(timezone.utc).isoformat(), #Leaving this empty might break it so I just set it too created_at time just in case
            }

            #Appends the array to the json file then saves it.
            users.append(new_user)
            save_users(users)

            with open(SHADOWS_FILE, "a") as f: #Opens shadows.txt
                f.write(f"{Username}:{ph.hash(Password)}\n") #apprends username, then the hashed password using Argon2 (which also hashes)
            with open("log.txt", "a") as f:
                f.write(f"Account created: {Username} at {datetime.now(timezone.utc).isoformat()}, IP: {socket.gethostbyname(socket.gethostname())}\n")
            print("Account created successfully.")
    else:
        print("Invalid option.")

if __name__ == "__main__":
    main()