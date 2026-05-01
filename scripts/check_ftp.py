#!/usr/bin/env python3
"""
Check FTP files
"""

import ftplib
import json

def check_ftp_files():
    """Check files on FTP server"""
    ftp_config = {
        'host': 'testing.techsup.od.ua',
        'user': 'aidata',
        'password': 'lkhvvssvfasDsrvr234523--!fwevrwe',
        'port': 21,
        'timeout': 30,
        'passive_mode': True
    }
    
    try:
        # Connect to FTP
        ftp = ftplib.FTP()
        ftp.connect(
            host=ftp_config['host'],
            port=ftp_config['port'],
            timeout=ftp_config['timeout']
        )
        ftp.login(
            user=ftp_config['user'],
            passwd=ftp_config['password']
        )
        
        if ftp_config['passive_mode']:
            ftp.set_pasv(True)
        
        # List files
        files = ftp.nlst()
        print("Files on FTP server:")
        for file in files:
            print(f"  - {file}")
        
        ftp.quit()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_ftp_files() 