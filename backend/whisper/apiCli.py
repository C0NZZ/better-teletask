from database import add_api_key, remove_api_key, get_all_api_keys, get_api_key_by_name

import hashlib
import argparse
import os

# --- Utility Functions ---

def handle_add(args):
    """
    Handles the 'add' subcommand (minimal: name and key).
    """
    print(f"\n--- Add Command ---")
    print(f"Action: Adding user.")
    print(f"Name: {args.name}")
    print(f"Email: {args.email}")
    print("\n[SUCCESS] User added. (Simulated.)")
    # Generate a secure random seed (32 bytes = 256 bits of entropy)
    random_seed = os.urandom(32) 
    
    # Hash the random seed to get the final SHA-256 hash
    sha256_hash = hashlib.sha256(random_seed).hexdigest()[:32]
    print(f"Generated API Key: {sha256_hash}\n")
    add_api_key(sha256_hash, args.name, args.email)

def handle_remove(args):
    """
    Handles the 'remove' subcommand (minimal: key for identification).
    """
    print(f"\n--- Remove Command ---")
    print(f"Action: Removing user by key.")
    print(f"Key to remove: {args.key}")
    print("\n[SUCCESS] Key removed. (Simulated.)")

def handle_show(args):
    """
    Handles the 'show' subcommand (minimal: key for lookup).
    """
    print(f"\n--- Show Command ---")
    print(f"Action: Looking up user details.")
    print(f"Key to look up: {args.key}")
    
    if args.key == "all":
        print("\nDisplaying all registered users/keys. (Simulated.)")
        keys = get_all_api_keys()
        for key in keys:
            print(f"- Key: {key['api_key']}, Name: {key['person_name']}, Email: {key['person_email']}")
    else:
        keys = get_api_key_by_name(args.key)

        for key in keys:
            print(f"- Key: {key['api_key']}, Name: {key['person_name']}, Email: {key['person_email']}")
        print("\nDisplaying details for specific key. (Simulated.)")

# --- Main CLI Setup ---

def main():
    """
    Sets up the main parser and subcommands: add, remove, show.
    """
    parser = argparse.ArgumentParser(
        description="A minimal CLI for managing API user keys.",
        epilog="Usage examples: \n  python apiCli.py add 'Alice' 'API-A1'\n  python apiCli.py remove 'API-A1'\n  python apiCli.py show 'all'"
    )

    subparsers = parser.add_subparsers(
        title='Available Commands',
        required=True,
        dest='command'
    )

    # 1. Setup for 'add' command: requires name and key
    add_parser = subparsers.add_parser('add', help='Add a new user/key pair (add <name> <email>).')
    add_parser.add_argument('name', type=str, help='The user name.')
    add_parser.add_argument('email', type=str, help='The user email.')
    add_parser.set_defaults(func=handle_add)

    # 2. Setup for 'remove' command: requires key
    remove_parser = subparsers.add_parser('remove', help='Remove a user/key by key (remove <key>).')
    remove_parser.add_argument('key', type=str, help='The API key string to remove.')
    remove_parser.set_defaults(func=handle_remove)

    # 3. Setup for 'show' command: requires key (or 'all')
    show_parser = subparsers.add_parser('show', help='Show details for a key, or "all" (show <key> | show all).')
    show_parser.add_argument('key', type=str, help='The API key to look up, or use "all" to list everything.')
    show_parser.set_defaults(func=handle_show)

    # --- Parse Arguments and Execute Function ---
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    
if __name__ == '__main__':
    main()