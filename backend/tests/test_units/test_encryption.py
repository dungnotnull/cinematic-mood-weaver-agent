"""Tests for AES-256-GCM encryption utilities."""

import pytest
from cinematic_mood_weaver.utils.encryption import decrypt_text, encrypt_text, get_cipher


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        key = "test-encryption-key-12345"
        original = "sensitive emotion data"
        token = encrypt_text(original, key)
        decrypted = decrypt_text(token, key)
        assert decrypted == original
        assert token != original  # Should be different (encrypted)

    def test_different_keys_fail(self):
        original = "hello world"
        token = encrypt_text(original, "key-a")
        with pytest.raises(Exception):
            decrypt_text(token, "key-b")

    def test_get_cipher_generates_valid_key(self):
        cipher = get_cipher("any-key")
        token = cipher.encrypt(b"test data")
        decrypted = cipher.decrypt(token)
        assert decrypted == b"test data"
