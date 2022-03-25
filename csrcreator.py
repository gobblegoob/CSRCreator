'''
    Generate CSRs for a series of hosts

    1. Open Excel File and create list of hostnames that require CSRs
    2. Create a Dir for each host
    3. Create CSR's and keys, populate each respective dir.

'''
from OpenSSL import crypto
import os, datetime
import colorama
from colorama import Fore, Back, Style
import json


colorama.init(autoreset=True)
now = datetime.datetime.now()
d = now.date()

# sna_hosts = ['testhost.batcave.com']

sna_hosts = [
    'smc-01.host.com',
    'smc-02.host.com',
    'fs-01.host.com',
    'fs-02.host.com',
    'fc-01.host.com',
    'fc-02.host.com',
    'db-01.host.com',
    'db-02.host.com'
]

csr_data = {
    'key': 4096,
    'o': 'Some Organization',
    'ou': 'IT',
    'l': 'Springfield',
    'st': 'Massachusetts',
    'c': 'US',
    'cn': ''
}

# A list of dictionaries containing csr and key file and path information
CERT_LIST = []

# csr key
key = crypto.PKey()

homedir = os.getcwd()


def create_dir(name):
    try:
        print(f'{Fore.GREEN}{Style.BRIGHT} Creating directory {name}')
        os.mkdir(name)
    except FileExistsError:
        print(f'{Fore.RED}{Style.BRIGHT}Directory {name} already exists')
        return
    except Exception as e:
        print(f'Error creating {name}! \n {e}')
        quit()


def generatekey(keypath):
    if os.path.exists(keypath):
        print(f"{Fore.RED}{Style.BRIGHT} ** Certificate file exists, aborting ** ")
        print(keypath)
    # else write the key file
    else:
        print(f"{Fore.BLUE} \n\n- Generating key file...\n\n")
        key.generate_key(crypto.TYPE_RSA, 4096)
        f = open(keypath, "w")

        keydump = crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
        kd = keydump.decode('UTF-8')
        f.write(kd)
        f.close()
        print(f'{Fore.GREEN}{Style.BRIGHT} - Keyfile Generated! {Fore.CYAN}{keypath}')

def create_csr(csrpath):
    req = crypto.X509Req()
    req.get_subject().CN = csr_data['cn']
    req.get_subject().C = csr_data['c']
    req.get_subject().ST = csr_data['st']
    req.get_subject().L = csr_data['l']
    req.get_subject().O = csr_data['o']
    req.get_subject().OU = csr_data['ou']
    req.set_pubkey(key)
    req.sign(key, "sha256")

    if os.path.exists(csrpath):
        print(f"{Fore.RED}{Style.BRIGHT} - Certificate File Exists. Aborting.")
        print(csrpath)
        return
    else:
        f = open(csrpath, "w")
        csrdump = crypto.dump_certificate_request(crypto.FILETYPE_PEM, req)
        # csrdump is a byte string with with characters that will corrupt the cert file.
        # Decode to UTF-8 to strip out characters.
        # The byte string must also be inlcuded in teh CERT_LIST dictionary
        # to be passed to certout.py so a pkcs12 can be created.
        cd = csrdump.decode('UTF-8')
        f.write(cd)
        f.close()
        print(f"CSR Created: {csrpath}")
    return


def csr_hosts():
    '''
    For each host that needs a csr, this will manage all functions to create the 
    directory structure and call all functions to create the csr's.
    '''
    for sna_host in sna_hosts:
        csr_data['cn'] = sna_host
        
        # create new dir
        os.chdir(homedir)
        print(os.getcwd())
        create_dir(sna_host)
        os.chdir(sna_host)
        keypath = os.getcwd() + '\\' + sna_host + '_' + str(d) + '.key'
        print(f'Keypath is: {keypath}')

        # Generate Key
        generatekey(keypath)

        # Create CSR
        csrpath = os.getcwd() + '\\' + sna_host + '_' + str(d) + '.csr'
        create_csr(csrpath)
        CERT_LIST.append({'hostname': sna_host, 'keyfile': keypath, 'csrfile': csrpath})
    return


if __name__ == '__main__':
    print(f'{Fore.BLUE}{Style.BRIGHT}=-=' * 45)
    print(f'{Fore.BLUE}{Style.BRIGHT}=-=' * 45)

    # Execute CSR Creation tasks
    csr_hosts()

    print('CSR\'s created! \nLets grab a \xf0\x9f\x8d\x95!')
    print(f'{Fore.BLUE}{Style.BRIGHT}=-=' * 45)
    print(f'{Fore.BLUE}{Style.BRIGHT}=-=' * 45)

    # Print everything ou just did!
    print('~!~!' * 30 )
    print(f'{Back.BLACK}{Fore.BLUE}{Style.BRIGHT}\nThe following CSRs and Keys were created:')
    print(json.dumps(CERT_LIST, sort_keys = False, indent = 4))
    print('~!~!' * 30 )