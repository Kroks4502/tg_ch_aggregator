from common.contracts import AdminNotifier, AlertNotifier, UserErrorNotifier

_admin: AdminNotifier | None = None
_user_error: UserErrorNotifier | None = None
_alert: AlertNotifier | None = None


def set_admin_notifier(impl: AdminNotifier) -> None:
    global _admin
    _admin = impl


def get_admin_notifier() -> AdminNotifier:
    if _admin is None:
        raise RuntimeError(
            "AdminNotifier is not registered. "
            "Make sure plugins.bot has been imported during startup."
        )
    return _admin


def set_user_error_notifier(impl: UserErrorNotifier) -> None:
    global _user_error
    _user_error = impl


def get_user_error_notifier() -> UserErrorNotifier:
    if _user_error is None:
        raise RuntimeError(
            "UserErrorNotifier is not registered. "
            "Make sure plugins.bot has been imported during startup."
        )
    return _user_error


def set_alert_notifier(impl: AlertNotifier) -> None:
    global _alert
    _alert = impl


def get_alert_notifier() -> AlertNotifier:
    if _alert is None:
        raise RuntimeError(
            "AlertNotifier is not registered. "
            "Make sure plugins.bot has been imported during startup."
        )
    return _alert
