from models import AlertRule
from plugins.bot import menu_params as g_params
from plugins.bot.constants.text import DIALOG, SUCCESS_TEXT
from plugins.bot.handlers.alert_rules.common import params
from plugins.bot.handlers.alert_rules.common.constants import (
    CATEGORY_TEXT,
    COUNT_INTERVAL_TEXT,
    JOB_INTERVAL_TEXT,
    REGEX_TEXT,
    SINGULAR_ALERT_RULE_TEXT,
    SINGULAR_COMMON_ALERT_RULE_TEXT,
    THRESHOLD_TEXT,
    USER_TEXT,
)
from plugins.bot.menu_text import get_menu_text
from plugins.bot.utils.links import get_channel_formatted_link, get_user_formatted_link


async def get_alert_rule_menu_text(
    title: str,
    title_common: str,
    user_id: int,
    category_id: int = None,
    rule_type: str = None,
    regex: str = None,
    job_interval: int = None,
    count_interval: int = None,
    threshold: int = None,
    question: str = "",
):
    text_params = [await g_params.user(user_id)]

    if category_id:
        text_params.append(await g_params.category(category_id))
    else:
        title = title_common

    if rule_type == "regex":
        text_params += get_regex_params(regex=regex)
    elif rule_type == "counter":
        text_params += get_counter_params(
            job_interval=job_interval,
            count_interval=count_interval,
            threshold=threshold,
        )

    return get_menu_text(
        title=title,
        params=text_params,
        question=question,
    )


def get_counter_params(
    job_interval: int = None,
    count_interval: int = None,
    threshold: int = None,
):
    items = [params.TYPE_COUNTER]

    if job_interval:
        items.append(params.job_interval(job_interval))

    if count_interval:
        items.append(params.count_interval(count_interval))

    if threshold:
        items.append(params.threshold(threshold))

    return items


def get_regex_params(regex: str = None):
    if regex:
        return params.TYPE_REGEX, params.regex(regex)

    return (params.TYPE_REGEX,)


async def get_dialog_text(
    user_id: int,
    category_id: int | None,
    doing: str,
    action: str,
    pattern: str = None,
    job_interval: int = None,
    count_interval: int = None,
    threshold: int = None,
):
    user_link = await get_user_formatted_link(user_id)
    user_text = USER_TEXT.format(user_link)

    category_text = ""
    if category_id:
        title_text = SINGULAR_ALERT_RULE_TEXT
        category_link = await get_channel_formatted_link(category_id)
        category_text = CATEGORY_TEXT.format(category_link)
    else:
        title_text = SINGULAR_COMMON_ALERT_RULE_TEXT

    text_items = [user_text]

    if pattern:
        text_items.append(REGEX_TEXT.format(regex=pattern))

    if job_interval:
        text_items.append(f"{JOB_INTERVAL_TEXT.format(job_interval=job_interval)},")

    if count_interval:
        text_items.append(
            f"{COUNT_INTERVAL_TEXT.format(count_interval=count_interval)}"
        )

    if threshold:
        text_items.append(f"и {THRESHOLD_TEXT.format(threshold=threshold)}")

    text_items.append(category_text)

    return DIALOG.format(
        doing=f"{doing} {title_text} {' '.join(text_items)}",
        action=action,
    )


async def get_alert_rule_menu_success_text(
    title: str,
    title_common: str,
    user_id: int,
    rule_obj: AlertRule,
    action: str,
) -> str:
    text = await get_full_text_about_alert_rule(
        title=title,
        title_common=title_common,
        rule_obj=rule_obj,
        user_id=user_id,
    )
    return SUCCESS_TEXT.format(text=f"{text} {action}")


async def get_full_text_about_alert_rule(
    title: str,
    title_common: str,
    rule_obj: AlertRule,
    user_id: int = None,
):
    user_text = ""
    if user_id:
        user_link = await get_user_formatted_link(user_id)
        user_text = f" {USER_TEXT.format(user_link)}"

    if rule_obj.category_id:
        category_link = await get_channel_formatted_link(rule_obj.category_id)
        category_text = f" {CATEGORY_TEXT.format(category_link)}"
    else:
        category_text = ""
        title = title_common

    if rule_obj.type == "counter":
        return (
            f"{title}{user_text} {JOB_INTERVAL_TEXT}, {COUNT_INTERVAL_TEXT} и"
            f" {THRESHOLD_TEXT}"
            + category_text
        ).format(**rule_obj.config)

    return f"{title}{user_text} {REGEX_TEXT}{category_text}".format(**rule_obj.config)
