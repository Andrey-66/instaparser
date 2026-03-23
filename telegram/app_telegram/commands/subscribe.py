from app_telegram.accses import restricted
from app_telegram.api.profiles import get_profile, create_profile
from app_telegram.api.subscriptions import get_subscription, create_subscription
from app_telegram.api.telegram_users import get_telegram_user


@restricted
async def subscribe(update, context):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Использование: /subscribe <username>")
        return

    username = context.args[0].strip()
    telegram_id = update.effective_user.id
    instagram_profile_database = get_profile(username)
    if not instagram_profile_database:
        instagram_profile_database = create_profile(username)
    telegram_profile_database = get_telegram_user(telegram_id)
    subscriptions = instagram_profile_database.get('subscriptions')
    for subscription_id in subscriptions:
        subscription = get_subscription(subscription_id)
        if subscription.get('telegram_user_id') == telegram_profile_database.get('id'):
            await update.message.reply_text(f"Вы уже подписаны на {username}!")
            return
    if create_subscription(instagram_profile_database.get('id'), telegram_profile_database.get('id')):
        await update.message.reply_text(f"🎉 Подписка на {username} оформлена!")
    else:
        await update.message.reply_text(f"Что-то пошло не так")