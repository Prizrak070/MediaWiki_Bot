import telebot
import re
import search_module
import json
from telebot import types

with open ('config.json', 'rb') as f:
    config = json.load(f)



def refactor(text_list, title):
    '''
    Удаляет весь непереводимый для телеграмма wikitext.
    Вытаскивает ссылки из текста
    :param text_list: str на вход текст, для правки
    :param title: str заголовок страницы
    :return: text_list - str измененный текст | links - list список ссылок (названий страниц)
    '''
    text_list = f'$ {title} $\n{text_list}'
    # добавляем к заголовку основной текст.
    # Заголовок нужен для обработки inline кнопок

    links = re.findall("'''\[\[(.+)\]\]'''", text_list)
    text_list = re.sub("'''\[\[", 'страница: ', text_list)
    text_list = re.sub("\]\]'''", '', text_list)
    text_list = re.sub('(&lt;accesscontrol>.+>)'
                       '|(&lt;br \/>)'
                       '|(&lt;span style="color:red">)'
                       '|(&lt;\/span>)'
                       '|(\|title.center=)'
                       '|(\|title-right=)'
                       '|(\|content-left=)'
                       '|(\|title-left=)'
                       '|({{ycgu-cooltable-3)'
                       '|(\|content-center=)'
                       '|(\|content-right=)'
                       '|(&lt;br \/>)'
                       '|(&lt;p class="mw_paragraph">)'
                       '|(&lt;ul>&lt;li class="mw_paragraph">)'
                       '|(&lt;\/li>&lt;\/ul>)'
                       '|({\| class="wikitable"\n\|-\n!)'
                       '|(\|})|(\[tel:[\d\+\-]+)|(\])'
                       '|(# \[\[)|(amp;)|(\[\[)'
                       '|(\{ class="wikitable sortable" (.)+)' # здесь начато новое
                       '|(\n\n)'
                       '|(! style="width: .+")'
                       '|( style="width: .+")'
                       '|( style="height: .+")'
                       '|( )'
                       '|(&lt;span.+>)', '', text_list)
    text_list = re.sub('(\|)|(-)|(!!)', '', text_list)
    text_list = re.sub('\[mailto:[\w\.\d@]+', '', text_list)
    text_list = re.sub('Текст ячейки', '', text_list)



    return text_list, links


def check_id_status(id):
    """
    Проверяет ID на совпадение в White_List'e
    :param id: id пользователя для проверки
    :return: False или True в зависимости от нахождения в списке
    """

    f = open('white_list.txt', 'r')
    for line in f:
        if re.search('\d\d\d\d\d\d\d\d\d', line).group(0) == str(id):
            f.close()
            return(True)




# БОТ ЧАСТЬ ----------------------------------------------------------------------------



bot = telebot.TeleBot(config["token"])

@bot.message_handler(commands=['test'])
def recent_changes(message):
    if check_id_status(message.from_user.id):
        search_module.recent_changes()



@bot.message_handler(commands=['status'])
def status(message):
    '''
    Отладочная команда. Проверка статуса работы бота.
    :param message:
    :return: текущий статус
    '''
    if check_id_status(message.from_user.id):
        bot.send_message(message.chat.id, "i'm okey")

@bot.message_handler(commands=['start'])
def start(message):
    '''
    При запуске бота происходит проверка на возможность общения с ним
    '''
    if check_id_status(message.from_user.id): # Проверка на соответствие списку
        bot.send_message(message.chat.id, "Приветствую! Ваш ID есть в спике, приятного пользования :)")
    else:
        print(message.from_user.id) # При необходимости добавления нового пользователя
        bot.send_message(message.chat.id, "К сожалению Вашего ID нет в списках. "
                                          "Возможно произошла какая-то ошибка? "
                                          "Обратитесь к системному администратору")

@bot.message_handler(commands=['search'])
def search(message):
    '''
    Пытается найти страницы на вики по запросу пользователя.
    Синтаксис "/search text_to_search"
    При успешном нахождении отправляет сообщения в виде Inline кнопок
    :param message: str слово на поиск
    '''
    if check_id_status(message.chat.id):
        try:
            page, head = search_module.searching(re.search('(/search)(.+)', message.text).group(2))
            mark = types.InlineKeyboardMarkup(row_width=3)
            a = 0
            if len(head) != 0 or len(page) != 0:
                if len(head) != 0:
                    for i in head:
                        a += 1
                        mark.add(types.InlineKeyboardButton(text=i, callback_data= a))
                    mark.add(types.InlineKeyboardButton(text='Закрыть ❌', callback_data='page 0'))
                    bot.send_message(message.chat.id, text="Найденные страницы", reply_markup=mark)
                mark = types.InlineKeyboardMarkup()
                a = 0
                if len(page) != 0:
                    for i in page:
                        a += 1
                        mark.add(types.InlineKeyboardButton(text=i, callback_data= a))
                    mark.add(types.InlineKeyboardButton(text='Закрыть ❌', callback_data='page 0'))
                    bot.send_message(message.chat.id, text="Найденно совпадение внутри страниц",
                                     reply_markup=mark)
            else:
                bot.send_message(message.chat.id, text="Похоже ничего не найдено...")
        except Exception as e:
            print(e)
            bot.send_message(message.chat.id, 'Ошибка запроса. Попробуйте "/search ваш текст"')




@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    '''
    Прослушивание нажатий по Inline кнопкам
    '''
    if check_id_status(call.from_user.id):
        page_name = re.search('\$ (.+) \$' ,call.message.text)
        if call.data == 'page 0':
            bot.delete_message(call.message.chat.id, call.message.id)

        elif page_name != None and call.data[:4] == 'page':
            page_name = page_name.group(1)

            if call.data[5:] != '' and int(call.data[5:]) > 1:
                numb = int(call.data[5:])
                text_content = refactor(search_module.content(page_name),
                                        page_name)[0][numb * 1000 - 1000 : numb * 1000]
                bot.edit_message_text(f'$ {page_name} $\n{text_content}',
                                      call.message.chat.id, call.message.id)
                mark = types.InlineKeyboardMarkup()
                mark.add(types.InlineKeyboardButton(text=f'Назад {numb - 1}',
                                                    callback_data=f'page {numb - 1}'))
                mark.add(types.InlineKeyboardButton(text='Закрыть ❌', callback_data='page 0'))
                mark.add(types.InlineKeyboardButton(text=f'Вперед {numb + 1}',
                                                    callback_data=f'page {numb + 1}'))
                bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                              message_id=call.message.id, reply_markup=mark)

            elif call.data[5:] != '' and int(call.data[5:]) == 1:
                text_content = refactor(search_module.content(page_name),
                                        page_name)[0][0:1000]
                bot.edit_message_text(f'$ {page_name} $\n{text_content}',
                                      call.message.chat.id, call.message.id)
                mark = types.InlineKeyboardMarkup()
                mark.add(types.InlineKeyboardButton(text='Закрыть ❌', callback_data='page 0'))
                mark.add(types.InlineKeyboardButton(text='Вперед [2]', callback_data='page 2'))
                bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                              message_id=call.message.id, reply_markup=mark)

        else:
            for i in call.message.json['reply_markup']['inline_keyboard']:
                if call.data == i[0]['callback_data']:
                    mark = types.InlineKeyboardMarkup()
                    text_content, links = refactor(search_module.content(i[0]['text']), i[0]['text'])
                    a = 0
                    for i in links:
                        a += 1
                        mark.add(types.InlineKeyboardButton(text=i, callback_data=a))
                    if len(text_content) > 1000:
                        # button = types.InlineKeyboardMarkup()
                        mark.add(types.InlineKeyboardButton(text='Закрыть ❌', callback_data='page 0'))
                        mark.add(types.InlineKeyboardButton(text='Вперед [2]', callback_data='page 2'))
                        bot.send_message(call.message.chat.id, text_content[0:1000], reply_markup=mark)
                        # print(len(text_content))
                        print('Сообщение больше 2000 символов')
                    else:
                        # mark.add(types.InlineKeyboardButton
                        # (text='Закрыть ❌', callback_data='page 0'))
                        mark.add(types.InlineKeyboardButton(text='Закрыть ❌', callback_data='page 0'))
                        bot.send_message(call.message.chat.id, text_content, reply_markup=mark)
        # except Exception as e:
        #     print(e)








bot.polling()
