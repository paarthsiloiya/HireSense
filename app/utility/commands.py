import click
import random
from flask.cli import with_appcontext
from .. import db
from ..models import User
from werkzeug.security import generate_password_hash

@click.command("seed-users")
@click.argument("number", default=10)
@with_appcontext
def seed_users(number):
    from faker import Faker

    fake = Faker()
    
    roles = ["manager", "employee"]

    print("Seeding users ...")

    for i in range(number):
        username = fake.user_name()
        email = fake.unique.email()
        role = random.choice(roles)

        password = generate_password_hash("password123")

        user = User(
            username = username,
            email=email,
            password_hash=password,
            role=role
        )

        db.session.add(user)
    
    db.session.commit()
    print(f"Successfully added {number} fake users.")
