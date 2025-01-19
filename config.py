from cryptography.fernet import Fernet
from dotenv import load_dotenv

from src.services.config import AppConfig, EncryptedEnvironment


# Пример использования:
if __name__ == "__main__":
    print("1. generate key")
    print("2. generate encrypted env")
    print("3. show decrypted env by name")
    print("4. show decrypted target envs by name")
    
    input_choice = input("choice: ")
    
    match input_choice:
        case "1":
            print("generate key")
        
            # Генерация ключа шифрования (один раз, сохраните этот ключ!)
            encryption_key = Fernet.generate_key()
            print("Сохраните этот ключ:", encryption_key.decode())
        case "2":
            print("generate encrypted env")
            encryption_key = input("your-secret-key-here: ")
            env_manager = EncryptedEnvironment(encryption_key)
            
            value = input("your-secret-value-here: ")
            print(env_manager.encrypt_value(value))
            
        case "3":
            print("decrypt env")
            encryption_key = input("your-secret-key-here: ")
            env_manager = EncryptedEnvironment(encryption_key)
            
            value = input("your-secret-encrypted-value-here: ")
            print(env_manager.decrypt_value(value))
            
        case "4":
            print("decrypt target envs")        

            config = AppConfig();

            # Получаем и расшифровываем значение переменной
            try:
                # ENCRYPTED_TH_API_HASH
                print(f"Значение переменной: \nENCRYPTED_TG_API_ID: {config.tg_api_id}\nENCRYPTED_TG_API_HASH: {config.tg_api_hash}")
            except KeyError as e:
                print(e)
