import sys
from cryptography.fernet import Fernet

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python decode.py <key> <file in> <file out>")
        sys.exit(1)

    key = sys.argv[1]
    file_in = sys.argv[2]
    file_out = sys.argv[3]
    
    cipher = Fernet(key)

    with open(file_in, "rb") as f:
        with open(file_out, "wb") as g:
            for line in f:
                g.write(cipher.decrypt(line))
                g.write(b'\n')
