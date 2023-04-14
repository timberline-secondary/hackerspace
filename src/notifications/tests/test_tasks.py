import json
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django_celery_beat.models import PeriodicTask
from unittest.mock import patch

from model_bakery import baker
from django_tenants.test.cases import TenantTestCase

from notifications import tasks
from notifications.models import Notification
from notifications.tasks import create_email_notification_tasks, generate_notification_email, get_notification_emails
from siteconfig.models import SiteConfig

User = get_user_model()


class NotificationTasksTests(TenantTestCase):
    """ Run tasks asyncronously with apply() """

    def setUp(self):

        # need a teacher before students can be created or the profile creation will fail when trying to notify
        self.test_teacher = User.objects.create_user('test_teacher', is_staff=True)
        self.test_student1 = User.objects.create_user('test_student', email="student@email.com")
        self.test_student2 = baker.make(User)

        self.ai_user, _ = User.objects.get_or_create(
            pk=SiteConfig.get().deck_ai.pk,
            defaults={
                'username': "Autogenerated AI",
            },
        )

    def test_get_notification_emails(self):
        """ Test that the correct list of notification emails are generated"""
        root_url = 'https://test.com'

        # 1 notifications to start
        emails = get_notification_emails(root_url)
        self.assertEqual(type(emails), list)
        self.assertEqual(len(emails), 1)

        # Create a notification for student 1, but they have emails turned off by default
        notification1 = baker.make(Notification, recipient=self.test_student1)
        emails = get_notification_emails(root_url)
        self.assertEqual(len(emails), 1)

        # Turn on notification emails for student1, now it should appear
        self.test_student1.profile.get_notifications_by_email = True
        self.test_student1.profile.save()
        emails = get_notification_emails(root_url)
        self.assertEqual(len(emails), 2)

        # Turn on notification emails for student2, should still only be 1 + deck_owner
        self.test_student2.profile.get_notifications_by_email = True
        self.test_student2.profile.save()
        emails = get_notification_emails(root_url)
        self.assertEqual(len(emails), 2)

        # Make a bunch of notifications for student2, so now we should have 2 emails + deck_owner
        baker.make(Notification, recipient=self.test_student2, _quantity=10)
        emails = get_notification_emails(root_url)
        self.assertEqual(len(emails), 3)

        # mark the original notification as read, so only student2 email now + deck_owner
        notification1.unread = False
        notification1.save()
        emails = get_notification_emails(root_url)
        self.assertEqual(len(emails), 2)

    def test_email_notifications_to_users(self):
        task_result = tasks.email_notifications_to_users.apply(
            kwargs={
                "root_url": "https://test.com",
            }
        )
        self.assertTrue(task_result.successful())

    def test_generate_notification_email__student(self):
        """ Test that the content of a notification email is correct """
        notifications = baker.make(Notification, recipient=self.test_student1, _quantity=2)

        root_url = 'https://test.com'
        email = generate_notification_email(self.test_student1, root_url)

        self.assertEqual(type(email), EmailMultiAlternatives)
        self.assertEqual(email.to, [self.test_student1.email])
        # Default deck short name is "Deck"
        print(email.subject)
        self.assertEqual(email.subject, "Deck Notifications")

        # https://stackoverflow.com/questions/62958111/how-to-display-html-content-of-an-emailmultialternatives-mail-object
        html_content = email.alternatives[0][0]

        self.assertNotIn("Quest submissions awaiting your approval", html_content)  # Teachers only

        self.assertIn("Unread notifications:", html_content)
        self.assertIn(str(notifications[0]), html_content)  # Links to notifications
        self.assertIn(str(notifications[1]), html_content)  # Links to notifications

    def test_generate_notification_email__staff(self):
        """ Test that staff notification emails include quests awaiting approval """
        notification = baker.make(Notification, recipient=self.test_teacher)
        root_url = 'https://test.com'
        sub = baker.make('quest_manager.questsubmission')

        # fake the call to `QuestSubmission.objects.all_awaiting_approval` made within
        # `generate_notification_email` so that it return a submission
        with patch('notifications.tasks.QuestSubmission.objects.all_awaiting_approval', return_value=[sub]):
            email = generate_notification_email(self.test_teacher, root_url)

        self.assertEqual(type(email), EmailMultiAlternatives)
        self.assertEqual(email.to, [self.test_teacher.email])

        # https://stackoverflow.com/questions/62958111/how-to-display-html-content-of-an-emailmultialternatives-mail-object
        html_content = email.alternatives[0][0]
        self.assertIn("Quest submissions awaiting your approval", html_content)  # Teachers only
        self.assertIn(str(sub), html_content)

        self.assertIn("Unread notifications:", html_content)
        self.assertIn(str(notification), html_content)  # Links to notifications


class CreateEmailNotificationTasksTest(TenantTestCase):
    """ Tests of the create_email_notification_tasks() method"""

    def setUp(self):
        self.app = apps.get_app_config('notifications')

    def test_task_is_created_with_new_tenant(self):
        """ The email notifcation task should be created in ready() on when the app starts up
        BUT DOES NOT HAPPEN ON TEST DB!
        This is because the ready() method runs on the default db, before django knows it is testing.
        https://code.djangoproject.com/ticket/22002
        However, we also call the method when initializing a new tenant in
        tenant.initialization.load_initial_tenant_data()
        """
        tasks = PeriodicTask.objects.filter(task='notifications.tasks.email_notifications_to_users')
        self.assertEqual(tasks.count(), 1)

        # ready is idempotent, doesn't cause problems running it again, doesn't create a new task:
        self.app.ready()
        tasks = PeriodicTask.objects.filter(task='notifications.tasks.email_notifications_to_users')
        self.assertEqual(tasks.count(), 1)

    def test_create_email_notification_tasks(self):
        """ A task should have been created for the test tenant"""
        create_email_notification_tasks()
        tasks = PeriodicTask.objects.filter(task='notifications.tasks.email_notifications_to_users')
        self.assertEqual(tasks.count(), 1)
        task = tasks.first()
        self.assertEqual(task.headers, json.dumps({"_schema_name": "test"}))
        self.assertTrue(task.enabled)
        self.assertFalse(task.one_off)
