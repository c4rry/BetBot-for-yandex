import csv
import emoji
import re
import time
import datetime
from random import choice
import requests
import telegram
from bs4 import BeautifulSoup

bot = telegram.Bot(token='AAAA') # указать токен бота


def get_proxy():
    try:
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
                    proxy = {'schema': schema, 'address': ip + ':' + port}
                    proxies.append(proxy)
                except:
                    continue
        except:
            return False

        return choice(proxies)
    except:
        return False


def get_html(url):
    try:
        p = get_proxy()
        proxy = {p['schema']: p['address']}
        # #print(proxy)
        user_agent = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15'}
        r = requests.get(url, headers=user_agent, proxies=proxy, timeout=10)
        if r.ok:  # ok=kod 200 true
            return r.text
    except:
        while True:
            try:
                r = requests.get(url)
                #print(r.status_code)
                return r.text
                # #print(r.status_code)
            except:
                time.sleep(5)


def read_csv(name, tg_text):
    pA = 0.
    nA = 0.

    pC1 = 0.
    nC1 = 0.

    pC2 = 0.
    nC2 = 0.

    pC3 = 0.
    nC3 = 0.

    pB = 0.
    nB = 0.

    positive = 0.
    negative = 0.
    return_bet = 0.
    total = 0.

    risk_p = 0.
    risk_n = 0.

    bank = 100.  # банк на начало дня
    coef = 1.55  # минимальная ставка при коэф. 1.5
    bet_bank = 7. / 100.  # ставка в процентах от банка

    with open(name, encoding='cp1251') as f:
        order = ['country', 'time', 'names', 'score', 'link', 'PenTB', 'bet_type', 'result']
        reader = csv.DictReader(f, fieldnames=order)

        for data in reader:
            soup = BeautifulSoup(get_html(data['link']), 'lxml')
            final_score = 0.

            if re.search('первого тайма больше ', str(data['bet_type'])) or re.search('второго тайма больше ',
                                                                                      str(data['bet_type'])):

                if re.search('первого тайма больше ', str(data['bet_type'])):  # ставка на первый тайм тотал больше
                    final_score = float(soup.find_all('b')[1].text[0]) + float(
                        soup.find_all('b')[1].text[-1])  # результат

                if re.search('второго тайма больше ', str(data['bet_type'])):  # ставка на второй тайм тотал больше
                    final_score = float(soup.find_all('b')[2].text[0]) + float(
                        soup.find_all('b')[2].text[-1])  # результат

                bet = float(str(data['bet_type']).split(' ')[4])  # ставка на ТБ

                if final_score > bet:
                    #    seen_link = data['link'].replace('http://m', 'https://www')
                    #    #print(data['country'][:-2] + '\n' + data['names'] + '\n' + seen_link + '\nПрогноз:' + data[
                    #        'bet_type'] + '\nИтог: Тотал первого тайма - ' + str(int(final_score)))
                    tg_text += emoji.emojize('\n:white_check_mark: ' + data['names'], use_aliases=True)

                    if re.search('alg A', str(data['bet_type'])):
                        pA += 1.

                    elif re.search('alg B', str(data['bet_type'])):
                        pB += 1.

                    elif re.search('alg C1', str(data['bet_type'])):
                        pC1 += 1.

                    elif re.search('alg C2', str(data['bet_type'])):
                        pC2 += 1.

                    elif re.search('alg C3', str(data['bet_type'])):
                        pC3 += 1.

                    positive += 1.
                    # bank += (coef - 1) * bet_bank * bank

                elif final_score < bet:
                    tg_text += emoji.emojize('\n:x: ' + data['names'], use_aliases=True)

                    if re.search('alg A', str(data['bet_type'])):
                        nA += 1.

                    elif re.search('alg B', str(data['bet_type'])):
                        nB += 1.

                    elif re.search('alg C1', str(data['bet_type'])):
                        nC1 += 1.

                    elif re.search('alg C2', str(data['bet_type'])):
                        nC2 += 1.

                    elif re.search('alg C3', str(data['bet_type'])):
                        nC3 += 1.

                    negative += 1.
                    # bank = bank * (1 - bet_bank)


                else:
                    tg_text += emoji.emojize('\n♻️ ' + data['names'], use_aliases=True)
                    return_bet += 1.

                total += 1.

            if re.search('Тотал больше ', str(data['bet_type'])):  # ставка на тотал больше

                final_score = float(soup.find_all('b')[0].text[0]) + float(soup.find_all('b')[0].text[-1])  # результат
                bet = float(str(data['bet_type']).split(' ')[2])  # прогноз

                if final_score > bet:
                    tg_text += emoji.emojize('\n:white_check_mark: ' + data['names'], use_aliases=True)

                    if re.search('alg A', str(data['bet_type'])):
                        pA += 1.

                    elif re.search('alg B', str(data['bet_type'])):
                        pB += 1.

                    elif re.search('alg C1', str(data['bet_type'])):
                        pC1 += 1.

                    elif re.search('alg C2', str(data['bet_type'])):
                        pC2 += 1.

                    elif re.search('alg C3', str(data['bet_type'])):
                        pC3 += 1.

                    positive += 1.

                elif final_score < bet:
                    tg_text += emoji.emojize('\n:x: ' + data['names'], use_aliases=True)

                    if re.search('alg A', str(data['bet_type'])):
                        nA += 1.

                    elif re.search('alg B', str(data['bet_type'])):
                        nB += 1.

                    elif re.search('alg C1', str(data['bet_type'])):
                        nC1 += 1.

                    elif re.search('alg C2', str(data['bet_type'])):
                        nC2 += 1.

                    elif re.search('alg C3', str(data['bet_type'])):
                        nC3 += 1.

                    negative += 1.

                else:
                    tg_text += emoji.emojize('\n♻️ ' + data['names'], use_aliases=True)
                    return_bet += 1.

                total += 1.

            if re.search('первого тайма меньше ', str(data['bet_type'])) or re.search('второго тайма меньше ',
                                                                                      str(data['bet_type'])):

                if re.search('первого тайма меньше ', str(data['bet_type'])):  # ставка на первый тайм тотал больше
                    final_score = float(soup.find_all('b')[1].text[0]) + float(
                        soup.find_all('b')[1].text[-1])  # результат

                if re.search('второго тайма меньше ', str(data['bet_type'])):  # ставка на второй тайм тотал больше
                    final_score = float(soup.find_all('b')[2].text[0]) + float(
                        soup.find_all('b')[2].text[-1])  # результат

                bet = float(str(data['bet_type']).split(' ')[4])  # ставка на ТБ

                if final_score < bet:
                    #    seen_link = data['link'].replace('http://m', 'https://www')
                    #    #print(data['country'][:-2] + '\n' + data['names'] + '\n' + seen_link + '\nПрогноз:' + data[
                    #        'bet_type'] + '\nИтог: Тотал первого тайма - ' + str(int(final_score)))
                    tg_text += emoji.emojize('\n:white_check_mark: ' + data['names'], use_aliases=True)

                    if re.search('alg A', str(data['bet_type'])):
                        pA += 1.

                    elif re.search('alg B', str(data['bet_type'])):
                        pB += 1.

                    elif re.search('alg C1', str(data['bet_type'])):
                        pC1 += 1.

                    elif re.search('alg C2', str(data['bet_type'])):
                        pC2 += 1.

                    elif re.search('alg C3', str(data['bet_type'])):
                        pC3 += 1.

                    positive += 1.

                elif final_score > bet:
                    tg_text += emoji.emojize('\n:x: ' + data['names'], use_aliases=True)

                    if re.search('alg A', str(data['bet_type'])):
                        nA += 1.

                    elif re.search('alg B', str(data['bet_type'])):
                        nB += 1.

                    elif re.search('alg C1', str(data['bet_type'])):
                        nC1 += 1.

                    elif re.search('alg C2', str(data['bet_type'])):
                        nC2 += 1.

                    elif re.search('alg C3', str(data['bet_type'])):
                        nC3 += 1.

                    negative += 1.

                else:
                    tg_text += emoji.emojize('\n♻️ ' + data['names'], use_aliases=True)
                    return_bet += 1.

                total += 1.

            if re.search('Тотал меньше ', str(data['bet_type'])):  # ставка на тотал меньше

                final_score = float(soup.find_all('b')[0].text[0]) + float(soup.find_all('b')[0].text[-1])  # результат
                bet = float(str(data['bet_type']).split(' ')[2])  # прогноз

                if final_score < bet:
                    tg_text += emoji.emojize('\n:white_check_mark: ' + data['names'], use_aliases=True)

                    if re.search('alg A', str(data['bet_type'])):
                        pA += 1.

                    elif re.search('alg B', str(data['bet_type'])):
                        pB += 1.

                    elif re.search('alg C1', str(data['bet_type'])):
                        pC1 += 1.

                    elif re.search('alg C2', str(data['bet_type'])):
                        pC2 += 1.

                    elif re.search('alg C3', str(data['bet_type'])):
                        pC3 += 1.

                    positive += 1.

                elif final_score > bet:
                    tg_text += emoji.emojize('\n:x: ' + data['names'], use_aliases=True)

                    if re.search('alg A', str(data['bet_type'])):
                        nA += 1.

                    elif re.search('alg B', str(data['bet_type'])):
                        nB += 1.

                    elif re.search('alg C1', str(data['bet_type'])):
                        nC1 += 1.

                    elif re.search('alg C2', str(data['bet_type'])):
                        nC2 += 1.

                    elif re.search('alg C3', str(data['bet_type'])):
                        nC3 += 1.

                    negative += 1.

                else:
                    tg_text += emoji.emojize('\n♻️ ' + data['names'], use_aliases=True)
                    return_bet += 1.

                total += 1.

        tg_text += emoji.emojize(
            '\nalg A:\n{}:white_check_mark: :heavy_minus_sign: {}:x:'.format(str(int(pA)), str(int(nA))),
            use_aliases=True) + emoji.emojize(
            '\nalg B:\n{}:white_check_mark: :heavy_minus_sign: {}:x:'.format(str(int(pB)), str(int(nB))),
            use_aliases=True) + emoji.emojize(
            '\nalg C1:\n{}:white_check_mark: :heavy_minus_sign: {}:x:'.format(str(int(pC1)), str(int(nC1))),
            use_aliases=True) + emoji.emojize(
            '\nalg C3:\n{}:white_check_mark: :heavy_minus_sign: {}:x:'.format(str(int(pC3)), str(int(nC3))),
            use_aliases=True)

        tg_text += '\nЗа сегодня:'
        tg_text += emoji.emojize('\n{} :white_check_mark:'.format(str(int(positive))), use_aliases=True)
        tg_text += emoji.emojize('\n{} :x:'.format(str(int(negative))), use_aliases=True)
        tg_text += emoji.emojize('\n{} ♻️'.format(str(int(return_bet))), use_aliases=True)
        tg_text += emoji.emojize('\nВсего игр: {}'.format(str(int(total))), use_aliases=True)

        tg_text += '\nПроцент правильных прогнозов всего: ' + str(
            round(((positive / (total - return_bet)) * 100), 2)) + '%'

        tg_text += '\nПроцент правильных прогнозов по стратегиям A, C1: ' + str(
            round((((pA + pC1) / (pA + pC1 + nA + nC1)) * 100), 2)) + '%'
        tg_text += '\nПроцент правильных прогнозов по стратегиям A, B, C1, C3: ' + str(
            round((((pA + pB + pC1 + pC3) / (pA + pB + pC1 + pC3 + nA + nB + nC1 + nC3)) * 100), 2)) + '%'

        bankC3 = bank
        bank *= (1 + (coef - 1) * bet_bank) ** (pA + pC1)  # положительные исходы
        bank *= (1 - bet_bank) ** (nA + nC1)  # отрицательные исходы

        bankC3 *= (1 + (coef - 1) * bet_bank) ** (pC3)  # положительные исходы
        bankC3 *= (1 - bet_bank) ** (nC3)  # отрицательные исходы

        tg_text += '\nМинимальное изменение банка за сегодня по alg A, C1: 100% -> ' + str(round(bank, 1)) + '%'
        tg_text += '\nМинимальное изменение банка за сегодня по alg C3: 100% -> ' + str(round(bankC3, 1)) + '%'

        tg_text += '\n\n*В статистике не отображаются и не учитываются прогнозы с высоким риском. При расчете ' \
                   'изменения банка берется пессимистичный сценарий: ставка в 7% от банка при коэффициенте  1.55 '
        return tg_text

def tg_res():
    now = datetime.datetime.now()

    file_name = 'football_' + str(now.date()) + '.csv'
    #file_name = 'football_' + str('2019-04-12') + '.csv'

    tg_text = 'Итоги работы алгоритмов за сегодня (' + file_name[9:-4] + '):'

    tg_text = read_csv(file_name, tg_text)
    #print(tg_text)
    while True:
        try:
            bot.send_message(chat_id=-10000000, # указать группу, куда будут отправляться итоги
                             text=tg_text)
            break
        except Exception:
            time.sleep(15)

