"""
    This module defines a small singleton that runs various scripts in the
    context of the service.
"""

# external imports
import click

class ServiceManager:

    def __init__(self, service):
        self.service = service
        self._running_service = False

        @click.group()
        def group():
            pass

        @group.command()
        def syncdb():
            print('sync db')

        @group.command()
        @click.option('--port', default=8000, help="The port for the service http server.")
        @click.option('--host', default='127.0.0.1', help="The host for the http server.")
        def runserver(port, host):
            # run the service
            service.run(
                host = host,
                port = int(port),
            )

        # @self.commandManager.command
        # def syncdb():
        #     """ Create the database entries. """
        #     # import the db module
        #     from nautilus.db import db
        #     # create all of the tables
        #     db.create_all()
        #     # notify the user
        #     print("Successfully created database entries.")

        # save the command group to the manager
        self.group = group


    def run(self):
        """ run the command manager """
        try:
            # run the command group
            self.group()
        # if there is a normal exception
        except Exception as err:
            print("Closing due to error: %s" % err)
            # if the service is running
            if self._running_service:
                # stop the service and clean up
                self.service.stop()
            # bubble up the exception for someone else
            raise err
