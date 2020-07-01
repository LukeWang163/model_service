import argparse

from CryptoAPI import CryptoAPI


class SccTool:
    api = CryptoAPI()
    APP_XXX_DOMAIN_ID = 4
    APP_SHARED_DOMAIN_ID = 5

    exampleCfgFile = "/home/mind/sec/scc.conf"

    api.initialize(exampleCfgFile)

    maxKeyID = api.getMaxMkID(APP_XXX_DOMAIN_ID)
    if maxKeyID == 0:
        api.activeNewKey(APP_XXX_DOMAIN_ID)


    @classmethod
    def encrypt(cls, plain):
        return cls.api.encrypt(plain)

    @classmethod
    def decrypt(cls, cipher):
        return cls.api.decrypt(cipher)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='scc tool arg parser')
    parser.add_argument('--file', action="store", default="/etc/nginx/keys/ssl_key", type=str)
    args = parser.parse_args()

    file_path = args.file

    with open(file_path, "r") as f:
        encrypted_text = f.read()

        print(SccTool.decrypt(encrypted_text))
