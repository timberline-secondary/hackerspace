from django import forms
from django.contrib.contenttypes.models import ContentType

from utilities.forms import FutureModelForm
from utilities.fields import AllowedContentObjectChoiceField as ContentObjectChoiceField

from .models import CytoScape


class AllowedContentObjectChoiceField(ContentObjectChoiceField):

    def get_allowed_model_classes(self):
        model_classes = [
            ct.model_class() for ct in ContentType.objects.filter(
                CytoScape.ALLOWED_INITIAL_CONTENT_TYPES
            )
        ]
        return model_classes


class GenerateQuestMapForm(FutureModelForm):

    class Meta:
        model = CytoScape
        fields = [
            'name',
            'initial_content_object',
            'parent_scape',
        ]

    name = forms.CharField(max_length=50, required=False, help_text="If not provided, the initial quest's name will be used")
    
    initial_content_object = AllowedContentObjectChoiceField(label='Initial Object')

    parent_scape = forms.ModelChoiceField(
        label='Parent Quest Map', 
        required=False,
        queryset=CytoScape.objects.all(),
    )

    def __init__(self, *args, **kwargs):
        self.autobreak = kwargs.pop('autobreak', None)
        super().__init__(*args, **kwargs)

        self.fields['initial_content_object'].widget.attrs['data-placeholder'] = 'Type to search'

    def save(self, **kwargs):
        obj = self.cleaned_data['initial_content_object']
        name = self.cleaned_data['name'] or str(obj)
        parent_scape = self.cleaned_data['parent_scape']

        return CytoScape.generate_map(initial_object=obj, name=name, parent_scape=parent_scape, autobreak=self.autobreak)


class QuestMapForm(GenerateQuestMapForm, forms.ModelForm):
    """  Only used when updating Cytoscape map"""

    class Meta(GenerateQuestMapForm.Meta):
        fields = [
            *GenerateQuestMapForm.Meta.fields,
            'is_the_primary_scape',
            'autobreak',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # prevent recursive maps
        self.fields['parent_scape'].queryset = self.fields['parent_scape'].queryset.exclude(id=self.instance.id)
    
    # save with ModelForm default instead of CytoScape.generate_map()
    def save(self, **kwargs):
        return super(forms.ModelForm, self).save(**kwargs)
