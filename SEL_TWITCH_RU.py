import multiprocessing
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import SessionNotCreatedException, NoSuchElementException,\
    StaleElementReferenceException, InvalidArgumentException, WebDriverException
import time
from multiprocessing import Process
from datetime import datetime
import getpass
import sys
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QVBoxLayout, QMainWindow, QApplication, QLabel, QWidget
from PyQt5.QtGui import QPixmap, QPalette, QIcon
from PyQt5.QtCore import Qt, QObject, QThread


Path = r'chromedriver.exe'
LiveXPath = '/html/body/div[1]/div/div[2]/div/main/div[2]/div[3]/div/div/div[1]/div[1]/div[2]/div/div[1]/div/div/div/div[1]/div/div/div/a/div[2]/div/div/div/div/p'
OffXPath = '/html/body/div[1]/div/div[2]/div/main/div[2]/div[3]/div/div/div[1]/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div[1]/div[1]/div/div[1]/div/p'
DropsXPath = '/html/body/div[1]/div/div[2]/div/div[2]/div/div[1]/div/div/div/div/div/section/div/div[3]/div/div[2]/div/div[3]/div/div/div[1]/div/div/div/div/div/div/div[1]/div/div/div[1]/div/div[2]/p[1]'

ProfileXPath = '/html/body/div[1]/div/div[2]/nav/div/div[3]/div[6]/div/div/div/div/button'
DropsStatusXPath = '/html/body/div[5]/div/div/div/div/div/div/div/div/div/div/div/div[3]/div/div/div[1]/div[9]/a/div/div[2]/p[2]'
done_streamer = []


def streamers_file():
    try:
        file = open('streamers.txt', 'r')
    except FileNotFoundError:
        file = open('streamers.txt', 'w')
        file.close()
        print('В папке с приложением нет "streamers.txt".\nФайл был создан. Заполните его в таком формате.')
        print('Пример:\nhttps://www.twitch.tv/zxcghoul\nhttps://www.twitch.tv/deadinside')
        print('Закройте это окно и повторите попытку.')
        time.sleep(300)
        raise SystemExit(1)

    streamers = file.read().split('\n')
    for name in range(len(streamers)):
        if 'https://www.twitch.tv/' not in streamers[name]:
            streamers.remove(streamers[name])
        else:
            pass
    file.close()
    return streamers

def LiveCheck(LiveXPath,OffXPath, streamer_link, streamers_links, driver):
    driver.get(streamer_link)
    try:
        try:
            driver.implicitly_wait(5)
            live = driver.find_element_by_xpath(LiveXPath)
            if live.is_displayed():
                driver.implicitly_wait(5)
                if live.text == 'В ЭФИРЕ':
                    print(streamer_link, ' в эфире')
                    return 'live'
        except (NoSuchElementException, StaleElementReferenceException) as e:
            pass
        try:
            driver.implicitly_wait(5)
            off = driver.find_element_by_xpath(OffXPath)
            if off.is_displayed():
                if off.text == 'НЕ В СЕТИ' or off.text == 'РЕТРАНСЛИРУЕТ':
                    print(streamer_link, ' не в сети')
                    return 'off'
        except (NoSuchElementException, StaleElementReferenceException) as e:
            pass
    except (NoSuchElementException, StaleElementReferenceException) as e:
        stream_status = StreamerStatus(LiveXPath, OffXPath, streamers_links, driver)
        online_streams, dropson_streams = OnlineStreamers(stream_status, DropsXPath, streamers_links, driver)
        WatchingDrops(online_streams, dropson_streams, ProfileXPath, DropsStatusXPath, done_streamer, streamers_links, driver)
        print(' Error:gg')

def StreamerStatus(LiveXPath, OffXPath, streamers_links, driver):
    streamers_status = {
        streamers_links[s]: LiveCheck(LiveXPath, OffXPath, streamers_links[s], streamers_links, driver)
        for s in range(len(streamers_links))
                        }
    return streamers_status

def OnlineStreamers(stream_status, DropsXPath, streamers_links, driver):
    online_streamers = []
    drops_streamers = []
    amount = 0
    d_amount = 0
    for streamer in stream_status:
        if stream_status.get(streamer) == 'live':
            online_streamers.append(streamer)
            amount += 1
    if amount == 0:
        print('нет онлайн стримеров, ждём 5 минут   ' + str(datetime.now().time()))
        time.sleep(300)
        stream_status = StreamerStatus(LiveXPath, OffXPath, streamers_links, driver)
        online_streams, dropson_streams = OnlineStreamers(stream_status, DropsXPath, streamers_links, driver)
        WatchingDrops(online_streams, dropson_streams, ProfileXPath, DropsStatusXPath, done_streamer, streamers_links, driver)
    for drops in online_streamers:
        driver.get(drops)
        driver.implicitly_wait(10)
        try:
            drop_enbl = driver.find_element_by_link_text('Drops включены')
            if drop_enbl.is_displayed():
                if drop_enbl.text == 'Drops включены':
                    print(drops, ' дропс включены!')
                    d_amount += 1
                    drops_streamers.append(drops)
        except (NoSuchElementException, StaleElementReferenceException) as e:
            pass
    if d_amount == 0:
        print('нет стримеров с дропсами, ждём 5 минут   ' + str(datetime.now().time()))
        time.sleep(300)
        stream_status = StreamerStatus(LiveXPath, OffXPath, streamers_links, driver)
        online_streams, dropson_streams = OnlineStreamers(stream_status, DropsXPath, streamers_links, driver)
        WatchingDrops(online_streams, dropson_streams, ProfileXPath, DropsStatusXPath, done_streamer, streamers_links, driver)
    return online_streamers, drops_streamers





def StartWatching(percent, streams, done_streamer, drops_status_mas_0, streamers_links, driver):
    live_check = '300'
    while percent != '100':
        try:
            live_status = driver.find_element_by_link_text('Drops включены')
            RightStreamer(streams, ProfileXPath, drops_status_mas_0, streamers_links, driver)
            drops_status = driver.find_element_by_xpath(DropsStatusXPath)
            if live_status.is_displayed() and live_status.text == 'Drops включены':
                if drops_status.is_displayed():
                    drops_status = drops_status.text
                else:
                    try:
                        profile = driver.find_element_by_xpath(ProfileXPath)
                        profile.click()
                        time.sleep(5)
                        profile.click()
                        profile.click()
                        driver.implicitly_wait(5)
                        drops_status = driver.find_element_by_xpath(DropsStatusXPath)
                        drops_status = drops_status.text
                    except (NoSuchElementException, StaleElementReferenceException) as e:
                        stream_status = StreamerStatus(LiveXPath, OffXPath, streamers_links, driver)
                        online_streams, dropson_streams = OnlineStreamers(stream_status, DropsXPath, streamers_links, driver)
                        WatchingDrops(online_streams, dropson_streams, ProfileXPath, DropsStatusXPath, done_streamer, streamers_links, driver)

                drops_status_mas = drops_status.split('на канале ')
                drops_status_mas = drops_status_mas[1]
                drops_status_mas = drops_status_mas.split(':')
                percent = drops_status_mas[1]
                percent = percent[1:-1]

                if percent != live_check:
                    print(str(percent) + ' %        ' + str(datetime.now().time()))
                    driver.refresh()
                    driver.implicitly_wait(5)
                    profile = driver.find_element_by_xpath(ProfileXPath)
                    profile.click()
                    time.sleep(5)
                    profile.click()
                    profile.click()

                live_check = percent

                if percent == '100':
                    done_streamer.append(streams)
                    driver.get('https://www.twitch.tv/drops/inventory')
                    driver.implicitly_wait(5)
                    try:
                        claim_button = driver.find_element_by_xpath("//button[@data-test-selector ='DropsCampaignInProgressRewardPresentation-claim-button']")
                        claim_button.click()
                        print(streams, ' забрали дроп!')
                        driver.implicitly_wait(5)
                        stream_status = StreamerStatus(LiveXPath, OffXPath, streamers_links, driver)
                        online_streams, dropson_streams = OnlineStreamers(stream_status, DropsXPath, streamers_links, driver)
                        WatchingDrops(online_streams, dropson_streams, ProfileXPath, DropsStatusXPath, done_streamer, streamers_links, driver)

                    except (NoSuchElementException, StaleElementReferenceException) as e:
                        print(' Error:aad')
                        stream_status = StreamerStatus(LiveXPath, OffXPath, streamers_links, driver)
                        online_streams, dropson_streams = OnlineStreamers(stream_status, DropsXPath, streamers_links, driver)
                        WatchingDrops(online_streams, dropson_streams, ProfileXPath, DropsStatusXPath, done_streamer, streamers_links, driver)

            else:
                print(streams, 'офлайн или нет drops ищем другог стримера')
                stream_status = StreamerStatus(LiveXPath, OffXPath, streamers_links, driver)
                online_streams, dropson_streams = OnlineStreamers(stream_status, DropsXPath, streamers_links, driver)
                WatchingDrops(online_streams, dropson_streams, ProfileXPath, DropsStatusXPath, done_streamer, streamers_links, driver)

        except StaleElementReferenceException:
            print(streams, 'офлайн или нет drops ищем другог стримера')
            stream_status = StreamerStatus(LiveXPath, OffXPath, streamers_links, driver)
            online_streams, dropson_streams = OnlineStreamers(stream_status, DropsXPath, streamers_links, driver)
            WatchingDrops(online_streams, dropson_streams, ProfileXPath, DropsStatusXPath, done_streamer, streamers_links, driver)


def RightStreamer(streams, ProfileXPath, drops_status_mas_0, streamers_links, driver):
    if streams != 'https://www.twitch.tv/' + drops_status_mas_0:
        print('не тот стример, переключаемся на https://www.twitch.tv/' + drops_status_mas_0)
        driver.get('https://www.twitch.tv/' + drops_status_mas_0)
        driver.implicitly_wait(5)
        profile = driver.find_element_by_xpath(ProfileXPath)
        profile.click()
        driver.implicitly_wait(5)
        drops_status = driver.find_element_by_xpath(DropsStatusXPath)
        drops_status = drops_status.text
        drops_status_mas = drops_status.split('на канале ')
        drops_status_mas = drops_status_mas[1]
        drops_status_mas = drops_status_mas.split(':')
        percent = drops_status_mas[1]
        StartWatching(percent, 'https://www.twitch.tv/' + drops_status_mas[0], done_streamer, drops_status_mas_0, streamers_links, driver)
    else:
        return


def WatchingDrops(online_streams, dropson_streams,  ProfileXPath, DropsStatusXPath, done_streamer, streamers_links, driver):
    for stream_drop in dropson_streams:
        driver.get(stream_drop)
        time.sleep(10)
        try:
            driver.get(stream_drop)
            driver.implicitly_wait(5)
            profile = driver.find_element_by_xpath(ProfileXPath)
            profile.click()
            time.sleep(5)
            profile.click()
            profile.click()
            time.sleep(5)
            profile.click()
            profile.click()
            driver.implicitly_wait(5)
            drops_status = driver.find_element_by_xpath(DropsStatusXPath)
            drops_status = drops_status.text
            drops_status_mas = drops_status.split('на канале ')
            drops_status_mas = drops_status_mas[1]
            drops_status_mas = drops_status_mas.split(':')
            percent = drops_status_mas[1]
            if stream_drop == 'https://www.twitch.tv/' + drops_status_mas[0]:
                print('смотрим ' + drops_status_mas[0])
                StartWatching(percent, 'https://www.twitch.tv/'+drops_status_mas[0], done_streamer, drops_status_mas[0], streamers_links, driver)
            else:
                RightStreamer(stream_drop, ProfileXPath, drops_status_mas[0], streamers_links, driver)

        except (NoSuchElementException, StaleElementReferenceException) as e:
            print('нет дропсов у ' + stream_drop + ' ждём 1 минуту   ' + str(datetime.now().time()))
            time.sleep(60)
    stream_status = StreamerStatus(LiveXPath, OffXPath, streamers_links, driver)
    online_streams, dropson_streams = OnlineStreamers(stream_status, DropsXPath,  streamers_links, driver)
    WatchingDrops(online_streams, dropson_streams, ProfileXPath, DropsStatusXPath, done_streamer, streamers_links, driver)

class UiMainWindow(object):
    def __init__(self, streamers_links):
        self.streamers_links = streamers_links

    def statusUpgrader(self, status):
        _translate = QtCore.QCoreApplication.translate
        self.label.setText(_translate("MainWindow", status))
        self.label.repaint()

    def exit(self):
        os.system("TASKKILL /F /IM chromedriver.exe")
        os.system("TASKKILL /F /IM chrome.exe")
        raise SystemExit(1)

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(362, 400)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.listWidget = QtWidgets.QListWidget(self.centralwidget)
        self.listWidget.setGeometry(QtCore.QRect(10, 10, 336, 192))
        self.listWidget.setObjectName("listWidget")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(20, 270, 331, 200))
        self.label.setObjectName("label")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(10, 270, 141, 31))
        self.pushButton.setObjectName("pushButton")
        self.pushButton.clicked.connect(self.exit)
        for links in range(len(self.streamers_links)):
            item = QtWidgets.QListWidgetItem()
            self.listWidget.addItem(item)
            __sortingEnabled = self.listWidget.isSortingEnabled()
            _translate = QtCore.QCoreApplication.translate
            item = self.listWidget.item(links)
            item.setText(_translate("MainWindow", self.streamers_links[links]))
            self.listWidget.setSortingEnabled(__sortingEnabled)
        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)


    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowIcon(QIcon('dropico.ico'))
        MainWindow.setWindowTitle(_translate("MainWindow", "Twitch Drops Grabber"))
        self.pushButton.setText(_translate("MainWindow", "Закрыть"))



def gui(streamers_links):
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = UiMainWindow(streamers_links)
    ui.setupUi(MainWindow)
    ui.statusUpgrader('')
    MainWindow.show()
    sys.exit(app.exec_())





def starter(LiveXPath, OffXPath, streamers_links):
    option = webdriver.ChromeOptions()
    option.add_argument('no-sandbox')
    option.add_argument('--disable-gpu')
    option.add_argument('--log-level=3')
    option.add_argument('user-data-dir=C:\\Users\\{}\\AppData\\Local\\Google\\Chrome\\User Data'.format(getpass.getuser()))
    try:
        driver = webdriver.Chrome(Path, options=option)
        stream_status = StreamerStatus(LiveXPath, OffXPath, streamers_links, driver)
        online_streams, dropson_streams = OnlineStreamers(stream_status, DropsXPath, streamers_links, driver)
        WatchingDrops(online_streams, dropson_streams, ProfileXPath, DropsStatusXPath, done_streamer, streamers_links, driver)
    except(SessionNotCreatedException):
        print('Обновите chromedriver')
        time.sleep(30)
        raise SystemExit(1)
    except(InvalidArgumentException):
        print('Закройте chrome или нажите закрыть, перезапустите программу')
        time.sleep(30)
        raise SystemExit(1)
    except(WebDriverException):
        print('"chromedriver.exe" нет в папке с приложением.\nПрочитайте инструкцию и добавьте "chromedriver.exe" в папку.\nПерезапустите программу.')
        time.sleep(30)
        raise SystemExit(1)




if __name__ == '__main__':
    multiprocessing.freeze_support()
    streamers_links = streamers_file()
    status = 'status'


    twitch_p = Process(target=starter, args=(LiveXPath, OffXPath, streamers_links))
    gui_p = Process(target=gui, args=(streamers_links,))
    twitch_p.start()
    gui_p.start()
    twitch_p.join()
    gui_p.join()




#driver.quit()