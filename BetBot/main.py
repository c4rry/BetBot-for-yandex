import csv
import re
import time
import datetime
from random import choice

import requests
import telegram
from bs4 import BeautifulSoup

import tg_result
# Нужно устанавливать:
# python-telegram-bot --upgrade
# requests BeautifulSoup4 lxml

# Добавить потом:
# from multiprocessing import Pool
# from datetime import datetime
# Время работы бота: с 10:00 до 21:30

bot = telegram.Bot(token='5ВВВВ') # Указать токен бота

matches = []  # все ссылки на успешные матчи

def get_proxy():
    try:
        # if len(proxies) != 0:
        #    return choice(proxies)
        try:
            html = requests.get('https://free-proxy-list.net').text
            soup = BeautifulSoup(html, 'lxml')

            trs = soup.find('table', id='proxylisttable').find_all('tr')[1:]

            proxies = []

            for tr in trs:
                try:
                    tds = tr.find_all('td')
                    ip = tds[0].text.strip()
                    port = tds[1].text.strip()
                    schema = 'https'

                    if 'yes' not in tds[6].text.strip():
                        continue
                    # schema = 'https' if 'yes' in tds[6].text.strip() else 'http'
                    proxy = {'schema': schema, 'address': ip + ':' + port}
                    proxies.append(proxy)
                except:
                    continue
        except:
            print('Troubles w/ proxies')
            return False

        return choice(proxies)
    except:
        return False


def get_html(url):
    try:
        p = get_proxy()
        proxy = {p['schema']: p['address']}
        print(proxy)
        user_agent = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15'}
        r = requests.get(url, headers=user_agent, proxies=proxy, timeout=60)
        if r.ok:  # ok=kod 200 true
            return r.text
    except:
        while True:
            try:
                r = requests.get(url)
                print(r.status_code)
                return r.text
                # print(r.status_code)
            except:
                time.sleep(30)


def write_csv(data):
    now = datetime.datetime.now()
    if (int(now.hour) >= 22) | (int(now.hour) < 10):
        #time.sleep(10 * 60 * 60)  # Сон на 10 часов, если время 22 часа
        file_name = 'football_' + str(now.date()) + '_night.csv'
    else:
        file_name = 'football_' + str(now.date()) + '.csv'

    with open(file_name, 'a') as f:
        order = ['country', 'time', 'names', 'score', 'link', 'PenTB', 'bet_type']
        writer = csv.DictWriter(f, fieldnames=order)
        # writer.writeheader()
        writer.writerow(data)


def country_check(j, score_data):
    bad_countries = ['США', 'РОССИЯ', 'КОРЕЯ', 'ЧЕХИЯ', 'ПОЛЬША', 'АВСТРИЯ', 'РУМЫНИЯ', 'АЗЕРБАЙДЖАН',
                     'УЗБЕКИСТАН', 'ИНДИЯ']  # список плохих стран

    bad_ligues = ['ЖЕН', 'U\d{2}', 'МОЛОД', 'WOMEN', 'ТОВАРИЩ', 'ДО \d{2} ЛЕТ', 'ЮНИОРОВ', 'МЛАДШАЯ','ЛИГА ЧЕМПИОНОВ','ЛИГА ЕВРОПЫ']
    match = ''  # название матча
    if score_data.find_all('a')[j].previous_element != ' ':
        match = score_data.find_all('a')[j].previous_element
    else:
        match = score_data.find_all('a')[j].previous_element.previous_element.previous_element

    while str(score_data.find_all('span', class_='live')[j].previous_element) == '<br/>':
        j -= 1
    ligue = str(score_data.find_all('span', class_='live')[j].previous_element)

    for reason in (bad_countries + bad_ligues):
        if re.search(reason, ligue.upper()):
            return ligue + ' 0'

    if re.search('U\d{2}', match) or re.search('(Ж)', match):  # молодежка или женщинч
        return match + 'Young or femail 0'

    return ligue + ' 1'  # название лиги


def penalti_check(goals):
    try:
        pattern = re.compile('Пенальти')
        str_pen = str(goals[-1].next_element.next_element).strip()  # строка с голом

        if pattern.findall(str_pen):  # если гол с пенальти не первый
            team = (str_pen.split('[')[1]).split(']')[0]
            print('Penalti')
            return '1', team
        else:
            # print('No penalti')
            return '0', ''
    except:
        return '0', ''


def total_check(goals):
    try:
        first_goal = int(goals[0].previous_element[:-1])
        sec_goal = int(goals[1].previous_element[:-1])
        if (first_goal in range(3, 12)) and (sec_goal in range(12, 23)) and (
                abs(first_goal - sec_goal) in range(7, 12)):
            print('TB 2.5')
            return 1  # матч подходит под ТБ в первом 2.5
        else:
            # print('NO TB')
            return 0
    except:
        return 0


def coef_check(soup, scored_team):
    try:
        coefs = soup.find('p', class_='p-set odds-detail').find_all('a', target='_blank')
        if coefs:  # если коэфы даны на странице
            team1 = soup.find('title').text.split(' ')[0]
            team2 = soup.find('title').text.split(' ')[2]

            if (float(coefs[0].text) < 1.91) and (float(coefs[0].text) < float(coefs[2].text)):
                if team1 == scored_team:
                    return 'fav'
                else:
                    return 'out'
            elif (float(coefs[2].text) < 1.91) and (float(coefs[2].text) < float(coefs[0].text)):
                if team2 == scored_team:
                    return 'fav'
                else:
                    return 'out'
            else:
                return 'bad'
        else:
            return 'bad'
    except:
        return 'NDA'


def get_match_data(html, countries):
    try:
        soup = BeautifulSoup(html, 'lxml')
    # events = soup.find('div', id='detail-tab-content').find_all('div', class_='incident soccer')#все события матча
    # проверка на красную карточку или автогол
        if re.search(r'Автогол', ''.join(
                [m.text for m in
                 soup.find('div', id='detail-tab-content').find_all('div', class_='incident soccer')])) or (
                soup.find('p', class_='i-field icon r-card')):
            return 0, 0
    except:
        return 0, 0

    try:
        goals = soup.find('div', id='detail-tab-content').find_all('p', class_='i-field icon ball')
        result = ''  # первый - пенальти, второй - тотал
        result, scored_team = penalti_check(goals)
        scored_team = coef_check(soup, scored_team)  # меняем значение на фаворита или аута
        if (len(goals) > 1) & (scored_team == 'fav'):  # если гол с пенальти не первый
            result = '0'

        result += str(total_check(goals))

        bet_type = 'Тотал '
        sum_score = float(soup.find('h4').find('b').text[0]) + float(
            soup.find('h4').find('b').text[-1])  # суммарный счет
        if int(result) >= 10:  # если есть пенальти
            if scored_team == 'fav':
                sum_score += 1.5
                bet_type += 'больше ' + str(sum_score)
                    # C1 - пенальти, забил аутсайдер
                    # C2 - пенальти, забил фаворит, но не первый гол
                    # C3 - пенальти, нет явного фаворита
                    # A - пенальти, забил фаворит первым голом
                    # B - ТБ2.5
                bet_type += ' [alg A]'

            elif scored_team == 'out':
                sum_score += 1.0
                bet_type += 'больше ' + str(int(sum_score))
                bet_type += '  [alg C1]'

            elif scored_team == 'bad':
                sum_score += 1.0
                bet_type += 'больше ' + str(int(sum_score))
                bet_type += '  [alg C3]'

            elif scored_team == 'NDA':
                bet_type += 'игры узнавайте у саппорта. Код NDA ' + str(int(sum_score))
            # elif scored_team == 'bad':
            #    sum_score += 1.5
            #    bet_type += 'больше ' + str(sum_score)
            #    bet_type += '. ПОНИЖЕННАЯ ПРОХОДИМОСТЬ'
            else:
                list(result)[0] = '0'

            bet_type += '\n Ставить при коэффициенте не менее 1.55'

            #if (len(goals) > 1) and (scored_team not in ['bad', 'out']):  # ели гол с пенальти не первый
            #    bet_type += '. [alg C2]'


        elif int(result) == 1:  # если по страте ТБ
            good_countries = ['ПЕРУ', 'САУДОВСКАЯ', 'ИТАЛИЯ', 'ИРЛАНДИЯ', 'СЛОВЕНИЯ', 'ГЕРМАНИЯ', 'ГОЛЛАНДИЯ',
                              'БРАЗИЛИЯ',
                              'СЕРБИЯ', 'ГРЕЦИЯ', 'ШОТЛАНДИЯ']
            bet_len = len(bet_type)  # длина строки с прогнозом
            for country in good_countries:
                if re.search(country, countries.upper()):
                    if country in ['СЛОВЕНИЯ', 'ГЕРМАНИЯ', 'ГОЛЛАНДИЯ', 'БРАЗИЛИЯ', 'СЕРБИЯ', 'ГРЕЦИЯ', 'ШОТЛАНДИЯ']:
                        bet_type += 'первого тайма больше 2.5 [alg B]'

                    elif country in ['ПЕРУ', 'САУДОВСКАЯ', 'ИТАЛИЯ', 'ИРЛАНДИЯ']:
                        if country == 'ИТАЛИЯ':
                            bet_type += 'второго тайма больше 0.5 [alg B]'
                        else:
                            bet_type += 'второго тайма больше 1 [alg B]'

            if bet_len == len(bet_type):
                #bet_type += 'в первом тайме больше 2.5. НЕОПРАВДАНО ВЫСОКИЙ РИСК'
                return 0, 0

        # bet_type += str(sum_score)
        return int(result), bet_type
    except:
        return 0, 0
        # first_goal = events.find('p', class_='i-field time')
        # sec_goal = events.find('p', class_)
    # print(events)


def tg_msg(data):
    seen_link = data['link'].replace('http://m', 'https://www')
    while True:
        try:
            bot.send_message(chat_id=-100,  #указать группу, куда присылать прогноз
                             text=data['country'][:-2] + '\n' + data['names'] + '\n' + seen_link + '\n\n' + data[
                                 'bet_type'])
            break
        except Exception:
            time.sleep(15)
    # bot.send_message(chat_id='@NikArt_blog',
    #                 text=data['country'][:-2] + '\n' + data['names'] + '\n' + seen_link + '\n\n' + data['bet_type'])


def get_data(html):  # получить данные из html-кода страницы
    try:
        soup = BeautifulSoup(html, 'lxml')  # преобразовать в дерево объектов питона
        # передав его в конструктор (html-код, название парсера)
        score_data = soup.find('div', id='score-data')

        if len(score_data.find_all('a')) == 0:
            return
    except:
        return
    link = []  # ссылки на трансляции
    score = []  # счет матча
    names = []  # матч
    time = []  # время матча
    country = []  # стран а проведения матча

    for i in range(0, len(score_data.find_all('a'))):
        # for i in range(0,2):
        domain = 'http://m.myscore.ru'
        try:
            country.append(country_check(i, score_data))
        except:
            country.append(' 0')
        try:
            time.append(int((re.match('\d{2}', score_data.find_all('span', class_='live')[i].text)).group(0)))
        except:
            time.append(404)  # ошибка
        # names.append(score_data.find_all('a')[i].previous_element)
        try:
            link.append(domain + score_data.find_all('a')[i].get('href'))
        except:
            link.append('')
        try:
            score.append(score_data.find_all('a')[i].text)
        except:
            score.append('')
        try:
            if score_data.find_all('a')[i].previous_element != ' ':
                names.append(score_data.find_all('a')[i].previous_element)
            else:
                names.append(score_data.find_all('a')[i].previous_element.previous_element.previous_element)
        except:
            names.append('')

        if (time[i] not in range(0, 46)) or (country[i][-1] != '1'):  # если не первый тайм или плохая лига
            continue

        pen_tb, bet_type = get_match_data(get_html(link[i]), country_check(i, score_data))

        # print(PenTB)
        # print(country[i].split(':')[0])
        # try:
        #    if (country[i].split(':')[0] in ['АВСТРИЯ', 'ПОЛЬША', 'РУМЫНИЯ']) and (bet_type.split(' ')[1] != 'меньше'):
        #        continue
        # except:
        #    continue

        if (pen_tb != 0) and (link[i] not in matches):
            data = {'country': country[i],
                    'time': time[i],
                    'names': names[i],
                    'score': score[i],
                    'link': link[i],
                    'PenTB': pen_tb,
                    'bet_type': bet_type}
            print(data)
            print(matches)
            try:
                matches.append(link[i])
                print(matches)
            except:
                print('Матчик не добавлен(')

            now = datetime.datetime.now()
            if not ((int(now.hour) >= 22) | (int(now.hour) < 10)):
                tg_msg(data)

            try:
                write_csv(data)
            except:
                print('did not written')


def main():
    url = 'http://m.myscore.ru/?s=2'

    # get_data(get_html(url))
    i = 1
    flag_stat = True
    while True:
        now = datetime.datetime.now()
        get_data(get_html(url))
        i += 1
        if (int(now.hour) == 23) & flag_stat:
            try:
                tg_result.tg_res()
            except:
                print('Стата не выложена. Ошибка или отсутсвует файл')
            flag_stat = False
        elif (not flag_stat) & (not (int(now.hour) == 23)):
            flag_stat = True
        time.sleep(1 * 60)  # Сон на минуту (Для тестовых целей указать меньшее число)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
