from django.http import HttpResponse
from django.shortcuts import render


# Home page view for the booking app
def home(request):
	"""Return a simple page for the booking home route."""
	return HttpResponse("<h1>University Resource Booking System</h1><p>Welcome to the  URBS app!</p>")
