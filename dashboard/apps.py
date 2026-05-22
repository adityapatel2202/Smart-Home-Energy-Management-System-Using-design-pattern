from django.apps import AppConfig
import sys

class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    def ready(self):
        import os
        # Prevent running scheduler twice in dev mode
        if os.environ.get('RUN_MAIN', None) != 'true' and 'runserver' in sys.argv:
            return
            
        from apscheduler.schedulers.background import BackgroundScheduler
        from .models import DeviceSchedule
        from django.utils import timezone

        def check_schedules():
            now = timezone.now()
            print(f"Checking schedules at {now} (tz: {timezone.get_default_timezone()})")
            # Fetch not-executed schedules and compare in Python to avoid DB tz pitfalls
            pending_schedules = DeviceSchedule.objects.filter(is_executed=False)
            for schedule in pending_schedules:
                sched_time = schedule.scheduled_time
                aware = timezone.is_aware(sched_time)
                print(f"Schedule {schedule.id}: stored={sched_time!r}, aware={aware}")
                if timezone.is_naive(sched_time):
                    sched_time = timezone.make_aware(sched_time, timezone.get_default_timezone())
                    print(f"Schedule {schedule.id}: made aware={sched_time!r}")
                if sched_time <= now:
                    app = schedule.appliance
                    try:
                        if schedule.action == 'ON':
                            app.turn_on()
                        else:
                            app.turn_off()
                        schedule.is_executed = True
                        schedule.save()
                        print(f"Executed schedule: turned {schedule.action} for {app.name}")
                    except Exception as e:
                        print(f"Error executing schedule {schedule.id}: {e}")

        scheduler = BackgroundScheduler()
        scheduler.add_job(check_schedules, 'interval', seconds=10)
        scheduler.start()
        print("Scheduler started...")
