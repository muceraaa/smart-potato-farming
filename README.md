# SmartPotatoFarming

## Description
Smart Potato Farming is a digital platform designed for small-scale farmers to detect late blight in potato crops early through AI-powered image analysis. Farmers can upload a photo of a potato leaf to instantly check for infection. The platform also includes a chatbot assistant that offers real-time guidance, farming tips, and answers to common questions—making expert help accessible anytime.

## Technologies used
SmartPotatoFarming is built using `Python` with `Django` framework for the backend and `HTML` and `CSS` for the frontend.

### Third-party Packages used
- `Django-allauth` - for the authentication system
- `python-dotenv` - to secure my environmental variables within the `.env` file
- `Pillow` - to handle images during production

## Getting Started
### Prerequisites
To test SmartPotatoFarming locally, you will need to have `Python` installed on your machine. You can download it [here](https://www.python.org/downloads/).

### Run the application
You will need to do a couple of things before spinning up the server:
 

- Run the inbuilt django server using `python manage.py runserver`
- You can now access the application on `http://127.0.0.1:8000/`

### Django Admin
Django comes with an inbuilt admin panel that can be accessed on `http://127.0.0.1:8000/admin`, but first you will need a superuser.
#### Creating a Superuser
To create a superuser, on your terminal, run `python manage.py createsuperuser` and follow the prompts given.

_Note :  The password fields will appear blank as you are typing them in. Don't panic, it's to protect your password from prying eyes_ 👀
