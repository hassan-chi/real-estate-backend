from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from core.models import Subscription, Notification
from core.services.onesignal_service import send_push_notification


class Command(BaseCommand):
    help = 'Check for subscriptions expiring in 3 days and send notifications'

    def handle(self, *args, **options):
        # Calculate date 3 days from now
        three_days_from_now = timezone.now() + timedelta(days=3)
        
        # Get start and end of that day
        start_of_day = three_days_from_now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = three_days_from_now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Find active subscriptions expiring in 3 days (exclude per-listing plans)
        expiring_subscriptions = Subscription.objects.filter(
            active=True,
            end_date__gte=start_of_day,
            end_date__lte=end_of_day
        ).exclude(plan=Subscription.Plan.PERLISTING)
        
        count = 0
        for subscription in expiring_subscriptions:
            # Check if notification already sent
            existing_notification = Notification.objects.filter(
                user=subscription.user,
                notification_type=Notification.NotificationType.SUBSCRIPTION_EXPIRING,
                created_at__date=timezone.now().date()
            ).exists()
            
            if existing_notification:
                self.stdout.write(
                    self.style.WARNING(
                        f'Notification already sent for {subscription.user.username}'
                    )
                )
                continue
            
            # Create notification
            notification = Notification.objects.create(
                user=subscription.user,
                notification_type=Notification.NotificationType.SUBSCRIPTION_EXPIRING,
                title='Subscription Expiring Soon',
                message=f'Your {subscription.get_plan_display()} subscription will expire in 3 days. Please renew to continue listing properties.',
            )
            
            # Send push notification
            result = send_push_notification(
                user_id=subscription.user.id,
                title=notification.title,
                message=notification.message,
                data={'type': 'subscription_expiring', 'subscription_id': subscription.id}
            )
            
            if result.get('success') and result.get('notification_id'):
                notification.is_pushed = True
                notification.onesignal_id = result['notification_id']
                notification.save(update_fields=['is_pushed', 'onesignal_id'])
            
            count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'Sent expiry notification to {subscription.user.username} ({subscription.get_plan_display()})'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully sent {count} expiry notification(s)'
            )
        )
