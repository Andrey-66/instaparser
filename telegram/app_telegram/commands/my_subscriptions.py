from app_telegram.accses import restricted
from app_telegram.api.telegram_users import get_telegram_user


@restricted
async def my_subscriptions(update, context):
    telegram_id = update.effective_user.id
    telegram_profile_database = get_telegram_user(telegram_id)
    subscriptions = telegram_profile_database.get('subscriptions_profiles')
    if subscriptions:
        subscription_list = '\n'.join(subscriptions)
        await update.message.reply_text(f"Ваши подписки: \n\n{subscription_list}!")
    else:
        await update.message.reply_text('У Вас нет подписок')
