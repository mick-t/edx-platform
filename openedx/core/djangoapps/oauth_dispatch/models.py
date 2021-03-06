"""
Specialized models for oauth_dispatch djangoapp
"""

from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_mysql.models import ListCharField
from oauth2_provider.models import AbstractApplication
from oauth2_provider.settings import oauth2_settings
from pytz import utc


class RestrictedApplication(models.Model):
    """
    This model lists which django-oauth-toolkit Applications are considered 'restricted'
    and thus have a limited ability to use various APIs.

    A restricted Application will only get expired token/JWT payloads
    so that they cannot be used to call into APIs.
    """

    application = models.ForeignKey(oauth2_settings.APPLICATION_MODEL, null=False, on_delete=models.CASCADE)

    def __unicode__(self):
        """
        Return a unicode representation of this object
        """
        return u"<RestrictedApplication '{name}'>".format(
            name=self.application.name
        )

    @classmethod
    def set_access_token_as_expired(cls, access_token):
        """
        For access_tokens for RestrictedApplications, put the expire timestamp into the beginning of the epoch
        which is Jan. 1, 1970
        """
        access_token.expires = datetime(1970, 1, 1, tzinfo=utc)

    @classmethod
    def verify_access_token_as_expired(cls, access_token):
        """
        For access_tokens for RestrictedApplications, make sure that the expiry date
        is set at the beginning of the epoch which is Jan. 1, 1970
        """
        return access_token.expires == datetime(1970, 1, 1, tzinfo=utc)


class ScopedApplication(AbstractApplication):
    """
    Custom Django OAuth Toolkit Application model that enables the definition
    of scopes that are authorized for the given Application.
    """
    FILTER_USER_ME = 'user:me'

    # TODO: Remove the id field once we perform the inital migrations for this model.
    # We need to copy data over from the oauth2_provider.models.Application model to
    # this new model with the intial migration and the model IDs will need to match
    # so that existing AccessTokens will still work when switching over to the new model.
    # Once we have the data copied over we can move back to an auto-increment primary key.
    id = models.IntegerField(primary_key=True)
    scopes = ListCharField(
        base_field=models.CharField(max_length=32),
        size=25,
        max_length=(25 * 33),  # 25 * 32 character scopes, plus commas
        help_text=_('Comma-separated list of scopes that this application will be allowed to request.'),
    )

    class Meta:
        app_label = 'oauth_dispatch'

    def __unicode__(self):
        """
        Return a unicode representation of this object.
        """
        return u"<ScopedApplication '{name}'>".format(
            name=self.name
        )

    @property
    def authorization_filters(self):
        """
        Return the list of authorization filters for this application.
        """
        filters = [':'.join([org.provider_type, org.short_name]) for org in self.organizations.all()]
        if self.authorization_grant_type == self.GRANT_CLIENT_CREDENTIALS:
            filters.append(self.FILTER_USER_ME)
        return filters


class ScopedApplicationOrganization(models.Model):
    """
    Associates an organization to a given ScopedApplication including the
    provider type of the organization so that organization-based filters
    can be added to access tokens provided to the given Application.

    See openedx/core/djangoapps/oauth_dispatch/docs/decisions/0007-include-organizations-in-tokens.rst
    for the intended use of this model.
    """
    CONTENT_PROVIDER_TYPE = 'content_org'
    ORGANIZATION_PROVIDER_TYPES = (
        (CONTENT_PROVIDER_TYPE, _('Content Provider')),
    )

    # In practice, short_name should match the short_name of an Organization model.
    # This is not a foreign key because the organizations app is not installed by default.
    short_name = models.CharField(
        max_length=255,
        help_text=_('The short_name of an existing Organization.'),
    )
    provider_type = models.CharField(
        max_length=32,
        choices=ORGANIZATION_PROVIDER_TYPES,
        default=CONTENT_PROVIDER_TYPE,
    )
    application = models.ForeignKey(
        oauth2_settings.APPLICATION_MODEL,
        related_name='organizations',
    )

    class Meta:
        app_label = 'oauth_dispatch'

    def __unicode__(self):
        """
        Return a unicode representation of this object.
        """
        return u"<ScopedApplicationOrganization '{application_name}':'{org}'>".format(
            application_name=self.application.name,
            org=self.short_name,
        )
