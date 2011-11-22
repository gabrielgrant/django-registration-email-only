from django.test import TestCase
from django.test.client import RequestFactory
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core import mail
from django.core.urlresolvers import reverse

from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware

import registration.signals

from registration_email_only.backends import EmailOnlySignupBackend
from registration_email_only.utils import *
from registration_email_only.forms import *

class RegisterTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()
		self.req = self.factory.get('/accouts/register')
		SessionMiddleware().process_request(self.req)
		self.b = EmailOnlySignupBackend()
	def test_register_no_email(self):
		with self.assertRaises(ValueError):
			self.b.register(self.req)
	def test_colliding_username_hashes(self):
		pass
		# mock out hash function
		def silly_username_creation(request, user):
			user.username = 'user'
			return user
		#with self.setings(REGISTRATION_EMAIL_ONLY_USERNAME_CREATOR=
	def test_unusable_password(self):
		u = self.b.register(self.req, email='this@that.com')
		self.assertFalse(u.has_usable_password())
	def test_signal_sent(self):
		signal_user = set()
		def user_registered_signal_handler(sender, request, user, **kwargs):
			signal_user.add(user)
		registration.signals.user_registered.connect(
			user_registered_signal_handler)
		u = self.b.register(self.req, email='this@that.com')
		self.assertIn(u, signal_user)
	def test_logged_in(self):
		signal_user = set()
		def login_signal_handler(sender, request, user, **kwargs):
			signal_user.add(user)
		user_logged_in.connect(login_signal_handler)
		u = self.b.register(self.req, email='this@that.com')
		self.assertIn(u, signal_user)
	def test_email_sent(self):
		self.b.register(self.req, email='this@that.com')
		self.assertEqual(len(mail.outbox), 1)

class GetUsernameCreatorTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()
		self.req = self.factory.get('/accouts/register')
		SessionMiddleware().process_request(self.req)
	def test_default_create_username(self):
		req1 = self.req
		req2 = self.factory.get('/accouts/register')
		username = default_create_username(req1, 'this@that.com')
		self.assertNotEqual(username, default_create_username(req2, 'this@that.com'))
		self.assertEqual(len(username), 30)
	def test_no_username_creator(self):
		self.assertEqual(get_username_creator(), default_create_username)
	def test_bad_username_creator_string(self):
		#TODO convert this to use the settings context manager in Django 1.4:
		# with self.settings(REGISTRATION_EMAIL_ONLY_USERNAME_CREATOR='not.a.module'):
		old = getattr(settings, 'REGISTRATION_EMAIL_ONLY_USERNAME_CREATOR', None)
		try:
			settings.REGISTRATION_EMAIL_ONLY_USERNAME_CREATOR = 'not.a.module'
			with self.assertRaises(ImproperlyConfigured):
				get_username_creator()
		finally:
			if old is None:
				del settings.REGISTRATION_EMAIL_ONLY_USERNAME_CREATOR
			else:
				settings.REGISTRATION_EMAIL_ONLY_USERNAME_CREATOR = old
	def test_bad_type(self):
		old = getattr(settings, 'REGISTRATION_EMAIL_ONLY_USERNAME_CREATOR', None)
		try:
			settings.REGISTRATION_EMAIL_ONLY_USERNAME_CREATOR = object()
			with self.assertRaises(ImproperlyConfigured):
				get_username_creator()
		finally:
			if old is None:
				del settings.REGISTRATION_EMAIL_ONLY_USERNAME_CREATOR
			else:
				settings.REGISTRATION_EMAIL_ONLY_USERNAME_CREATOR = old
		
	def test_username_creator_unset(self):
		pass

class UtilsTests(TestCase):
	def test_uid_userid_conversion_even_digits(self):
		userid = 23
		cycled_userid = uid_to_userid(userid_to_uid(userid))
		self.assertEqual(userid, cycled_userid)
	def test_uid_userid_conversion_odd_digits(self):
		userid = 3
		cycled_userid = uid_to_userid(userid_to_uid(userid))
		self.assertEqual(userid, cycled_userid)
	def test_activation_key_cycle(self):
		u = User.objects.create_user('username', 'em@il.com')
		activation_key = user_to_activation_key(u)
		retrieved_user = activation_key_to_user(activation_key)
		self.assertEqual(u, retrieved_user)

class ActivateTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()
		self.req = self.factory.get('/accouts/register')
		SessionMiddleware().process_request(self.req)
		self.b = EmailOnlySignupBackend()
		self.u = self.b.register(self.req, email='this@that.com')
		self.activation_key = user_to_activation_key(self.u)
	def test_activate(self):
		self.assertFalse(self.u.has_usable_password())
		u = self.b.activate(self.req, self.activation_key, 'username', 'pass')
		u = User.objects.get(username='username')
		self.assertTrue(u.has_usable_password())

class ViewTests(TestCase):
	urls = 'registration_email_only.urls'
	def test_full_flow(self):
		url = reverse('registration_register')
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertIsInstance(response.context['form'], RegistrationForm)
		response = self.client.post(url, data={'email':'em@il.com'}, follow=True)
		self.assertEqual(response.status_code, 200)
		# is the user logged in?
		self.assertIsInstance(response.context['user'], User)
		# did the email get sent?
		self.assertEqual(len(mail.outbox), 1)
		# does the email contain the activation_key?
		activation_key = user_to_activation_key(response.context['user'])
		self.assertIn(activation_key, mail.outbox[0].body)
		# log out
		self.client.logout()
		# do activation
		url = reverse('registration_activate', kwargs={'activation_key': activation_key})
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertIsInstance(response.context['form'], ActivationForm)
		self.assertIsInstance(response.context['user'], AnonymousUser)
		response = self.client.post(url,
			 data={'username':'username', 'password':'pass'}, follow=True)
		self.assertEqual(response.status_code, 200)
		# is user setup?
		self.assertTrue(User.objects.get(username='username').check_password('pass'))
		# is the user logged in?
		self.assertEqual(response.context['user'].username, 'username')
		
		
