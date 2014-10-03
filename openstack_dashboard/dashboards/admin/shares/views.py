# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Admin views for managing shares.
"""

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tabs

from openstack_dashboard.api import manila
from openstack_dashboard.dashboards.admin.shares \
    import forms as project_forms
from openstack_dashboard.dashboards.admin.shares \
    import tabs as project_tabs

from openstack_dashboard.dashboards.project.shares.shares \
    import views as share_views


class IndexView(tabs.TabbedTableView, share_views.ShareTableMixIn):
    tab_group_class = project_tabs.ShareTabs
    template_name = "admin/shares/index.html"


class DetailView(share_views.DetailView):
    template_name = "admin/shares/detail.html"


class CreateVolumeTypeView(forms.ModalFormView):
    form_class = project_forms.CreateVolumeType
    template_name = 'admin/shares/create_volume_type.html'
    success_url = 'horizon:admin:shares:index'

    def get_success_url(self):
        return reverse(self.success_url)


class UpdateVolumeTypeView(forms.ModalFormView):
    form_class = project_forms.UpdateVolumeType
    template_name = "admin/shares/update_volume_type.html"
    success_url = reverse_lazy("horizon:admin:shares:index")

    def get_object(self):
        if not hasattr(self, "_object"):
            vt_id = self.kwargs["volume_type_id"]
            try:
                self._object = manila.volume_type_get(self.request, vt_id)
            except Exception:
                msg = _("Unable to retrieve volume_type.")
                url = reverse("horizon:admin:shares:index")
                exceptions.handle(self.request, msg, redirect=url)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateVolumeTypeView, self).get_context_data(**kwargs)
        context["volume_type"] = self.get_object()
        return context

    def get_initial(self):
        volume_type = self.get_object()
        return {
            "id": self.kwargs["volume_type_id"],
            "name": volume_type.name,
            "extra_specs": volume_type.extra_specs,
        }