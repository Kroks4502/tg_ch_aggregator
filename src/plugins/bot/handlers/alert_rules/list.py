from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from alerts.common import get_alert_rule_title
from models import AlertRule, Category
from plugins.bot.menu import Menu
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.links import get_user_formatted_link
from utils.menu import ButtonData


@Client.on_callback_query(
    filters.regex(r"/r/(p/\d+/|)$"),
)
async def list_alerts_rules(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    category_id = menu.path.get_value("c")

    if is_admin(callback_query.from_user.id):
        menu.add_button.add()

    query = AlertRule.select().where(
        (AlertRule.user_id == callback_query.from_user.id)
        & (AlertRule.category_id == category_id)
    )

    pagination = menu.set_pagination(total_items=query.count())
    menu.add_rows_from_data(
        data=[
            ButtonData(
                title=get_alert_rule_title(alert_rule=i),
                path=i.id,
            )
            for i in query.paginate(pagination.page, pagination.size)
        ],
    )

    text = await menu.get_text(
        category_obj=Category.get(category_id) if category_id else None,
        last_text=(
            f"**{'П' if category_id else 'Общие п'}равила уведомлений"
            f" {await get_user_formatted_link(callback_query.from_user.id)}**"
        ),
    )

    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
