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

from django.core.urlresolvers import reverse
from django.forms import ValidationError  # noqa
from django.template.defaultfilters import filesizeformat  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils.memoized import memoized  # noqa

from openstack_dashboard.api import manila
from openstack_dashboard.api import neutron


class Create(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Name"))
    neutron_net_id = forms.ChoiceField(choices=(),
                                       label=_("Neutron Net ID"),
                                       widget=forms.Select(attrs={
                                           'class': 'switchable',
                                           'data-slug': 'net'
                                       }))
    #neutron_subnet_id = forms.ChoiceField(choices=(),
    #                                      label=_("Neutron Subnet ID"))
    description = forms.CharField(widget=forms.Textarea,
                                  label=_("Description"), required=False)

    def __init__(self, request, *args, **kwargs):
        super(Create, self).__init__(
            request, *args, **kwargs)
        net_choices = neutron.network_list(request)
        self.fields['neutron_net_id'].choices = [(' ', ' ')] + \
                                                [(choice.id, choice.name_or_id)
                                                 for choice in net_choices]
        for net in net_choices:
            # For each network create switched choice field with
            # the its subnet choices
            subnet_field_name = 'subnet-choices-%s' % net.id
            subnet_field = forms.ChoiceField(
                choices=(), label=_("Neutron Subnet ID"),
                widget=forms.Select(attrs={
                    'class': 'switched',
                    'data-switch-on': 'net',
                    'data-net-%s' % net.id: _("Neutron Subnet ID")
                }))
            # Insert subnet choice field under network choice field
            # (before Description field that has index 2)
            self.fields.insert(2, subnet_field_name, subnet_field)
            subnet_choices = neutron.subnet_list(request, network_id=net.id)
            self.fields[subnet_field_name].choices = [(' ', ' ')] + \
                                                     [(choice.id,
                                                       choice.name_or_id) for
                                                      choice in subnet_choices]

    def handle(self, request, data):
        try:
            # Remove any new lines in the public key
            share_net_id = data['neutron_net_id']
            subnet_key = 'subnet-choices-%s' % share_net_id
            data['neutron_subnet_id'] = data[subnet_key]
            share_network = manila.share_network_create(
                request, name=data['name'], description=data['description'],
                neutron_net_id=data['neutron_net_id'],
                neutron_subnet_id=data[subnet_key])
            messages.success(request, _('Successfully created share'
                                        ' network: %s') % data['name'])
            return share_network
        except Exception:
            exceptions.handle(request,
                              _('Unable to create share network.'))
            return False


class Update(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Share Name"))
    description = forms.CharField(widget=forms.Textarea,
            label=_("Description"), required=False)

    def handle(self, request, data, *args, **kwargs):
        share_net_id = self.initial['share_network_id']
        try:
            manila.share_network_update(request, share_net_id,
                                        name=data['name'],
                                        description=data['description'])

            message = _('Updating share network "%s"') % data['name']
            messages.info(request, message)
            return True
        except Exception:
            redirect = reverse("horizon:project:shares:index")
            exceptions.handle(request,
                              _('Unable to update share network.'),
                              redirect=redirect)


class AddSecurityServiceForm(forms.SelfHandlingForm):
    sec_service = forms.MultipleChoiceField(
        label=_("Networks"),
        required=True,
        widget=forms.CheckboxSelectMultiple(),
        error_messages={
            'required': _(
                "At least one security service"
                " must be specified.")})

    def __init__(self, request, *args, **kwargs):
        super(AddSecurityServiceForm, self).__init__(
            request, *args, **kwargs)
        sec_services_choices = manila.security_service_list(request)
        self.fields['sec_service'].choices = [(' ', ' ')] + \
                                             [(choice.id, choice.name
                                              or choice.id) for choice in
                                              sec_services_choices]

    def handle(self, request, data):
        pass