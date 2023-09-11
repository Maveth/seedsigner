import hashlib
import os
import json
import time

from embit.descriptor import Descriptor
from PIL import Image
from PIL.ImageOps import autocontrast
from seedsigner.controller import Controller
from seedsigner.gui.screens import nostr_screens
from seedsigner.gui.screens.screen import LoadingScreenThread, QRDisplayScreen
from seedsigner.gui.screens.nostr_screens import NostrButtonListScreen
from seedsigner.hardware.camera import Camera
from seedsigner.gui.components import FontAwesomeIconConstants, GUIConstants, SeedSignerIconConstants
from seedsigner.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen)
from seedsigner.gui.screens.tools_screens import ToolsCalcFinalWordDoneScreen, ToolsCalcFinalWordFinalizePromptScreen, ToolsCalcFinalWordScreen, ToolsCoinFlipEntryScreen, ToolsDiceEntropyEntryScreen, ToolsImageEntropyFinalImageScreen, ToolsImageEntropyLivePreviewScreen, ToolsAddressExplorerAddressTypeScreen
from seedsigner.helpers import embit_utils, mnemonic_generation
from seedsigner.helpers import nostr
from seedsigner.models.encode_qr import EncodeQR
from seedsigner.models.qr_type import QRType
from seedsigner.models.seed import Seed
from seedsigner.models.settings_definition import SettingsConstants
from seedsigner.views.seed_views import SeedDiscardView, SeedFinalizeView, SeedMnemonicEntryView, SeedWordsWarningView, SeedExportXpubScriptTypeView
from seedsigner.views.view import NotYetImplementedView, OptionDisabledView, View, Destination, BackStackView, MainMenuView

from .view import View, Destination, BackStackView

class BaseNostrView(View):
    @property
    def seed_num(self) -> int:
        return self.controller.nostr_data["seed_num"]
    
    @property
    def seed(self) -> Seed:
        return self.controller.storage.seeds[self.seed_num]

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
        SEEDS = ("Generate New Seed",SeedSignerIconConstants.SEEDS)
        IMAGE = ("Load Nsec", FontAwesomeIconConstants.CAMERA)
        KEYBOARD = ("Load Nsec", FontAwesomeIconConstants.KEYBOARD)
        SIGN = ("Sign Message Hash", FontAwesomeIconConstants.CAMERA)
        
        
        button_data = [SIGN, SEEDS, IMAGE, KEYBOARD]
        screen = NostrButtonListScreen(
            title="Nostr Menu",
            is_button_text_centered=False,
            button_data=button_data
        )
        selected_menu_num = screen.display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

        elif button_data[selected_menu_num] == SEEDS:            
            return Destination(NostrLoadNsecView)
        
        elif button_data[selected_menu_num] == IMAGE:
            return Destination(NotYetImplementedView)            

        elif button_data[selected_menu_num] == KEYBOARD:
            return Destination(NotYetImplementedView)            

        elif button_data[selected_menu_num] == SIGN:
            return Destination(NostrSignEventStartView)            


"""****************************************************************************
    Nostr Menus
****************************************************************************"""
class NostrLoadNsecView(BaseNostrView):
    def run(self):
        # return Destination(NotYetImplementedView)
        raise NotYetImplementedView("Storing NOSTR nsec not yet ready")
        self.controller.image_entropy_preview_frames = None
        ret = ToolsImageEntropyLivePreviewScreen().display()

        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        self.controller.image_entropy_preview_frames = ret
        return Destination(ToolsImageEntropyFinalImageView)
    
    
class NostrSignEventStartView(BaseNostrView):
    def run(self):
        print("NostrSignEventStartView.1")
        from seedsigner.gui.screens.nostr_screens import NostrSignEventStartScreen
        selected_menu_num = NostrSignEventStartScreen(
            title="Sign Event"
        ).display()
        print("NostrSignEventStartView.2")

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        print("NostrSignEventStartView.3")
        from seedsigner.views.scan_views import ScanNostrJsonEventView
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
        
        print("WE GOT THE THE REVIEW PROCESS")
        print(nostr_add)
        print(nostr_add_type)
        print(nostr_event)
        
        
        from seedsigner.helpers.nostr import sign_event_id
        
        self.nostr_signature = sign_event_id(nostr_add=nostr_add,nostr_add_type=nostr_add_type,nostr_event=nostr_event)
        # print("we got sig:",nostr_signature)
        print("we got sig:",self.nostr_signature)
        
        # raise NotYetImplementedView("Display qr of signature")
    
    def run(self):
        
        print("line 142 nostr view: ",self.nostr_signature)
        # print("line 142 nostr view: ",nostr_signature)
        
        e = EncodeQR(
            qr_type=QRType.NOSTR__SIGNED_EVENT,
            nostr_signature = self.nostr_signature
        )
        data = e.next_part()

        ret = nostr_screens.NostrSignatureQRWholeQRScreen(
            qr_data=data,
            num_modules=self.num_modules,
        ).display()

        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        else:
            return Destination(BackStackView)

 
"""****************************************************************************
    Nostr Address Views
****************************************************************************"""
#TODO this should have the class for what to do after nostr address is scanned
# inital goal is to store it like a seed is stored (temporarly)

class NostrAddressStartView(View):
    
      def __init__(self, nostr_add: str, nostr_add_type: str):
        super().__init__()
        self.nostr_add=nostr_add,
        self.nostr_add_type=nostr_add_type,
        
        #like below, if option is disabled then it should do so
        #if not then should check is stored
        # the bulk of the signed might be done with the below code
        #for now we just want to print a success and leave
        print("got to Address start view")
        print("got to Address start view")
        print("got to Address start view")
        
        raise NotYetImplementedView("Storing NOSTR nsec not yet ready")
        