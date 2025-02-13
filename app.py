import AO3
import os
import signal
from dotenv import load_dotenv
from colorama import Fore, Style
from ebooklib import epub

load_dotenv()

BOOK_FORMAT = "EPUB"
TARGET_DIR = os.getenv("BOOKS_DIRECTORY") or os.path.join(os.path.curdir, "books")

def handle_exit_signals(signum, frame):
    print(f"{Fore.MAGENTA}{Style.BRIGHT}Exiting...{Style.RESET_ALL}")
    exit(signum)

signal.signal(signal.SIGINT, handle_exit_signals)
signal.signal(signal.SIGTERM, handle_exit_signals)

def safe_filename(filename: str) -> str:
    critical_chars = ["<", ">", ":", "\"", "/", "\\", "|", "?", "*"]
    for char in critical_chars:
        filename = filename.replace(char, "")
    return filename

def download_subscriptions(session: AO3.Session, target_dir: str):
    # Create target directory if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    i = 0

    for subscription in session.get_work_subscriptions():

        try:
            work = AO3.Work(subscription.id, session=session, load_chapters=False)
            title = f"{Fore.CYAN}{subscription.authors[0].username} - {subscription.title}".ljust(80)

            # Skip the download if the work is restricted
            if work.restricted:
                print(f"{title}\t{Fore.YELLOW}SKIPPED - RESTRICTED{Style.RESET_ALL}")
                continue

            filename = f"{safe_filename(subscription.authors[0].username)} - {safe_filename(subscription.title)}.{BOOK_FORMAT.lower()}"
            filename_tmp = filename + ".tmp"

            # Check if the file already exists in the EBOOKS_PATH with the same number of chapters
            if not work_has_changed(work, os.path.join(target_dir, filename)):
                print(f"{title}\t{Fore.GREEN}SKIPPED - UP TO DATE{Style.RESET_ALL}")
                continue

            # Remove any remains of TMP files and download the work
            if os.path.exists(os.path.join(target_dir, filename_tmp)):
                os.remove(os.path.join(target_dir, filename_tmp))
            work.download_to_file(os.path.join(target_dir, filename_tmp), BOOK_FORMAT)
            
            # If the file is empty, download failed
            if os.path.getsize(os.path.join(target_dir, filename_tmp)) == 0:
                print(f"{title}\t{Fore.RED}FAILED - EMPTY FILE{Style.RESET_ALL}")
                os.remove(os.path.join(target_dir, filename_tmp))
                continue
            
            # If the file is not empty, remove old file and rename the new file accordingly
            if os.path.exists(os.path.join(target_dir, filename)):
                os.remove(os.path.join(target_dir, filename))
            os.rename(os.path.join(target_dir, filename_tmp), os.path.join(target_dir, filename))
            print(f"{title}\t{Fore.GREEN}DOWNLOADED{Style.RESET_ALL}")

        except Exception as e:
            print(f"{title}\t{Fore.RED}FAILED\t\t{Style.DIM}{e.args[0]}{Style.RESET_ALL}")

    print(f"{Fore.MAGENTA}{Style.BRIGHT}Download complete!{Style.RESET_ALL}")


def work_has_changed(work: AO3.Work, filepath: str) -> bool:
    try:
        # Test if there is even a local file to compare to
        if not os.path.exists(filepath):
            return True
        
        # Test if the file changed date is older than the work's last updated date
        if os.path.getmtime(filepath) < work.date_updated.timestamp():
            return True
        
        # Test if the file has less chapters than the work
        existing_work = epub.read_epub(filepath)
        return work.nchapters > len(existing_work.spine) - 3 # Subtract 3 to account for the title page, table of contents, and cover page
    
    except Exception as e:
        print(f"{Fore.RED}Error reading existing file: {filepath}\t\t{Style.DIM}{e.args[0]}{Style.RESET_ALL}")
        return False

# Main function
def main():
    # Login to AO3
    session = AO3.Session(os.getenv("AO3_USERNAME"), os.getenv("AO3_PASSWORD"))
    session.refresh_auth_token()

    download_subscriptions(session, TARGET_DIR)

main()
