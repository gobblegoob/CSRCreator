'''
    Find all signed certificate files and output a pks12
'''

from click import open_file
import datetime
from OpenSSL.crypto import (
    dump_certificate, 
    FILETYPE_PEM,
    PKCS12,
    load_certificate,
    load_privatekey
)
import os

now = datetime.datetime.now()
d = now.date()

HOME_DIR = os.getcwd()

CERT_LIST = [    
    {
        "hostname": "testhost.batcave.com",
        "keyfile": "C:\\Users\\gamunson\\Documents\\PythonProjects\\testhost.batcave.com\\testhost.batcave.com_2022-03-21.key",
        "csrfile": "C:\\Users\\gamunson\\Documents\\PythonProjects\\testhost.batcave.com\\testhost.batcave.com_2022-03-21.csr"
    }
]


def generate_pkcs12(host, cert_pem, pkey):
    '''
    cert_pem: signed pem file from CA
    pkey: private key file from csr

    This command will take the key and the signed cert and output a pkcs12 file that can be imported

    Returns a class pkcs12_bin.  How do i get that into a file i can import?
    '''
    try:
        p12 = PKCS12()
        friendly_name = host + '.pfx'
        pem_bytes= file_bytes(cert_pem)
        pkey_bytes = file_bytes(pkey)
        p12.set_certificate(load_certificate(FILETYPE_PEM, pem_bytes))
        p12.set_privatekey(load_privatekey(FILETYPE_PEM, pkey_bytes))

        passphrase = b'password123'

        pkcs12_bin = p12.export(passphrase=passphrase)

        return pkcs12_bin

    except Exception as e:
        print('-' * 50)
        print(f'Error Creating pfx file {friendly_name}')
        print(e)
        print('-' * 50)


def write_pks12(pfx_name, pfx):
    try:
        # Successfully tested with a Base 64 cert.  
        # Need to test with a DER
        with open(pfx_name, 'wb') as pfxfile:
            pfxfile.write(pfx)
    except Exception as e:
        print(f'Error writing pfx file {pfx_name}')
        print(e)

def file_bytes(input):
    '''
    PKCS12() file input requires the contents to be formatted as bytes. Take the input parameter, open the file an output a 
    bitstream of the contents.
    '''
    try: 
        f = open(input, 'r', encoding='utf-8', errors="surrogateescape")
        file_bytes = f.read()
        f.close()
        return file_bytes
    except:
        file_bytes_utf8(input)


def file_bytes_utf8(input):
    try:
        f = open(input, 'r', encoding='utf-8', errors="surrogateescape")
        file_bytes = f.read()
        f.close()
        fb_encoded = file_bytes.encode(encoding='UTF-8')
        return fb_encoded
    except Exception as e:
        print(f'Error reading file {input}')
        print(e)
        quit()


def validate_certfiles():
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
        print('We are missing a certificate or key')
        print(f'Cert Present: {hascert}\nKey present: {haskey}')
        return False


def get_filename(path):
    l = path.split('\\')
    len = l.__len__()
    return l[len-1]


def get_certfilename():
    files = os.listdir()
    for f in files:
        if f[-4:] == '.cer':
            return f
    
def set_pfx_name(host):
    pfx_name = host + '_' + str(d) + '.pfx'
    return pfx_name

def decrypt_certs(CERT_LIST):
    pkey = CERT_LIST[0]["keyfile"]
    csr = CERT_LIST[0]["csrfile"] # Not needed, since certs should be signed.
    host = CERT_LIST[0]["hostname"]

    os.chdir(HOME_DIR)
    os.chdir(host)
    print(os.getcwd())
    
    if validate_certfiles() == True:
        pfx_name = set_pfx_name(host)
        pk = get_filename(pkey)
        cert = get_certfilename()
        #print(pk, cert)
        pfx = generate_pkcs12(host, cert, pk)
        write_pks12(pfx_name, pfx)


    os.chdir('..')
    return

decrypt_certs(CERT_LIST)