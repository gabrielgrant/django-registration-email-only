
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.http import int_to_base36
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site

class RegistrationForm(forms.Form):
    email = forms.EmailField(label=_("E-mail"), max_length=75)

    def clean_email(self):
        """ Ensure that the supplied email address is unique. """
        if User.objects.filter(email__iexact=self.cleaned_data['email']).count():
            raise forms.ValidationError(_(u'This email address is already in use. Please supply a different email address.'))
        return self.cleaned_data['email']


class ActivationForm(forms.Form):
    username = forms.RegexField(label=_("Username"), max_length=30, regex=r'^\w+$',
        help_text = _("Required. 30 characters or fewer. Alphanumeric characters only (letters, digits and underscores)."),
        error_message = _("This value must contain only letters, numbers and underscores."))
    password = forms.CharField(widget=forms.PasswordInput(render_value=False),
                                label=_("Password"))

    def clean_username(self):
        """ Ensure that the supplied username is unique. """
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(_("A user with that username already exists."))
