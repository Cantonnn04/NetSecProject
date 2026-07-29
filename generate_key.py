from cryptography.fernet import Fernet

if __name__ == "__main__":
    try:
        with open("secret.key", "xb") as f:
            f.write(Fernet.generate_key())
        print(f"Key Generated")
    except Exception as e:
        print(f"Key not generated")