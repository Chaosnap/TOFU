#!/usr/bin/python

from Crypto.Cipher import AES


def outputAES(key, txt):
    print("-------------------------")
    print("key:        %s" % key)
    print("plaintext:  %s" % txt)
    cipher = AES.new(bytes.fromhex(key), AES.MODE_ECB)
    output = str(cipher.encrypt(bytes.fromhex(txt)).hex())
    print("ciphertext: %s" % output)
    return output


key = "00000000000000000000000000000000"
plaintext = "00000000000000000000000000000000"
result = "66e94bd4ef8a2c3b884cfa59ca342b2e"
ciphertext = outputAES(key, plaintext)
assert ciphertext == result, "Error Ciphertext output is wrong, correct ciphertext is: %s" % result

plaintext = "3243f6a8885a308d313198a2e0370734"
key = "2b7e151628aed2a6abf7158809cf4f3c"
result = "3925841d02dc09fbdc118597196a0b32"
ciphertext = outputAES(key, plaintext)
assert ciphertext == result, "Error Ciphertext output is wrong, correct ciphertext is: %s" % result

key = "6465666768696a6b6c6d6e6f70717273"
plaintext = "6D6BBC9C37845506835BB8050585D23F"
result = "07213ebf1c88789ecd949252ea6b7528"
ciphertext = outputAES(key, plaintext)
assert ciphertext == result, "Error Ciphertext output is wrong, correct ciphertext is: %s" % result
