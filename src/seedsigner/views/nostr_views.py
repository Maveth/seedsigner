import hashlib
import os

import time

from embit.descriptor import Descriptor
from PIL import Image
from PIL.ImageOps import autocontrast
from seedsigner.controller import Controller
from seedsigner.gui.screens.screen import LoadingScreenThread, QRDisplayScreen

from seedsigner.hardware.camera import Camera
from seedsigner.gui.components import FontAwesomeIconConstants, GUIConstants, SeedSignerCustomIconConstants
from seedsigner.gui.screens import (RET_CODE__BACK_BUTTON, ButtonListScreen)
from seedsigner.gui.screens.tools_screens import ToolsCalcFinalWordDoneScreen, ToolsCalcFinalWordFinalizePromptScreen, ToolsCalcFinalWordScreen, ToolsCoinFlipEntryScreen, ToolsDiceEntropyEntryScreen, ToolsImageEntropyFinalImageScreen, ToolsImageEntropyLivePreviewScreen, ToolsAddressExplorerAddressTypeScreen
from seedsigner.helpers import embit_utils, mnemonic_generation
from seedsigner.models.encode_qr import EncodeQR
from seedsigner.models.qr_type import QRType
from seedsigner.models.seed import Seed
from seedsigner.models.settings_definition import SettingsConstants
from seedsigner.views.seed_views import SeedDiscardView, SeedFinalizeView, SeedMnemonicEntryView, SeedWordsWarningView, SeedExportXpubScriptTypeView
from seedsigner.views.view import NotYetImplementedView, OptionDisabledView, View, Destination, BackStackView, MainMenuView

from .view import View, Destination, BackStackView



class NostrMenuView(View):
    def run(self): 
        IMAGE = ("Load Nsec", FontAwesomeIconConstants.CAMERA)
        KEYBOARD = ("Load Nsec", FontAwesomeIconConstants.KEYBOARD)
        EXPLORER = "Address Explorer"
        button_data = [IMAGE, KEYBOARD, EXPLORER]
        screen = ButtonListScreen(
            title="Tools",
            is_button_text_centered=False,
            button_data=button_data
        )
        selected_menu_num = screen.display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

        elif button_data[selected_menu_num] == IMAGE:
            return Destination(NostrLoadNsecView)

        elif button_data[selected_menu_num] == KEYBOARD:
            return Destination(NostrLoadNsecView)

        elif button_data[selected_menu_num] == EXPLORER:
            return Destination(NostrLoadNsecView)


"""****************************************************************************
    Image entropy Views
****************************************************************************"""
class NostrLoadNsecView(View):
    def run(self):
        raise NotYetImplementedView("Storing NOSTR nsec not yet ready")
        self.controller.image_entropy_preview_frames = None
        ret = ToolsImageEntropyLivePreviewScreen().display()

        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        self.controller.image_entropy_preview_frames = ret
        return Destination(ToolsImageEntropyFinalImageView)
