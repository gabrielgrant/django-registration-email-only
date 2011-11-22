import uuid
from base64 import b16encode, b16decode, b32encode, b32decode

from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.template.loader import render_to_string

import pyDes

from simple_import import import_item

def create_user_and_password(request, email):
	create_username = get_username_creator()
	username = create_username(request, email)
	password = uuid.uuid4().hex
	user = User.objects.create_user(username, email, password)
	return user, password

def default_create_username(request, email):
	""" generate and set a unique username
	
		from http://www.xairon.net/2011/05/django-email-only-authentication/
	"""
	username = uuid.uuid4().hex[:30]
	# ensure it is, in fact, unique
	# (and yes, there is a race condition -- good luck triggering it :)
	try:
		while True:
			User.objects.get(username=username)
			username = uuid.uuid4().hex[:30]
	except User.DoesNotExist:
		pass
	return username

def get_username_creator():
	username_creator = getattr(settings, 'REGISTRATION_EMAIL_ONLY_USERNAME_CREATOR', None)
	if username_creator is None:
		create_username = default_create_username
	elif isinstance(username_creator, basestring):
		try:
			create_username = import_item(username_creator)
		except ImportError:
			raise ImproperlyConfigured(
			'REGISTRATION_EMAIL_ONLY_USERNAME_CREATOR setting is invalid\n\n'
			'The value you provided (%s) cannot be imported' % username_creator
		)
	elif callable(username_creator):
		create_username = username_creator
	else:
		raise ImproperlyConfigured(
			'REGISTRATION_EMAIL_ONLY_USERNAME_CREATOR setting is invalid\n\n'
			'If specified, REGISTRATION_EMAIL_ONLY_USERNAME_CREATOR must be\n'
			'either a callable which returns a username or a string\n'
			'containing the import-able path to such a callable.'
		)
	return create_username

def send_activation_email(user, site=None, activation_key=None):
	"""
	Send an activation email to the provided User.
	
	The activation email will make use of two templates:

	``registration/activation_email_subject.txt``
		This template will be used for the subject line of the
		email. Because it is used as the subject line of an email,
		this template's output **must** be only a single line of
		text; output longer than one line will be forcibly joined
		into only a single line.

	``registration/activation_email.txt``
		This template will be used for the body of the email.

	These templates will each receive the following context
	variables:

	``activation_key``
		The activation key for the new account.
		
		This function is adapted from django-registration's method
		of the same name.

		``site``
			An object representing the site on which the user
			registered; depending on whether ``django.contrib.sites``
			is installed, this will be an instance of either
			``django.contrib.sites.models.Site`` (if the sites
			application is installed) or
			``django.contrib.sites.models.RequestSite`` (if
			not). Consult the documentation for the Django sites
			framework for details regarding these objects' interfaces.
	"""
	# generate activation key
	if not activation_key:
		activation_key = user_to_activation_key(user)
	ctx_dict = {'activation_key': activation_key,
				'site': site}
	subject = render_to_string('registration/activation_email_subject.txt',
							   ctx_dict)
	# Email subject *must not* contain newlines
	subject = ''.join(subject.splitlines())
	
	message = render_to_string('registration/activation_email.txt',
							   ctx_dict)
	
	user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)

def user_to_activation_key(user):
	uid = userid_to_uid(user.id)
	token = token_generator.make_token(user)
	return '-'.join([uid, token])

def activation_key_to_user(activation_key):
	try:
		uid, token = activation_key.split('-', 1)
	except ValueError:
		return None
	try:
		user = User.objects.get(id=uid_to_userid(uid))
	except User.DoesNotExist:
		return None
	if not token_generator.check_token(user, token):
		return None
	return user

if len(settings.SECRET_KEY) < 8:
	raise ImproperlyConfigured(
		'SECRET_KEY setting must be at least 8 characters long')
_d = pyDes.triple_des(b16encode(settings.SECRET_KEY)[:16])

def userid_to_uid(userid):
	""" b32 encoding requires mod-4 length strings to avoid padding """
	encrypted_uid = _d.encrypt(str(userid), ' ')  # use space as padding
	uid = b32encode(encrypted_uid)
	uid = uid.replace('=', '0')  # replace pad chars with '0'
	return uid
def uid_to_userid(uid):
	uid = uid.replace('0', '=')  # fix pad chars
	encrypted_uid = b32decode(uid)
	userid = _d.decrypt(encrypted_uid, ' ')
	return int(userid)
	
