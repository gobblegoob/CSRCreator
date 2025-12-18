import datetime
import os
import json
import re # Added for parsing multiple PEM blocks
import getpass # Added for secure passphrase input

# Using colorama for colored output
from colorama import Style, Back, Fore

# Importing specific OpenSSL exceptions for better error handling
from OpenSSL.crypto import (
    dump_certificate,
    FILETYPE_PEM,
    PKCS12,
    load_certificate,
    load_privatekey,
    Error as OpenSSLError # Specific OpenSSL error type
)

class PFXCreator:
    """
    Finds signed certificate files and their corresponding private keys,
    then outputs PKCS12 (.pfx) files.
    Optionally includes the full certificate chain (intermediate and root CAs).
    """
    def __init__(self):
        self.HOME_DIR = os.getcwd()
        self.cert_list_data = [] # Renamed for clarity and consistency
        self.today_date = datetime.datetime.now().date() # Renamed for clarity

    def set_cert_list(self, certlist):
        """
        Sets the internal certificate list data.
        Expected format: list of dictionaries, each containing 'hostname', 'keyfile', 'certfile',
        and optionally 'ca_chain_file'.
        """
        self.cert_list_data = certlist
        return

    def find_cert_list_file(self):
        """
        Searches the current working directory for a JSON file starting with "csr_list".
        Returns the full path to the first found file, or None if not found.
        """
        files = os.listdir(self.HOME_DIR) # Specify directory for os.listdir
        for f in files:
            if f.startswith("csr_list") and f.endswith('.json'):
                return os.path.join(self.HOME_DIR, f) # Return full path
        print(f'{Fore.RED}Source JSON file not found (looking for csr_list*.json).')
        return None # Explicitly return None

    def read_cert_list_file(self, fn):
        """
        Reads the specified JSON file and populates self.cert_list_data.
        Handles FileNotFoundError and JSONDecodeError.
        """
        if not fn:
            print(f'{Fore.RED}No certificate list file path provided to read.')
            return None
        try:
            with open(fn, 'r', encoding='utf-8') as file:
                self.cert_list_data = json.loads(file.read())
            print(f'{Fore.GREEN}Successfully loaded certificate list from {fn}')
            return self.cert_list_data
        except FileNotFoundError:
            print(f'{Fore.RED}Error: Certificate list file not found at {fn}')
            return None
        except json.JSONDecodeError:
            print(f'{Fore.RED}Error: Invalid JSON format in {fn}. Please check the file content.')
            return None
        except Exception as e:
            print(f'{Fore.RED}Error reading certificate list file {fn}: {e}')
            return None

    def _read_file_as_bytes(self, filepath):
        """
        Helper method to read a file's content as bytes.
        Suitable for OpenSSL functions that expect byte input.
        """
        try:
            with open(filepath, 'rb') as f: # Read in binary mode
                return f.read()
        except FileNotFoundError:
            print(f'{Fore.RED}Error: File not found at {filepath}')
            return None
        except Exception as e:
            print(f'{Fore.RED}Error reading file {filepath} as bytes: {e}')
            return None

    def _load_pem_certificates_from_file(self, filepath):
        """
        Reads a file that may contain one or more concatenated PEM certificates
        and returns a list of OpenSSL.crypto.X509 objects.
        Returns an empty list if the file is not found, empty, or contains no valid certs.
        """
        certs = []
        if not filepath or not os.path.exists(filepath):
            # print(f'{Fore.YELLOW}Warning: CA chain file not found or path is empty: {filepath}')
            return [] # Return empty list if file doesn't exist or path is invalid

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Regular expression to find all PEM certificate blocks
            # re.DOTALL ensures '.' matches newlines
            pem_blocks = re.findall(r"(-+BEGIN CERTIFICATE-+\n.+?\n-+END CERTIFICATE-+)", content, re.DOTALL)

            if not pem_blocks:
                print(f'{Fore.YELLOW}Warning: No PEM certificate blocks found in {filepath}.')
                return []

            for block in pem_blocks:
                try:
                    # load_certificate expects bytes
                    certs.append(load_certificate(FILETYPE_PEM, block.encode('utf-8')))
                except OpenSSLError as e:
                    print(f'{Fore.YELLOW}Warning: Could not load one certificate block from {filepath} (OpenSSL error): {e}')
                except Exception as e:
                    print(f'{Fore.YELLOW}Warning: Unexpected error loading certificate block from {filepath}: {e}')
            return certs
        except FileNotFoundError:
            print(f'{Fore.RED}Error: CA chain file not found at {filepath}')
            return []
        except Exception as e:
            print(f'{Fore.RED}Error loading CA certificates from {filepath}: {e}')
            return []

    def generate_pkcs12(self, host, cert_filepath, pkey_filepath, passphrase, ca_chain_filepath=None):
        """
        Generates a PKCS12 (.pfx) file from a signed certificate, private key,
        and an optional CA certificate chain.

        Args:
            host (str): The hostname, used for friendly naming.
            cert_filepath (str): Full path to the signed PEM certificate file.
            pkey_filepath (str): Full path to the private key file.
            passphrase (bytes): The passphrase to encrypt the PKCS12 file.
            ca_chain_filepath (str, optional): Full path to a file containing
                                               concatenated CA/intermediate certificates.

        Returns:
            bytes: The binary content of the PKCS12 file, or None on failure.
        """
        friendly_name = f'{host}.pfx'
        try:
            if not self.validate_base64_cert(cert_filepath):
                print(f'{Fore.RED}{Style.BRIGHT}Unable to create PKCS12 for {friendly_name} - Host certificate not valid Base64 PEM.')
                return None

            p12 = PKCS12()
            pem_bytes = self._read_file_as_bytes(cert_filepath)
            pkey_bytes = self._read_file_as_bytes(pkey_filepath)

            if pem_bytes is None or pkey_bytes is None:
                print(f'{Fore.RED}Failed to read host certificate or private key files for {host}.')
                return None

            p12.set_certificate(load_certificate(FILETYPE_PEM, pem_bytes))
            p12.set_privatekey(load_privatekey(FILETYPE_PEM, pkey_bytes))

            # --- NEW: Add CA certificates to the PKCS12 object if provided ---
            if ca_chain_filepath:
                ca_certs = self._load_pem_certificates_from_file(ca_chain_filepath)
                if ca_certs:
                    p12.set_ca_certificates(ca_certs)
                    print(f'{Fore.CYAN} -- Added {len(ca_certs)} CA certificates from {ca_chain_filepath} to {friendly_name}')
                else:
                    print(f'{Fore.YELLOW}Warning: No valid CA certificates loaded from {ca_chain_filepath} for {host}. PKCS12 will be created without a CA chain.')
            # --- END NEW ---

            pkcs12_bin = p12.export(passphrase=passphrase)
            return pkcs12_bin

        except OpenSSLError as e:
            print(f'{Fore.RED}OpenSSL Error creating PKCS12 file {friendly_name}: {e}')
            return None
        except Exception as e:
            print(f'{Fore.RED}generate_pkcs12() Error creating PKCS12 file {friendly_name}: {e}')
            return None

    def write_pks12(self, pfx_output_path, pfx_data):
        """
        Writes the binary PKCS12 data to a file.
        """
        if pfx_data is None:
            print(f'{Fore.RED}No PKCS12 data to write to {pfx_output_path}.')
            return False
        try:
            with open(pfx_output_path, 'wb') as pfxfile:
                pfxfile.write(pfx_data)
            print(f'{Fore.GREEN}{Style.BRIGHT} -- Successfully Created {pfx_output_path}')
            return True
        except Exception as e:
            print(f'{Fore.RED}Error writing PKCS12 file {pfx_output_path}: {e}')
            return False

    def validate_base64_cert(self, cert_filepath):
        """
        Validates if a file contains a valid Base64 encoded X.509 certificate.
        Performs a basic header check and attempts to load the certificate.
        """
        try:
            with open(cert_filepath, 'r', encoding='utf-8') as certfile:
                content = certfile.read()

            # Basic header check
            if not content.strip().startswith('-----BEGIN CERTIFICATE-----'):
                print(f'{Fore.RED}Certificate {cert_filepath} does not start with -----BEGIN CERTIFICATE-----')
                return False

            # More robust validation by attempting to load it
            try:
                load_certificate(FILETYPE_PEM, content.encode('utf-8'))
                return True
            except OpenSSLError:
                print(f'{Fore.RED}Certificate {cert_filepath} is not a valid PEM certificate (OpenSSL error).')
                return False
        except FileNotFoundError:
            print(f'{Fore.RED}Error: Certificate file not found at {cert_filepath}')
            return False
        except Exception as e:
            print(f'{Fore.RED}Error validating base 64 x509 certificate {cert_filepath}: {e}')
            return False

    def validate_cert_and_key_files(self, host_dir, cert_filename, key_filename):
        """
        Validates the presence of the host certificate and private key files
        within the specified host directory.
        Returns (True, cert_full_path, key_full_path) if both exist, else (False, None, None).
        """
        cert_full_path = os.path.join(host_dir, cert_filename)
        key_full_path = os.path.join(host_dir, key_filename)

        has_cert = os.path.exists(cert_full_path) and os.path.isfile(cert_full_path)
        has_key = os.path.exists(key_full_path) and os.path.isfile(key_full_path)

        if not has_cert:
            print(f'{Fore.RED}Missing certificate file: {cert_full_path}')
            return False, None, None
        if not has_key:
            print(f'{Fore.RED}Missing key file: {key_full_path}')
            return False, None, None

        if has_cert and has_key:
            return True, cert_full_path, key_full_path
        else:
            print(f'{Fore.RED}Missing certificate or key in {host_dir}.')
            return False, None, None

    def get_filename_from_path(self, path):
        """
        Extracts the filename from a given path using os.path.basename.
        """
        return os.path.basename(path)

    def set_pfx_output_name(self, host):
        """
        Generates a standardized output filename for the PKCS12 file.
        """
        return f'{host}_{self.today_date}.pfx'
    
    
    def get_certfilename(self, cert_dir):
        # Locate a .cer file in your directory and return its name
        files = os.listdir(cert_dir)
        for f in files:
            if f[-4:] == '.cer':
                return f
            

    def process_all_certs(self, passphrase):
        """
        Iterates through the loaded certificate list, processes each entry,
        and generates the corresponding PKCS12 file.
        """
        if not self.cert_list_data:
            print(f'{Fore.RED}There is no certificate list data to process. Exiting.')
            return

        for cert_info in self.cert_list_data:
            pkey_relative_path = cert_info.get("keyfile")
            host = cert_info.get("hostname")
            # Manual append root ca cert
            cert_info["ca_chain_file"] = self.get_certfilename(self.HOME_DIR) # Get the root CA cert file name
            # Construct the host-specific directory path
            host_dir = os.path.join(self.HOME_DIR, host)
            cert_filename = cert_info.get("certfile") # Expecting this in your JSON
            # In case it's not populated in JSON
            if cert_filename is None:
                cert_filename = f'{host_dir}/certnew.cer'

            ca_chain_relative_path = cert_info.get("ca_chain_file") # Optional CA chain file

            if not all([pkey_relative_path, host, cert_filename]):
                print(f'{Fore.RED}Skipping entry due to missing "keyfile", "hostname", or "certfile" in: {cert_info}')
                continue

            # Construct the host-specific directory path
            host_dir = os.path.join(self.HOME_DIR, host)
            if not os.path.isdir(host_dir):
                print(f'{Fore.RED}Host directory not found: {host_dir}. Skipping {host}.')
                continue

            print(f'\n{Fore.BLUE}{Style.BRIGHT}--- Processing host: {host} in directory: {host_dir} ---{Style.RESET_ALL}')

            # Validate and get full paths for the main certificate and key
            files_present, cert_full_path, key_full_path = self.validate_cert_and_key_files(
                host_dir, cert_filename, self.get_filename_from_path(pkey_relative_path)
            )

            ca_chain_full_path = None
            if ca_chain_relative_path:
                ca_chain_full_path = os.path.join(host_dir, ca_chain_relative_path)
                # Check if the CA chain file actually exists
                if not os.path.exists(ca_chain_full_path):
                    print(f'{Fore.YELLOW}Warning: CA chain file specified ("{ca_chain_relative_path}") but not found at {ca_chain_full_path} for {host}. PKCS12 will be created without a CA chain.')
                    ca_chain_full_path = None # Ensure it's None if not found
                elif not os.path.isfile(ca_chain_full_path):
                    print(f'{Fore.YELLOW}Warning: CA chain path "{ca_chain_full_path}" is not a file. PKCS12 will be created without a CA chain.')
                    ca_chain_full_path = None

            if files_present:
                pfx_output_filename = self.set_pfx_output_name(host)
                pfx_output_path = os.path.join(host_dir, pfx_output_filename) # Output PFX to host's directory

                pkcs12_data = self.generate_pkcs12(
                    host,
                    cert_full_path,
                    key_full_path,
                    passphrase,
                    ca_chain_full_path # Pass the optional CA chain path
                )

                if pkcs12_data:
                    self.write_pks12(pfx_output_path, pkcs12_data)
                else:
                    print(f'{Fore.RED}Failed to generate PKCS12 data for {host}.')
            else:
                print(f'{Fore.RED}Skipping PKCS12 generation for {host} due to missing required files.')
        print(f'\n{Fore.GREEN}{Style.BRIGHT}--- PKCS12 generation process complete ---{Style.RESET_ALL}')


if __name__ == '__main__':
    creator = PFXCreator()

    # 1. Find the certificate list JSON file
    cert_list_json_file = creator.find_cert_list_file()

    if cert_list_json_file:
        # 2. Read the certificate list from the JSON file
        creator.read_cert_list_file(cert_list_json_file)

        if creator.cert_list_data: # Proceed only if cert_list_data was successfully loaded
            # 3. Securely get the passphrase for the PKCS12 files
            # IMPORTANT: For production, consider more robust secret management.
            # This uses getpass for basic secure console input.
            try:
                passphrase_input = getpass.getpass(f"{Fore.CYAN}Enter passphrase for PKCS12 files (will not be echoed): {Style.RESET_ALL}")
                if not passphrase_input:
                    print(f'{Fore.RED}Passphrase cannot be empty. Exiting.')
                    exit(1)
                secure_passphrase = passphrase_input.encode('utf-8')
            except Exception as e:
                print(f'{Fore.RED}Error getting passphrase: {e}. Exiting.')
                exit(1)

            # 4. Process all certificates and generate PKCS12 files
            creator.process_all_certs(secure_passphrase)
        else:
            print(f'{Fore.RED}No certificate entries found in the JSON file. Nothing to process.')
    else:
        print(f'{Fore.RED}No CSR list JSON file found. Cannot proceed with PKCS12 generation.')