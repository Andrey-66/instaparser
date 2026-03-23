from app_telegram.accses import restricted
from app_telegram.api.profiles import get_profile
from app_telegram.api.subscriptions import get_subscription
from app_telegram.api.telegram_users import get_telegram_user
from app_telegram.api.subscriptions import delete_subscription


@restricted
async def unsubscribe(update, context):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Использование: /unsubscribe <username>")
        return

    username = context.args[0].strip()
    telegram_id = update.effective_user.id
    instagram_profile_database = get_profile(username)
    if not instagram_profile_database:
        await update.message.reply_text(f"Вы не подписаны на {username}!")
        return
    telegram_profile_database = get_telegram_user(telegram_id)
    subscriptions = instagram_profile_database.get('subscriptions')
    for subscription_id in subscriptions:
        subscription = get_subscription(subscription_id)
        if subscription.get('telegram_user_id') == telegram_profile_database.get('id'):
            delete_subscription(subscription_id)
            await update.message.reply_text(f"Вы спешно отписалась от {username}!")
            return
    await update.message.reply_text(f"Вы не подписаны на {username}!")