import os
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Токен бери из переменных окружения или вставь свой
TOKEN = os.getenv('BOT_TOKEN', '8451941413:AAHTOJbygtDzb5vl63H_QCh47SiPczPaTgY')

# Настройки паролей
LOWERCASE = string.ascii_lowercase      # a-z
UPPERCASE = string.ascii_uppercase      # A-Z  
DIGITS = string.digits                 # 0-9
SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?" # Спецсимволы

# Смайлики для кнопок
EMOJI = {
    'length': '📏',
    'lower': '🔤',
    'upper': '🔠', 
    'digits': '🔢',
    'symbols': '🔣',
    'generate': '⚡',
    'copy': '📋',
    'refresh': '🔄'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветственное сообщение"""
    user = update.effective_user
    
    # Создаем настройки по умолчанию для пользователя
    if 'user_settings' not in context.user_data:
        context.user_data['user_settings'] = {
            'length': 12,
            'lower': True,
            'upper': True,
            'digits': True,
            'symbols': True
        }
    
    welcome_text = f"""
🔐 <b>ПРИВЕТ, {user.first_name}!</b>

Я помогу создать надежный пароль за секунду!

<b>Команды:</b>
/password [длина]  - сгенерировать пароль
/settings         - настроить параметры
/help            - подробная помощь

<b>Примеры:</b>
/password        - пароль 12 символов
/password 16     - пароль 16 символов
/password strong - сложный пароль

Нажми /password чтобы начать!
    """
    
    await update.message.reply_text(welcome_text, parse_mode='HTML')

async def generate_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерирует пароль"""
    
    # Получаем настройки пользователя
    settings = context.user_data.get('user_settings', {
        'length': 12,
        'lower': True,
        'upper': True,
        'digits': True,
        'symbols': True
    })
    
    # Проверяем аргументы команды
    if context.args:
        if context.args[0].isdigit():
            settings['length'] = int(context.args[0])
        elif context.args[0] == 'strong':
            settings.update({'length': 16, 'lower': True, 'upper': True, 
                           'digits': True, 'symbols': True})
        elif context.args[0] == 'simple':
            settings.update({'length': 8, 'lower': True, 'upper': False,
                           'digits': True, 'symbols': False})
    
    # Проверяем минимальную длину
    if settings['length'] < 4:
        settings['length'] = 4
    if settings['length'] > 64:
        settings['length'] = 64
    
    # Составляем алфавит
    chars = ''
    if settings['lower']:
        chars += LOWERCASE
    if settings['upper']:
        chars += UPPERCASE
    if settings['digits']:
        chars += DIGITS
    if settings['symbols']:
        chars += SYMBOLS
    
    # Если ничего не выбрано, включаем всё
    if not chars:
        chars = LOWERCASE + UPPERCASE + DIGITS + SYMBOLS
        settings.update({'lower': True, 'upper': True, 'digits': True, 'symbols': True})
    
    # Генерируем пароль
    password = ''.join(random.choice(chars) for _ in range(settings['length']))
    
    # Определяем надежность пароля
    strength, color = get_password_strength(password)
    
    # Сохраняем пароль в данные пользователя
    context.user_data['last_password'] = password
    
    # Создаем клавиатуру
    keyboard = [
        [
            InlineKeyboardButton(f"{EMOJI['copy']} Копировать", callback_data="copy"),
            InlineKeyboardButton(f"{EMOJI['refresh']} Ещё", callback_data="regenerate")
        ],
        [InlineKeyboardButton(f"{EMOJI['settings']} Настройки", callback_data="show_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Формируем сообщение
    message = f"""
{EMOJI['generate']} <b>ТВОЙ ПАРОЛЬ ГОТОВ!</b>

<code>{password}</code>

<b>Параметры:</b>
{EMOJI['length']} Длина: {settings['length']} символов
{'🔤 ' + 'Буквы (a-z)' if settings['lower'] else ''}
{'🔠 ' + 'Буквы (A-Z)' if settings['upper'] else ''}
{'🔢 ' + 'Цифры' if settings['digits'] else ''}
{'🔣 ' + 'Символы' if settings['symbols'] else ''}

<b>Надежность:</b> {strength}
    """
    
    await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню настроек"""
    settings = context.user_data.get('user_settings', {
        'length': 12,
        'lower': True,
        'upper': True,
        'digits': True,
        'symbols': True
    })
    
    keyboard = [
        [
            InlineKeyboardButton(
                f"{EMOJI['length']} Длина: {settings['length']}", 
                callback_data="adjust_length"
            )
        ],
        [
            InlineKeyboardButton(
                f"{'✅' if settings['lower'] else '❌'} Буквы (a-z)", 
                callback_data="toggle_lower"
            ),
            InlineKeyboardButton(
                f"{'✅' if settings['upper'] else '❌'} Буквы (A-Z)", 
                callback_data="toggle_upper"
            )
        ],
        [
            InlineKeyboardButton(
                f"{'✅' if settings['digits'] else '❌'} Цифры", 
                callback_data="toggle_digits"
            ),
            InlineKeyboardButton(
                f"{'✅' if settings['symbols'] else '❌'} Символы", 
                callback_data="toggle_symbols"
            )
        ],
        [
            InlineKeyboardButton("➕ +1", callback_data="length_plus"),
            InlineKeyboardButton("➖ -1", callback_data="length_minus"),
            InlineKeyboardButton("🔄 Сброс", callback_data="reset_settings")
        ],
        [InlineKeyboardButton("⚡ Сгенерировать", callback_data="generate_from_settings")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_password")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Если это callback, редактируем сообщение
    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(
            "⚙️ <b>НАСТРОЙКИ ПАРОЛЯ</b>\n\nВыберите параметры:", 
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    else:
        # Если это команда /settings
        await update.message.reply_text(
            "⚙️ <b>НАСТРОЙКИ ПАРОЛЯ</b>\n\nВыберите параметры:",
            parse_mode='HTML',
            reply_markup=reply_markup
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    settings = context.user_data.get('user_settings', {
        'length': 12,
        'lower': True,
        'upper': True,
        'digits': True,
        'symbols': True
    })
    
    if data == "copy":
        # Копирование пароля
        password = context.user_data.get('last_password', '')
        await query.message.reply_text(
            f"📋 Пароль скопирован:\n<code>{password}</code>",
            parse_mode='HTML'
        )
    
    elif data == "regenerate":
        # Сгенерировать новый пароль
        await regenerate_from_callback(query, context)
    
    elif data == "show_settings":
        await settings_menu(update, context)
    
    elif data == "toggle_lower":
        settings['lower'] = not settings['lower']
        context.user_data['user_settings'] = settings
        await settings_menu(update, context)
    
    elif data == "toggle_upper":
        settings['upper'] = not settings['upper']
        context.user_data['user_settings'] = settings
        await settings_menu(update, context)
    
    elif data == "toggle_digits":
        settings['digits'] = not settings['digits']
        context.user_data['user_settings'] = settings
        await settings_menu(update, context)
    
    elif data == "toggle_symbols":
        settings['symbols'] = not settings['symbols']
        context.user_data['user_settings'] = settings
        await settings_menu(update, context)
    
    elif data == "length_plus":
        settings['length'] = min(settings['length'] + 1, 64)
        context.user_data['user_settings'] = settings
        await settings_menu(update, context)
    
    elif data == "length_minus":
        settings['length'] = max(settings['length'] - 1, 4)
        context.user_data['user_settings'] = settings
        await settings_menu(update, context)
    
    elif data == "reset_settings":
        context.user_data['user_settings'] = {
            'length': 12,
            'lower': True,
            'upper': True,
            'digits': True,
            'symbols': True
        }
        await settings_menu(update, context)
    
    elif data == "generate_from_settings":
        await regenerate_from_callback(query, context)
    
    elif data == "back_to_password":
        # Возвращаем последний сгенерированный пароль
        password = context.user_data.get('last_password', '')
        if password:
            await show_password(query, password, settings, context)

async def regenerate_from_callback(query, context):
    """Генерирует новый пароль из callback"""
    settings = context.user_data.get('user_settings', {
        'length': 12,
        'lower': True,
        'upper': True,
        'digits': True,
        'symbols': True
    })
    
    # Составляем алфавит
    chars = ''
    if settings['lower']:
        chars += LOWERCASE
    if settings['upper']:
        chars += UPPERCASE
    if settings['digits']:
        chars += DIGITS
    if settings['symbols']:
        chars += SYMBOLS
    
    if not chars:
        chars = LOWERCASE + UPPERCASE + DIGITS + SYMBOLS
    
    password = ''.join(random.choice(chars) for _ in range(settings['length']))
    context.user_data['last_password'] = password
    
    await show_password(query, password, settings, context)

async def show_password(query, password, settings, context):
    """Показывает пароль с кнопками"""
    strength, color = get_password_strength(password)
    
    keyboard = [
        [
            InlineKeyboardButton(f"{EMOJI['copy']} Копировать", callback_data="copy"),
            InlineKeyboardButton(f"{EMOJI['refresh']} Ещё", callback_data="regenerate")
        ],
        [InlineKeyboardButton(f"{EMOJI['settings']} Настройки", callback_data="show_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"""
{EMOJI['generate']} <b>ТВОЙ ПАРОЛЬ ГОТОВ!</b>

<code>{password}</code>

<b>Параметры:</b>
{EMOJI['length']} Длина: {settings['length']} символов

<b>Надежность:</b> {strength}
    """
    
    await query.edit_message_text(message, parse_mode='HTML', reply_markup=reply_markup)

def get_password_strength(password):
    """Определяет надежность пароля"""
    score = 0
    
    # Длина
    if len(password) >= 16:
        score += 3
    elif len(password) >= 12:
        score += 2
    elif len(password) >= 8:
        score += 1
    
    # Разные типы символов
    if any(c in LOWERCASE for c in password):
        score += 1
    if any(c in UPPERCASE for c in password):
        score += 1
    if any(c in DIGITS for c in password):
        score += 1
    if any(c in SYMBOLS for c in password):
        score += 2
    
    # Оценка
    if score >= 7:
        return "🟢 Отличный", "green"
    elif score >= 5:
        return "🟡 Хороший", "yellow"
    elif score >= 3:
        return "🟠 Средний", "orange"
    else:
        return "🔴 Слабый", "red"

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь"""
    help_text = """
🔐 <b>ГЕНЕРАТОР ПАРОЛЕЙ - ПОМОЩЬ</b>

<b>Основные команды:</b>
/password [длина] - сгенерировать пароль
/settings - настроить параметры
/help - это сообщение

<b>Примеры:</b>
• /password - стандартный пароль (12 символов)
• /password 20 - пароль 20 символов
• /password strong - очень надежный пароль
• /password simple - простой пароль

<b>В настройках можно:</b>
• Установить длину (4-64 символа)
• Включить/выключить буквы, цифры, символы
• Сбросить настройки

<b>Советы по безопасности:</b>
✅ Используй 12+ символов
✅ Добавляй цифры и спецсимволы
✅ Не используй личные данные
✅ Для каждого сайта - свой пароль
    """
    
    await update.message.reply_text(help_text, parse_mode='HTML')

def main():
    """Запуск бота"""
    print("=" * 50)
    print("🔐 ЗАПУСК ГЕНЕРАТОРА ПАРОЛЕЙ")
    print("=" * 50)
    
    if TOKEN == 'ВАШ_ТОКЕН_СЮДА':
        print("⚠️ ВНИМАНИЕ: Замени 'ВАШ_ТОКЕН_СЮДА' на реальный токен!")
        print("📱 Получи токен у @BotFather в Telegram")
        return
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("password", generate_password))
    app.add_handler(CommandHandler("settings", settings_menu))
    app.add_handler(CommandHandler("help", help_command))
    
    # Обработчик кнопок
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Бот запущен! Нажми Ctrl+C для остановки")
    print("📱 Отправь /start боту в Telegram")
    print("=" * 50)
    
    # Запускаем бота
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
