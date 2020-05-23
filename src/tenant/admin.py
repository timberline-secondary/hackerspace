from django import forms
from django.contrib import admin
from django.db import connection
from django.contrib.sites.models import Site

from tenant_schemas.utils import get_public_schema_name

from tenant.models import Tenant


class PublicSchemaOnlyAdminAccessMixin:
    def has_view_or_change_permission(self, request, obj=None):
        return connection.schema_name == get_public_schema_name()

    def has_add_permission(self, request):
        return connection.schema_name == get_public_schema_name()

    def has_module_permission(self, request):
        return connection.schema_name == get_public_schema_name()


class NonPublicSchemaOnlyAdminAccessMixin:
    def has_view_or_change_permission(self, request, obj=None):
        return connection.schema_name != get_public_schema_name()

    def has_add_permission(self, request):
        return connection.schema_name != get_public_schema_name()

    def has_module_permission(self, request):
        return connection.schema_name != get_public_schema_name()


class TenantAdminForm(forms.ModelForm):

    class Meta:
        model = Tenant
        fields = ['name']

    def clean_name(self):
        name = self.cleaned_data["name"]
        # has already validated the model field at this point
        if name == "public":
            raise forms.ValidationError("The public tenant is restricted and cannot be edited")
        elif self.instance.schema_name and self.instance.schema_name != get_schema_name(name):
            # if the schema already exists, then can't change the name
            raise forms.ValidationError("The name cannot be changed after the tenant is created")
        else:
            return name


def get_schema_name(tenant_name):
    return tenant_name.replace('-', '_').lower()
    

class TenantAdmin(PublicSchemaOnlyAdminAccessMixin, admin.ModelAdmin):
    list_display = ('schema_name', 'domain_url', 'name', 'desc', 'created_on')
    form = TenantAdminForm

    def save_model(self, request, obj, form, change):
        if obj.name.lower() == "public":
            # Shouldn't get here due to the form validation via clean_name. So uneccesary? 
            return
        if not change:
            obj.schema_name = get_schema_name(obj.name)
            obj.domain_url = "%s.%s" % (obj.name.lower(), Site.objects.get(id=1).domain)
        
        obj.save()


admin.site.register(Tenant, TenantAdmin)
