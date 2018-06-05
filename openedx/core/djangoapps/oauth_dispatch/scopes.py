"""
Custom Django OAuth Toolkit scopes backends.
"""

from django.conf import settings
from django.utils import module_loading

from oauth2_provider.scopes import SettingsScopes


class ApplicationModelScopes(SettingsScopes):
    """
    Scopes backend that determines available scopes using the ScopedApplication model.
    """
    def get_available_scopes(self, application=None, request=None, *args, **kwargs):
        """ Returns valid scopes configured for the given application. """
        if hasattr('scopes', application):
            return set(application.scopes).intersection(self.get_all_scopes().keys())
        else:
            return super(ApplicationModelScopes, self).get_available_scopes(application, request, *args, **kwargs)
