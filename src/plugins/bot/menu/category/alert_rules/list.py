from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from alerts.common import get_alert_rule_title
from models import AlertRule, Category
from plugins.bot.constants import ADD_BNT_TEXT
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.menu import ButtonData, Menu


@Client.on_callback_query(
    filters.regex(r"/c/-\d+/r/(p/\d+/|)$"),
)
async def list_alerts_rules(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    if is_admin(callback_query.from_user.id):
        menu.add_row_button(ADD_BNT_TEXT + " правило", ":add")

    query = AlertRule.select().where(AlertRule.user_id == callback_query.from_user.id)

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

    category_id = menu.path.get_value("c")
    text = await menu.get_text(
        category_obj=Category.get(category_id),
        last_text="**Правила уведомлений**",
    )

    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
