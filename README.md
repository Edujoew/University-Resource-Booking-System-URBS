University Resource and Equipment booking system(UREBS)
## University-Resource-Booking-System-UREBS
The University Resource and Equipment Booking System is a straightforward website designed to fix the headache of getting access to essential campus gear and rooms. Every student knows the frustration of needing a specific piece of lab equipment or a quiet group study room, only to find the sign-up


## main.html

{% load static %}	 Essential Django tag that enables the use of the {% static '...' %} template tag to link to non-dynamic files like CSS and JavaScript (e.gcustom styles.css).
{% block title %}...{% endblock title %}	 Defines a reusable block for the page title. Child templates will override this to set a unique title for each page, which is crucial for SEO and user navigation history.

Bootstrap CDN	Why CDN? Using a Content Delivery Network for Bootstrap CSS and JS ensures fast loading times and avoids the need to host the files locally. The Bootstrap 5 classes are used throughout for responsive design.

{% if user.is_authenticated %}	 This conditional template logic is fundamental to the user experience. It checks the user's login status and displays dynamic content: showing "Hello, [User]" and "Logout" links when logged in, and "Register" / "Login" links when logged out.

{% if user.is_staff %}	 Implements role-based visibility (a security measure). Only users flagged as staff/admin see the "Pending Review" link, restricting administrative access in the navigation.

{% block content %}...{% endblock  %}	 This is the main content injection point. Every specific page template (home.html, login.html, booking_form.html) must use this block to inject its unique content while keeping the consistent header and footer.

## Home.html

Contextual Welcome	-Why Conditional? The text content adapts based on the user's authentication status. This personalization provides immediate, relevant directions: encouraging new users to log in, and reminding returning users where to find their existing bookings.

## hompage

![alt text](image.png)

Button Links	Purpose: The links use Django's {% url '...' %} tag, ensuring that navigation to the login and register pages works even if the URL structure changes later.

## login.html

{% load crispy_forms_tags %}	 Imports the tag needed to format Django forms beautifully using the Crispy Forms library and the Bootstrap 5 template pack.
{% csrf_token %}	 Mandatory security token. This hidden field prevents Cross-Site Request Forgery (CSRF) attacks, ensuring that the form submission is valid and originated from our application.

## login page

![alt text](image-1.png)

## logged_out

Template Path	Why templates/registration/logged_out.html? Similar to login.html, this is the default template path expected by Django's built-in LogoutView after a successful logout action.

## logout button

![alt text](image.png)

alert alert-info	Purpose: Uses Bootstrap components (alerts) to provide a clear, user-friendly, and styled message confirming the logout action.

## register.html

{% load crispy_forms_tags %}	Purpose: Ensures that when the custom registration view eventually passes a form object (like a UserCreationForm), we can use the `btn btn-primary	Purpose: Uses the primary brand color for the Register button, defining it as the main call-to-action on this page according to Bootstrap styling conventions.

## registartion page

![alt text](image-1.png)

## form.py

class BookingRequestForm(forms.ModelForm)	Purpose: It inherits from Django's forms.ModelForm. This choice is made because the form is directly tied to the database model (BookingRequest). ModelForm automatically handles field creation, validation, and saving data back to the model.

class Meta:	Purpose: This inner class provides metadata to the ModelForm builder, specifying exactly how the form should be created.

model = BookingRequest	Purpose: Explicitly tells the form builder to base the form fields on the fields defined in the BookingRequest database model.

fields = ['resource', 'start_time', 'end_time']	Purpose: This list specifies the three fields the user is allowed to input and change. Fields like user, status, and request_date are intentionally excluded because they are handled automatically by the system logic (in the view or model default), not by the user.

widgets = {...}	Purpose: Customizes the HTML input type for the date and time fields. Setting the type to datetime-local instructs modern web browsers to display a calendar and clock interface (a date/time picker), significantly improving the user experience and reducing errors compared to a plain text box.