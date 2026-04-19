from cryptography.fernet import Fernet

# Generate a new Fernet encryption key
key = Fernet.generate_key()
print("Your Encryption Key:")
print(key.decode())
print("\nIMPORTANT: Save this key securely - it cannot be recovered if lost!")
