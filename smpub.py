from pymongo import MongoClient
import os
import dropbox
import random
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)  # Set the logging level as needed
logger = logging.getLogger(__name__)

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
            random_image_metadata = dbx.files_get_metadata(random_image.id)
            unique_id = random_image_metadata.id
            temp_link = dbx.files_get_temporary_link(random_image.id).link
            logger.info(f"Randomly selected image's uniqueID: {unique_id}")
            logger.info(f"Temporary download link: {temp_link}")
            
            for data in nsfw_image_data:
                if data[0] == unique_id:
                    logger.info(f"Image Description: {data[2]}")
                    logger.info(f"Hashtags: {data[1]}")
                    logger.info(f"Tagline: {data[3]}")

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

if __name__ == "__main__":
    try:
        collection = get_mongodb_connection()
        dbx = get_dropbox_connection()
        select_random_nsfw_image(collection, dbx)
    except Exception as e:
        logger.error(f'Error: {e}')