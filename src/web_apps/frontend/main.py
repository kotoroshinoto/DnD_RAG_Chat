import click

from web_apps.frontend.flask_frontend_app import FlaskFrontEndApp


@click.command()
@click.option('--host', default='0.0.0.0', help='webapp hostname or ip to listen on')
@click.option('--port', default=2345, help='Port for webapp to listen on')
def main_cli(host, port):
    front_end_app = FlaskFrontEndApp(host=host, port=port, debug=True)
    front_end_app.run()

if __name__ == "__main__":
    main_cli()
