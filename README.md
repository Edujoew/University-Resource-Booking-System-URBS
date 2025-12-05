University Resource and Equipment booking system(UREBS)
## University-Resource-Booking-System-UREBS


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
![alt text](homepage.png)


Button Links	Purpose: The links use Django's {% url '...' %} tag, ensuring that navigation to the login and register pages works even if the URL structure changes later.

## login.html

{% load crispy_forms_tags %}	 Imports the tag needed to format Django forms beautifully using the Crispy Forms library and the Bootstrap 5 template pack.
{% csrf_token %}	 Mandatory security token. This hidden field prevents Cross-Site Request Forgery (CSRF) attacks, ensuring that the form submission is valid and originated from our application.
## landing page
"jumbotron text-center bg-light p-5 rounded shadow-sm">	Purpose: Uses the Bootstrap framework to create a large, prominent block (jumbotron styling) that centers the content, applies a light background (bg-light), adds padding (p-5), and gives it a slightly raised visual effect (rounded shadow-sm)
![alt text](<landing page.png>)

## updated landing page
![alt text](<landing pg.png>)

## login page
![alt text](<login page.png>)


## logged_out

Template Path	Why templates/registration/logged_out.html? Similar to login.html, this is the default template path expected by Django's built-in LogoutView after a successful logout action.

## logout button
![alt text](<logout button.png>)


alert alert-info	Purpose: Uses Bootstrap components (alerts) to provide a clear, user-friendly, and styled message confirming the logout action.

## register.html

{% load crispy_forms_tags %}	Purpose: Ensures that when the custom registration view eventually passes a form object (like a UserCreationForm), we can use the `btn btn-primary	Purpose: Uses the primary brand color for the Register button, defining it as the main call-to-action on this page according to Bootstrap styling conventions.

## registartion page
![alt text](<registration page.png>)


## form.py

class BookingRequestForm(forms.ModelForm)	Purpose: It inherits from Django's forms.ModelForm. This choice is made because the form is directly tied to the database model (BookingRequest). ModelForm automatically handles field creation, validation, and saving data back to the model.

class Meta:	Purpose: This inner class provides metadata to the ModelForm builder, specifying exactly how the form should be created.

model = BookingRequest	Purpose: Explicitly tells the form builder to base the form fields on the fields defined in the BookingRequest database model.

fields = ['resource', 'start_time', 'end_time']	Purpose: This list specifies the three fields the user is allowed to input and change. Fields like user, status, and request_date are intentionally excluded because they are handled automatically by the system logic (in the view or model default), not by the user.

widgets = {...}	Purpose: Customizes the HTML input type for the date and time fields. Setting the type to datetime-local instructs modern web browsers to display a calendar and clock interface (a date/time picker), significantly improving the user experience and reducing errors compared to a plain text box.

## models.py
from django.contrib.auth import get_user_model	
Imports the standard way to retrieve the active user model. This ensures compatibility whether the project uses the default Django User model or a custom one defined in settings.py.

RESOURCE_CHOICES	 Defines a set of predefined constants for the type field. This prevents data inconsistency and makes it easier to filter resources in the backend (e.g., filter only 'EQUIP'ment).

name = models.CharField(..., unique=True) Stores the common name of the resource. unique=True is crucial for data integrity, ensuring no two resources have the same name (e.g., only one "Lecture Hall A").

type = models.CharField(..., choices=RESOURCE_CHOICES)	 Categorizes the resource based on the defined choices. This is used for easy filtering and organization on the frontend.

is_available = models.BooleanField(default=True)	 A control field allowing administrators to temporarily disable a resource (e.g., if it's broken or undergoing maintenance) without deleting its record.

__str__ method	 Defines the human-readable representation of a resource object (e.g., "Room 33 (Room/Lecture Hall)"). This is vital for debugging and clarity in the Django Admin interface.

## booking form
!![alt text](<submit booking.png>)

## MPESA API
![alt text](<stk push.png>)

## booking confilict validation
Basic Sanity	Checks if start_time is less than end_time.	Prevents illogical bookings and potential database errors.

OCCUPIED_STATUSES	Defines ['APPROVED', 'PENDING'] as statuses that block new bookings.	Ensures resources reserved by users (even if pending payment/review) cannot be double-booked.

Database Query (A & B)	Filters by the requested resource and the OCCUPIED_STATUSES.	Narrows the search to relevant existing reservations.

Overlap Condition (C)	start_time__lt=end_time AND end_time__gt=start_time	This is the standard, most reliable method for checking if two time intervals conflict.

forms.ValidationError	If conflicting_bookings.exists() is True, the process stops, and the error message is displayed to the user.	Enforces the core business rule and provides user feedback.

# 📚 Student Booking Dashboard (Issue #7)

View (`views.py`): Uses `LoginRequiredMixin` + `ListView` for access control.

Filtering:`get_queryset` filters by current user: `BookingRequest.objects.filter(user=self.request.user)`.

 Context: `get_context_data` separates bookings into `pending_bookings` and `past_bookings`.

 URL: Mapped at `path('my_bookings_dashboard/', ...)` using `name='my_bookings_dashboard'`.

 Template: Renders data in `my_bookings_dashboard.html`, utilizing a partial table.

 Visuals: Uses color-coded Bootstrap badges (e.g., `bg-warning` for PENDING) for status.

 ![alt text](<booking dashboard.png>)
 