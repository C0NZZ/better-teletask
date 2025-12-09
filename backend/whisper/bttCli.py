from database import (
    add_api_key, remove_api_key, get_all_api_keys, get_api_key_by_name, get_api_key_by_key,
    getHighestTeletaskID ,get_all_lecture_ids, get_all_original_vtt_ids
)
from krabbler import getLecturerData, fetchBody, baseurl, pingVideoByID 
import hashlib
import argparse
import os

# --- API Management Commands ---

def handle_api_add(args):
    """Add a new API key."""
    print(f"\n--- Add Command ---")
    print(f"Action: Adding user.")
    print(f"Name: {args.name}")
    print(f"Email: {args.email}")
    
    # Generate a secure random seed (32 bytes = 256 bits of entropy)
    random_seed = os.urandom(32) 
    sha256_hash = hashlib.sha256(random_seed).hexdigest()[:32]
    
    print(f"Generated API Key: {sha256_hash}\n")
    add_api_key(sha256_hash, args.name, args.email)
    print("[SUCCESS] User added.\n")

def handle_api_remove(args):
    """Remove an API key."""
    print(f"\n--- Remove Command ---")
    print(f"Action: Removing user by key.")
    print(f"Key to remove: {args.key}")
    
    remove_api_key(args.key)
    print("[SUCCESS] Key removed.\n")

def handle_api_show(args):
    """Show API key details."""
    print(f"\n--- Show Command ---")
    
    if args.all:
        print("Displaying all registered users/keys:\n")
        keys = get_all_api_keys()
        if keys:
            for key in keys:
                print(f"- Key: {key['api_key']}, Name: {key['person_name']}, Email: {key['person_email']}")
        else:
            print("No API keys found.")
    elif args.key:
        print(f"Looking up by API key: {args.key}\n")
        key_info = get_api_key_by_key(args.key)
        if key_info:
            print(f"- Key: {key_info['api_key']}, Name: {key_info['person_name']}, Email: {key_info['person_email']}")
    elif args.name:
        print(f"Looking up by name: {args.name}\n")
        keys = get_api_key_by_name(args.name)
        if keys:
            for key in keys:
                print(f"- Key: {key['api_key']}, Name: {key['person_name']}, Email: {key['person_email']}")
    else:
        print("Please specify --all, --key, or --name")
    print()

# --- Scrape Commands ---


def handle_scrape_missing_lecture_data(args):
    """
    Fetches and updates missing lecture data for lectures that have original VTTs but lack lecturer data.
    """
    print("\n--- Fetching Missing Lecture Data ---\n")
    
    all_lecture_ids = set(get_all_lecture_ids())
    all_vtt_ids = set(get_all_original_vtt_ids())

    missing_lecturer_data_ids = all_vtt_ids - all_lecture_ids

    print(f"Found {len(missing_lecturer_data_ids)} lectures with missing lecturer data.")
    
    if not missing_lecturer_data_ids:
        print("No missing lecture data to fetch.\n")
        return

    for lecture_id in missing_lecturer_data_ids:
        try:
            url = baseurl + str(lecture_id)
            response = fetchBody(str(lecture_id))
            lecturer_data = getLecturerData(str(lecture_id), response, url)
            print(f"✓ Lecture ID {lecture_id}: {lecturer_data}")
        except Exception as e:
            print(f"✗ Lecture ID {lecture_id}: Error - {e}")
    
    print("\n--- Complete ---\n")


def handle_scrape_idstatus(args):
    """Check status of video IDs."""
    print("\n--- ID Status Check ---")
    res200 = []
    res404 = []
    res401 = []
    res403 = []
    resError = []

    highest = getHighestTeletaskID()
    if highest is None:
        print("No highest ID found in database. Please specify a starting ID.")
        return
    
    start_id = args.start if args.start else highest
    count = args.count if args.count else 10
    
    print(f"Checking {count} IDs starting from {start_id}...\n")
    
    for i in range(count):
        current_id = start_id + i
        res = pingVideoByID(str(current_id))
        
        if res == "200":
            res200.append(current_id)
            print(f"✓ {current_id}: Available (200)")
        elif res == "404":
            res404.append(current_id)
            print(f"✗ {current_id}: Not found (404)")
        elif res == "401":
            res401.append(current_id)
            print(f"✗ {current_id}: Unauthorized (401)")
        elif res == "403":
            res403.append(current_id)
            print(f"✗ {current_id}: Forbidden (403)")
        else:
            resError.append(current_id)
            print(f"✗ {current_id}: Error ({res})")
    
    # Summary
    print("\n--- Summary ---")
    print(f"✓ Available (200): {len(res200)}")
    print(f"✗ Not Found (404): {len(res404)}")
    print(f"✗ Unauthorized (401): {len(res401)}")
    print(f"✗ Forbidden (403): {len(res403)}")
    print(f"✗ Errors: {len(resError)}")
    print()


def main():
    """Main CLI entry point with grouped commands."""
    parser = argparse.ArgumentParser(
        description="Better Teletask CLI - Manage API keys and scrape lecture data.",
        epilog="Examples:\n"
               "  python bttCli.py api add 'Crisitan' 'conzz@culator.zaza'\n"
               "  python bttCli.py api show all\n"
               "  python bttCli.py api show --key 'your_api_key'\n"
               "  python bttCli.py api show --name 'Crisitan'\n"
               "  python bttCli.py scrape idstatus --count 20\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(
        title='Command Groups',
        required=True,
        dest='group'
    )

    # ====================
    # API Command Group
    # ====================
    api_parser = subparsers.add_parser('api', help='Manage API keys')
    api_subparsers = api_parser.add_subparsers(
        title='API Commands',
        required=True,
        dest='api_command'
    )

    # api add
    add_parser = api_subparsers.add_parser('add', help='Add a new API key for a user by username and email')
    add_parser.add_argument('name', type=str, help='The user name')
    add_parser.add_argument('email', type=str, help='The user email')
    add_parser.set_defaults(func=handle_api_add)

    # api remove
    remove_parser = api_subparsers.add_parser('remove', help='Remove a user/key by key')
    remove_parser.add_argument('key', type=str, help='The API key string to remove')
    remove_parser.set_defaults(func=handle_api_remove)

    # api show
    show_parser = api_subparsers.add_parser('show', help='Show API key details')
    show_group = show_parser.add_mutually_exclusive_group(required=True)
    show_group.add_argument('--all', action='store_true', help='Show all API keys')
    show_group.add_argument('--key', type=str, help='Show API key by key value')
    show_group.add_argument('--name', type=str, help='Show API key(s) by person name')
    show_parser.set_defaults(func=handle_api_show)

    # ====================
    # Scrape Command Group
    # ====================
    scrape_parser = subparsers.add_parser('scrape', help='Scrape and check lecture data')
    scrape_subparsers = scrape_parser.add_subparsers(
        title='Scrape Commands',
        required=True,
        dest='scrape_command'
    )

    # scrape idstatus
    idstatus_parser = scrape_subparsers.add_parser('idstatus', help='Check status of video IDs')
    idstatus_parser.add_argument('--start', type=int, help='Starting ID (default: highest in DB)')
    idstatus_parser.add_argument('--count', type=int, default=10, help='Number of IDs to check (default: 10)')
    idstatus_parser.set_defaults(func=handle_scrape_idstatus)

    # scrape missing_lecture_data
    missing_lecture_data_parser = scrape_subparsers.add_parser('lecturedata', help='Fetch missing lecture data for lectures with original VTTs but no lecturer data')
    missing_lecture_data_parser.set_defaults(func=handle_scrape_missing_lecture_data)

    # Parse and execute
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()