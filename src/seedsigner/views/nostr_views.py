import hashlib
import os
import json
import time

from embit.descriptor import Descriptor
from PIL import Image
from PIL.ImageOps import autocontrast
from seedsigner.controller import Controller
from seedsigner.gui.screens import nostr_screens
from seedsigner.gui.screens.screen import LargeIconStatusScreen, LoadingScreenThread, QRDisplayScreen
from seedsigner.gui.screens.nostr_screens import NostrButtonListScreen
from seedsigner.hardware.camera import Camera
from seedsigner.gui.components import FontAwesomeIconConstants, GUIConstants, SeedSignerIconConstants
from seedsigner.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen)
from seedsigner.gui.screens.nostr_screens import NostrSignEventStartScreen
from seedsigner.gui.screens.tools_screens import ToolsCalcFinalWordDoneScreen, ToolsCalcFinalWordFinalizePromptScreen, ToolsCalcFinalWordScreen, ToolsCoinFlipEntryScreen, ToolsDiceEntropyEntryScreen, ToolsImageEntropyFinalImageScreen, ToolsImageEntropyLivePreviewScreen, ToolsAddressExplorerAddressTypeScreen
from seedsigner.helpers import embit_utils, mnemonic_generation
from seedsigner.helpers import nostr
from seedsigner.models.encode_qr import EncodeQR
from seedsigner.models.qr_type import QRType
from seedsigner.models.seed import Seed
from seedsigner.models.settings_definition import SettingsConstants
from seedsigner.views.seed_views import SeedDiscardView, SeedFinalizeView, SeedMnemonicEntryView, SeedWordsWarningView, SeedExportXpubScriptTypeView
from seedsigner.views.view import NotYetImplementedView, OptionDisabledView, View, Destination, BackStackView, MainMenuView
from seedsigner.views.scan_views import ScanNostrAddView, ScanNostrJsonEventView

from .view import View, Destination, BackStackView

class BaseNostrView(View):
    @property
    def seed_num(self) -> int:
        return self.controller.nostr_data["seed_num"]
    
    @property
    def seed(self) -> Seed:
        return self.controller.storage.seeds[self.seed_num]
    
    # @property  #TODO is this needed - doesnt seem so....
    # def nsec(self) -> Nsec:
    #     return self.controller.storage.nsec[0]

    @property
    def nostr_npub(self) -> str:
        return nostr.get_npub(self.seed)

    @property
    def nostr_nsec(self) -> str:
        return nostr.get_nsec(self.seed)
    
    @property
    def nostr_pubkey_hex(self) -> str:
        return nostr.get_pubkey_hex(self.seed)

    @property
    def nostr_privkey_hex(self) -> str:
        return nostr.get_privkey_hex(self.seed)

class NostrMenuView(View):
    def run(self): 
        SEEDS = ("Get Nsec from Seed",SeedSignerIconConstants.SEEDS)
        IMAGE = ("Scan Nsec", FontAwesomeIconConstants.CAMERA)
        KEYBOARD = ("Enter Nsec", FontAwesomeIconConstants.KEYBOARD)
        SIGN = ("Sign Message Hash", FontAwesomeIconConstants.CAMERA)
        SHARED = ("Create Shared Secret for DMS", FontAwesomeIconConstants.LOCK)
        REMOVE = ("Remove Stored Nsec", SeedSignerIconConstants.RESTART)
        
        if self.controller.storage.nsec == "":
            button_data = [SEEDS, IMAGE, KEYBOARD]
        else:
            button_data = [SIGN, SHARED, REMOVE]
            
        screen = NostrButtonListScreen(
            title="Nostr Menu",
            is_button_text_centered=False,
            button_data=button_data
        )
        selected_menu_num = screen.display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            #TODO This should go back to man menu, can get caught in a loop here
            return Destination(MainMenuView)

        elif button_data[selected_menu_num] == SEEDS:            
            return Destination(NostrLoadNsecView)
        
        elif button_data[selected_menu_num] == IMAGE:
            return Destination(ScanNostrAddView)            

        elif button_data[selected_menu_num] == KEYBOARD:
            return Destination(NotYetImplementedView)            
        
        
        elif button_data[selected_menu_num] == SHARED:
            return Destination(NotYetImplementedView)       

        elif button_data[selected_menu_num] == SIGN:
            return Destination(NostrSignEventStartView)
        
        elif button_data[selected_menu_num] == REMOVE:
            return Destination(NostrRemoveNsecView)            


"""****************************************************************************
    Nostr Menus
****************************************************************************"""
class NostrLoadNsecView(BaseNostrView):
    def run(self):
        # return Destination(NotYetImplementedView)
        #TODO this is to load a nsec from a seed, review code from
        #https://gist.github.com/kdmukai/ae9911ed6fb92f8e7d2c553555b0cb86
        
        print("Generate a new seed from here")
        return Destination(NotYetImplementedView)     
        
        self.controller.image_entropy_preview_frames = None
        ret = ToolsImageEntropyLivePreviewScreen().display()

        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        self.controller.image_entropy_preview_frames = ret
        return Destination(ToolsImageEntropyFinalImageView)
    
class NostrRemoveNsecView(BaseNostrView):
    def run(self):
        if self.controller.storage.nsec == "":
            #THIS MENU OPTION IS NOW REMOVED if nsec is ""
            print("DEBUG : No Nsecloaded, return") #THIS SHOULD NEVER PRINT
            raise NotYetImplementedView("DEBUG : No Nsecloaded")
        else:
            self.controller.storage.remove_nsec()
        return Destination(BackStackView) 
        
    
    
class NostrSignEventStartView(BaseNostrView):
    def run(self):
        #THIS MENU OPTION IS DISABLED IF NO NSEC
        # if self.controller.storage.nsec == "":
        #     print ("NO NSEC IN STORAGE")
        #     print("loadnsec First")
        #     raise NotYetImplementedView("NOSTR nsec not loaded")
    
            
        selected_menu_num = NostrSignEventStartScreen(
            title="Sign Event"
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        # from seedsigner.views.scan_views import ScanNostrJsonEventView
        self.controller.resume_main_flow = Controller.FLOW__NOSTR_EVENT
        return Destination(ScanNostrJsonEventView)
    
class NostrSignEventReviewView(BaseNostrView):
    def __init__(self, nostr_add: str, nostr_add_type: str, nostr_signature: str = None, nostr_qrtype: str = None, nostr_event: str = None):
        super().__init__()
        self.nostr_event = nostr_event,
        self.nostr_add=nostr_add,
        self.nostr_qrtype = nostr_qrtype,
        self.nostr_add_type = nostr_add_type,
        self.nostr_signature = nostr_signature,
        
        # print("WE GOT THE THE REVIEW PROCESS") #TODO DEBUG REMOVE
        # print(nostr_add)
        # print(nostr_add_type)
        # print(nostr_event)
        
        
        from seedsigner.helpers.nostr import sign_event_id
        self.nostr_signature = sign_event_id(nostr_add=nostr_add,nostr_add_type=nostr_add_type,nostr_event=nostr_event)
        # print("we got sig:",nostr_signature)
        # print("we got sig:",self.nostr_signature)
        # raise NotYetImplementedView("Display qr of signature")
    
    def run(self):
        
        
        # print("line 142 nostr view: ",self.nostr_signature)
        # print("line 142 nostr view: ",nostr_signature)
        
        e = EncodeQR(
            qr_type=QRType.NOSTR__SIGNED_EVENT,
            nostr_signature = '{"event.signature": "' + self.nostr_signature.to_string() + '"}'
        )
        data = e.next_part()
        # data = '{"event.signature": "' + signature_data + '"}'
        print (data)
        ret = nostr_screens.NostrSignatureQRWholeQRScreen(
            qr_data=data,
        ).display()

        if ret == RET_CODE__BACK_BUTTON:
            return Destination(NostrMenuView)
        
        else:
            print("does this execute")
            return Destination(BackStackView)

 
"""****************************************************************************
    Nostr Nsec Address Views
****************************************************************************"""

class NostrAddressStartView(View):
    
    def __init__(self, nostr_add: str, nostr_add_type: str):
        super().__init__()
        self.nostr_add=nostr_add,
        self.nostr_add_type=nostr_add_type,
    
    def run(self):
        
        # print("got to Address start view")
        self.controller.storage.add_nsec(self.nostr_add)
        
        # print("we just tried to save nsec got:")
        # print(self.controller.storage.get_nsec())
        # print("since still a tuple changing to:")
        # print(self.controller.storage.get_nsec()[0])
        LargeIconStatusScreen(
            title="Nsec Loaded",
            show_back_button=False,
            status_headline="Success!",
            text="Nsec successfully loaded!",
            button_data=["OK"]
        ).display()
        
        return Destination(NostrMenuView)
        
        