import smtplib
from email.mime.text import MIMEText
import socket

def notify(*contact_list):
    """Send an notification to any email addresses specified in
    contact_list.

    """
    # this takes heavy inspiration from
    # http://docs.python.org/2/library/email-examples.html

    # TODO: switch to using loggin instead of print() statements so
    # that we can have output logged to a file in the .workflow
    # directory and also have output logged to the terminal

    # TODO: for now, read the last 100 lines of the log and put it in
    # the email. it may also be useful to include other meta
    # information, such as the commands that were run or the total
    # time it took

    msg = MIMEText((
        "XXXX workflow finished. yippee!"
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
