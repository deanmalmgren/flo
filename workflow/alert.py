import smtplib
from email.mime.text import MIMEText
import socket

def alert(*contact_list):
    """Send an alert to any email addresses specified in contact_list.
    """
    # this takes heavy inspiration from
    # http://docs.python.org/2/library/email-examples.html

    # Open a plain text file for reading.  For this example, assume that
    # the text file contains only ASCII characters.
    msg = MIMEText((
        "workflow finished. yippee!"
    ))

    # fill out the relevant header information
    msg['Subject'] = 'workflow finished'
    msg['From'] = 'root@localhost'
    msg['To'] = ', '.join(contact_list)

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    server = smtplib.SMTP('localhost')
    server.sendmail(msg['From'], contact_list, msg.as_string())
    server.quit()
