from django.urls import reverse
from django.utils.itercompat import is_iterable

from taggit.models import Tag
from django_select2.forms import ModelSelect2TagWidget


class TaggitSelect2Widget(ModelSelect2TagWidget):
    """Select2 tag widget for taggit's TagField."""

    model = Tag
    search_fields = ["name__icontains"]

    def __init__(self, *args, **kwargs):
        """ Despite what Select2 and django-select2 docs tell you. You cant actually change the default setting in javascript.
        For now modify the `attrs` variable to set default attributes.

        cant set defaults in `def build_attrs` since it populates the attrs with the select2 defaults beforehand.
        """
        attrs = kwargs.get('attrs', {})
        # As of `django-select2 7.1.2`, Select2 by default now has a minimum input length of 2.
        attrs.setdefault('data-minimum-input-length', '1')
        kwargs['attrs'] = attrs

        super().__init__(*args, **kwargs)

    def get_url(self):
        return reverse('tags:auto-json')

    def build_attrs(self, *args, **kwargs):
        """Add data-tags=","."""
        attrs = super().build_attrs(*args, **kwargs)
        attrs['data-tags'] = ','
        return attrs

    def option_value(self, value):
        """Return tag.name attribute of value."""
        return value.tag.name if hasattr(value, 'tag') else value

    def format_value(self, value):
        """Return the list of HTML option values for a form field value."""
        if not isinstance(value, (tuple, list)):
            value = [value]

        values = set()
        for v in value:
            if not v:
                continue

            v = v.split(',') if isinstance(v, str) else v
            v = [v] if not is_iterable(v) else v
            for t in v:
                values.add(self.option_value(t))
        return values

    def options(self, name, value, attrs=None):
        """Return only select options."""
        # When the data hasn't validated, we get the raw input
        if isinstance(value, str):
            value = value.split(',')

        for v in value:
            if not v:
                continue

            real_values = v.split(',') if hasattr(v, 'split') else v
            real_values = [real_values] if not is_iterable(real_values) else real_values
            for rv in real_values:
                yield self.option_value(rv)

    def optgroups(self, name, value, attrs=None):
        """Return a list of one optgroup and selected values."""
        default = (None, [], 0)
        groups = [default]

        for i, v in enumerate(self.options(name, value, attrs)):
            default[1].append(
                self.create_option(v, v, v, True, i)
            )
        return groups

    def value_from_datadict(self, data, files, name):
        """Return a comma-separated list of options.

        This is needed because Select2 uses a multiple select even in tag mode,
        and the model field expects a comma-separated list of tags.
        """
        value = ','.join(super().value_from_datadict(data, files, name))
        if value and ',' not in value:
            value = '%s,' % value
        return value
