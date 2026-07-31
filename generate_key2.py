from cryptography.fernet import Fernet

if __name__ == "__main__":
    try:
        with open("secret2.key", "xb") as f:
            f.write(Fernet.generate_key())
    except Exception as e:
        pass
