import click

from web_apps.backend.flask_backend_app import FlaskBackEndApp


@click.command()
@click.option('--llm_host', default='localhost', help='LLM endpoint host')
@click.option('--llm_port', default=1234, help='LLM endpoint port')
@click.option('--llm_version_str', default='v1', help='LLM endpoint version str')
@click.option('--host', default='0.0.0.0', help='webapp hostname or ip to listen on')
@click.option('--port', default=5000, help='Port for webapp to listen on')
def main_cli(llm_host, llm_port, llm_version_str, host, port):
    app = FlaskBackEndApp(host=host, port=port, llm_host=llm_host, llm_port=llm_port, llm_version_str=llm_version_str, debug=True)
    app.run()


if __name__ == "__main__":
    main_cli()
