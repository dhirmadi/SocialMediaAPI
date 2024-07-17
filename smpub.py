from pymongo import MongoClient
import os
import dropbox
import random
from dotenv import load_dotenv
import logging
from instagrapi import Client
import requests

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)  # Set the logging level as needed
logger = logging.getLogger(__name__)
insta_username = os.getenv('INSTAGRAM_NAME')
insta_password = os.getenv('INSTAGRAM_PASSWORD')

def get_mongodb_connection():
    try:
        mongo_client = MongoClient(os.getenv('MONGODB_URI'))
        db = mongo_client[os.getenv('MONGODB_DATABASE')]
        collection = db[os.getenv('MONGODB_COLLECTION')]
        return collection
    except Exception as e:
        logger.error(f'MongoDB connection error: {e}')
        raise

def get_dropbox_connection():
    try:
        db_app = os.getenv('DROPBOX_APP_KEY')
        db_refresh = os.getenv('DROPBOX_REFRESH_TOKEN')
        dbx = dropbox.Dropbox(oauth2_refresh_token=db_refresh, app_key=db_app)
        return dbx
    except Exception as e:
        logger.error(f'Dropbox connection error: {e}')
        raise

def select_random_nsfw_image(collection, dbx):
    try:
        nsfw_images = collection.find({"nsfw": False})
        nsfw_image_data = [(image["imageID"], image.get("hashtags", []), image.get("description", ""), image.get("tagline", "")) for image in nsfw_images]
        nsfw_image_ids = [data[0] for data in nsfw_image_data]

        folder_path = os.getenv('DROPBOX_FOLDER_PUBLISH', '/path/defaultfolder')
        files = dbx.files_list_folder(folder_path).entries

        filtered_files = [file for file in files if file.id in nsfw_image_ids]

        if filtered_files:
            random_image = random.choice(filtered_files)
            unique_id = random_image.id
            temp_link = dbx.files_get_temporary_link(random_image.id).link
            logger.info(f"Randomly selected image's uniqueID: {unique_id}")
            logger.info(f"Temporary download link: {temp_link}")
            
            for data in nsfw_image_data:
                if data[0] == unique_id:
                    image_description = data[2]
                    image_hashtags = ' '.join(data[1])
                    caption = f"{image_description}\n\n{image_hashtags}"
                    image_url = temp_link
                    publish_to_instagram(insta_username, insta_password, image_url, caption)

            archive(dbx, unique_id)
                    
        else:
            logger.info("No NSFW images found in the specified folder.")
    
    except Exception as e:
        logger.error(f'Error while selecting random NSFW image: {e}')
    

def archive(dbx, unique_id):
    try:
        publish_folder = os.getenv('DROPBOX_FOLDER_PUBLISH', '/path/defaultfolder')
        archive_folder = os.path.join(publish_folder, 'archive')  # Assuming 'archive' folder is within 'publish' folder

        # Check if the archive folder exists or create it if not
        if not any(folder.name == 'archive' for folder in dbx.files_list_folder(publish_folder).entries):
            dbx.files_create_folder(archive_folder)

        # Move the file with uniqueID from publish folder to archive folder
        file_to_archive = [file for file in dbx.files_list_folder(publish_folder).entries if file.id == unique_id][0]
        dbx.files_move(file_to_archive.path_lower, f'{archive_folder}/{file_to_archive.name}')

        logger.info(f"File with uniqueID {unique_id} has been archived.")
        
    except Exception as e:
        logger.error(f'Error archiving file with uniqueID {unique_id}: {e}')

def publish_to_instagram(username, password, image_url, caption):
    try:
        # Login to Instagram using the provided username and password
        client = Client()
        client.login(username, password)
        
        # Download the image from the provided URL
        image_path = "temp_image.jpg"
        response = requests.get(image_url)
        
        if response.status_code == 200:
            with open(image_path, 'wb') as file:
                file.write(response.content)

            # Publish the image with caption to Instagram
            media = client.photo_upload(image_path, caption=caption)
            client.media_like(media.pk)
            # client.media_comment(media.pk, caption) avoid double posting.
            
            # Logout from Instagram
            client.logout()
            logger.info("Image published successfully to Instagram!")
        else:
            logger.error("Error downloading image from the provided URL.")
    
    except Exception as e:
        logger.error(f"Error publishing image to Instagram: {e}")

if __name__ == "__main__":
    try:
        collection = get_mongodb_connection()
        dbx = get_dropbox_connection()
        select_random_nsfw_image(collection, dbx)
    except Exception as e:
        logger.error(f'Error: {e}')
