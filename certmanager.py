'''

This is the central hub script for user interation, cert csr creation and pkcs12
creation.

Allows you to grab a host list from a provided excel spreadsheet and create CSR's and merge certs to pkcs12 format for upload

Certificates must be signed in Base64 format.


'''

from pfxcreator import PFXCreator
from csrcreator import CSRCreator
from colorama import Fore, Style, Back
import openpyxl
import os
import json

class CertManager():

    def __init__(self):
        self.HOST_LIST = [] # List of hosts that require identity certificates
        self.CERT_LIST = [] # An array of dictionaries with directory and file info for the CSR's and key files
        self.SOURCE_XML_FILE = 'SNA Certificate Checklist.xlsx'

    def get_host_list(self, source_file):
        # XLSX checklist file.  Column A must have hostlist in it.
        wb = openpyxl.load_workbook(source_file)

        first_sheet = wb.get_sheet_names()[0]
        worksheet = wb.get_sheet_by_name(first_sheet)

        for row in range(2,worksheet.max_row+1): # first varible is the start row. 2 is to avoid the header
            host_dict = {}
            for column in "AB": # add or reduce columns - Just looking in column A
                cell_name = "{}{}".format(column, row)
                if column == 'A':
                    c = worksheet[cell_name].value
                    host_dict = {'hostname': c}
                elif column == 'B':
                    c = worksheet[cell_name].value
                    ip_dict = {'ip': c}
                    host_dict.update(ip_dict)
                    self.HOST_LIST.append(host_dict)


def script_start():
    print('\n',
    '=-' * 50,
    '=-' * 50,
    '\n')
    print(f'{Back.BLACK}{Style.BRIGHT}{Fore.CYAN}CSR Creator',
    '\n\n - Batch create CSR\'s and PKCS12 files for import.\n'
    )


def print_menu():
    print(
        'Main Menu:\n',
        f'{Fore.YELLOW}\t1.{Fore.RESET} \tSet Certificate Attributes\n'
        f'{Fore.YELLOW}\t2.{Fore.RESET} \tSet Source Excel Spreadsheet\n'
        f'{Fore.YELLOW}\t3.{Fore.RESET} \tGenerate CSR\'s\n'
        f'{Fore.YELLOW}\t4.{Fore.RESET} \tCreate PKCS12 certificates\n'
        f'{Fore.YELLOW}\tq.{Fore.RESET} \tQuit\n'
    )


def set_cert_attributes():
    '''
    Configure Certificate Attributes.  You can modify this dictionary directly
    in the code by editing csr_data in the csrcreator.py if you want 
    to change the default to something that makes more sense for you.
    '''
    print(f'{Style.BRIGHT}{Fore.CYAN}Adding Certificate Attributes')
    print(f'{Fore.CYAN}Current Attributes')
    for k, v in csrc.csr_data.items():
        print("{: >5}{: >20}".format(k, v))

    print(f'{Style.BRIGHT}{Fore.LIGHTBLUE_EX}UPDATE ATTRIBUTES?')
    i = input(f'{Style.BRIGHT}{Fore.LIGHTCYAN_EX}y/n: ')

    if i == 'y':   
        if csrc is not None:
            # Create new certifite attributes and add it to the CSRCreator object
            o = input('Enter Organiation: ')
            ou = input('Enter OU: ')
            l = input('Enter Locality(city): ')
            st = input('Enter State or Province: ')
            c = input('Enter Country: ')
    
            csr_attrib = {
                'key': 4096, 
                'o': o,
                'ou': ou,
                'l': l,
                'st': st,
                'c': c,
                'cn': ''
            }

            print(f'{Style.BRIGHT}{Fore.GREEN}Updated Certificate attributes to:')
            for k, v in csr_attrib.items():
                print("{:>5}{:>20}".format(k, v))

            apply = input('Accept? y/n:')

            if apply == 'y':
                csrc.csr_data = csr_attrib
            else:
                print_menu()
                return
            
    elif i == 'n':
        print_menu()
        return
    else:
        print('Input not supported.  Enter y or n')
        return
    
    csrc.set_cert_attributes(csr_attrib)

    return


def set_source_spreadsheet():
    src_xlsx = input('Source file name: ')
    if os.path.exists(src_xlsx):
        cm.SOURCE_XML_FILE = src_xlsx
        print(f'{Fore.LIGHTGREEN_EX}Source file is {src_xlsx}')
        return
    else:
        print(f'{Fore.RED}Unable to set source file as {src_xlsx}')
        return


def generate_csrs():
    cm.get_host_list(cm.SOURCE_XML_FILE)
    csrc.set_host_list(cm.HOST_LIST)
    csrc.csr_hosts()
    csrc.output_csr_list()
    return


def create_pkcs12s():
    # invoke pfxcreator.py object to create our pkcs12 certificates
    
    # TAGGED FOR DELETION
    '''
    # Identify json source file
    source_file = pfxc.find_cert_list_file()
    # Load the json file as an array of dicts
    cl = pfxc.read_cert_list_file(source_file)
    '''
    pfxc.cert_list_data = pfxc.read_cert_list_file(pfxc.find_cert_list_file())
    # For updated pfxcreator.py 2.0
    # The function now expects a passphrase.
    pfxc.process_all_certs('Password123')
    #TAGGED FOR DELETION
    '''
    # start parsing json and creating certs
    pfxc.parse_certs(cl)
    '''
    print_menu()
    navigate_menu()

def quit_script():
    print(f'{Fore.CYAN}{Style.BRIGHT}Goodbye.')
    print(f'{Style.RESET_ALL}{Fore.RESET}{Back.RESET}')
    quit()


def navigate_menu():
    while True:
        s = input('Enter Selection: ')

        if s == '1':
            set_cert_attributes()
            print_menu()
            continue
        elif s == '2':
            set_source_spreadsheet()
            print_menu()
            continue
        elif s == '3':
            generate_csrs()
            print_menu()
            continue
        elif s == '4':
            create_pkcs12s()
            print_menu()
            continue
        elif s == '5' or 'q':
            quit_script()
        else:
            print('Unsupported input.  Enter option 1 - 5')
    return

if __name__ == '__main__':
    '''
    THE FOLLOWING SECTION IS TESTING INGESTING HOST DATA FROM XML THAT INCLUDES IP ADDRESSES FOR 
    CREATING CSR'S WITH SAN IP FIELDS
    '''
    # os.chdir('CSRcreator')


    cm = CertManager()
    csrc = CSRCreator()
    pfxc = PFXCreator()
   
    # RESTORE THIS SECTION
    #os.chdir('CSRCreator')
    script_start()
    print_menu()
    navigate_menu()

    
    '''
    cm.get_host_list('SNA Certificate Checklist.xlsx')

    # Create the CSRs
    csrc = CSRCreator()
    csrc.set_host_list(cm.HOST_LIST)
    csrc.csr_hosts()
    csrc.output_csr_list()

    # Create the pkcs12 files

    '''
