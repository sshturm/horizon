# Copyright (c) 2014 NetApp, Inc.
# All rights reserved.

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Views for managing shares.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.forms import ValidationError  # noqa
from django.template.defaultfilters import filesizeformat  # noqa
from django.utils.translation import ugettext_lazy as _, ugettext_lazy
from django.views.decorators.debug import sensitive_variables

from horizon import exceptions, forms, messages
from horizon import forms
from horizon import messages
from horizon.utils import fields
from horizon.utils import functions
from horizon.utils.memoized import memoized  # noqa

from openstack_dashboard import api
from openstack_dashboard.api import keystone, manila
from openstack_dashboard.api import manila
from openstack_dashboard.api import neutron
from openstack_dashboard.dashboards.project.instances import tables
from openstack_dashboard.usage import quotas


class Create(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Name"))
    dns_ip = forms.CharField(max_length="15", label=_("DNS IP"))
    server = forms.CharField(max_length="255", label=_("Server"))
    domain = forms.CharField(max_length="255", label=_("Domain"))
    sid = forms.CharField(max_length="255", label=_("Sid"))
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(render_value=False))
    confirm_password = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(render_value=False))
    type = forms.ChoiceField(choices=(("", ""),
                                      ("active_directory", "Active Directory"),
                                      ("ldap", "LDAP"),
                                      ("kerberos", "Kerberos")),
                             label=_("Type"))
    description = forms.CharField(widget=forms.Textarea,
                                  label=_("Description"), required=False)

    def clean(self):
        '''Check to make sure password fields match.'''
        data = super(forms.Form, self).clean()
        if 'password' in data:
            if data['password'] != data.get('confirm_password', None):
                raise ValidationError(_('Passwords do not match.'))
        return data

    @sensitive_variables('data')
    def handle(self, request, data):
        try:
            data.pop('confirm_password')
            security_service = manila.security_service_create(
                request, **data)
            messages.success(request, _('Successfully created security service: %s')
                                      % data['name'])
            return security_service
        except Exception:
            exceptions.handle(request,
                              _('Unable to create security service.'))
            return False


class Update(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Share Name"))
    description = forms.CharField(widget=forms.Textarea,
            label=_("Description"), required=False)

    def handle(self, request, data):
        sec_service_id = self.initial['security_service_id']
        try:
            manila.security_service_update(request, sec_service_id, data['name'],
                                 data['description'])

            message = _('Updating security service "%s"') % data['name']
            messages.info(request, message)
            return True
        except Exception:
            redirect = reverse("horizon:project:shares:index")
            exceptions.handle(request,
                              _('Unable to update security service.'),
                              redirect=redirect)