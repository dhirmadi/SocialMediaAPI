```markdown
# TanjaX API

This project is a Flask-based web API that retrieves random images from specified Dropbox folders and provides direct links to these images. The API uses Auth0 for authentication and authorization, ensuring that only authorized users can access the API.

## Features

- Authenticate with Auth0
- List and fetch random images from specified Dropbox folders
- Provide direct links to images
- Handle existing shared links and create new ones if necessary
- Cross-Origin Resource Sharing (CORS) enabled

## Prerequisites

- Python 3.x
- A Dropbox account and a Dropbox app
- Auth0 account

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/tanjax-api.git
   cd tanjax-api
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file in the root directory and add the following environment variables:**

   ```plaintext
   API_TITLE=Your API Title
   DROPBOX_TOKEN=your_dropbox_token
   DROPBOX_APP_KEY=your_dropbox_app_key
   DROPBOX_REFRESH_TOKEN=your_dropbox_refresh_token
   DROPBOX_FOLDER_PATH=/path/to/your/dropbox/folder
   DROPBOX_FOLDER_APPROVE=/path/to/approve/folder
   DROPBOX_FOLDER_DELETE=/path/to/delete/folder
   DROPBOX_FOLDER_REWORK=/path/to/rework/folder
   REACT_APP_AUTH0_DOMAIN=your-auth0-domain
   REACT_APP_AUTH0_CLIENT_ID=your-auth0-client-id
   REACT_APP_AUTH0_AUDIENCE=your-auth0-audience
   ```

## Configuration

### Dropbox

1. **Create a Dropbox app:**
   - Go to the [Dropbox App Console](https://www.dropbox.com/developers/apps).
   - Create a new app and get the `APP_KEY` and `APP_SECRET`.

2. **Generate a Refresh Token:**
   - Follow the Dropbox OAuth 2 guide to generate a refresh token.
   - Ensure the necessary permissions (scopes) are granted to access the files.

### Auth0

1. **Create an Auth0 Application:**
   - Go to the [Auth0 Dashboard](https://manage.auth0.com/).
   - Create a new Single Page Application.
   - Get the `DOMAIN`, `CLIENT_ID`, and `AUDIENCE`.

2. **Update Application Settings:**
   - Ensure your application is configured to use the created API.
   - Enable CORS for your application's URL.

## Running the Application

1. **Run the Flask API:**

   ```bash
   flask run
   ```

2. **Run the React Application:**

   ```bash
   cd react-app
   npm install
   npm start
   ```

   Open your web browser and navigate to `http://localhost:3000/`.

## Deployment

### PythonAnywhere

1. **Set environment variables on PythonAnywhere:**
   - Go to the "Web" tab on PythonAnywhere.
   - Find the "Environment Variables" section and set your environment variables.

2. **Restart your web app:**
   - Ensure your changes take effect by restarting the web app from the "Web" tab.

## Usage

- Authenticate using Auth0.
- Access the random image endpoint to get a direct link to a random image from Dropbox.
- The API will handle existing shared links or create new ones as needed.

## Endpoints

- **`GET /`**: Returns the API title.
- **`GET /image`**: Returns a random image URL from the specified Dropbox folder.

## Logging

- The API uses Python's built-in logging module to log important events and errors.

## Contributing

1. **Fork the repository**
2. **Create a new branch (`git checkout -b feature-branch`)**
3. **Commit your changes (`git commit -am 'Add new feature'`)**
4. **Push to the branch (`git push origin feature-branch`)**
5. **Create a new Pull Request**

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Dropbox API](https://www.dropbox.com/developers/documentation)
- [Auth0](https://auth0.com/)
- [PythonAnywhere](https://www.pythonanywhere.com/)
