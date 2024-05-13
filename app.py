import AO3
import os
import threading
from dotenv import load_dotenv
from colorama import Fore, Style
from slugify import slugify
from ebooklib import epub
from datetime import datetime, timedelta

BOOK_FORMAT = "EPUB"
TARGET_DIR = os.path.join(os.path.curdir, "books")
SCHEDULE_FILE = "schedule.txt"
SCHEDULE = 60*60*24 # 24 hours in seconds


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

            filename = f"{subscription.authors[0].username}_{slugify(subscription.title)}.{BOOK_FORMAT.lower()}"
            filename_tmp = filename + ".tmp"

            # Check if the file already exists in the EBOKS_PATH with the same number of chapters
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

def check_and_set_timer() -> bool:

    # Check if the next scheduled run (in schedule.txt) is in the past, run it immediately
    # If the file does not exist, run the main function immediately and create the next scheduled run
    # If the scheduled run is in the future, wait until the scheduled time to run the main function
    if not os.path.exists(SCHEDULE_FILE):
        set_next_run(SCHEDULE)
        return True

    nextRun = None

    with open(SCHEDULE_FILE, "r") as file:
        nextRun = float(file.read())

    if nextRun < datetime.now().timestamp():
        set_next_run(SCHEDULE)
        return True
    
    timerInSeconds = nextRun - datetime.now().timestamp()
    set_next_run(timerInSeconds)
    return False

    

def set_next_run(timeInSeconds: int):
    # Print the Date and Time of the next run
    # Display in the format "YYYY-MM-DD HH:MM:SS"
    # Get current time in seconds and add the timerInSeconds

    now = datetime.now()
    nextRun = now + timedelta(seconds=timeInSeconds)

    # Write the timestamp of the next run to the schedule.txt file
    with open(SCHEDULE_FILE, "w") as file:
        file.write(str(nextRun.timestamp()))

    print(f"{Fore.MAGENTA}{Style.BRIGHT}Next run: {Style.RESET_ALL}{nextRun.strftime('%Y-%m-%d %H:%M:%S')} (UTC)\n\n")

    # Schedule the main function to run again after the timeInSeconds
    threading.Timer(timeInSeconds, main).start()

# Main function
def main():
    load_dotenv()

    runNow: bool = check_and_set_timer()

    if (not runNow):
        return

    # Login to AO3
    session = AO3.Session(os.getenv("AO3_USERNAME"), os.getenv("AO3_PASSWORD"))
    session.refresh_auth_token()

    download_subscriptions(session, TARGET_DIR)

main()
