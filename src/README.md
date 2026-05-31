# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View active announcements in the homepage banner
- Manage announcements (create, update, delete) when signed in as a teacher

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| GET    | `/announcements/active`                                           | Get the currently active announcement for the banner                |
| GET    | `/announcements?manager_username={username}`                      | List all announcements (signed-in users only)                      |
| POST   | `/announcements?manager_username={username}`                      | Create a new announcement (signed-in users only)                   |
| PUT    | `/announcements/{announcement_id}?manager_username={username}`    | Update an existing announcement (signed-in users only)             |
| DELETE | `/announcements/{announcement_id}?manager_username={username}`    | Delete an announcement (signed-in users only)                      |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

The application stores data in MongoDB and initializes sample records (activities, teachers, and an example announcement) when collections are empty.
