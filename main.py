import customtkinter
import os
from PIL import Image
import requests
import json
import subprocess
import platform
import psutil
import serial
import serial.tools.list_ports
import time
import RPi.GPIO as GPIO
import binascii
from py532lib.i2c import *
from py532lib.frame import *
from py532lib.constants import *
from py532lib.mifare import *
from threading import Thread, Event, Timer
from signal import SIGINT, signal
from datetime import datetime, timedelta, timezone
from database.scheme import Credential, Gateway, Node, Card, AccessRole, db
from secret.secret import header
from variable import *
from peewee import *


class DotDict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def millis():
    date = datetime.utcnow() - datetime(1970, 1, 1)
    seconds = (date.total_seconds())
    milliseconds = round(seconds*1000)
    return milliseconds


class Util():
    def __init__(self):
        pass

    image_path = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "static")

    OS = platform.system()
    URL = "http://192.168.226.130:8000"
    COLOR_BLUE_1 = "#1481B8"
    COLOR_BLUE_2 = "#26AEF3"
    COLOR_RED_1 = "#FF5E5E"
    COLOR_RED_2 = "#FE9393"
    COLOR_YELLOW_1 = "#F1C756"
    COLOR_YELLOW_2 = "#F3D686"
    COLOR_GREEN_1 = "#4C956C"
    COLOR_GREEN_2 = "#70BC92"
    COLOR_NEUTRAL_1 = "#1E1E2C"
    COLOR_NEUTRAL_2 = "#29283D"
    COLOR_NEUTRAL_3 = "#222133"
    COLOR_NEUTRAL_4 = "#E8E8E8"
    COLOR_NEUTRAL_5 = "#ECF0F1"
    COLOR_TRANSPARENT = "transparent"
    CORNER_RADIUS = 15
    CURRENT_FRAME = ""
    CARD_FORM = ""

    if OS == "Linux":
        APP_WIDTH = 800
        APP_HEIGHT = 400
        pn532 = Pn532_i2c()
        pn532.SAMconfigure()
        READER = Mifare()
        READER_STATUS = False
        FONT = DotDict({
            "Light": "Cantarell Thin",
            "Regular": "Cantarell",
            "SemiBold": "Cantarell SemiBold",
            "Bold": "Cantarell Extra Bold",
            "SIZE": DotDict({
                "Small": 12,
                "Regular": 14,
                "Large": 20,
                "ExtraLarge": 30,
                "SuperLarge": 60,
            })
        })

    if OS == "Windows":
        APP_WIDTH = 1024
        APP_HEIGHT = 600
        FONT = DotDict({
            "Light": "Quicksand Light",
            "Regular": "Quicksand",
            "SemiBold": "Quicksand SemiBold",
            "Bold": "Quicksand Bold",
            "SIZE": DotDict({
                "Small": 12,
                "Regular": 16,
                "Large": 22,
                "ExtraLarge": 40,
                "SuperLarge": 100,
            })
        })

    @staticmethod
    def pingServer():
        print("Try Connect To Server for Updating Gateway Online Time....")
        gatewayInfo = Gateway.select().dicts()
        online = requests.post(
            f"{Util.URL}/api/v1/gateway/device/h/update-online-time/{gatewayInfo[0]['shortId']}", headers=header)
        if (online.status_code == 200):  # jika perangkat masih online, maka redirect
            print("Success Update Gateway Online Time")

        nodes = Node.select().dicts()

        for node in nodes:
            nodeShortId = node["shortId"]
            nodeAccumulativeResponseTime = Variable.getLog(nodeShortId)
            print(
                f"Try Connect To Server for Updating Node {nodeShortId} Online Time....")
            nodeOnline = requests.post(
                f"{Util.URL}/api/v1/gateway/device/h/node-online-update", headers=header, json={
                    "duid": nodeShortId,
                    "responsesTime": nodeAccumulativeResponseTime
                })
            if (nodeOnline.status_code == 200):  # jika perangkat masih online, maka redirect
                print(f"Success Update Node {nodeShortId} Online Time")
                Variable.reSetLog(nodeShortId)  # reset log for spesific node

    @staticmethod
    def frameDestroyer(fr):
        fr.destroy()

    @staticmethod
    def frameSwitcher(originFrame, destinationFrame, master, row=0, column=0, fg_color="transparent", padx=20, pady=20):
        originFrame.destroy()
        frameToRender = destinationFrame(master=master, fg_color=fg_color)
        frameToRender.grid(row=row, column=column,
                           padx=padx, pady=pady, sticky="nsew")

    @staticmethod
    def imageGenerator(fileName, size=26):
        if size > 0:
            icon = customtkinter.CTkImage(Image.open(
                os.path.join(Util.image_path, fileName)), size=(size, size))
        if size == -1:
            icon = customtkinter.CTkImage(Image.open(
                os.path.join(Util.image_path, fileName)))
        return icon

    @staticmethod
    def startScript(pythonScript):
        if platform.system() == "Windows":
            subprocess.call(f"start /wait python {pythonScript}", shell=True)

        if platform.system() == "Linux":
            subprocess.call(
                f"lxterminal -e 'bash -c \"source ./venv/bin/activate && python {pythonScript}; exec bash\"'", shell=True)

    @staticmethod
    def stopScript(pid):
        if platform.system() == "Windows":
            os.kill(pid, SIGINT)

        if platform.system() == "Linux":
            subprocess.run(["kill", "-9", str(pid)])


class LoginFrames(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        master.grid_rowconfigure(0, weight=1)  # configure grid system
        master.grid_columnconfigure(0, weight=1)

        self.toplevel_window = None
        self.iconSettings = Util.imageGenerator("icon_settings.png")
        self.settingButton = customtkinter.CTkButton(master=self, text="", width=30, image=self.iconSettings, fg_color="transparent",
                                                     hover=False, compound="right", command=lambda: Util.frameSwitcher(originFrame=self, destinationFrame=ApiFormFrames, master=master))
        self.settingButton.place(relx=1, rely=0, anchor="ne")
        self.formFrame = customtkinter.CTkFrame(
            master=self, fg_color=Util.COLOR_TRANSPARENT)
        self.formFrame.place(relx=0.5, rely=0.5, anchor="center")

        self.usernameLabel = customtkinter.CTkLabel(
            master=self.formFrame, text="Username", font=(Util.FONT.Bold, Util.FONT.SIZE.Regular), text_color=Util.COLOR_NEUTRAL_5)
        self.usernameLabel.grid(row=0, column=0, sticky="w", pady=[0, 10])
        self.usernameForm = customtkinter.CTkEntry(master=self.formFrame, width=500, height=50, placeholder_text="Please Input Your Username",
                                                   fg_color=Util.COLOR_NEUTRAL_2, border_color=Util.COLOR_NEUTRAL_4, corner_radius=Util.CORNER_RADIUS, text_color=Util.COLOR_NEUTRAL_5)
        self.usernameForm.grid(row=1, column=0, sticky="w")
        self.passwordLabel = customtkinter.CTkLabel(
            master=self.formFrame, text="Password", font=(Util.FONT.Bold, Util.FONT.SIZE.Regular), text_color=Util.COLOR_NEUTRAL_5)
        self.passwordLabel.grid(row=2, column=0, pady=[20, 10], sticky="w")
        self.passwordForm = customtkinter.CTkEntry(master=self.formFrame, width=500, height=50, placeholder_text="Please Input Your Password",
                                                   show="*", fg_color=Util.COLOR_NEUTRAL_2, border_color=Util.COLOR_NEUTRAL_4, corner_radius=Util.CORNER_RADIUS, text_color=Util.COLOR_NEUTRAL_5)
        self.passwordForm.grid(row=3, column=0, sticky="w")
        self.submitButton = customtkinter.CTkButton(master=self.formFrame, width=500, height=45, text="Login", command=self.fetchLogin,
                                                    fg_color=Util.COLOR_BLUE_1, hover_color=Util.COLOR_BLUE_2, corner_radius=Util.CORNER_RADIUS, font=(Util.FONT.Bold, 16))
        self.submitButton.grid(row=4, column=0, pady=[40, 0], sticky="w")

    def fetchLogin(self):
        username = self.usernameForm.get()
        paasword = self.passwordForm.get()
        resp = requests.post(f"{Util.URL}/api/v1/user/login",
                             json={'username': username, 'password': paasword})

        if (resp.status_code == 200):
            data = []
            datas = Gateway.select().dicts()

            for d in datas:
                data.append(d)

            # Jika data belum tersimpan di database maka request ID ke cloud
            if len(data) <= 0:
                print(" [!main]: DB Tidak Tersedia")
                gatewayResp = self.initializeGateway()

                if (gatewayResp.status_code == 200):
                    self.redirectPage()

            # Jika Data sudah ada cek apakah masih tersedia
            if len(data) > 0:
                print(" [!main]: DB Tersedia")
                online = requests.post(
                    f"{Util.URL}/api/v1/gateway/device/h/update-online-time/{datas[0]['shortId']}", headers=header)
                if (online.status_code == 200):  # jika perangkat masih online, maka redirect
                    print(" [!main]: Device ready")
                    self.redirectPage()

                # jika perangkat tidak terdeteksi maka inisialisasi perangkat baru
                if (online.status_code != 200):
                    print(" [!main]: init Device")
                    Gateway.delete_by_id(1)
                    gatewayResp = self.initializeGateway()

                    if (gatewayResp.status_code == 200):
                        self.redirectPage()

        if (resp.status_code != 200):
            Toast(master=self.master, color=Util.COLOR_RED_1,
                  errMsg="Username and Password Not Match")

    def initializeGateway(self):
        gatewayResp = requests.post(
            f"{Util.URL}/api/v1/gateway/device/h/init", headers=header)
        respData = gatewayResp.json()

        if (gatewayResp.status_code == 200):
            Gateway.create(shortId=respData["data"]["gateway_short_id"])

        return gatewayResp

    def redirectPage(self):
        Util.frameDestroyer(self)
        self.sideBarFrame = SideBarFrames(
            master=self.master, fg_color="#29283D")
        self.sideBarFrame.grid(row=0, column=0, padx=[
                               20, 0], pady=20, sticky="nwsw")


class ApiFormFrames(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        # LAYOUT
        # --Setting Button
        # --formFrame
        #   |-- usernameLabel
        #   |-- usernameForm
        #   |-- passwordLabel
        #   |-- passwordForm
        super().__init__(master, **kwargs)
        self.master = master
        self.iconBack = Util.imageGenerator("icon_back.png")
        self.settingButton = customtkinter.CTkButton(master=self, text="", width=30, image=self.iconBack, fg_color="transparent", hover=False,
                                                     compound="right", command=lambda: Util.frameSwitcher(originFrame=self, destinationFrame=LoginFrames, master=master))
        self.settingButton.place(relx=1, rely=0, anchor="ne")
        self.formFrame = customtkinter.CTkFrame(
            master=self, fg_color="transparent")
        self.formFrame.place(relx=0.5, rely=0.5, anchor="center")

        self.apiIdLabel = customtkinter.CTkLabel(
            master=self.formFrame, text="API ID", font=(Util.FONT.Bold, Util.FONT.SIZE.Regular), text_color=Util.COLOR_NEUTRAL_5)
        self.apiIdLabel.grid(row=0, column=0, sticky="w", pady=[0, 10])
        self.apiIdForm = customtkinter.CTkEntry(master=self.formFrame, width=500, height=50, placeholder_text="Please Input API ID",
                                                fg_color=Util.COLOR_NEUTRAL_2, border_color=Util.COLOR_NEUTRAL_4, corner_radius=Util.CORNER_RADIUS, text_color=Util.COLOR_NEUTRAL_5)
        self.apiIdForm.grid(row=1, column=0, sticky="w")
        self.apiKeyLabel = customtkinter.CTkLabel(
            master=self.formFrame, text="API Key", font=(Util.FONT.Bold, Util.FONT.SIZE.Regular), text_color=Util.COLOR_NEUTRAL_5)
        self.apiKeyLabel.grid(row=2, column=0, pady=[20, 10], sticky="w")
        self.apiKeyForm = customtkinter.CTkEntry(master=self.formFrame, width=500, height=50, placeholder_text="Please Input API Key",
                                                 fg_color=Util.COLOR_NEUTRAL_2, border_color=Util.COLOR_NEUTRAL_4, corner_radius=Util.CORNER_RADIUS, text_color=Util.COLOR_NEUTRAL_5)
        self.apiKeyForm.grid(row=3, column=0, sticky="w")
        self.submitButton = customtkinter.CTkButton(master=self.formFrame, width=500, height=45, text="Save", command=self.saveOnClick,
                                                    fg_color=Util.COLOR_BLUE_1, hover_color=Util.COLOR_BLUE_2, corner_radius=Util.CORNER_RADIUS, font=(Util.FONT.Bold, Util.FONT.SIZE.Regular))
        self.submitButton.grid(row=4, column=0, pady=[40, 0], sticky="w")

    def saveOnClick(self):
        apiId = self.apiIdForm.get()
        apiKey = self.apiKeyForm.get()
        availableData = []
        datas = Credential.select().dicts()
        for data in datas:
            availableData.append(data)

        if len(apiId) < 1 or len(apiKey) < 1:
            Toast(master=self.master, color=Util.COLOR_RED_1,
                  errMsg="Api Id & Key can't empty")
            return

        if len(availableData) > 0:
            Credential.update(apiID=apiId, apiKey=apiKey).where(
                Credential.id == int(availableData[0]["id"])).execute()
            Toast(master=self.master, color=Util.COLOR_GREEN_1,
                  errMsg="Success Save Data")
        else:
            Credential.create(apiID=apiId, apiKey=apiKey)
            Toast(master=self.master, color=Util.COLOR_GREEN_1,
                  errMsg="Success Save Data")


class SideBarFrames(customtkinter.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, width=120, **kwargs)
        self.stopEvent = Event()
        # self.t = Timer(30*60, self.autoLogout, ())
        # self.t.start()

        self.master = master
        master.grid_rowconfigure(0, weight=1)  # configure grid system
        master.grid_columnconfigure(0, weight=1)
        self.homeButtonIcon = Util.imageGenerator("icon_home.png")
        self.homeButton = customtkinter.CTkButton(master=self, text="Home", font=(Util.FONT.Bold, Util.FONT.SIZE.Small), image=self.homeButtonIcon,
                                                  anchor="w", fg_color=Util.COLOR_BLUE_1, hover_color=Util.COLOR_BLUE_2, command=lambda: self.widgetOnClick(self.homeButton))
        self.homeButton.pack(fill="both", anchor="w", pady=[0, 20])
        self.homeFrame = HomeFrames(
            master=self.master, fg_color=Util.COLOR_TRANSPARENT)
        self.homeFrame.grid(row=0, column=1, padx=[
                            0, 20], pady=10, sticky="nsew")

        self.roomButtonIcon = Util.imageGenerator("icon_room.png")
        self.roomButton = customtkinter.CTkButton(master=self, text="Room", font=(Util.FONT.Bold, Util.FONT.SIZE.Small), image=self.roomButtonIcon,
                                                  anchor="w", fg_color="transparent", hover_color=Util.COLOR_BLUE_2, command=lambda: self.widgetOnClick(self.roomButton))
        self.roomButton.pack(fill="both", anchor="w", pady=[0, 20])

        if Util.OS == "Linux":
            self.cardButtonIcon = Util.imageGenerator("icon_card.png")
            self.cardButton = customtkinter.CTkButton(master=self, text="Card", font=(Util.FONT.Bold, Util.FONT.SIZE.Small), image=self.cardButtonIcon,
                                                      anchor="w", fg_color="transparent", hover_color=Util.COLOR_BLUE_2, command=lambda: self.widgetOnClick(self.cardButton))
            self.cardButton.pack(fill="both", anchor="w", pady=[0, 20])

        self.syncButtonIcon = Util.imageGenerator("icon_sync.png")
        self.syncButton = customtkinter.CTkButton(master=self, text="Sync", font=(Util.FONT.Bold, Util.FONT.SIZE.Small), image=self.syncButtonIcon,
                                                  anchor="w", fg_color="transparent", hover_color=Util.COLOR_BLUE_2, command=lambda: self.widgetOnClick(self.syncButton))
        self.syncButton.pack(fill="both", anchor="w", pady=[0, 20])

        self.networkButtonIcon = Util.imageGenerator("icon_mesh.png")
        self.networkButton = customtkinter.CTkButton(master=self, text="Network", font=(Util.FONT.Bold, Util.FONT.SIZE.Small), image=self.networkButtonIcon,
                                                     anchor="w", fg_color="transparent", hover_color=Util.COLOR_BLUE_2, command=lambda: self.widgetOnClick(self.networkButton))
        self.networkButton.pack(fill="both", anchor="w", pady=[0, 20])

        self.settingButtonIcon = Util.imageGenerator("icon_settings.png")
        self.settingButton = customtkinter.CTkButton(master=self, text="Setting", font=(Util.FONT.Bold, Util.FONT.SIZE.Small), image=self.settingButtonIcon,
                                                     anchor="w", fg_color="transparent", hover_color=Util.COLOR_BLUE_2, command=lambda: self.widgetOnClick(self.settingButton))
        self.settingButton.pack(fill="both", anchor="w", pady=[0, 20])

        self.logoutButtonIcon = Util.imageGenerator("logout.png")
        self.logoutButton = customtkinter.CTkButton(master=self, text="Logout", font=(Util.FONT.Bold, Util.FONT.SIZE.Small), image=self.logoutButtonIcon,
                                                    anchor="w", fg_color="transparent", hover_color=Util.COLOR_BLUE_2, command=lambda: self.widgetOnClick(self.logoutButton))
        self.logoutButton.pack(fill="both", anchor="w", pady=[0, 20])

    def widgetOnClick(self, item):
        for child in self.winfo_children():
            child.configure(fg_color="transparent")
        item.configure(fg_color=Util.COLOR_BLUE_1)
        state = item.cget("text")
        # self.t.cancel()
        # self.t = Timer(15, self.autoLogout, ())
        # self.t.start()
        Util.CURRENT_FRAME = state
        if state == "Home":
            print(" [!main]: Render Home Frame")
            Util.frameSwitcher(originFrame=self.master.winfo_children()[
                               1], destinationFrame=HomeFrames, master=self.master, row=0, column=1, padx=[0, 20], pady=20, fg_color=Util.COLOR_TRANSPARENT)

        if state == "Room":
            print(" [!main]: Render Room Frame")
            Util.frameSwitcher(originFrame=self.master.winfo_children()[
                               1], destinationFrame=RoomFrames, master=self.master, row=0, column=1, padx=[0, 20], pady=20, fg_color=Util.COLOR_TRANSPARENT)

        if state == "Sync":
            print(" [!main]: Render Sync Frame")
            Util.frameSwitcher(originFrame=self.master.winfo_children()[
                               1], destinationFrame=SyncFrames, master=self.master, row=0, column=1, padx=[0, 20], pady=20)

        if state == "Network":
            print(" [!main]: Render Network Frame")
            Util.frameSwitcher(originFrame=self.master.winfo_children()[
                               1], destinationFrame=NetworkFrames, master=self.master, row=0, column=1, padx=[0, 20], pady=20, fg_color=Util.COLOR_TRANSPARENT)

        if state == "Setting":
            print(" [!main]: Render Setting Frame")
            Util.frameSwitcher(originFrame=self.master.winfo_children()[
                               1], destinationFrame=SettingFrames, master=self.master, row=0, column=1, padx=[0, 20], pady=20, fg_color=Util.COLOR_TRANSPARENT)

        if state == "Card" and Util.OS == "Linux":
            print(" [!main]: Render Card Frame")
            Util.frameSwitcher(originFrame=self.master.winfo_children()[
                               1], destinationFrame=CardFrames, master=self.master, row=0, column=1, padx=[0, 20], pady=20, fg_color=Util.COLOR_TRANSPARENT)

        if state == "Logout":
            print(" [!main]: Logout")
            self.logoutRedirect()
            self.stopEvent.set()

    def autoLogout(self):
        self.logoutRedirect()

    def logoutRedirect(self):
        # self.t.cancel()
        Util.frameSwitcher(originFrame=self.master.winfo_children()[
            1], destinationFrame=LoginFrames, master=self.master, row=0, column=1, padx=[0, 20], pady=20, fg_color=Util.COLOR_TRANSPARENT)
        Util.frameDestroyer(self.master.winfo_children()[0])


class HomeFrames(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        nodeCount = Node.select().count()
        cardCount = Card.select().count()
        lastSync = Gateway.get_by_id(1).lastSync
        lastSyncTime = None
        lastSyncDate = None
        lastSyncHour = None
        if (lastSync):
            # execpetion for linux
            try:
                formatedDate = datetime.fromisoformat(
                    lastSync).astimezone(timezone(timedelta(hours=7)))
            except:
                formatedDate = datetime.fromisoformat(
                    lastSync.replace('Z', '+00:00')).astimezone(timezone(timedelta(hours=7)))
            syncDate = f"{formatedDate.date()} {formatedDate.hour}:{formatedDate.minute}"
            lastSyncDate = formatedDate.date()
            lastSyncHour = formatedDate.hour
            lastSyncminutes = formatedDate.minute
            lastSyncTime = f"{lastSyncHour}.{lastSyncminutes}"
        if (not lastSync):
            lastSyncTime = f"~"
            lastSyncDate = "Not Sync yet"

        master.grid_columnconfigure(1, weight=40)
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=9)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self.headerFrame = customtkinter.CTkFrame(master=self, height=250, fg_color=Util.COLOR_NEUTRAL_2,
                                                  corner_radius=Util.CORNER_RADIUS, border_width=1, border_color=Util.COLOR_NEUTRAL_5)
        self.headerFrame.grid(row=0, column=0, sticky="nwne", columnspan=3)
        self.headerFrame.grid_propagate(False)
        self.headerFrame.grid_columnconfigure(0, weight=1)
        self.headerFrame.grid_rowconfigure(0, weight=1)
        self.headerFrame.grid_rowconfigure(1, weight=1)
        self.appTitle = customtkinter.CTkLabel(master=self.headerFrame, font=(
            Util.FONT.Bold, Util.FONT.SIZE.ExtraLarge), fg_color=Util.COLOR_TRANSPARENT, text="Smart Door Gateway Device", text_color=Util.COLOR_NEUTRAL_5)
        self.appTitle.pack(anchor="w", pady=20, padx=[10, 10])
        self.appDescription = customtkinter.CTkLabel(master=self.headerFrame, anchor="w", justify="left", font=(
            Util.FONT.Regular, Util.FONT.SIZE.Regular), wraplength=500, text_color=Util.COLOR_NEUTRAL_5, text="The gateway device is the authentication center hardware for the smart door node. This device will store user card data, as well as be used to register user cards.")
        self.appDescription.pack(anchor="w", pady=[0, 40], padx=[10, 10])

        self.nodeFrame = customtkinter.CTkFrame(
            master=self, height=200, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.nodeFrame.grid(row=1, column=0, pady=[
                            30, 0], padx=[0, 10], sticky="nwne")
        self.nodeFrame.grid_propagate(False)
        self.nodeFrameCount = customtkinter.CTkLabel(master=self.nodeFrame, font=(
            Util.FONT.Bold, Util.FONT.SIZE.SuperLarge), text_color=Util.COLOR_NEUTRAL_5, text=nodeCount, fg_color="transparent")
        self.nodeFrameTitle = customtkinter.CTkLabel(
            master=self.nodeFrame, text_color=Util.COLOR_NEUTRAL_5, wraplength=100, justify="left", font=(Util.FONT.SemiBold, Util.FONT.SIZE.Regular), text="Smart Door Node")
        self.nodeFrameDescription = customtkinter.CTkLabel(
            master=self.nodeFrame, text_color=Util.COLOR_NEUTRAL_5, font=(Util.FONT.Light, Util.FONT.SIZE.Regular), text="Linked Device")
        self.nodeFrameTitle.pack(anchor="w", pady=[20, 0], padx=[20, 10])
        self.nodeFrameCount.pack(anchor="w", pady=[0, 0], padx=[20, 10])
        self.nodeFrameDescription.pack(anchor="w", pady=[0, 20], padx=[20, 10])

        self.syncFrame = customtkinter.CTkFrame(
            master=self, height=200, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.syncFrame.grid(row=1, column=1, pady=[
                            30, 0], padx=0, sticky="nwne")
        self.syncFrame.grid_propagate(False)
        self.nodeFrameCount = customtkinter.CTkLabel(master=self.syncFrame, font=(
            Util.FONT.Bold, Util.FONT.SIZE.SuperLarge), text_color=Util.COLOR_NEUTRAL_5, text=lastSyncTime, fg_color="transparent")
        self.nodeFrameTitle = customtkinter.CTkLabel(
            master=self.syncFrame, text_color=Util.COLOR_NEUTRAL_5, font=(Util.FONT.SemiBold, Util.FONT.SIZE.Regular), text="Last Sync")
        self.nodeFrameDescription = customtkinter.CTkLabel(
            master=self.syncFrame, text_color=Util.COLOR_NEUTRAL_5, font=(Util.FONT.Light, Util.FONT.SIZE.Regular), text=lastSyncDate)
        self.nodeFrameTitle.pack(anchor="w", pady=[20, 0], padx=[20, 10])
        self.nodeFrameCount.pack(anchor="w", pady=[0, 0], padx=[20, 10])
        self.nodeFrameDescription.pack(anchor="w", pady=[0, 20], padx=[20, 10])

        self.cardFrame = customtkinter.CTkFrame(
            master=self, height=200, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.cardFrame.grid(row=1, column=2, pady=[
                            30, 0], padx=[10, 0], sticky="nwne")
        self.cardFrame.grid_propagate(False)
        self.nodeFrameCount = customtkinter.CTkLabel(master=self.cardFrame, font=(
            Util.FONT.Bold, Util.FONT.SIZE.SuperLarge), text_color=Util.COLOR_NEUTRAL_5, text=cardCount, fg_color="transparent")
        self.nodeFrameTitle = customtkinter.CTkLabel(
            master=self.cardFrame, wraplength=100, justify="left", font=(Util.FONT.SemiBold, Util.FONT.SIZE.Regular), text_color=Util.COLOR_NEUTRAL_5, text="Accapted Card")
        self.nodeFrameDescription = customtkinter.CTkLabel(
            master=self.cardFrame, font=(Util.FONT.Light, Util.FONT.SIZE.Regular), text_color=Util.COLOR_NEUTRAL_5, text="Card")
        self.nodeFrameTitle.pack(anchor="w", pady=[20, 0], padx=[20, 10])
        self.nodeFrameCount.pack(anchor="w", pady=[0, 0], padx=[20, 10])
        self.nodeFrameDescription.pack(anchor="w", pady=[0, 20], padx=[20, 10])


class RoomFrames(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        master.grid_columnconfigure(1, weight=40)
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        # DEVICE LIST
        self.deviceListFrame = customtkinter.CTkScrollableFrame(
            master=self, fg_color=Util.COLOR_NEUTRAL_1, width=300, corner_radius=Util.CORNER_RADIUS)
        self.deviceListFrame.grid(row=0, column=0, sticky="nswe", padx=[0, 5])
        self.deviceListLabel = customtkinter.CTkLabel(
           master=self.deviceListFrame, text_color=Util.COLOR_NEUTRAL_5, text="Node List", font=(Util.FONT.SemiBold, Util.FONT.SIZE.Large))
        self.deviceListLabel.pack(anchor="w")
        self.button = customtkinter.CTkButton(master=self.deviceListFrame, command=self.addNewNodeOnClick, text="Create New Node" if Util.OS == "Windows" else "Create Node", image=Util.imageGenerator(
            "icon_plus.png", 20), corner_radius=Util.CORNER_RADIUS, compound="right", font=(Util.FONT.SemiBold, Util.FONT.SIZE.Regular), fg_color=Util.COLOR_GREEN_1, hover_color=Util.COLOR_GREEN_2)
        self.button.pack(anchor="center", fill="both",
                         ipady=10, pady=20, padx=[0, 10])
        self.devices = []

        # LOAD DATA FROM DB
        node_DB = Node.select().dicts()

        for data in node_DB:
            self.devices.append(data)

        if len(self.devices) >= 0:
            for device in self.devices:
                self.itemContainer(device["shortId"])

        # DEVICE DETAIL
        self.deviceDetailFrame = customtkinter.CTkScrollableFrame(
            master=self, fg_color=Util.COLOR_NEUTRAL_1, width=300, corner_radius=Util.CORNER_RADIUS)
        self.deviceDetailFrame.grid(row=0, column=1, sticky="nswe", padx=0)
        self.deviceDetailLabel = customtkinter.CTkLabel(
            master=self.deviceDetailFrame, text_color=Util.COLOR_NEUTRAL_5, text="Node Detail", font=(Util.FONT.SemiBold, Util.FONT.SIZE.Large))
        self.deviceDetailLabel.pack(anchor="w")

        # DEVICE CARD
        self.cardFrame = customtkinter.CTkScrollableFrame(
            master=self, fg_color=Util.COLOR_NEUTRAL_1, width=300, corner_radius=Util.CORNER_RADIUS)
        self.cardFrame.grid(row=0, column=2, sticky="nswe", padx=[5, 0])
        self.cardLabel = customtkinter.CTkLabel(
            master=self.cardFrame, text_color=Util.COLOR_NEUTRAL_5, text="Accaptable Card", font=(Util.FONT.SemiBold, Util.FONT.SIZE.Large))
        self.cardLabel.pack(anchor="w")

    def itemContainer(self, title):
        self.nodeItemContainer = customtkinter.CTkFrame(
            master=self.deviceListFrame, height=50, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.nodeItemContainer.pack(
            anchor="center", fill="both", padx=[0, 10], pady=10)
        self.nodeItemLabel = customtkinter.CTkLabel(
            master=self.nodeItemContainer, text_color=Util.COLOR_NEUTRAL_5, text=f"{title}", font=(Util.FONT.Regular, Util.FONT.SIZE.Regular), pady=0)
        self.nodeItemLabel.place(relx=0.1, rely=0.17, anchor="nw")
        self.nodeButton = customtkinter.CTkButton(master=self.nodeItemContainer, command=lambda: self.roomDetailOnClick(title), text="Detail" if Util.OS == "Windows" else "", image=Util.imageGenerator(
            "icon_arrow.png", 10), width=30, compound="right", hover=False, font=(Util.FONT.SemiBold, Util.FONT.SIZE.Small), fg_color=Util.COLOR_GREEN_1, corner_radius=Util.CORNER_RADIUS)
        self.nodeButton.place(relx=0.9, rely=0.23, anchor="ne")

    def roomDetailTemplate(self, title, desc):
        self.roomDetailFrame = customtkinter.CTkFrame(
            master=self.deviceDetailFrame, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.roomDetailFrame.pack(
            anchor="w", fill="both", padx=[0, 10], pady=10)
        self.roomDetailTitle = customtkinter.CTkLabel(
            master=self.roomDetailFrame, text_color=Util.COLOR_NEUTRAL_5, text=title, font=(Util.FONT.Regular, Util.FONT.SIZE.Regular))
        self.roomDetailTitle.pack(anchor="w", padx=[20, 0], pady=[20, 0])
        self.roomDetailDescription = customtkinter.CTkLabel(
            master=self.roomDetailFrame, text_color=Util.COLOR_NEUTRAL_5, justify="left", text=desc, font=(Util.FONT.Bold, Util.FONT.SIZE.Large))
        self.roomDetailDescription.pack(anchor="w", padx=[20, 0], pady=[0, 40])

    def cardDetailTemplate(self, title):
        self.cardDetailFrame = customtkinter.CTkFrame(
            master=self.cardFrame, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.cardDetailFrame.pack(
            anchor="w", fill="both", padx=[0, 10], pady=10)
        self.cardDetailTitle = customtkinter.CTkLabel(
            master=self.cardDetailFrame, wraplength=70, justify="left", text_color=Util.COLOR_NEUTRAL_5, text=title, font=(Util.FONT.Regular, Util.FONT.SIZE.Regular), pady=0)
        self.cardDetailTitle.pack(anchor="w", padx=[20, 0], pady=10)

    def addNewNodeOnClick(self):
        availableData = Gateway.get_by_id(1)
        gatewayShortId = availableData.shortId
        resp = requests.post(f"{Util.URL}/api/v1/gateway/device/h/initialize-new-node",
                             json={"gatewayShortId": gatewayShortId}, headers=header)
        if (resp.status_code == 200):
            respData = resp.json()
            Node.create(shortId=respData["data"]["device_id"])
            self.itemContainer(respData["data"]["device_id"])
            os.kill(Variable.syncPid(), SIGINT)
            self.threadSync()

        if (resp.status_code != 200):
            Toast(master=self.master, color=Util.COLOR_RED_1,
                  errMsg="Failed To Create Node")
            print(resp.json())

    def roomDetailOnClick(self, id):
        self.deviceFrameToRemove = self.deviceDetailFrame.winfo_children()[1::]
        self.cardFrameToRemove = self.cardFrame.winfo_children()[1::]
        for frame in self.deviceFrameToRemove:
            Util.frameDestroyer(frame)
        for frame in self.cardFrameToRemove:
            Util.frameDestroyer(frame)

        # Load From DB
        node_DB = Node.get(Node.shortId == id)
        nodeID = node_DB.shortId
        nodeName = node_DB.buildingName if node_DB.buildingName != None else "Not Link"
        lastOnline = ""
        if node_DB.lastOnline != None:
            # execpetion for linux
            try:
                formatedDate = datetime.fromisoformat(
                    node_DB.lastOnline).astimezone(timezone(timedelta(hours=7)))
            except:
                formatedDate = datetime.fromisoformat(
                    node_DB.lastOnline).replace('Z', '+00:00').astimezone(timezone(timedelta(hours=7)))

            lastOnline = f"{formatedDate.date()}\n{formatedDate.hour}:{formatedDate.minute}"
        else:
            lastOnline = "Offline"

        self.roomDetailTemplate("Room ID", nodeID)
        self.roomDetailTemplate("Room Name", nodeName)
        self.roomDetailTemplate("Last Online", lastOnline)

        cards = Card.select().join(AccessRole).join(Node).where(Node.shortId == nodeID)
        for card in cards:
            self.cardDetailTemplate(card.cardId)

    def threadSync(self):
        syncThread = Thread(target=self.startSync)
        syncThread.start()

    def startSync(self):
        print(" [!main]: Start Sync")
        if platform.system() == "Windows":
            subprocess.call('start /wait python ./amqp.py', shell=True)

        if platform.system() == "Linux":
            pass


class NetworkFrames(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        master.grid_columnconfigure(1, weight=40)
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        # DEVICE LIST
        self.deviceListFrame = customtkinter.CTkScrollableFrame(
            master=self, width=350, fg_color=Util.COLOR_NEUTRAL_1,  corner_radius=Util.CORNER_RADIUS)
        self.deviceListFrame.grid(row=0, column=0, sticky="nswe", padx=10)
        self.deviceListLabel = customtkinter.CTkLabel(
            master=self.deviceListFrame, text_color=Util.COLOR_NEUTRAL_5, text="Mesh AP Port", font=(Util.FONT.SemiBold, Util.FONT.SIZE.Large))
        self.deviceListLabel.pack(anchor="w")
        self.devices = []

        # LIST ALL AVAILABLE PORT
        ports = serial.tools.list_ports.comports()
        portsList = []
        portsListForUserInterface = []
        for port in ports:
            portsList.append(str(port))
            portsListForUserInterface.append(str(port).split(" - ")[0])

        # DISPLAY ALL AVAILABLE PORT
        for port in portsListForUserInterface:
            self.itemContainer(port)
        # self.itemContainer("/dev/ttyUSB0")

        # NETWORK DETAIL
        self.networkDetailFrame = customtkinter.CTkScrollableFrame(
            master=self, width=350, fg_color=Util.COLOR_NEUTRAL_1,  corner_radius=Util.CORNER_RADIUS)
        self.networkDetailFrame.grid(
            row=0, column=1, sticky="nswe", padx=[0, 10])
        self.networkDetailLabel = customtkinter.CTkLabel(
            master=self.networkDetailFrame, text_color=Util.COLOR_NEUTRAL_5, text="Network Status", font=(Util.FONT.SemiBold, Util.FONT.SIZE.Large))
        self.networkDetailLabel.pack(anchor="w")

    def itemContainer(self, title):
        self.nodeItemContainer = customtkinter.CTkFrame(
            master=self.deviceListFrame, height=50, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.nodeItemContainer.pack(
            anchor="center", fill="both", padx=[0, 10], pady=10)
        self.nodeItemLabel = customtkinter.CTkLabel(
            master=self.nodeItemContainer, text_color=Util.COLOR_NEUTRAL_5, text=f"{title}", font=(Util.FONT.Regular, Util.FONT.SIZE.Regular), pady=0)
        self.nodeItemLabel.place(relx=0.1, rely=0.17, anchor="nw")
        # CEK APAKAH PORT YANG DITUJU SUDAH AKTIF DAN MEMILIKI PID
        port_pid = Variable.getPortAuthDaemonPID(title)
        # JIKA TERDAPAT PID AKTIF MAKA BUTTON MENAMPILKAN TULISAN STATUS
        if port_pid:
            statusPid = psutil.pid_exists(port_pid)
            if (statusPid):
                self.nodeButton = customtkinter.CTkButton(master=self.nodeItemContainer, text="Status" if Util.OS == "Windows" else "", image=Util.imageGenerator(
                    "icon_arrow.png" if Util.OS == "Windows" else "icon_information.png", 10), width=30, compound="right", hover=False, font=(Util.FONT.SemiBold, Util.FONT.SIZE.Small), fg_color=Util.COLOR_GREEN_1, corner_radius=Util.CORNER_RADIUS, command=lambda: self.portOnClick(title))
            if (not statusPid):
                port_pid = False

        # JIKA TIDAK TERDAPAT PID AKTIF MAKA BUTTON MENAMPILKAN TULISAN START
        if port_pid == False:
            self.nodeButton = customtkinter.CTkButton(master=self.nodeItemContainer, text="Start" if Util.OS == "Windows" else "", image=Util.imageGenerator(
                "icon_arrow.png", 10), width=30, compound="right", hover=False, font=(Util.FONT.SemiBold, Util.FONT.SIZE.Small), fg_color=Util.COLOR_GREEN_1, corner_radius=Util.CORNER_RADIUS, command=lambda: self.portOnClick(title))
        self.nodeButton.place(relx=0.9, rely=0.23, anchor="ne")

    def networkDetailTemplate(self, title, desc):
        self.networkItemFrame = customtkinter.CTkFrame(
            master=self.networkDetailFrame, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.networkItemFrame.pack(
            anchor="w", fill="both", padx=[0, 10], pady=10)
        self.roomDetailTitle = customtkinter.CTkLabel(
            master=self.networkItemFrame, text_color=Util.COLOR_NEUTRAL_5, text=title, font=(Util.FONT.Regular, Util.FONT.SIZE.Regular))
        self.roomDetailTitle.pack(anchor="w", padx=[20, 0], pady=[10, 0])
        self.roomDetailDescription = customtkinter.CTkLabel(
            master=self.networkItemFrame, justify="left", wraplength=375 if Util.OS == "Windows" else 210, text_color=Util.COLOR_NEUTRAL_5, text=desc, font=(Util.FONT.Bold, Util.FONT.SIZE.Large))
        self.roomDetailDescription.pack(anchor="w", padx=[20, 0], pady=[0, 20])

    def portOnClick(self, port):
        # REMOVE PREVIUS CONTENT
        self.networkFrameToRemove = self.networkDetailFrame.winfo_children()[
            1::]
        for frame in self.networkFrameToRemove:
            Util.frameDestroyer(frame)

        # GET PID
        authPid = Variable.getPortAuthDaemonPID(port)
        if (authPid):
            statusPid = psutil.pid_exists(authPid)
        else:
            statusPid = False

        # TRYING START CONNECTION IF NO DAEMON STARTED YET
        if (statusPid == False):
            self.startConnectionOnClick(port)

        # GET PORT INFO
        availableData = Variable.getPortNetwrokCredential(port)

        # DISPLAY INFORMATION
        if (availableData):
            self.networkDetailTemplate("MESH SSID", availableData["SSID"])
            self.networkDetailTemplate(
                "MESH PASSWORD", availableData["PASSWORD"])
            self.networkDetailTemplate(
                "GATEWAY NAME", availableData["GATEWAY"])
            self.networkDetailTemplate("LAST SEEN", "DAEMON ID")
            self.meshDaemonStatus = customtkinter.CTkButton(
                master=self.networkDetailFrame, text_color=Util.COLOR_NEUTRAL_5, text="Daemon Status", command=lambda: self.checkAuthDaemon(port), fg_color=Util.COLOR_GREEN_1, hover_color=Util.COLOR_GREEN_2, height=40, font=(Util.FONT.SemiBold, Util.FONT.SIZE.Regular))
            self.meshDaemonStatus.pack(anchor="center",
                                       padx=[0, 10], pady=[10, 15], fill="x")
            self.meshDaemonStop = customtkinter.CTkButton(
                master=self.networkDetailFrame, text_color=Util.COLOR_NEUTRAL_5, text="Stop Daemon", command=lambda: self.stopConnectionOnClick(port), fg_color=Util.COLOR_RED_1, hover_color=Util.COLOR_RED_2, height=40, font=(Util.FONT.SemiBold, Util.FONT.SIZE.Regular))
            self.meshDaemonStop.pack(anchor="center",
                                     padx=[0, 10], pady=[0, 20], fill="x")

    def startConnectionOnClick(self, port):
        networkThread = Thread(target=lambda: self.startConnection(port))
        networkThread.start()

    def stopConnectionOnClick(self, port):
        Util.stopScript(Variable.getPortAuthDaemonPID(port))

    def startConnection(self, port):
        print("selected port", port)
        Util.startScript(f"./serialWorker.py \"{port}\"")

    def checkAuthDaemon(self, port):
        authPid = Variable.getPortAuthDaemonPID(port)
        statusPid = psutil.pid_exists(authPid)
        if (statusPid):
            Toast(master=self.master, color=Util.COLOR_GREEN_1,
                  errMsg="ESP Mesh Auth Service Running")

        if (statusPid == False):
            Toast(master=self.master, color=Util.COLOR_RED_1,
                  errMsg="ESP Mesh Auth Service Stop")


class SyncFrames(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Load DB DATA
        availableData = Gateway.get_by_id(1)

        gatewayShortId = availableData.shortId
        gatewayName = availableData.name if availableData.name != None else "Not Linked"
        syncDate = ""
        if availableData.lastSync != None:
            # execpetion for linux
            try:
                formatedDate = datetime.fromisoformat(
                    availableData.lastSync).astimezone(timezone(timedelta(hours=7)))
            except:
                formatedDate = datetime.fromisoformat(
                    availableData.lastSync.replace('Z', '+00:00')).astimezone(timezone(timedelta(hours=7)))

            syncDate = f"{formatedDate.date()}\n{formatedDate.hour}:{formatedDate.minute}"
        else:
            syncDate = "Not Sync"

        master.grid_columnconfigure(1, weight=40)
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=4)

        self.syncSettingFrame = customtkinter.CTkScrollableFrame(
            master=self, width=400, fg_color=Util.COLOR_NEUTRAL_1, corner_radius=Util.CORNER_RADIUS)
        self.syncSettingFrame.grid(
            row=0, column=0, sticky="nswe", padx=[0, 20])
        self.syncLabel = customtkinter.CTkLabel(
            master=self.syncSettingFrame, text_color=Util.COLOR_NEUTRAL_5, text="Gateway Sync", font=(Util.FONT.SemiBold, Util.FONT.SIZE.Large), anchor="w")
        self.syncLabel.pack(anchor="w", fill="both", padx=[20, 0], pady=10)
        self.gatewayFrame = customtkinter.CTkFrame(
            master=self.syncSettingFrame, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.gatewayFrame.pack(anchor="w", fill="both", padx=20, pady=10)
        self.gatewayTitle = customtkinter.CTkLabel(
            master=self.gatewayFrame, text_color=Util.COLOR_NEUTRAL_5, text=f"Gateway ID: {gatewayShortId}", font=(Util.FONT.Regular, Util.FONT.SIZE.Regular))
        self.gatewayTitle.pack(anchor="w", padx=20, pady=15)
        self.syncDetailTemplate("Gateway Spot Name", f"{gatewayName}")
        self.syncDetailTemplate("Last Card Sync", f"{syncDate}")
        self.gatewayButton = customtkinter.CTkButton(master=self.syncSettingFrame, text="Sync Now", font=(Util.FONT.Bold, Util.FONT.SIZE.Regular), image=Util.imageGenerator(
            "icon_sync.png"), compound="right", fg_color=Util.COLOR_NEUTRAL_2, hover_color=Util.COLOR_BLUE_1, corner_radius=Util.CORNER_RADIUS, command=self.syncOnClick)
        self.gatewayButton.pack(
            anchor="center", fill="both", padx=20, pady=15, ipady=10)

        # Syncy Service
        self.syncFrame = customtkinter.CTkFrame(
            master=self, fg_color=Util.COLOR_NEUTRAL_1, corner_radius=Util.CORNER_RADIUS)
        self.syncFrame.grid(row=0, column=1, sticky="nswe", padx=[0, 20])
        self.syncLabel = customtkinter.CTkLabel(master=self.syncFrame, wraplength=275 if Util.OS == "Windows" else 175, justify="left", text="Syncronization Daeomon Settings", font=(
            Util.FONT.SemiBold, Util.FONT.SIZE.Large), text_color=Util.COLOR_NEUTRAL_5, pady=0, width=330, anchor="w")
        self.syncLabel.pack(anchor="w", fill="both", padx=[20, 20], pady=10)
        self.syncStartBtn = customtkinter.CTkButton(master=self.syncFrame, text="Start", height=35,
                                                    fg_color=Util.COLOR_GREEN_1, hover_color=Util.COLOR_GREEN_2, command=self.threadSync)
        self.syncStartBtn.pack(anchor="w", fill="both",
                               padx=[20, 20], pady=10)
        self.syncStopBtn = customtkinter.CTkButton(master=self.syncFrame, text="Stop", width=90,
                                                   height=35, fg_color=Util.COLOR_RED_1, hover_color=Util.COLOR_RED_2, command=self.stopSync)
        self.syncStopBtn.pack(anchor="w", fill="both",
                              padx=[20, 20], pady=10)
        self.syncStatusBtn = customtkinter.CTkButton(
            master=self.syncFrame, text="Status", width=90, height=35, fg_color=Util.COLOR_BLUE_1, hover_color=Util.COLOR_BLUE_2, command=self.checkSync)
        self.syncStatusBtn.pack(anchor="w", fill="both",
                                padx=[20, 20], pady=10)

    def syncDetailTemplate(self, title, desc):
        self.syncDetailFrame = customtkinter.CTkFrame(
            master=self.syncSettingFrame, fg_color=Util.COLOR_NEUTRAL_2, height=100, corner_radius=Util.CORNER_RADIUS)
        self.syncDetailFrame.pack(anchor="w", fill="both", padx=20, pady=10)
        self.syncDetailTitle = customtkinter.CTkLabel(
            master=self.syncDetailFrame, text_color=Util.COLOR_NEUTRAL_5, text=title, font=(Util.FONT.Regular, Util.FONT.SIZE.Regular))
        self.syncDetailTitle.pack(anchor="w", padx=[20, 0], pady=[20, 0])
        self.syncDetailDescription = customtkinter.CTkLabel(
            master=self.syncDetailFrame, wraplength=200, justify="left", text_color=Util.COLOR_NEUTRAL_5, text=desc, font=(Util.FONT.Bold, Util.FONT.SIZE.Large))
        self.syncDetailDescription.pack(anchor="w", padx=[20, 0], pady=[0, 30])

    def syncOnClick(self):
        gatewayId = Gateway.get_by_id(1)
        resp = requests.get(
            f"{Util.URL}/api/v1/gateway/device/h/access-card-for-gateway/{gatewayId.shortId}", headers=header)
        if resp.status_code == 200:
            respData = resp.json()
            AccessRole.delete().execute()
            for data in respData["data"]:
                for device in data["room"]:
                    node = Node.get(
                        Node.shortId == device["device"]["device_id"])
                    try:
                        card = Card.get(Card.cardId == data["card_number"])
                    except:
                        card = Card.create(cardId=data["card_number"], pin=data["pin"],
                                           isTwoStepAuth=data["isTwoStepAuth"], cardStatus=data["card_status"], isBanned=data["banned"])

                    AccessRole.create(card=card, node=node)

                    # Card.create(node=node, cardId=data["card_number"], pin=data["pin"], isTwoStepAuth=data["isTwoStepAuth"])
            availableGateway = Gateway.get_by_id(1)
            current_date = datetime.now()
            availableGateway.lastSync = current_date.isoformat()
            availableGateway.save()

            Toast(master=self.master, color=Util.COLOR_GREEN_1,
                  errMsg="Success Syncy Card Data")

    def threadSync(self):
        syncThread = Thread(target=self.startSync)
        syncThread.start()

    def startSync(self):
        print(" [!main]: Start Sync")
        statusPid = psutil.pid_exists(Variable.syncPid())
        if (not statusPid):
            Util.startScript("./amqp.py")
        if (statusPid):
            Toast(master=self.master, color=Util.COLOR_GREEN_1,
                  errMsg="Service Already Running")

    def stopSync(self):
        print(" [!main]: Stop Sync")
        Util.stopScript(Variable.syncPid())

    def checkSync(self):
        syncPid = Variable.syncPid()
        statusPid = psutil.pid_exists(syncPid)
        if (statusPid):
            Toast(master=self.master, color=Util.COLOR_GREEN_1,
                  errMsg="Service Running")

        if (statusPid == False):
            Toast(master=self.master, color=Util.COLOR_RED_1,
                  errMsg="Service Stop")


class SettingFrames(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        master.grid_columnconfigure(1, weight=40)
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=4)

        self.credentialFrame = customtkinter.CTkFrame(
            master=self, fg_color=Util.COLOR_NEUTRAL_1, corner_radius=Util.CORNER_RADIUS, width=400)
        self.credentialFrame.grid(
            row=0, column=0, sticky="nswe", padx=[0, 20])
        self.credentialLabel = customtkinter.CTkLabel(
            master=self.credentialFrame, text_color=Util.COLOR_NEUTRAL_5, text="Gateway Credential Settings", font=(Util.FONT.SemiBold, Util.FONT.SIZE.Large), pady=0, anchor="w")
        self.credentialLabel.pack(anchor="w", fill="both",
                                  padx=[20, 20], pady=10)
        self.apiIdLabel = customtkinter.CTkLabel(
            master=self.credentialFrame, text_color=Util.COLOR_NEUTRAL_5, text="API ID", font=(Util.FONT.Bold, Util.FONT.SIZE.Regular))
        self.apiIdLabel.pack(anchor="w",
                             padx=[20, 20], pady=0)
        self.apiIdForm = customtkinter.CTkEntry(master=self.credentialFrame, text_color=Util.COLOR_NEUTRAL_5, height=50, placeholder_text="Please Input API ID",
                                                fg_color=Util.COLOR_NEUTRAL_2, border_color=Util.COLOR_NEUTRAL_4, corner_radius=Util.CORNER_RADIUS)
        self.apiIdForm.pack(anchor="w", fill="both", padx=[20, 20], pady=10)
        self.apiKeyLabel = customtkinter.CTkLabel(
            master=self.credentialFrame, text_color=Util.COLOR_NEUTRAL_5, text="API Key", font=(Util.FONT.Bold, Util.FONT.SIZE.Regular))
        self.apiKeyLabel.pack(anchor="w", padx=[20, 20], pady=0)
        self.apiKeyForm = customtkinter.CTkEntry(master=self.credentialFrame, text_color=Util.COLOR_NEUTRAL_5, height=50, placeholder_text="Please Input API Key",
                                                 fg_color=Util.COLOR_NEUTRAL_2, border_color=Util.COLOR_NEUTRAL_4, corner_radius=Util.CORNER_RADIUS, width=350)
        self.apiKeyForm.pack(anchor="w", fill="both", padx=[20, 20], pady=10)
        self.submitButton = customtkinter.CTkButton(master=self.credentialFrame, width=350, height=45, text="Save", fg_color=Util.COLOR_BLUE_1,
                                                    hover_color=Util.COLOR_BLUE_2, corner_radius=Util.CORNER_RADIUS, font=(Util.FONT.Bold, Util.FONT.SIZE.Regular), command=self.saveOnClick)
        self.submitButton.pack(anchor="w", padx=[20, 20], pady=10, fill="both")

        self.aboutFrame = customtkinter.CTkFrame(
            master=self, fg_color=Util.COLOR_NEUTRAL_1, corner_radius=Util.CORNER_RADIUS, width=400)
        self.aboutFrame.grid(
            row=0, column=1, sticky="nswe", padx=[0, 0])
        self.aboutLabel = customtkinter.CTkLabel(
            master=self.aboutFrame, text="About", text_color=Util.COLOR_NEUTRAL_5, font=(Util.FONT.SemiBold, Util.FONT.SIZE.Large), pady=0, anchor="w", width=350)
        self.aboutLabel.pack(anchor="w", fill="both",
                             padx=[20, 20], pady=10)
        self.information("Device Version: 1.0.0")
        self.information("Developed by Dimas Aulia")

    def information(self, text):
        self.informationLabel = customtkinter.CTkLabel(
            master=self.aboutFrame, text=text, text_color=Util.COLOR_NEUTRAL_5, font=(Util.FONT.Regular, Util.FONT.SIZE.Regular), pady=0, anchor="w", width=350)
        self.informationLabel.pack(anchor="w", fill="both",
                                   padx=[20, 20], pady=0)

    def saveOnClick(self):
        apiId = self.apiIdForm.get()
        apiKey = self.apiKeyForm.get()
        availableData = []
        datas = Credential.select().dicts()
        for data in datas:
            availableData.append(data)

        if len(apiId) < 1 or len(apiKey) < 1:
            Toast(master=self.master, color=Util.COLOR_RED_1,
                  errMsg="Api Id & Key can't empty")
            return

        if len(availableData) > 0:
            Credential.update(apiID=apiId, apiKey=apiKey).where(
                Credential.id == int(availableData[0]["id"])).execute()
            Toast(master=self.master, color=Util.COLOR_GREEN_1,
                  errMsg="Success Save Data")
        else:
            Credential.create(apiID=apiId, apiKey=apiKey)
            Toast(master=self.master, color=Util.COLOR_GREEN_1,
                  errMsg="Success Save Data")


class CardFrames(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        master.grid_columnconfigure(1, weight=40)
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        if Util.READER_STATUS == False:
        #if True:
            print("starting reader")
            Util.READER_STATUS = True
            cardReadingProcess = Thread(target=self.cardReading)
            cardReadingProcess.daemon = True
            cardReadingProcess.start()

        self.credentialFrame = customtkinter.CTkFrame(
            master=self, fg_color=Util.COLOR_NEUTRAL_1, corner_radius=Util.CORNER_RADIUS, width=400)
        self.credentialFrame.grid(
            row=0, column=0, sticky="nswe", padx=[0, 20])
        self.credentialLabel = customtkinter.CTkLabel(
            master=self.credentialFrame, text_color=Util.COLOR_NEUTRAL_5, text="Card Registration", font=(Util.FONT.Bold, Util.FONT.SIZE.Large), pady=0, anchor="w")
        self.credentialLabel.pack(anchor="w", fill="both",
                                  padx=[20, 20], pady=10)

        self.cardIdLabel = customtkinter.CTkLabel(
            master=self.credentialFrame, text_color=Util.COLOR_NEUTRAL_5, text="CARD ID", font=(Util.FONT.Bold, Util.FONT.SIZE.Regular))
        self.cardIdLabel.pack(anchor="w",
                              padx=[20, 20], pady=0)
        self.cardIdForm = customtkinter.CTkEntry(master=self.credentialFrame, text_color=Util.COLOR_NEUTRAL_5, height=50, placeholder_text="Card ID will appear here when card detected",
                                                 fg_color=Util.COLOR_NEUTRAL_2, border_color=Util.COLOR_NEUTRAL_4, corner_radius=Util.CORNER_RADIUS)
        self.cardIdForm.pack(anchor="w", fill="both", padx=[20, 20], pady=10)
        self.cardIdForm.configure(state="disable")

        self.cardPinLabel = customtkinter.CTkLabel(
            master=self.credentialFrame, text_color=Util.COLOR_NEUTRAL_5, text="CARD PIN", font=(Util.FONT.Bold, Util.FONT.SIZE.Regular))
        self.cardPinLabel.pack(anchor="w", padx=[20, 20], pady=0)
        self.cardPinForm = customtkinter.CTkEntry(master=self.credentialFrame, text_color=Util.COLOR_NEUTRAL_5, height=50, placeholder_text="Optional to proivde card pin",
                                                  fg_color=Util.COLOR_NEUTRAL_2, border_color=Util.COLOR_NEUTRAL_4, corner_radius=Util.CORNER_RADIUS, width=350)
        self.cardPinForm.pack(anchor="w", fill="both", padx=[20, 20], pady=10)

        self.cardOwnerLabel = customtkinter.CTkLabel(
            master=self.credentialFrame, text_color=Util.COLOR_NEUTRAL_5, text="CARD OWNER", font=(Util.FONT.Bold, Util.FONT.SIZE.Regular))
        self.cardOwnerLabel.pack(anchor="w", padx=[20, 20], pady=0)
        self.cardOwnerForm = customtkinter.CTkEntry(master=self.credentialFrame, text_color=Util.COLOR_NEUTRAL_5, height=50, placeholder_text="Optional to proivde card owner (username)",
                                                    fg_color=Util.COLOR_NEUTRAL_2, border_color=Util.COLOR_NEUTRAL_4, corner_radius=Util.CORNER_RADIUS, width=350)
        self.cardOwnerForm.pack(anchor="w", fill="both",
                                padx=[20, 20], pady=10)

        self.submitButton = customtkinter.CTkButton(master=self.credentialFrame, width=350, height=45, text="Save", fg_color=Util.COLOR_GREEN_1,
                                                    hover_color=Util.COLOR_GREEN_2, corner_radius=Util.CORNER_RADIUS, font=(Util.FONT.Bold, Util.FONT.SIZE.Regular), command=self.saveOnClick)
        self.submitButton.pack(anchor="w", padx=[20, 20], pady=10, fill="both")

        self.aboutFrame = customtkinter.CTkFrame(
            master=self, fg_color=Util.COLOR_NEUTRAL_1, corner_radius=Util.CORNER_RADIUS, width=400)
        self.aboutFrame.grid(
            row=0, column=1, sticky="nswe", padx=[0, 0])
        self.aboutLabel = customtkinter.CTkLabel(
            master=self.aboutFrame, text_color=Util.COLOR_NEUTRAL_5, text="Instruction", font=(Util.FONT.Bold, Util.FONT.SIZE.Large), pady=0, anchor="w", width=350)
        self.aboutLabel.pack(anchor="w", fill="both",
                             padx=[20, 20], pady=10)
        self.information("1. Please tap your card on RFID Reader")
        self.information(
            "2. If you want activate two step authentication, please fill PIN form")
        self.information(
            "3. If you want pair card with user please provide username")
        self.information("4. Save Your Data")
        Util.CARD_FORM = self.cardIdForm

    def information(self, text):
        self.informationLabel = customtkinter.CTkLabel(
            master=self.aboutFrame, text_color=Util.COLOR_NEUTRAL_5, text=text, wraplength=375 if Util.OS == "Windows" else 175, justify="left", font=(Util.FONT.Regular, Util.FONT.SIZE.Regular), pady=0, anchor="w", width=350)
        self.informationLabel.pack(anchor="w", fill="both",
                                   padx=[20, 20], pady=0)

    def saveOnClick(self):
        pass

    def cardReading(self):
        while True:
            try:
                id = Util.READER.scan_field()
                id_hex = binascii.hexlify(id).decode()
                #print("HEX", id_hex)
                Util.CARD_FORM.configure(state="normal")
                Util.CARD_FORM.configure(placeholder_text=id_hex)
                Util.CARD_FORM.configure(state="disable")

            except:
               #print("restarting")
               GPIO.cleanup()
               break
            finally:
                GPIO.cleanup()
  
        #print("waking up rfid again")
        cardReadingProcess = Thread(target=self.cardReading)
        cardReadingProcess.daemon = True
        cardReadingProcess.start()

class Toast(customtkinter.CTkFrame):
    count = 0

    def __init__(self, master, errMsg, color, text_color=Util.COLOR_NEUTRAL_5, **kwargs):

        Toast.count += 1
        self.marginY = [100, 10] if Toast.count <= 1 else [10, 10]
        super().__init__(master, width=500, height=50, fg_color=color,
                         corner_radius=Util.CORNER_RADIUS, bg_color=Util.COLOR_TRANSPARENT, **kwargs)
        self.pack(anchor="n", pady=self.marginY)

        self.errorLabel = customtkinter.CTkLabel(
            master=self, text=errMsg, font=(Util.FONT.Bold, Util.FONT.SIZE.Large), text_color=text_color)
        self.errorLabel.place(relx=0.05, rely=0.48, anchor="w")

        self.closeButton = customtkinter.CTkButton(master=self, text="", image=Util.imageGenerator(
            "icon_close.png", 35), compound="right", anchor="e", width=30, hover=False, fg_color=Util.COLOR_TRANSPARENT, command=self.closeOnClick)
        self.closeButton.place(relx=0.96, rely=0.5, anchor="e")

    def closeOnClick(self):
        Util.frameDestroyer(self)
        if Toast.count > 0:
            Toast.count -= 1


class SetInterval:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.stopEvent = Event()
        thread = Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self):
        nextTime = time.time()+self.interval
        while not self.stopEvent.wait(nextTime-time.time()):
            nextTime += self.interval
            self.action()

    def cancel(self):
        self.stopEvent.set()


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry(f"{Util.APP_WIDTH}x{Util.APP_HEIGHT}")
        self.title("Smart Door App")
        self.minsize(Util.APP_WIDTH, Util.APP_HEIGHT)
        self.grid_propagate(False)
        self.configure(fg_color=Util.COLOR_NEUTRAL_3)
        self.cancelPingDaeomon = SetInterval(25*60, Util.pingServer)
        # loginFrame = LoginFrames(master=self, fg_color=Util.COLOR_TRANSPARENT)
        # loginFrame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.sideBarFrame = SideBarFrames(
            master=self, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.sideBarFrame.grid(row=0, column=0, padx=[
                               20, 0], pady=20, sticky="nwsw")


if __name__ == "__main__":
    app = App()
    mainApp = Thread(target=app.mainloop())
    mainApp.start()
    print("Try to cancel ping")
    # for development, when app close system stop pinging server
    app.cancelPingDaeomon.cancel()
