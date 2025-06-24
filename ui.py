from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup_ui_handlers(bot, AUTHORIZED_USERS, save_auth, is_authorized):

    @bot.message_handler(commands=['start'])
    def start_handler(msg):
        user_id = msg.from_user.id
        user_name = msg.from_user.first_name or "User"
        username = msg.from_user.username
        display = username if username else user_name

        caption = (
            "<b>[⌬] BUNNY | Version - 1</b>\n"
            "━━━━━━━━━━━━━\n"
            f"Hello, <b>{display}</b>\n"
            "How Can I Help You Today.?! 📊\n"
            f"👤 <b>Your UserID</b> - <code>{user_id}</code>\n"
            "🤖 <b>BOT Status</b> - <b>Online 🟢</b>\n"
        )

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("Register", callback_data="register"),
            InlineKeyboardButton("Command", callback_data="command")
        )
        kb.add(InlineKeyboardButton("Close", callback_data="close"))

        with open('6b08ab9dc9f305652657a5aead75742e.jpg', 'rb') as photo:
            bot.send_photo(
                msg.chat.id,
                photo,
                caption=caption,
                parse_mode="HTML",
                reply_markup=kb,
                reply_to_message_id=msg.message_id,
                disable_notification=False
            )

    @bot.callback_query_handler(func=lambda call: call.data == "register")
    def handle_register(call):
        user_id = str(call.from_user.id)
        already = user_id in AUTHORIZED_USERS
        AUTHORIZED_USERS[user_id] = "forever"
        save_auth(AUTHORIZED_USERS)
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("Register", callback_data="register"),
            InlineKeyboardButton("Command", callback_data="command")
        )
        kb.add(InlineKeyboardButton("Close", callback_data="close"))
        msg_text = (
            "✅ <b>Registration Complete!</b>\n"
            "You are now registered, <b>{}</b>.".format(call.from_user.first_name)
            if not already else
            "ℹ️ <b>You are already registered, <b>{}</b>!</b>".format(call.from_user.first_name)
        )
        bot.edit_message_text(
            msg_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "command")
    def command_menu_handler(call):
        text = (
            "<b>JOIN BEFORE USING. ✅</b>\n"
            "- Main : <a href='https://t.me/approvedccm'>Join Now</a>\n"
            "- Chat Group : <a href='https://t.me/approvedccm'>Join Now</a>\n"
            "- Scrapper : <a href='https://t.me/+jLj5grD0l_Y5ZmU1'>Join Now</a>\n\n"
            "Choose Your Gate Type :"
        )
        kb = InlineKeyboardMarkup(row_width=3)
        kb.add(
            InlineKeyboardButton("Gate", callback_data="gate"),
            InlineKeyboardButton("Tools", callback_data="tools"),
            InlineKeyboardButton("Terms", callback_data="terms")
        )
        kb.add(InlineKeyboardButton("Close", callback_data="close"))
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb,
            disable_web_page_preview=True
        )

    @bot.callback_query_handler(func=lambda call: call.data == "gate")
    def handle_gate_menu(call):
        text = (
            "BUNNY [ALL GATES]\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "【✦】Name: Braintree Auth\n"
            "【✦】Commands:\n"
            "【✦】<code>/b3 cc|mm|yy|cvv</code> — Single check\n"
            "【✦】<code>/mb3</code> — Mass check (max 20 cards)\n"
            "【✦】Status: <b>Active ✅</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "【✦】Name: Stripe Auth 1$\n"
            "【✦】Command: <code>/stripe1</code>\n"
            "【✦】Status: <b>Active ✅</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "【✦】Name: Stripe Auth\n"
            "【✦】Command: <code>/stripe</code>\n"
            "【✦】Status: <b>Off ❌</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "【✦】Name: Shopify $1 Auth\n"
            "【✦】Command: <code>/shopify1</code>\n"
            "【✦】Status: <b>Off ❌</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("Back", callback_data="command"),
            InlineKeyboardButton("Next", callback_data="gate_next")
        )
        bot.edit_message_text(
            text, call.message.chat.id, call.message.message_id,
            parse_mode="HTML", reply_markup=kb,
            disable_web_page_preview=True
        )

    @bot.callback_query_handler(func=lambda call: call.data == "tools")
    def handle_tools_menu(call):
        text = (
            "BUNNY [TOOLS]\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "【✦】Name: CC Scrapper\n"
            "【✦】Command: <code>$scr channel_username 100</code>\n"
            "【✦】Limit: 5k\n"
            "【✦】Status: <b>Active ✅</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "【✦】Name: Bin Info\n"
            "【✦】Command: <code>/bin bin/cc</code>\n"
            "【✦】Status: <b>Active ✅</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "【✦】Name: Card Generator\n"
            "【✦】Command: <code>/gen bin [qty]</code>\n"
            "【✦】Status: <b>Active ✅</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "【✦】Name: Fake Random Details\n"
            "【✦】Command: <code>/fake [country]</code>\n"
            "【✦】Status: <b>Active ✅</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("Back", callback_data="command"),
            InlineKeyboardButton("Next", callback_data="tools_next")
        )
        bot.edit_message_text(
            text, call.message.chat.id, call.message.message_id,
            parse_mode="HTML", reply_markup=kb,
            disable_web_page_preview=True
        )

    @bot.callback_query_handler(func=lambda call: call.data == "tools_next")
    def handle_tools_next_menu(call):
        text = (
            "BUNNY [TOOLS - PAGE 2]\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "【✦】Name: Image Generator\n"
            "【✦】Command: <code>/img [prompt]</code>\n"
            "【✦】Status: <b>Active ✅</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "【✦】Name: Gateway Fider\n"
            "【✦】Command: <code>/url</code>\n"
            "【✦】Status: <b>Active ✅</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "【✦】Name: CC Filter\n"
            "【✦】Command: <code>/fl</code>\n"
            "【✦】Status: <b>Active ✅</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("Back", callback_data="tools"),
            InlineKeyboardButton("Close", callback_data="close")
        )
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb,
            disable_web_page_preview=True
        )

    @bot.callback_query_handler(func=lambda call: call.data == "terms")
    def handle_terms_menu(call):
        text = (
            "BUNNY [TERMS]\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ Disclaimer: The information shared is sourced solely from public domains. We do not collect, store, or distribute any private or sensitive data.\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Back", callback_data="command"))
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=kb,
            disable_web_page_preview=True
        )

    @bot.callback_query_handler(func=lambda call: call.data == "close")
    def close_menu(call):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
