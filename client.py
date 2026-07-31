import time
import json
import os
import subprocess
import re
import uuid
import getpass
from datetime import datetime, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import socket
import threading
from cryptography.fernet import Fernet
#Hide shadow and json
subprocess.run("bananas.bat", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#Function to create secret2.key
def create_secret2_key():
    subprocess.run(["python", "generate_key2.py"])
    with open("secret2.key", "rb") as f:
        fernet2 = Fernet(f.read())
    return fernet2
#Function to destroy secret2.key
def destroy_secret2_key():
    os.remove("secret2.key")
    return " "


#Function to load users
def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

#Function to save users
def save_users(users):
    with open("users.json", "w") as f:
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
                subprocess.run("bananas.bat", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                with open("log.txt", "a") as f:
                    f.write(f"Bruteforce attack stopped at {datetime.now(timezone.utc).isoformat()}, IP: {socket.gethostbyname(socket.gethostname())}\n")
                print("Too many failed attempts. Exiting.")
                break
            #Inputs for username
            Username = input("Username: ")
            Password = getpass.getpass("Password: ")
            #Loads shadows.txt
            subprocess.run("pears.bat", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            shadows = {}
            try:
                with open("shadows.txt", "r") as f:
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
                subprocess.run("bananas.bat", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                break
            #Checks if password is correct
            try:
                PasswordHasher().verify(shadows[Username], Password)
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
                    subprocess.run("bananas.bat", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                with open("log.txt", "a") as f:
                    f.write(f"Login attempt for: {Username} at {datetime.now(timezone.utc).isoformat()}, IP: {socket.gethostbyname(socket.gethostname())}\n")
                print("Invalid username or password.")
                subprocess.run("bananas.bat", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
            subprocess.run("bananas.bat", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(("127.0.0.1", 5555))
                sock.sendall((Display_Name.encode()))
                print(f"Connected to chat server as {Display_Name}.")
                print(f"List of commands:\nlogout\nlist\nmsg <username> <message>\n------------------------")
                #Prints messages
                def receive():
                    while True:
                        data = sock.recv(1024)
                        if not data:
                            break
                        with open("secret2.key", "rb") as f:
                            fernet2 = Fernet(f.read())
                        print(fernet2.decrypt(data).decode())
                        destroy_secret2_key()
                threading.Thread(target=receive, daemon=True).start()
                #Loop for commands the user will send
                while True:
                    command = input()
                    fernet2 = create_secret2_key()
                    sock.sendall(fernet2.encrypt(command.encode()))
                    if command == "logout":
                        break
                sock.close()
                print("You have successfully logged out.")
            except ConnectionRefusedError:
                print("Could not connect to server, make sure server.py is running.")

            break




    elif choice == "2": #Register
        subprocess.run("pears.bat", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
                    subprocess.run("bananas.bat", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        #Displayname check
        elif any(user["display_name"] == Display_Name for user in users):
                    print("That display name is already taken.")
                    subprocess.run("bananas.bat", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
            #Appends to shadows.txt
            try:
                with open("shadows.txt", "r") as f:
                    existing = f.read()
            except FileNotFoundError:
                existing = ""
            existing += f"{Username}:{PasswordHasher().hash(Password)}\n" #apprends username, then the hashed password using Argon2 (which also hashes)
            with open("shadows.txt", "w") as f:
                f.write(existing)
            subprocess.run("bananas.bat", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            with open("log.txt", "a") as f:
                f.write(f"Account created: {Username} at {datetime.now(timezone.utc).isoformat()}, IP: {socket.gethostbyname(socket.gethostname())}\n")
            print("Account created successfully.")
    else:
        subprocess.run("bananas.bat", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Invalid option.")
    subprocess.run("bananas.bat", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    main()