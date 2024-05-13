# AO3 Subscription Downloader

This is a simple Python script that downloads all subscribed works in your [Archive of Our Own](https://archiveofourown.org/) account.  

This script is intended to be run in a Docker container using `docker-compose`, but can also be run directly on your machine.

## Usage

Ensure that you have `Docker` and `docker-compose` installed on your machine.

1. Clone this repository and navigate into the cloned directory.
2. Create a file named `.env` in the same directory as `app.py` with the following content:
    ```env
    AO3_USERNAME="<your_username>"
    AO3_PASSWORD="<your_password>"
    ```
    Replace `<your_username>` and `<your_password>` with your AO3 username and password.

3. In the `docker-compose.yml` file, change the `volumes` section to map the `downloads` directory to a directory on your host machine where you want the downloaded works to be saved. 
    ```yaml
    volumes:
      - type: bind
        source: ~/<your_ebooks_directory>
        target: /app/books
    ```
    Replace `~/<your_ebooks_directory>` with the path to the directory where you want the downloaded works to be saved.

4. Run the following command to start the Docker container:
    ```bash
    docker-compose up -d
    ```