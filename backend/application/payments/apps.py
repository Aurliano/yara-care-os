from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "application.payments"
    verbose_name = "Payments Application"
    def ready(self):
        from domains.licensing.hooks import register_paid_plan_checker
        from domains.billing.models import PlanPrice
        from decimal import Decimal

        def _is_paid_plan(plan_code: str) -> bool:
            price = PlanPrice.objects.filter(plan_code=plan_code, is_active=True).first()
            if price is not None:
                return price.amount > Decimal("0")
            return plan_code not in {"BASIC", "FREE"}

        register_paid_plan_checker(_is_paid_plan)

        from domains.synchronization.hooks import register_replica_access_checker

        def _check_replica_access(user, replica_identifier):
            from domains.device.services.assignments import get_assignments
            from domains.identity_access.services.authorization import user_is_associated_with_elder
            from domains.device.enums import AssignmentStatus

            assignments = get_assignments(device_id=replica_identifier)
            if not assignments:
                return True
            assigned = [a for a in assignments if a.status == AssignmentStatus.ASSIGNED]
            elder = assigned[0].elder if assigned else assignments[0].elder
            return user_is_associated_with_elder(user, elder)

        register_replica_access_checker(_check_replica_access)
