from cryptography.fernet import Fernet

if __name__ == "__main__":
    try:
        with open("secret.key", "xb") as f:
            f.write(Fernet.generate_key())
        print(f"Key Generated")
    except Exception as e:
        print(f"Key not generated")

with open("secret.key", "rb") as f:
    fernet = Fernet(f.read())

for filename in ["users.json", "shadows.txt"]:
    with open(filename, "rb") as f:
        data = f.read()
    with open(filename, "wb") as f:
        f.write(fernet.encrypt(data))
