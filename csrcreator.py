'''
    Generate CSRs for a series of hosts

    1. Open Excel File and create list of hostnames that require CSRs
    2. Create a Dir for each host
    3. Create CSR's and keys, populate each respective dir.

'''
from OpenSSL import crypto
import os, datetime
import colorama
from colorama import Fore, Style
import json


colorama.init(autoreset=True)
now = datetime.datetime.now()
d = now.date()

class CSRCreator():

    def __init__(self):

        #Set the certificate data
        self.csr_data = {    
            'key': 4096,
            'o': 'Some Organization',
            'ou': 'IT',
            'l': 'Springfield',
            'st': 'Massachusetts',
            'c': 'US',
            'cn': ''
        }

        # Array of hostnames used to create directories and filenames
        self.HOST_LIST = [] 
        # Contains CSR hostnames and paths for CSR and keys
        self.CERT_LIST = []
        # Home directory is wherever the script lives.  Feel free to change
        self.HOMEDIR = os.getcwd() 
        self.key = crypto.PKey() 


    def set_host_list(self, host_list):
        # Takes a dictionary as input to set the host list
        # the dictionary contains a hostname for cn fields
        # and an IP address for the SAN field.
        self.HOST_LIST = host_list

    def set_cert_attributes(self, attributes):
        # Takes a dictionary containing the certificate attributes
        self.csr_data = attributes
        return

    def set_cert_data(self, csr_json):
        self.CERT_LIST = csr_json

    

    def create_dir(self, name):
        try:
            if name is not None:
                print(f'{Fore.GREEN}{Style.BRIGHT} Creating directory {name}')
                os.mkdir(name)
                return
            else:
                return
        except FileExistsError:
            print(f'{Fore.RED}{Style.BRIGHT}Directory {name} already exists')
            return
        except Exception as e:
            print(f'Error creating {name}! \n {e}')
            quit()


    def generatekey(self, keypath):
        if os.path.exists(keypath):
            print(f"{Fore.RED}{Style.BRIGHT} ** Certificate file exists, aborting ** ")
            print(keypath)
        # else write the key file
        else:
            print(f"{Fore.BLUE} \n- Generating key file...\n")
            self.key.generate_key(crypto.TYPE_RSA, 4096)
            f = open(keypath, "w")

            keydump = crypto.dump_privatekey(crypto.FILETYPE_PEM, self.key)
            kd = keydump.decode('UTF-8')
            f.write(kd)
            f.close()
            print(f'{Fore.GREEN}{Style.BRIGHT} - Keyfile Generated! {Fore.CYAN}{keypath}')

    def create_csr(self, csrpath, subjectAltName):
        req = crypto.X509Req()
        req.get_subject().CN = self.csr_data['cn']
        req.get_subject().C = self.csr_data['c']
        req.get_subject().ST = self.csr_data['st']
        req.get_subject().L = self.csr_data['l']
        req.get_subject().O = self.csr_data['o']
        req.get_subject().OU = self.csr_data['ou']

        # Set subject alternative names
        req.add_extensions([crypto.X509Extension(
            b'subjectAltName', False,
            subjectAltName.encode('ascii'))])

        req.set_pubkey(self.key)
        req.sign(self.key, "sha256")
    
        if os.path.exists(csrpath):
            print(f"{Fore.RED}{Style.BRIGHT} - Certificate File Exists. Aborting.")
            print(csrpath)
            return
        else:
            f = open(csrpath, "w")
            csrdump = crypto.dump_certificate_request(crypto.FILETYPE_PEM, req)
            # csrdump is a byte string with with characters that will corrupt the cert file.
            # Decode to UTF-8 to strip out characters.
            # The byte string must also be inlcuded in the CERT_LIST dictionary
            # to be passed to certout.py so a pkcs12 can be created.
            cd = csrdump.decode('UTF-8')
            f.write(cd)
            f.close()
            print(f"CSR Created: {csrpath}")
        return

    def cert_request(self, hostname, subjectAltName):
        # create new dir
        if hostname is not None:
            os.chdir(self.HOMEDIR)
            print(os.getcwd())
            self.create_dir(hostname)
            os.chdir(hostname)
            keypath = os.getcwd() + '/' + hostname + '_' + str(d) + '.key'
            print(f'Keypath is: {keypath}')
    
            # Generate Key
            self.generatekey(keypath)
    
            # Create CSR
            csrpath = os.getcwd() + '/' + hostname + '_' + str(d) + '.csr'
            self.create_csr(csrpath, subjectAltName)
            self.CERT_LIST.append({'hostname': hostname, 'keyfile': keypath, 'csrfile': csrpath})
        else:
            return


    def csr_hosts(self):
        '''
        For each host that needs a csr, this will manage all functions to create the 
        directory structure and call all functions to create the csr's.
        '''
        for h in self.HOST_LIST:
            # SNA Identity Certs contain CN and two SANS.
            # SAN1 contains the hostname which matches the CN
            # SAN2 is the IP address of the appliance
            self.csr_data['cn'] = h['hostname']
            san1 = h['hostname']

            if h['ip'] is not None:
                # If IP address is present in file, 
                san2 = h['ip']
                subjectAltName = f'DNS:{san1},IP:{san2}'

                self.cert_request(h['hostname'], subjectAltName)

            else:
                # If ip address field is blank, don't include second SAN
                subjectAltName = f'DNS:{san1}'
                self.cert_request(h['hostname'], subjectAltName)
                    
        return


    def output_csr_list(self):
        try:
            os.chdir(self.HOMEDIR)
            csr_json_file = 'csr_list_' + str(d) + '.json'
            csr_json_data  = json.dumps(self.CERT_LIST)
            with open(csr_json_file, 'w') as csrfile:
                csrfile.write(csr_json_data)
            return
        except Exception as e:
            print(f'Error creating CSR list json file.  Quitting. \n{e}')
            quit()


if __name__ == '__main__':
    print(f'{Fore.BLUE}{Style.BRIGHT}=-=' * 45)
    print(f'{Fore.BLUE}{Style.BRIGHT}=-=' * 45)

    # Execute CSR Creation tasks
    cc = CSRCreator()
    cc.csr_hosts()

    print('CSR\'s created! \nLets grab a \xf0\x9f\x8d\x95!')
    print(f'{Fore.BLUE}{Style.BRIGHT}=-=' * 45)
    print(f'{Fore.BLUE}{Style.BRIGHT}=-=' * 45)

    # Print everything ou just did!
    print('~!~!' * 30 )
    # print(f'{Back.BLACK}{Fore.BLUE}{Style.BRIGHT}\nThe following CSRs and Keys were created:')
    # print(json.dumps(CERT_LIST, sort_keys = False, indent = 4))
    cc.output_csr_list()
    print('~!~!' * 30 )