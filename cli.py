"""Database commands.   flask --app app <command>

  init-db                 create all tables (safe to run again)
  reset-db                DROP everything and recreate (asks for --yes)
  db-info                 tables, columns and row counts
  show-readings           print the latest readings
  create-demo             demo parent + one child, prints the device key
"""
import click
from sqlalchemy import inspect, text

import repositories as repo
from extensions import db


def register(app):
    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        click.echo("Tables ready.")

    @app.cli.command("reset-db")
    @click.option("--yes", is_flag=True, help="confirm that ALL data will be deleted")
    def reset_db(yes):
        if not yes:
            raise click.UsageError("This deletes all data. Re-run with --yes")
        db.drop_all()
        db.create_all()
        click.echo("Database recreated (empty).")

    @app.cli.command("db-info")
    def db_info():
        insp = inspect(db.engine)
        click.echo(f"Database: {db.engine.url}\n")
        for table in insp.get_table_names():
            count = db.session.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
            click.echo(f"== {table}  ({count} rows)")
            for col in insp.get_columns(table):
                click.echo(f"   {col['name']:<20} {col['type']}")
            click.echo("")

    @app.cli.command("show-readings")
    @click.option("--child", "child_id", type=int, default=None)
    @click.option("--limit", default=10)
    def show_readings(child_id, limit):
        q = "SELECT id, child_id, timestamp, heart_rate, gsr, temperature, risk, status, engine FROM readings"
        params = {"n": limit}
        if child_id:
            q += " WHERE child_id = :c"
            params["c"] = child_id
        q += " ORDER BY id DESC LIMIT :n"
        for row in db.session.execute(text(q), params):
            click.echo(" | ".join(str(v) for v in row))

    @app.cli.command("create-demo")
    def create_demo():
        user = repo.get_user_by_email("demo@calmband.com") or repo.create_user(
            "Demo Parent", "demo@calmband.com", "demo123")
        child = repo.create_child(user.id, "Demo Child")
        click.echo("login:      demo@calmband.com / demo123")
        click.echo(f"child id:   {child.id}")
        click.echo(f"device key: {child.device_key}")
