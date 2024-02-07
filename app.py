import AO3
import os
import threading
from dotenv import load_dotenv
from colorama import Fore, Style
from slugify import slugify
from ebooklib import epub

BOOK_FORMAT = "EPUB"
TARGET_DIR = os.path.join(os.path.curdir, "books")


def download_subscriptions(session: AO3.Session, target_dir: str):
    # Create target directory if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    for subscription in session.get_work_subscriptions():

        work = AO3.Work(subscription.id, session=session, load_chapters=False)

        # Skip the download if the work is restricted
        if work.restricted:
            print(f"{Fore.YELLOW}Download failed: {work.title} - RESTRICTED{Style.RESET_ALL}")
            continue

        filename = f"{work.authors[0].username}_{slugify(work.title)}.{BOOK_FORMAT.lower()}"
        filename_tmp = filename + ".tmp"

        # Check if the file already exists in the EBOKS_PATH with the same number of chapters
        if os.path.exists(os.path.join(target_dir, filename)):
            existing_work_filepath = os.path.join(target_dir, filename)
            existing_work = epub.read_epub(existing_work_filepath)

            # If the file has the same number of chapters or less, skip the download
            # (the -3 is to account for the 3 extra chapters in the epub file created by AO3)
            if work.nchapters <= len(existing_work.spine) - 3:
                print(f"{Fore.GREEN}Download skipped: {work.title} - UP TO DATE{Style.RESET_ALL}")
                continue

        print(f"{Fore.BLUE}Downloading: {Fore.CYAN}{work.authors[0].username} - {work.title}{Style.RESET_ALL}\r")

        try:
            # Download the work
            work.download_to_file(os.path.join(target_dir, filename_tmp), BOOK_FORMAT)
            
            # If the file is empty, download failed
            if os.path.getsize(os.path.join(target_dir, filename_tmp)) == 0:
                print(f"{Fore.RED}Download failed: {work.title} - EMPTY{Style.RESET_ALL}")
                os.remove(os.path.join(target_dir, filename_tmp))
                continue
            
            # If the file is not empty, rename it to the final filename
            os.rename(os.path.join(target_dir, filename_tmp), os.path.join(target_dir, filename))

        except Exception as e:
            print(f"{Fore.RED}Download failed: {work.title}\t\t{Style.DIM}{e.args[0]}{Style.RESET_ALL}")

    print(f"{Fore.GREEN}Download complete!{Style.RESET_ALL}")


# Main function
def main():
    load_dotenv()

    # Login to AO3
    session = AO3.Session(os.getenv("AO3_USERNAME"), os.getenv("AO3_PASSWORD"))
    session.refresh_auth_token()

    download_subscriptions(session, TARGET_DIR)

    # Schedule the main function to run again in 24 hours
    threading.Timer(60*60*24, main).start()


main()
