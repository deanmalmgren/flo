from six.moves import BaseHTTPServer
from six.moves import socketserver
import socket

from .run import Command as RunCommand
from .base import BaseCommand
from .. import templates
from ..exceptions import CommandLineException


class Handler(BaseHTTPServer.BaseHTTPRequestHandler):

    task_graph = None

    def render_template(self):
        return "hello world"

    def do_GET(self, *args, **kwargs):
        # this is all of the header information, which is lifted
        # straight out of the SimpleHTTPServer.send_head method
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        # self.send_header("Content-Length", str(fs[6]))
        # self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()

        # render the template
        self.wfile.write(templates.render_from_file(
            "status.html", task_graph=self.task_graph
        ))


class Command(RunCommand):
    help_text = (
        "Check the status of the current workflow "
        "to see which tasks, if any, are out of sync and would be run."
    )

    def serve_status_page(self, port):
        Handler.task_graph = self.task_graph
        print("Starting server at http://localhost:%d" % port)
        try:
            httpd = socketserver.TCPServer(("", port), Handler)
        except socket.error as error:
            raise CommandLineException(error.strerror)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass

    def execute(self, task_id=None, start_at=None, skip=None, only=None,
                force=False, serve=None, port=None, **kwargs):
        BaseCommand.execute(self, **kwargs)
        if serve:
            self.serve_status_page(port)
        else:
            self.inner_execute(task_id, start_at, skip, only, force,
                               mock_run=True)

    def add_command_line_options(self):
        BaseCommand.add_command_line_options(self)
        self.add_common_run_options()
        self.option_parser.add_argument(
            '--serve',
            action="store_true",
            dest="serve",
            help='Serve a light webserver that displays the workflow status.',
        )
        self.option_parser.add_argument(
            '--port',
            type=int,
            default=8000,
            dest="port",
            help="The port to use for serving the webserver.",
        )
