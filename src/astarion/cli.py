import click

@click.group()
def cli():
    pass

@cli.command()
def start():
    print("Starting Astarion...")


def main():
    cli()

if __name__ == "__main__":
    main()