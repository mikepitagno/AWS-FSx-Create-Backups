#!/usr/bin/env python3
    
'''
###########################################
# AWS FSx Create On-Demand Backups Script #
###########################################

-Description: a Python 3 script to backup each FSx filesystem in multiple 
AWS cloud accounts.
-Author: Mike Pitagno
'''

import json
import subprocess
import smtplib
from email.mime.text import MIMEText

email_sender = '<EMAIL SENDER>'
email_receiver = '<EMAIL RECEIVER>'
smtp_server = '<SMTP SERVER>'

def get_fsxinfo_dict(profile='default'): # Use Python subprocess to have the AWS CLI pull all FSx filesystems into a JSON formatted variable
    
    fsxinfo = subprocess.run(["/usr/local/bin/aws", "fsx", "describe-file-systems", "--output", "json", "--profile", profile], stdout=subprocess.PIPE)
    fsxinfo_utf8 = fsxinfo.stdout.decode('utf-8')
    fsxinfo_utf8_json = json.loads(fsxinfo_utf8)
    return fsxinfo_utf8_json

def get_fsxinfo_list(dict): # Extract a list of FSx filesystem ID's from the provided dictionary
    
    list = []
    for i in dict['FileSystems']:
        list.append(i['FileSystemId'])
    return list

def backup_fsx(list, profile='default'): # Use Python subprocess to have the AWS CLI backup all FSx filesystems provided from list
    
    results_dict = {}
    for i in list:
        proc = subprocess.Popen(["/usr/local/bin/aws", "fsx", "create-backup", "--file-system-id", i, "--profile", profile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if stdout.hex(): # If standard output contains data, backup was successful and should be included in dict; if empty, then standard error should be included 
            results_dict[i] = stdout.decode().strip()
        else:
            results_dict[i] = stderr.decode().strip()
    return results_dict

def convert_dict2string(dict): # Convert dictionary into string format for use in email 
    
    output_file = ''
    for k, v in sorted(dict.items()):
        output_file = output_file + '\n'
        output_file = output_file + k + '\n'
        for k1, v1 in sorted(v.items()):
            output_file = output_file + "-%s: %s" % (k1, v1) + '\n'
    return output_file

def email_report(dict, email_sender, email_receiver, smtp_server): # Email backup report
    
    title = "### AWS FSx Quarterly Backup Creation Report ###"
    body = title + "\n" + convert_dict2string(dict) + "\n"
    msg = MIMEText(body)
    msg['Subject'] = "AWS FSx Quarterly Backup Creation Report"
    msg['From'] = email_sender
    msg['To'] = email_receiver
    s = smtplib.SMTP(smtp_server)
    s.sendmail(email_sender, [email_receiver], msg.as_string())
    s.quit()

# Create dictionaries of FSx info from each account 
fsx_dict_default = get_fsxinfo_dict('default')
fsx_dict_dev = get_fsxinfo_dict('dev')
fsx_dict_prod = get_fsxinfo_dict('prod')

# Use dictionaries to create lists of file system ID's for each account
fsx_list_default = get_fsxinfo_list(fsx_dict_default)
fsx_list_dev = get_fsxinfo_list(fsx_dict_dev)
fsx_list_prod = get_fsxinfo_list(fsx_dict_prod)

# Run backups for each account and collect results in a dictionary
backup_results_default = backup_fsx(fsx_list_default)
backup_results_dev = backup_fsx(fsx_list_dev, 'dev')
backup_results_prod = backup_fsx(fsx_list_prod, 'prod')

# Combine all backup results into a dictionary
backup_results_all = {}
backup_results_all['Backups-default'] = backup_results_default
backup_results_all['Backups-dev'] = backup_results_dev
backup_results_all['Backups-prod'] = backup_results_prod

# Call 'email_report' to covert 'backup_results_all' dictionary into email format and send
email_report(backup_results_all, email_sender, email_receiver, smtp_server)
