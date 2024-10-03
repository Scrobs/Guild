import os
import sys
import getpass
from dotenv import load_dotenv
from app import create_app
from app.models import db, User
from app.bgg import update_games_for_user
from sqlalchemy.exc import SQLAlchemyError
import logging

# Load environment variables from .env file
load_dotenv()

app = create_app()
app.app_context().push()


def verify_admin_auth():
    admin_password = os.getenv('ADMIN_PASSWORD')
    if not admin_password:
        print("Error: ADMIN_PASSWORD environment variable not set.")
        sys.exit(1)
    input_password = getpass.getpass("Enter admin password: ").strip()
    if input_password != admin_password:
        print("Error: Incorrect admin password.")
        sys.exit(1)


def add_user():
    name = input("Enter user's name: ").strip()
    if not name:
        print("Error: Name cannot be empty.")
        return

    bgg_username = input("Enter user's BGG username: ").strip()
    if not bgg_username:
        print("Error: BGG username cannot be empty.")
        return

    # Check if user with the same name or BGG username already exists
    existing_user = User.query.filter(
        (User.name.ilike(name)) | (User.bgg_username.ilike(bgg_username))
    ).first()
    if existing_user:
        print("Error: User with this name or BGG username already exists.")
        return

    # Set initial password as BGG username
    password = bgg_username

    # Create new user instance
    user = User(name=name, bgg_username=bgg_username)
    user.set_password(password)

    # Add user to the session
    db.session.add(user)
    try:
        db.session.commit()
        print(f"Success: User '{name}' added successfully with initial password as BGG username.")
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Error: Failed to add user '{name}'. Details: {e}")
        return

    # Update games for the newly added user
    print(f"Fetching and updating games for user '{name}'...")
    try:
        update_games_for_user(user)
        print(f"Success: Games for user '{name}' have been updated.")
    except Exception as e:
        logging.error(f"Error updating games for user '{name}': {e}")


def edit_user():
    name = input("Enter the name of the user to edit: ").strip()
    if not name:
        print("Error: Name cannot be empty.")
        return

    user = User.query.filter(User.name.ilike(name)).first()
    if not user:
        print(f"Error: No user found with the name '{name}'.")
        return

    new_name = input(f"Enter new name for '{user.name}' (leave empty to keep unchanged): ").strip()
    new_bgg_username = input(f"Enter new BGG username for '{user.bgg_username}' (leave empty to keep unchanged): ").strip()

    if new_name:
        user.name = new_name
    if new_bgg_username:
        user.bgg_username = new_bgg_username

    try:
        db.session.commit()
        print(f"Success: User '{user.name}' updated successfully.")
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Error: Failed to update user '{user.name}'. Details: {e}")


def delete_user():
    name = input("Enter the name of the user to delete: ").strip()
    if not name:
        print("Error: Name cannot be empty.")
        return

    user = User.query.filter(User.name.ilike(name)).first()
    if not user:
        print(f"Error: No user found with the name '{name}'.")
        return

    confirm = input(f"Are you sure you want to delete user '{name}'? This will remove all their votes and associations. (y/n): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return

    try:
        db.session.delete(user)
        db.session.commit()
        print(f"Success: User '{name}' has been deleted.")
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Error: Failed to delete user '{name}'. Details: {e}")


def list_users():
    users = User.query.order_by(User.name.asc()).all()
    if not users:
        print("No users found.")
        return
    print("\nList of Users:")
    for user in users:
        print(f"- {user.name} (BGG Username: {user.bgg_username})")
    print("") 


def update_user_games():
    name = input("Enter the name of the user to update games: ").strip()
    if not name:
        print("Error: Name cannot be empty.")
        return

    user = User.query.filter(User.name.ilike(name)).first()
    if not user:
        print(f"Error: No user found with the name '{name}'.")
        return

    print(f"Fetching and updating games for user '{name}'...")
    try:
        update_games_for_user(user)
        print(f"Success: Games for user '{name}' have been updated.")
    except Exception as e:
        logging.error(f"Error updating games for user '{name}': {e}")


def update_all_club_games():
    users = User.query.all()
    if not users:
        print("No users found.")
        return

    print("Updating games for all users in the club...")
    for user in users:
        print(f"Updating games for user: {user.name} ({user.bgg_username})")
        try:
            update_games_for_user(user)
            print(f"Success: Games for user '{user.name}' have been updated.")
        except Exception as e:
            logging.error(f"Error updating games for user '{user.name}': {e}")
    print("All club games have been updated.")


def main():
    verify_admin_auth()  
    print("\nAdmin Commands:")
    print("1. Add a new user")
    print("2. Edit a user")
    print("3. Delete a user")
    print("4. List all users")
    print("5. Update a user's games")
    print("6. Update all club's games")
    print("7. Exit")
    while True:
        choice = input("\nSelect an option (1-7): ").strip()
        if choice == '1':
            add_user()
        elif choice == '2':
            edit_user()
        elif choice == '3':
            delete_user()
        elif choice == '4':
            list_users()
        elif choice == '5':
            update_user_games()
        elif choice == '6':
            update_all_club_games()
        elif choice == '7':
            print("Exiting admin commands.")
            break
        else:
            print("Invalid option. Please select a number between 1 and 7.")


if __name__ == '__main__':
    main()
