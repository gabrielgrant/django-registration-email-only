
class SetTestCookieMiddleware(object):
	""" Set the test cookie on every page for non-logged-in users
	
	    This allows you to use a quick login forms outside of the
	    django.contrib.auth.views.login view, the cookie will be
	    deleted once you login.
	    
	    from http://djangosnippets.org/snippets/684/
	"""
	def process_request(self, request):
		if not request.user.is_authenticated():
			request.session.set_test_cookie()
