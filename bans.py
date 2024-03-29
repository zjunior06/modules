import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Parece que você não está se referindo a um usuário.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuário não encontrado":
            message.reply_text("Não consigo encontrar este usuário")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Eu queria muito banir admins...")
        return ""

    if user_id == bot.id:
        message.reply_text("Eu não vou me banir, tá doido?")
        return ""

    log = "<b>{}:</b>" \
          "\n#BANIDO" \
          "\n<b>Admin:</b> {}" \
          "\n<b>Usuário:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Motivo:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Banido!")
        return log

    except BadRequest as excp:
        if excp.message == "Mensagem não encontrada!":
            # Do not reply
            message.reply_text('Banido!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERRO ao banir o usuário %s no chat %s (%s) ID %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Ops. Não posso banir esse usuário.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Você não está se referindo a nenhum usuário.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Não consigo encontrar esse usuário")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Eu queria muito banir admins...")
        return ""

    if user_id == bot.id:
        message.reply_text("Eu não vou me banir, tá doido?")
        return ""

    if not reason:
        message.reply_text("Você não especificou por quanto tempo devo banir esse usuário!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#BANIDO TEMPORARIAMENTE" \
          "\n<b>Admin:</b> {}" \
          "\n<b>Usuário:</b> {} (<code>{}</code>)" \
          "\n<b>Tempo:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name),
                                     member.user.id,
                                     time_val)
    if reason:
        log += "\n<b>Motivo:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Banido! Usuário ficará banido por {}.".format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "Mensagem não encontrada!":
            # Do not reply
            message.reply_text("Banido! Usuário ficará banido por {}.".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERRO ao banir o usuário %s no chat %s (%s) ID %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Ops, não posso banir esse usuário.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuário não encontrado.":
            message.reply_text("Não consigo encontrar esse usuário.")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("Eu queria muito kickar admins...")
        return ""

    if user_id == bot.id:
        message.reply_text("Mehhhh eu não vou fazer isso.")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Kicked!")
        log = "<b>{}:</b>" \
              "\n#KICKADO" \
              "\n<b>Admin:</b> {}" \
              "\n<b>Usuário:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                           mention_html(user.id, user.first_name),
                                                           mention_html(member.user.id, member.user.first_name),
                                                           member.user.id)
        if reason:
            log += "\n<b>Motivo:</b> {}".format(reason)

        return log

    else:
        message.reply_text("Ops, eu não posso kickar esse usuário.")

    return ""


@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Eu queria... mas você é admin!")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("Beleza.")
    else:
        update.effective_message.reply_text("Hm? Eu não posso :/")


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuário não encontrado.":
            message.reply_text("Não consigo encontrar esse usuário.")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Como eu iria me desbanir se eu não estava aqui...?")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("Por quê você está tentando desbanir alguém que já está no chat?")
        return ""

    chat.unban_member(user_id)
    message.reply_text("Beleza, pode entrar!")

    log = "<b>{}:</b>" \
          "\n#DESBANIDO" \
          "\n<b>Admin:</b> {}" \
          "\n<b>Usuário:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Motivo:</b> {}".format(reason)

    return log


__help__ = """
 - /kickme: kicks the user who issued the command

*Admin only:*
 - /ban <userhandle>: bans a user. (via handle, or reply)
 - /tban <userhandle> x(m/h/d): bans a user for x time. (via handle, or reply). m = minutes, h = hours, d = days.
 - /unban <userhandle>: unbans a user. (via handle, or reply)
 - /kick <userhandle>: kicks a user, (via handle, or reply)
"""

__mod_name__ = "Bans"

BAN_HANDLER = CommandHandler("ban", ban, pass_args=True, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)