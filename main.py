import customtkinter
import os
from PIL import Image
import requests
import json
import subprocess
import platform
import psutil
from threading import Thread
from signal import SIGBREAK, SIGINT, signal
from datetime import datetime, timedelta, timezone
from database.scheme import Credential, Gateway, Node, Card, AccessRole, db
from secret.secret import header
from variable import *
from peewee import *


class Util():
    def __init__(self):
        pass

    image_path = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "static")

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
    URL = "http://localhost:8000"

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
            master=self, fg_color="transparent")
        self.formFrame.place(relx=0.5, rely=0.5, anchor="center")

        self.usernameLabel = customtkinter.CTkLabel(
            master=self.formFrame, text="Username", font=("Quicksand Bold", 16))
        self.usernameLabel.grid(row=0, column=0, sticky="w", pady=[0, 10])
        self.usernameForm = customtkinter.CTkEntry(master=self.formFrame, width=500, height=50, placeholder_text="Please Input Your Username",
                                                   fg_color=Util.COLOR_NEUTRAL_2, border_color=Util.COLOR_NEUTRAL_4, corner_radius=Util.CORNER_RADIUS)
        self.usernameForm.grid(row=1, column=0, sticky="w")
        self.passwordLabel = customtkinter.CTkLabel(
            master=self.formFrame, text="Password", font=("Quicksand Bold", 16))
        self.passwordLabel.grid(row=2, column=0, pady=[20, 10], sticky="w")
        self.passwordForm = customtkinter.CTkEntry(master=self.formFrame, width=500, height=50, placeholder_text="Please Input Your Password",
                                                   show="*", fg_color=Util.COLOR_NEUTRAL_2, border_color=Util.COLOR_NEUTRAL_4, corner_radius=Util.CORNER_RADIUS)
        self.passwordForm.grid(row=3, column=0, sticky="w")
        self.submitButton = customtkinter.CTkButton(master=self.formFrame, width=500, height=45, text="Login", command=self.fetchLogin,
                                                    fg_color=Util.COLOR_BLUE_1, hover_color=Util.COLOR_BLUE_2, corner_radius=Util.CORNER_RADIUS, font=("Quicksand Bold", 16))
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
            master=self.master, width=100, fg_color="#29283D")
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
            master=self.formFrame, text="API ID", font=("Quicksand Bold", 16))
        self.apiIdLabel.grid(row=0, column=0, sticky="w", pady=[0, 10])
        self.apiIdForm = customtkinter.CTkEntry(master=self.formFrame, width=500, height=50, placeholder_text="Please Input API ID",
                                                fg_color=Util.COLOR_NEUTRAL_2, border_color=Util.COLOR_NEUTRAL_4, corner_radius=Util.CORNER_RADIUS)
        self.apiIdForm.grid(row=1, column=0, sticky="w")
        self.apiKeyLabel = customtkinter.CTkLabel(
            master=self.formFrame, text="API Key", font=("Quicksand Bold", 16))
        self.apiKeyLabel.grid(row=2, column=0, pady=[20, 10], sticky="w")
        self.apiKeyForm = customtkinter.CTkEntry(master=self.formFrame, width=500, height=50, placeholder_text="Please Input API Key",
                                                 fg_color=Util.COLOR_NEUTRAL_2, border_color=Util.COLOR_NEUTRAL_4, corner_radius=Util.CORNER_RADIUS)
        self.apiKeyForm.grid(row=3, column=0, sticky="w")
        self.submitButton = customtkinter.CTkButton(master=self.formFrame, width=500, height=45, text="Save", command=self.saveOnClick,
                                                    fg_color=Util.COLOR_BLUE_1, hover_color=Util.COLOR_BLUE_2, corner_radius=Util.CORNER_RADIUS, font=("Quicksand Bold", 16))
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


class SideBarFrames(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.master = master
        master.grid_rowconfigure(0, weight=1)  # configure grid system
        master.grid_columnconfigure(0, weight=1)
        self.homeButtonIcon = Util.imageGenerator("icon_home.png")
        self.homeButton = customtkinter.CTkButton(master=self, text="Home", font=("Quicksand Bold", 12), image=self.homeButtonIcon,
                                                  anchor="w", fg_color=Util.COLOR_BLUE_1, hover_color=Util.COLOR_BLUE_2, command=lambda: self.widgetOnClick(self.homeButton))
        self.homeButton.grid(row=0, column=0, padx=10, pady=20, sticky="w")
        self.homeFrame = HomeFrames(
            master=master, fg_color=Util.COLOR_TRANSPARENT)
        self.homeFrame.grid(row=0, column=1, padx=[
                            0, 20], pady=20, sticky="nsew")

        self.roomButtonIcon = Util.imageGenerator("icon_room.png")
        self.roomButton = customtkinter.CTkButton(master=self, text="Room", font=("Quicksand Bold", 12), image=self.roomButtonIcon,
                                                  anchor="w", fg_color="transparent", hover_color=Util.COLOR_BLUE_2, command=lambda: self.widgetOnClick(self.roomButton))
        self.roomButton.grid(row=1, column=0, padx=10, pady=20, sticky="w")

        self.syncButtonIcon = Util.imageGenerator("icon_sync.png")
        self.syncButton = customtkinter.CTkButton(master=self, text="Sync", font=("Quicksand Bold", 12), image=self.syncButtonIcon,
                                                  anchor="w", fg_color="transparent", hover_color=Util.COLOR_BLUE_2, command=lambda: self.widgetOnClick(self.syncButton))
        self.syncButton.grid(row=2, column=0, padx=10, pady=20, sticky="w")

        self.settingButtonIcon = Util.imageGenerator("icon_settings.png")
        self.settingButton = customtkinter.CTkButton(master=self, text="Setting", font=("Quicksand Bold", 12), image=self.settingButtonIcon,
                                                     anchor="w", fg_color="transparent", hover_color=Util.COLOR_BLUE_2, command=lambda: self.widgetOnClick(self.settingButton))
        self.settingButton.grid(row=4, column=0, padx=10, pady=20, sticky="w")

    def widgetOnClick(self, item):
        for child in self.winfo_children():
            child.configure(fg_color="transparent")
        item.configure(fg_color=Util.COLOR_BLUE_1)

        state = item.cget("text")
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

        if state == "Setting":
            print(" [!main]: Render Setting Frame")
            Util.frameSwitcher(originFrame=self.master.winfo_children()[
                               1], destinationFrame=SettingFrames, master=self.master, row=0, column=1, padx=[0, 20], pady=20, fg_color=Util.COLOR_TRANSPARENT)


class HomeFrames(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

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
            "Quicksand Bold", 40), text="Smart Door Gateway Device")
        self.appTitle.place(relx=0.02, rely=0.01)
        self.appDescription = customtkinter.CTkLabel(master=self.headerFrame, anchor="w", justify="left", font=(
            "Quicksand", 16), wraplength=600, text="The gateway device is the authentication center hardware for the smart door node. This device will store user card data, as well as be used to register user cards.")
        self.appDescription.place(relx=0.02, rely=0.25)

        self.nodeFrame = customtkinter.CTkFrame(
            master=self, height=200, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.nodeFrame.grid(row=1, column=0, pady=[
                            30, 0], padx=[0, 30], sticky="nwne")
        self.nodeFrame.grid_propagate(False)
        self.nodeFrameCount = customtkinter.CTkLabel(master=self.nodeFrame, font=(
            "Quicksand Bold", 100), text="10", fg_color="transparent")
        self.nodeFrameTitle = customtkinter.CTkLabel(
            master=self.nodeFrame, font=("Quicksand SemiBold", 18), text="Smart Door Node")
        self.nodeFrameDescription = customtkinter.CTkLabel(
            master=self.nodeFrame, font=("Quicksand Light", 18), text="Linked Device")
        self.nodeFrameTitle.place(relx=0.05, rely=0.1)
        self.nodeFrameCount.place(relx=0.05, rely=0.05)
        self.nodeFrameDescription.place(relx=0.05, rely=0.675)

        self.syncFrame = customtkinter.CTkFrame(
            master=self, height=200, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.syncFrame.grid(row=1, column=1, pady=[
                            30, 0], padx=30, sticky="nwne")
        self.syncFrame.grid_propagate(False)
        self.nodeFrameCount = customtkinter.CTkLabel(master=self.syncFrame, font=(
            "Quicksand Bold", 70), text="23:55", fg_color="transparent")
        self.nodeFrameTitle = customtkinter.CTkLabel(
            master=self.syncFrame, font=("Quicksand SemiBold", 18), text="Last Sync")
        self.nodeFrameDescription = customtkinter.CTkLabel(
            master=self.syncFrame, font=("Quicksand Light", 18), text="20 March 2023")
        self.nodeFrameTitle.place(relx=0.05, rely=0.1)
        self.nodeFrameCount.place(relx=0.05, rely=0.17)
        self.nodeFrameDescription.place(relx=0.05, rely=0.675)

        self.cardFrame = customtkinter.CTkFrame(
            master=self, height=200, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.cardFrame.grid(row=1, column=2, pady=[
                            30, 0], padx=[30, 0], sticky="nwne")
        self.cardFrame.grid_propagate(False)
        self.nodeFrameCount = customtkinter.CTkLabel(master=self.cardFrame, font=(
            "Quicksand Bold", 100), text="17", fg_color="transparent")
        self.nodeFrameTitle = customtkinter.CTkLabel(
            master=self.cardFrame, font=("Quicksand SemiBold", 18), text="Accapted Card")
        self.nodeFrameDescription = customtkinter.CTkLabel(
            master=self.cardFrame, font=("Quicksand Light", 18), text="Card")
        self.nodeFrameTitle.place(relx=0.05, rely=0.1)
        self.nodeFrameCount.place(relx=0.05, rely=0.05)
        self.nodeFrameDescription.place(relx=0.05, rely=0.675)


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
            master=self, fg_color=Util.COLOR_NEUTRAL_1, width=230, corner_radius=Util.CORNER_RADIUS)
        self.deviceListFrame.grid(row=0, column=0, sticky="nswe", padx=[0, 20])
        self.deviceListLabel = customtkinter.CTkLabel(
            master=self.deviceListFrame, text="Node List", font=("Quicksand SemiBold", 20))
        self.deviceListLabel.pack(anchor="w")
        self.button = customtkinter.CTkButton(master=self.deviceListFrame, command=self.addNewNodeOnClick, text="Create New Node", image=Util.imageGenerator(
            "icon_plus.png", 20), corner_radius=Util.CORNER_RADIUS, compound="right", font=("Quicksand SemiBold", 18), fg_color=Util.COLOR_GREEN_1, hover_color=Util.COLOR_GREEN_2)
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
            master=self, fg_color=Util.COLOR_NEUTRAL_1, width=250, corner_radius=Util.CORNER_RADIUS)
        self.deviceDetailFrame.grid(row=0, column=1, sticky="nswe", padx=20)
        self.deviceDetailLabel = customtkinter.CTkLabel(
            master=self.deviceDetailFrame, text="Node Detail", font=("Quicksand SemiBold", 20))
        self.deviceDetailLabel.pack(anchor="w")

        # DEVICE CARD
        self.cardFrame = customtkinter.CTkScrollableFrame(
            master=self, fg_color=Util.COLOR_NEUTRAL_1, width=230, corner_radius=Util.CORNER_RADIUS)
        self.cardFrame.grid(row=0, column=2, sticky="nswe", padx=[20, 0])
        self.cardLabel = customtkinter.CTkLabel(
            master=self.cardFrame, text="Accaptable Card", font=("Quicksand SemiBold", 20))
        self.cardLabel.pack(anchor="w")

    def itemContainer(self, title):
        self.nodeItemContainer = customtkinter.CTkFrame(
            master=self.deviceListFrame, height=50, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.nodeItemContainer.pack(
            anchor="center", fill="both", padx=[0, 10], pady=10)
        self.nodeItemLabel = customtkinter.CTkLabel(
            master=self.nodeItemContainer, text=f"{title}", font=("Quicksand", 16), pady=0)
        self.nodeItemLabel.place(relx=0.1, rely=0.17, anchor="nw")
        self.nodeButton = customtkinter.CTkButton(master=self.nodeItemContainer, command=lambda: self.roomDetailOnClick(title), text="Detail", image=Util.imageGenerator(
            "icon_arrow.png", 10), width=30, compound="right", hover=False, font=("Quicksand SemiBold", 14), fg_color=Util.COLOR_GREEN_1, corner_radius=Util.CORNER_RADIUS)
        self.nodeButton.place(relx=0.9, rely=0.23, anchor="ne")

    def roomDetailTemplate(self, title, desc):
        self.roomDetailFrame = customtkinter.CTkFrame(
            master=self.deviceDetailFrame, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.roomDetailFrame.pack(
            anchor="w", fill="both", padx=[0, 10], pady=10)
        self.roomDetailTitle = customtkinter.CTkLabel(
            master=self.roomDetailFrame, text=title, font=("Quicksand", 16))
        self.roomDetailTitle.pack(anchor="w", padx=[20, 0], pady=[20, 0])
        self.roomDetailDescription = customtkinter.CTkLabel(
            master=self.roomDetailFrame, text=desc, font=("Quicksand Bold", 24))
        self.roomDetailDescription.pack(anchor="w", padx=[20, 0], pady=[0, 40])

    def cardDetailTemplate(self, title):
        self.cardDetailFrame = customtkinter.CTkFrame(
            master=self.cardFrame, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.cardDetailFrame.pack(
            anchor="w", fill="both", padx=[0, 10], pady=10)
        self.cardDetailTitle = customtkinter.CTkLabel(
            master=self.cardDetailFrame, text=title, font=("Quicksand", 16), pady=0)
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
            formatedDate = datetime.fromisoformat(
                node_DB.lastOnline).astimezone(timezone(timedelta(hours=7)))
            lastOnline = f"{formatedDate.date()} {formatedDate.hour}:{formatedDate.minute}"
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
        print("  [!main]:  Start Sync")
        os.system("py amqp.py")


class SyncFrames(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Load DB DATA
        availableData = Gateway.get_by_id(1)

        gatewayShortId = availableData.shortId
        gatewayName = availableData.name if availableData.name != None else "Not Linked"
        syncDate = ""
        if availableData.lastSync != None:
            formatedDate = datetime.fromisoformat(
                availableData.lastSync).astimezone(timezone(timedelta(hours=7)))
            syncDate = f"{formatedDate.date()} {formatedDate.hour}:{formatedDate.minute}"
        else:
            syncDate = "Not Sync"

        master.grid_columnconfigure(1, weight=40)
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.syncSettingFrame = customtkinter.CTkFrame(
            master=self, fg_color=Util.COLOR_NEUTRAL_1, width=300, corner_radius=Util.CORNER_RADIUS)
        self.syncSettingFrame.grid(
            row=0, column=0, sticky="nwsw", padx=[0, 20])
        self.syncLabel = customtkinter.CTkLabel(
            master=self.syncSettingFrame, text="Gateway Sync", font=("Quicksand SemiBold", 20), anchor="w")
        self.syncLabel.pack(anchor="w", fill="both", padx=[20, 180], pady=10)
        self.gatewayFrame = customtkinter.CTkFrame(
            master=self.syncSettingFrame, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.gatewayFrame.pack(anchor="w", fill="both", padx=20, pady=10)
        self.gatewayTitle = customtkinter.CTkLabel(
            master=self.gatewayFrame, text=f"Gateway ID: {gatewayShortId}", font=("Quicksand", 16))
        self.gatewayTitle.pack(anchor="w", padx=20, pady=15)
        self.syncDetailTemplate("Gateway Spot Name", f"{gatewayName}")
        self.syncDetailTemplate("Last Card Sync", f"{syncDate}")
        self.gatewayButton = customtkinter.CTkButton(master=self.syncSettingFrame, text="Syncy Now", font=("Quicksand Bold", 18), image=Util.imageGenerator(
            "icon_sync.png"), compound="right", fg_color=Util.COLOR_NEUTRAL_2, hover_color=Util.COLOR_BLUE_1, corner_radius=Util.CORNER_RADIUS, command=self.syncOnClick)
        self.gatewayButton.pack(
            anchor="center", fill="both", padx=20, pady=15, ipady=10)

    def syncDetailTemplate(self, title, desc):
        self.syncDetailFrame = customtkinter.CTkFrame(
            master=self.syncSettingFrame, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.syncDetailFrame.pack(anchor="w", fill="both", padx=20, pady=10)
        self.syncDetailTitle = customtkinter.CTkLabel(
            master=self.syncDetailFrame, text=title, font=("Quicksand", 16))
        self.syncDetailTitle.pack(anchor="w", padx=[20, 0], pady=[30, 0])
        self.syncDetailDescription = customtkinter.CTkLabel(
            master=self.syncDetailFrame, text=desc, font=("Quicksand Bold", 24))
        self.syncDetailDescription.pack(anchor="w", padx=[20, 0], pady=[0, 60])

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
            Toast(master=self.master, color=Util.COLOR_GREEN_1,
                  errMsg="Success Syncy Card Data")


class SettingFrames(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        master.grid_columnconfigure(1, weight=40)
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=2)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.authFrame = customtkinter.CTkFrame(
            master=self, fg_color=Util.COLOR_NEUTRAL_1, corner_radius=Util.CORNER_RADIUS)
        self.authFrame.grid(row=0, column=0, padx=[
                            0, 20], pady=[0, 20], sticky="nsew")
        self.authLabel = customtkinter.CTkLabel(master=self.authFrame, text="Authentication Daeomon Settings", font=(
            "Quicksand SemiBold", 20), pady=0, width=330, anchor="w")
        self.authLabel.grid(row=0, column=0, padx=10, pady=10)
        self.authStartBtn = customtkinter.CTkButton(
            master=self.authFrame, text="Start", width=90, height=35, fg_color=Util.COLOR_GREEN_1, hover_color=Util.COLOR_GREEN_2)
        self.authStartBtn.grid(row=1, column=0, padx=10, pady=10, sticky="nw")
        self.authStopBtn = customtkinter.CTkButton(
            master=self.authFrame, text="Stop", width=90, height=35, fg_color=Util.COLOR_RED_1, hover_color=Util.COLOR_RED_2)
        self.authStopBtn.grid(row=1, column=0, padx=10, pady=10, sticky="n")
        self.authStatusBtn = customtkinter.CTkButton(
            master=self.authFrame, text="Status", width=90, height=35, fg_color=Util.COLOR_BLUE_1, hover_color=Util.COLOR_BLUE_2)
        self.authStatusBtn.grid(row=1, column=0, padx=10, pady=10, sticky="ne")

        self.credentialFrame = customtkinter.CTkFrame(
            master=self, fg_color=Util.COLOR_NEUTRAL_1, corner_radius=Util.CORNER_RADIUS)
        self.credentialFrame.grid(
            row=1, column=0, rowspan=2, sticky="nsew", padx=[0, 20])
        self.credentialLabel = customtkinter.CTkLabel(
            master=self.credentialFrame, text="Gateway Credential Settings", font=("Quicksand SemiBold", 20), pady=0, anchor="w")
        self.credentialLabel.grid(
            row=0, column=0, padx=20, pady=10, sticky="w")
        self.apiIdLabel = customtkinter.CTkLabel(
            master=self.credentialFrame, text="API ID", font=("Quicksand Bold", 16))
        self.apiIdLabel.grid(row=1, column=0, sticky="w",
                             pady=[0, 10], padx=20)
        self.apiIdForm = customtkinter.CTkEntry(master=self.credentialFrame, width=350, height=50, placeholder_text="Please Input API ID",
                                                fg_color=Util.COLOR_NEUTRAL_2, border_color=Util.COLOR_NEUTRAL_4, corner_radius=Util.CORNER_RADIUS)
        self.apiIdForm.grid(row=2, column=0, sticky="w", padx=20)
        self.apiKeyLabel = customtkinter.CTkLabel(
            master=self.credentialFrame, text="API Key", font=("Quicksand Bold", 16))
        self.apiKeyLabel.grid(row=3, column=0, pady=[
                              20, 10], sticky="w", padx=20)
        self.apiKeyForm = customtkinter.CTkEntry(master=self.credentialFrame, width=350, height=50, placeholder_text="Please Input API Key",
                                                 fg_color=Util.COLOR_NEUTRAL_2, border_color=Util.COLOR_NEUTRAL_4, corner_radius=Util.CORNER_RADIUS)
        self.apiKeyForm.grid(row=4, column=0, sticky="w", padx=20)
        self.submitButton = customtkinter.CTkButton(master=self.credentialFrame, width=350, height=45, text="Save", fg_color=Util.COLOR_BLUE_1,
                                                    hover_color=Util.COLOR_BLUE_2, corner_radius=Util.CORNER_RADIUS, font=("Quicksand Bold", 16), command=self.saveOnClick)
        self.submitButton.grid(row=5, column=0, pady=[
                               40, 0], sticky="w", padx=20)

        self.syncFrame = customtkinter.CTkFrame(
            master=self, fg_color=Util.COLOR_NEUTRAL_1, corner_radius=Util.CORNER_RADIUS)
        self.syncFrame.grid(row=0, column=1, sticky="nsew", pady=[0, 20])
        self.syncLabel = customtkinter.CTkLabel(master=self.syncFrame, text="Syncronization Daeomon Settings", font=(
            "Quicksand SemiBold", 20), pady=0, width=330, anchor="w")
        self.syncLabel.grid(row=0, column=0, padx=10, pady=10)
        self.syncStartBtn = customtkinter.CTkButton(master=self.syncFrame, text="Start", width=90, height=35,
                                                    fg_color=Util.COLOR_GREEN_1, hover_color=Util.COLOR_GREEN_2, command=self.threadSync)
        self.syncStartBtn.grid(row=1, column=0, padx=10, pady=10, sticky="nw")
        self.syncStopBtn = customtkinter.CTkButton(master=self.syncFrame, text="Stop", width=90,
                                                   height=35, fg_color=Util.COLOR_RED_1, hover_color=Util.COLOR_RED_2, command=self.stopSync)
        self.syncStopBtn.grid(row=1, column=0, padx=10, pady=10, sticky="n")
        self.syncStatusBtn = customtkinter.CTkButton(
            master=self.syncFrame, text="Status", width=90, height=35, fg_color=Util.COLOR_BLUE_1, hover_color=Util.COLOR_BLUE_2, command=self.checkSync)
        self.syncStatusBtn.grid(row=1, column=0, padx=10, pady=10, sticky="ne")

        self.meshFrame = customtkinter.CTkFrame(
            master=self, fg_color=Util.COLOR_NEUTRAL_1, corner_radius=Util.CORNER_RADIUS)
        self.meshFrame.grid(row=1, column=1, padx=[
                            0, 0], pady=[0, 20], sticky="nwne")
        self.meshLabel = customtkinter.CTkLabel(master=self.meshFrame, text="ESP Mesh Network Settings", font=(
            "Quicksand SemiBold", 20), pady=0, width=330, anchor="w")
        self.meshLabel.grid(row=0, column=0, padx=10, pady=10)
        self.meshStartBtn = customtkinter.CTkButton(
            master=self.meshFrame, text="Start", width=90, height=35, fg_color=Util.COLOR_GREEN_1, hover_color=Util.COLOR_GREEN_2)
        self.meshStartBtn.grid(row=1, column=0, padx=10,
                               pady=[10, 60], sticky="nw")
        self.meshStopBtn = customtkinter.CTkButton(
            master=self.meshFrame, text="Stop", width=90, height=35, fg_color=Util.COLOR_RED_1, hover_color=Util.COLOR_RED_2)
        self.meshStopBtn.grid(row=1, column=0, padx=10,
                              pady=[10, 60], sticky="n")
        self.meshStatusBtn = customtkinter.CTkButton(
            master=self.meshFrame, text="Status", width=90, height=35, fg_color=Util.COLOR_BLUE_1, hover_color=Util.COLOR_BLUE_2)
        self.meshStatusBtn.grid(row=1, column=0, padx=10,
                                pady=[10, 60], sticky="ne")

        self.ident = None

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

    def threadSync(self):
        syncThread = Thread(target=self.startSync)
        syncThread.start()

    def startSync(self):
        print(" [!main]: Start Sync")
        if platform.system() == "Windows":
            subprocess.call('start /wait python ./amqp.py', shell=True)

        if platform.system() == "Linux":
            pass

    def stopSync(self):
        print(" [!main]: Stop Sync")
        os.kill(Variable.syncPid(), SIGINT)

    def checkSync(self):
        syncPid = Variable.syncPid()
        statusPid = psutil.pid_exists(syncPid)
        if (statusPid):
            Toast(master=self.master, color=Util.COLOR_GREEN_1,
                  errMsg="Service Running")

        if (statusPid == False):
            Toast(master=self.master, color=Util.COLOR_RED_1,
                  errMsg="Service Stop")


class Toast(customtkinter.CTkFrame):
    count = 0

    def __init__(self, master, errMsg, color, **kwargs):

        Toast.count += 1
        self.marginY = [100, 10] if Toast.count <= 1 else [10, 10]
        super().__init__(master, width=500, height=50, fg_color=color,
                         corner_radius=Util.CORNER_RADIUS, bg_color=Util.COLOR_TRANSPARENT, **kwargs)
        self.pack(anchor="n", pady=self.marginY)

        self.errorLabel = customtkinter.CTkLabel(
            master=self, text=errMsg, font=("Quicksand Bold", 20))
        self.errorLabel.place(relx=0.05, rely=0.48, anchor="w")

        self.closeButton = customtkinter.CTkButton(master=self, text="", image=Util.imageGenerator(
            "icon_close.png", 35), compound="right", anchor="e", width=30, hover=False, fg_color=Util.COLOR_TRANSPARENT, command=self.closeOnClick)
        self.closeButton.place(relx=0.96, rely=0.5, anchor="e")

    def closeOnClick(self):
        Util.frameDestroyer(self)
        if Toast.count > 0:
            Toast.count -= 1


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1024x600")
        self.title("Smart Door App")
        self.minsize(1024, 600)
        self.grid_propagate(False)
        self.configure(fg_color=Util.COLOR_NEUTRAL_3)
        # loginFrame = LoginFrames(master=self,fg_color="transparent")
        # loginFrame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.sideBarFrame = SideBarFrames(
            master=self, width=100, fg_color=Util.COLOR_NEUTRAL_2, corner_radius=Util.CORNER_RADIUS)
        self.sideBarFrame.grid(row=0, column=0, padx=[
                               20, 0], pady=20, sticky="nwsw")


if __name__ == "__main__":
    app = App()
    mainApp = Thread(target=app.mainloop())
    # app.mainloop()
    mainApp.start()
    # mainApp.join()
