from cryptography.fernet import Fernet, InvalidToken, MultiFernet


class CryptographyProvider:
    def __init__(self, fernet_key_list: list[str], encryption_ttl: int = 3600) -> None:
        self.encryptor = MultiFernet(
            (Fernet(key.encode("utf-8")) for key in fernet_key_list)
        )
        self.encryption_ttl: int = encryption_ttl

    def encrypt(self, data: str) -> str:
        return self.encryptor.encrypt(msg=data.encode("utf-8")).decode("utf-8")

    def decrypt(self, encrypted_data: bytes | str, ttl: int = 0) -> str | None:
        encryption_ttl: int = self.encryption_ttl if ttl == 0 else ttl
        try:
            return self.encryptor.decrypt(encrypted_data, ttl=encryption_ttl).decode(
                "utf-8"
            )
        except InvalidToken:
            return None
