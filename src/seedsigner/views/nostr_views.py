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
from seedsigner.gui.screens.nostr_screens import NostrButtonListScreen, NostrSignEventStartScreen
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
from seedsigner.views.scan_views import ScanNostrAddView, ScanNostrJsonEventIDView

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
    
    
"""****************************************************************************
    Nostr Main Menu
****************************************************************************"""

class NostrMenuView(View):
    def __init__(self):
        super().__init__()
        self.seeds = []
        for seed in self.controller.storage.seeds:
            self.seeds.append({
                "fingerprint": seed.get_fingerprint(self.settings.get_value(SettingsConstants.SETTING__NETWORK))
            })

        
        
    def run(self): 
        SEEDS = ("Get Nsec from Seed",SeedSignerIconConstants.SEEDS)
        IMAGE = ("Scan Nsec", FontAwesomeIconConstants.CAMERA)
        KEYBOARD = ("Enter Nsec", FontAwesomeIconConstants.KEYBOARD)
        SIGN = ("Sign Message Hash", FontAwesomeIconConstants.CAMERA)
        FULLSIGN = ("Sign Full Event", FontAwesomeIconConstants.CAMERA)
        REMOVE = ("Remove Stored Nsec", SeedSignerIconConstants.RESTART)
        
        
        if self.controller.storage.nsec == "":
            
            if not self.seeds:
                button_data = [IMAGE, KEYBOARD]
            else:
                button_data = [SEEDS, IMAGE, KEYBOARD]
        else:
            button_data = [SIGN, REMOVE, FULLSIGN]
            
        screen = NostrButtonListScreen(
            title="Nostr Menu",
            is_button_text_centered=False,
            button_data=button_data
        )
        selected_menu_num = screen.display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(MainMenuView)

        elif button_data[selected_menu_num] == SEEDS:            
            return Destination(NostrLoadNsecSeedView)
        
        elif button_data[selected_menu_num] == IMAGE:
            return Destination(ScanNostrAddView)            

        #TODO Use keyboard to load in a nsec
        elif button_data[selected_menu_num] == KEYBOARD:
            return Destination(NotYetImplementedView)            

        elif button_data[selected_menu_num] == SIGN:
            return Destination(NostrSignEventStartView)
        
        elif button_data[selected_menu_num] == REMOVE:
            return Destination(NostrRemoveNsecView)               


"""****************************************************************************
    Nostr Menus
****************************************************************************"""

class NostrLoadNsecSeedView(BaseNostrView):

    def __init__(self):
        super().__init__()
        self.seeds = []
        for seed in self.controller.storage.seeds:
            self.seeds.append({
                "fingerprint": seed.get_fingerprint(self.settings.get_value(SettingsConstants.SETTING__NETWORK))
            })


    def run(self):
        if not self.seeds:
            return Destination(NostrMenuView, clear_history=True)

        button_data = []
        for seed in self.seeds:
            button_data.append((seed["fingerprint"], SeedSignerIconConstants.FINGERPRINT))

        selected_menu_num = self.run_screen(
            ButtonListScreen,
            title="In-Memory Seeds",
            is_button_text_centered=False,
            button_data=button_data
        )

        if len(self.seeds) > 0 and selected_menu_num < len(self.seeds):
            self.nostr_add = nostr.get_nsec(self.controller.get_seed(selected_menu_num))
            self.controller.storage.add_nsec(self.nostr_add)
            LargeIconStatusScreen(
                title="Nsec Loaded",
                show_back_button=False,
                status_headline="Success!",
                text="Nsec successfully loaded!",
                button_data=["OK"]
            ).display()
            return Destination(NostrMenuView, clear_history=True)

        elif selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
    
class NostrRemoveNsecView(BaseNostrView):
    def run(self):
        if self.controller.storage.nsec == "":
            #THIS MENU OPTION IS NOW REMOVED if nsec is ""
            print("DEBUG : No Nsecloaded, return") #THIS SHOULD NEVER PRINT
            raise NotYetImplementedView("DEBUG : No Nsecloaded")
        else:
            self.controller.storage.remove_nsec()
        return Destination(BackStackView) 
    
# class NostrSignEventIDStartView(BaseNostrView):
#     def run(self):    
            
#         selected_menu_num = NostrSignEventIDStartScreen(
#             title="Sign Event"
#         ).display()

#         if selected_menu_num == RET_CODE__BACK_BUTTON:
#             return Destination(BackStackView)
        
#         # from seedsigner.views.scan_views import ScanNostrJsonEventView
#         self.controller.resume_main_flow = Controller.FLOW__NOSTR_EVENT_ID
#         return Destination(ScanNostrJsonEventIDView)
    
class NostrSignEventIDReviewView(BaseNostrView):
    def __init__(self, nostr_add: str, nostr_add_type: str, nostr_signature: str = None, nostr_qrtype: str = None, nostr_event: str = None):
        super().__init__()
        self.nostr_event = nostr_event,
        self.nostr_add=nostr_add,
        self.nostr_qrtype = nostr_qrtype,
        self.nostr_add_type = nostr_add_type,
        self.nostr_signature = nostr_signature,
        
        
        from seedsigner.helpers.nostr import sign_event_id
        self.nostr_signature = sign_event_id(nostr_add=nostr_add,nostr_add_type=nostr_add_type,nostr_event=nostr_event)
    
    def run(self):
        
        e = EncodeQR(
            qr_type=QRType.NOSTR_EVENT_SIGNATURE,
            nostr_signature = '{"event.signature": "' + self.nostr_signature.to_string() + '"}'
        )
        data = e.next_part()
        print (data)
        ret = nostr_screens.NostrSignatureQRWholeQRScreen(
            qr_data=data,
        ).display()

        if ret == RET_CODE__BACK_BUTTON:
            return Destination(NostrMenuView)
        
        else:
            print("does this execute")
            return Destination(BackStackView)

class NostrSignEventStartView(BaseNostrView):
    def run(self):    
            
        selected_menu_num = NostrSignEventStartScreen(
            title="Sign Full Nostr Event"
        ).display()
        
        if selected_menu_num == 0:
            self.controller.resume_main_flow = Controller.FLOW__NOSTR_EVENT_ID
            return Destination(ScanNostrJsonEventIDView)
        elif selected_menu_num == 1:
            self.controller.resume_main_flow = Controller.FLOW__NOSTR_EVENT
            #TODO porting over - might need to change
            raise NotImplementedError()
            return Destination(ScanView)

        elif selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        print("NEED TO DEBUG HERE")
        print (selected_menu_num)
        ## NOTE TO SELF, THIS RETURNS A 0 for first option and 1 for second.
        ##TODO WE SHOULD NOT GET HERE
        # from seedsigner.views.scan_views import ScanNostrJsonEventView
        # self.controller.resume_main_flow = Controller.FLOW__NOSTR_EVENT
        raise NotImplementedError()
        
 
"""****************************************************************************
    Nostr Nsec Address Views
****************************************************************************"""

class NostrAddressStartView(View):
    
    #TODO CAN REMOVE, THIS just prints a success laoded, it used to do more, but doesnt need to.
    def __init__(self, nostr_add: str, nostr_add_type: str):
        super().__init__()
        # self.controller.storage.add_nsec(nostr_add)
    
    def run(self):
        LargeIconStatusScreen(
            title="Nsec Loaded",
            show_back_button=False,
            status_headline="Success!",
            text="Nsec successfully loaded!",
            button_data=["OK"]
        ).display()
        
        return Destination(NostrMenuView)
        
        