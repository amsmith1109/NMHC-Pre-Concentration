import ftplib

def append_to_ftp_file(ftp_host, ftp_user, ftp_pass, remote_file, local_file):
    with ftplib.FTP(ftp_host, ftp_user, ftp_pass) as ftp:
        with open(local_file, 'rb') as file:
            ftp.storbinary('APPE ' + remote_file, file)

# Example usage
ftp_host = '192.168.1.1'
ftp_user = 'anonymous'
ftp_pass = ''
remote_file = ''
local_file = 'Licor Data.txt'

append_to_ftp_file(ftp_host, ftp_user, ftp_pass, remote_file, local_file)