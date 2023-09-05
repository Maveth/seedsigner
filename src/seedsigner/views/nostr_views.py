import hashlib
import os
import json
import time

from embit.descriptor import Descriptor
from PIL import Image
from PIL.ImageOps import autocontrast
from seedsigner.controller import Controller
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
        
        
        button_data = [SEEDS, IMAGE, KEYBOARD, SIGN]
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
        from seedsigner.gui.screens.nostr_screens import NostrSignEventStartScreen
        from seedsigner.views.scan_views import ScanView
        selected_menu_num = NostrSignEventStartScreen(
            title="Sign Event"
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        return Destination(ScanView)
    
class NostrSignEventReviewView(BaseNostrView):
    def __init__(self, serialized_event: str = None, json_event: str = None):
        super().__init__()
        if json_event:
            event_dict = json.loads(json_event)
            serialized_event = nostr.serialize_event(event_dict)

        self.controller.nostr_data["raw_serialized_event"] = serialized_event
        self.serialized_event = json.loads(serialized_event)
    

    def run(self):
        from seedsigner.gui.screens.nostr_screens import NostrSignEventReviewScreen

