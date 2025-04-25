# Bookmarker

A Flask-based web application for managing bookmarks across different browsers.

## Features

- User authentication (login, register, logout)
- Bookmark management (add, view, delete)
- Browser detection
- RESTful API endpoints

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run the application:
   ```
   python run.py
   ```

## API Documentation

The application provides the following API endpoints:

### Authentication
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `POST /api/register` - Register new user

### Bookmarks
- `GET /api/bookmarks` - Get all bookmarks
- `POST /api/bookmarks` - Add new bookmark
- `DELETE /api/bookmarks/<id>` - Delete bookmark

### Browsers
- `GET /api/browsers` - Get detected browsers

For detailed API documentation, visit `/api/docs` endpoint.

## Security Notes

- Change the `SECRET_KEY` in production
- Use HTTPS in production
- Implement proper password hashing
- Validate all user inputs