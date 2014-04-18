import smtplib
from email.mime.text import MIMEText
import socket

from .parser import load_task_graph


def notify(*contact_list):
    """Send an notification to any email addresses specified in
    contact_list.
    """
    # this takes heavy inspiration from
    # http://docs.python.org/2/library/email-examples.html

    # set the subject to notify about success/failure on this
    # particular host
    task_graph = load_task_graph()
    status = 'FAILED'
    if task_graph.successful:
        status = 'successfully finished'

    # read in the logs for the body of the message
    # TODO: this reads the ENTIRE log into memory. likely not a good idea.
    n_lines = 100
    with open(task_graph.abs_log_path, 'r') as stream:
        text = "the last %d lines of %s\n\n" % (
            n_lines, task_graph.abs_log_path
        )
        text += '"'*80 + "\n\n"
        text += '\n'.join(stream.readlines()[-100:])

    # fill out the relevant header information
    msg = MIMEText(text)
    msg['Subject'] = "flo %s on '%s'" % (status, socket.gethostname(), )
    msg['From'] = 'root@localhost'
    msg['To'] = ', '.join(contact_list)

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    server = smtplib.SMTP('localhost')
    server.sendmail(msg['From'], contact_list, msg.as_string())
    server.quit()
