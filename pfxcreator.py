'''
    Find all signed certificate files and output a pks12
'''

import datetime
import os
import json
from colorama import Style, Back, Fore
from OpenSSL.crypto import (
    dump_certificate, 
    FILETYPE_PEM,
    PKCS12,
    load_certificate,
    load_privatekey
)

class PFXCreator():
    def __init__(self):
        self.HOME_DIR = os.getcwd()
        self.CERT_LIST = []
        now = datetime.datetime.now()
        self.d = now.date()



    def set_cert_list(self, certlist):
        self.CERT_LIST = certlist
        return
    

    def find_cert_list_file(self):
        # return the filename of the json file created
        files = os.listdir()
        isfound = False
    
        for f in files:
            if f[0:8] == "csr_list" and f[-4:] == 'json':
                cert_list_file = f
                isfound = True
                break
        
        if isfound == True:
            return f
        else:
            print('Source json file not found.  Whats up with that?')


    def read_cert_list_file(self, fn):
        # Get the file name and read the json structure into an 
        # array of dicts - then set to CERT_LIST.
        with open(fn, 'r') as file:
            self.CERT_LIST = json.loads(file.read())
        return self.CERT_LIST

    def generate_pkcs12(self, host, cert_pem, pkey):
        '''
        cert_pem: signed pem file from CA
        pkey: private key file from csr
    
        This command will take the key and the signed cert and output a pkcs12 file that can be imported
    
        Returns a class pkcs12_bin.
        '''
        try:
            friendly_name = host + '.pfx'
            if self.validate_base64_cert(cert_pem) == True:
                p12 = PKCS12()
                pem_bytes= self.file_bytes(cert_pem)
                pkey_bytes = self.file_bytes(pkey)
                p12.set_certificate(load_certificate(FILETYPE_PEM, pem_bytes))
                p12.set_privatekey(load_privatekey(FILETYPE_PEM, pkey_bytes))
    
                # Certificate encryption passphrase
                passphrase = b'password123'
    
                pkcs12_bin = p12.export(passphrase=passphrase)
                self.write_pks12(friendly_name, pkcs12_bin)
                return pkcs12_bin
    
            else:
                print(f'{Fore.RED}{Style.BRIGHT}Unable to create certificate {friendly_name}')
                return
    
        except Exception as e:
            print('-' * 50)
            print(f'{Fore.RED}generate_pkcs12() Error Creating pfx file {friendly_name}')
            print(e)
            print('-' * 50)
    
    
    def write_pks12(self, pfx_name, pfx):
        try:
            # Successfully tested with a Base 64 cert.  
            # Need to test with a DER
            with open(pfx_name, 'wb') as pfxfile:
                pfxfile.write(pfx)
            pfxfile.close()
            print(f'{Fore.GREEN}{Style.BRIGHT} -- Successfully Created {pfx_name}')
        except Exception as e:
            print(f'Error writing pfx file {pfx_name}')
            print(e)
    
    def file_bytes(self, input):
        '''
        PKCS12() file input requires the contents to be formatted as bytes. Take the input parameter, open the file an output a 
        bitstream of the contents.
        '''
        try: 
            f = open(input, 'r', encoding='utf-8', errors="surrogateescape")
            file_bytes = f.read()
            f.close()
            return file_bytes
        except  Exception as e:
            print(f'{Fore.RED}Error at file_bytes().  Unable to read file')
            print(e)
    
    
    
    def validate_base64_cert(self, cert):
        # Conversion to pkcs12 requires signed x509 cert in Base64!
        # Check first line of signed cert file to make sure it contains
        # The correct Base64 string will begin with -----BEGIN CERTIFICATE-----
        # Improve this check if able
        try:
            with open(cert, 'r') as certfile:
                t = certfile.read()
            b64_text = t[:27]
            if (b64_text == '-----BEGIN CERTIFICATE-----'):
                return True
            else:
                return False
        except Exception as e:
            print(f'{Fore.RED}Error validating base 64 x509 certificate')
            print(e)
    
    
    
    def validate_certfiles(self):
        # Validate that the certificate and key files are in the correct directory
        haskey = False
        hascert = False
        files = os.listdir()
        for f in files:
            if f[-4:] == '.cer':
                hascert = True
            elif f[-4:] == '.key':
                haskey = True
        
        if hascert == True and haskey == True:
            return True
        else:
            print(f'{Fore.RED}We are missing a certificate or key')
            print(f'{Fore.RED}Cert Present: {hascert}\nKey present: {haskey}')
            return False
    
    
    def get_filename(self, path):
        # Pulls the filename from a path string
        l = path.split('\\')
        len = l.__len__()
        return l[len-1]
    
    
    def get_certfilename(self):
        # Locate a .cer file in your directory and return its name
        files = os.listdir()
        for f in files:
            if f[-4:] == '.cer':
                return f
        
    def set_pfx_name(self, host):
        # Create filename for your pfx file.  Includes hostname, date, and extension .pfx
        pfx_name = host + '_' + str(self.d) + '.pfx'
        return pfx_name
    
    def decrypt_certs(self, CERT_LIST):
        pkey = CERT_LIST[0]["keyfile"]
        csr = CERT_LIST[0]["csrfile"] # Not needed, since certs should be signed.
        host = CERT_LIST[0]["hostname"]
    
        os.chdir(self.HOME_DIR)
        os.chdir(host)
        print(os.getcwd())
        
        if self.validate_certfiles() == True:
            pfx_name = self.set_pfx_name(host)
            pk = self.get_filename(pkey)
            cert = self.get_certfilename()
            #print(pk, cert)
            pfx = self.generate_pkcs12(host, cert, pk)
            self.write_pks12(pfx_name, pfx)
    
    
        os.chdir('..')
        return
    
    
    def parse_certs(self, CERT_LIST):
        # Get the list of CSR's and keys, use that info to validate 
        # that the necessary files are there and then 
        # create the pkcs12's
        if CERT_LIST is not None:
            os.chdir(self.HOME_DIR)
            i = 0
            while i < CERT_LIST.__len__():
                pkey = CERT_LIST[i]["keyfile"]
                csr = CERT_LIST[i]["csrfile"] # Not needed since we need the signed certs
                host = CERT_LIST[i]["hostname"]
      
                os.chdir(host)
                print(os.getcwd())
    
                if self.validate_certfiles() == True:
                    pfx_name = self.set_pfx_name(host)
                    pk = self.get_filename(pkey)
                    # gets a .cer file in the directory it's searching.  
                    # Will have issues if there is more than one .cer file!
                    cert = self.get_certfilename()
                    pfx = self.generate_pkcs12(host, cert, pk)
                    # write_pks12(pfx_name, pfx)
    
                os.chdir('..')
                i += 1
            return
        
        else:
            print(f'{Fore.RED}There is no certificate list.  Exiting.')
            quit()


if __name__ == '__main__':
    # do something 
    print('hello')