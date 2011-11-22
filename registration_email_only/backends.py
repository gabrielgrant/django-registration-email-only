import uuid

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.sites.models import RequestSite
from django.contrib.sites.models import Site

from registration.backends.default import DefaultBackend
import registration.signals

from .utils import create_user_and_password,  send_activation_email, activation_key_to_user
from .forms import RegistrationForm, ActivationForm

class EmailOnlySignupBackend(DefaultBackend):
	""" Two-step flow, requiring only email at first
	
	    1. User signs up with only an email.
	    2. a) User is logged in and can start using the site
	       b) Email is sent to the User with an activation link
	    3. User clicks activation link
	    4. User completes form with username and password.
	    5. Account is active
	    
	    While there are more steps than a traditional signup flow,
	    the advantage is that it is extremely easy for users to get
	    started. Once they've started using the site, they have more
	    of an incentive to complete the rest of the registration.
	    
	    Registration can be temporarily closed by adding the setting
	    ``REGISTRATION_OPEN`` and setting it to False.
	
	"""
	def register(self, request, email=None):
		""" Create user; log in; send activation email
		
		Here's how it works:
		 - Create a user with a random password
		 - log them in (requires a password to be set)
		 - sets the password to be unusable
		 - send an email to complete registration
		
		This function assumes that the form has already valided,
		meaning the email has already been verified as unique.
		"""
		if email is None:
			raise ValueError('email cannot be None')
		user, password = create_user_and_password(request, email)
		# log in
		auth_user = authenticate(username=user.username, password=password)
		assert auth_user == user
		login(request, auth_user)
		user.set_unusable_password()
		user.save()
		# get site
		if Site._meta.installed:
			site = Site.objects.get_current()
		else:
			site = RequestSite(request)
		send_activation_email(user, site)
		registration.signals.user_registered.send(
			sender=self.__class__,
			user=user,
			request=request
		)
		return user
	def activate(self, request, activation_key, username, password):
		user = activation_key_to_user(activation_key)
		if not user:
			return False
		user.username = username
		user.set_password(password)
		user.save()
		auth_user = authenticate(username=username, password=password)
		login(request, auth_user)
		return user
	def get_form_class(self, request):
		return RegistrationForm
	def get_activation_form_class(self, request):
		return ActivationForm

	
