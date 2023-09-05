from django.utils.safestring import mark_safe

from django.contrib.auth import get_user_model
from django.db import models

from url_or_relative_url_field.fields import URLOrRelativeURLField


# http://stackoverflow.com/questions/2472422/django-file-upload-size-limit
# https://github.com/mixkorshun/django-safe-filefield/blob/master/safe_filefield/models.py
from utilities.fields import RestrictedFileFormField

User = get_user_model()


class RestrictedFileField(models.FileField):
    """
    Same as FileField, but you can specify:
    * content_types - list containing allowed content_types. Example: ['application/pdf', 'image/jpeg']
    * max_upload_size - a number indicating the maximum file size allowed for upload.
    """

    def __init__(self, **kwargs):
        self.content_types = kwargs.pop("content_types", "All")
        self.max_upload_size = kwargs.pop("max_upload_size", 512000)

        super().__init__(**kwargs)

    def formfield(self, **kwargs):
        return super().formfield(
            form_class=RestrictedFileFormField,

            max_upload_size=self.max_upload_size,
            content_types=self.content_types
        )


class ImageResource(models.Model):
    """

    """
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='images/', height_field='height', width_field='width')
    height = models.PositiveIntegerField(editable=False)
    width = models.PositiveIntegerField(editable=False)
    datetime_created = models.DateTimeField(auto_now_add=True, auto_now=False)
    datetime_last_edit = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.name


class VideoResource(models.Model):
    """

    """
    title = models.CharField(max_length=50)
    video_file = models.FileField(upload_to='videos/')  # verbose_name=""
    datetime_created = models.DateTimeField(auto_now_add=True, auto_now=False)
    datetime_last_edit = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return self.title + ": " + str(self.video_file)


class MenuItemQueryset(models.QuerySet):

    def get_visible_items(self):
        return self.filter(visible=True)

    def get_main_menu_items(self):
        return self.filter(is_side_menu=False)

    def get_side_menu_items(self):
        self.get_or_create_default_side_menu_items()
        return self.filter(is_side_menu=True)

    def get_or_create_default_side_menu_items(self):
        """
        Create if these items don't exist yet, else return them
        These are the default items which are non-deletable but can be set to visible = False
        """

        labels = list(self.model.SIDE_MENU_ITEMS.keys())
        menu_items = self.filter(label__in=labels)

        if menu_items.count() == len(labels):
            return menu_items

        for menu_item, defaults in self.model.SIDE_MENU_ITEMS.items():
            self.get_or_create(label=menu_item, defaults=defaults)

        return self.filter(label__in=labels)


class MenuItem(models.Model):

    label = models.CharField(max_length=25, help_text="This is the text that will appear for the menu item.")
    fa_icon = models.CharField(max_length=50, default="link",
                               help_text=mark_safe("The Font Awesome icon to display beside the text. E.g. 'star-o'. "
                                                   "Options from <a target='_blank'"
                                                   "href='http://fontawesome.com/v4.7.0/icons/'>Font Awesome</a>."))
    url = URLOrRelativeURLField(help_text="Relative URLs will work too.  E.g. '/courses/ranks/'", verbose_name="URL")
    open_link_in_new_tab = models.BooleanField()
    sort_order = models.IntegerField(default=0, help_text="Lowest will be at the top.")
    visible = models.BooleanField(default=True)
    is_side_menu = models.BooleanField(default=False, help_text="If true, this will be displayed in the side menu")

    objects = MenuItemQueryset.as_manager()

    SIDE_MENU_ITEMS = {
        "Maps": {
            "label": "Maps",
            "fa_icon": "map-signs",
            "url": "/maps/primary/",
            "open_link_in_new_tab": False,
            "is_side_menu": True,
            "sort_order": 0
        },
        "Announcements": {
            "label": "Announcements",
            "fa_icon": "newspaper-o",
            "url": "/announcements/",
            "open_link_in_new_tab": False,
            "is_side_menu": True,
            "sort_order": 1
        },
        "Profile": {
            "label": "Profile",
            "fa_icon": "user",
            "url": "/profiles/own/",
            "open_link_in_new_tab": False,
            "is_side_menu": True,
            "sort_order": 2
        },
        "Portfolio": {
            "label": "Portfolio",
            "fa_icon": "picture-o",
            "url": "/portfolios/detail/",
            "open_link_in_new_tab": False,
            "is_side_menu": True,
            "sort_order": 3
        },
    }

    class Meta:
        ordering = ["sort_order"]
        constraints = [
            models.UniqueConstraint(fields=['label', 'is_side_menu'], name='unique_menu_item_label', deferrable=models.Deferrable.DEFERRED)
        ]

    def __str__(self):
        target = 'target="_blank"' if self.open_link_in_new_tab else ''
        return (
            f'<a href="{self.url}" {target} class="menuitem">'
            f'<i class="fa fa-fw fa-{self.fa_icon}"></i>&nbsp;&nbsp;{self.label}</a>'
        )

    def can_delete(self):
        """
        Returns True if this menu item can be deleted.
        """
        if self.label in self.SIDE_MENU_ITEMS:
            return False

        return True
