from dataclasses import dataclass
from datetime import datetime
from typing import List
from seedsigner.gui.components import Button, CheckboxButton, FontAwesomeIconConstants, SeedSignerIconConstants, GUIConstants, Icon, IconButton, TextArea

from seedsigner.gui.screens.screen import BaseTopNavScreen, ButtonListScreen, WarningEdgesMixin
from seedsigner.hardware.buttons import HardwareButtonsConstants

from PIL import Image, ImageDraw, ImageFilter
from seedsigner.gui.renderer import Renderer
from seedsigner.helpers.qr import QR



NOSTR_BACKGROUND_COLOR = "#5d006f"
NOSTR_ACCENT_COLOR = "#dd23ef"



@dataclass
class NostrButtonListScreen(ButtonListScreen):
    def __post_init__(self):
        # Lock in overrided defaults
        self.top_nav_background_color = NOSTR_BACKGROUND_COLOR
        self.top_nav_button_selected_color = NOSTR_ACCENT_COLOR
        self.button_selected_color = NOSTR_ACCENT_COLOR
        super().__post_init__()



@dataclass
class NostrBaseTopNavScreen(BaseTopNavScreen):
    def __post_init__(self):
        # Lock in overrided defaults
        self.top_nav_background_color = NOSTR_BACKGROUND_COLOR
        self.top_nav_button_selected_color = NOSTR_ACCENT_COLOR
        super().__post_init__()
        


"""****************************************************************************
    Sign Event
****************************************************************************"""
@dataclass
class NostrSignEventStartScreen(NostrButtonListScreen):
    def __post_init__(self):
        # Customize defaults
        self.is_bottom_list = True
        self.button_data = [("Scan", SeedSignerIconConstants.SCAN)]

        super().__post_init__()

        self.components.append(TextArea(
            text="Scan the event hash",
            is_text_centered=True,
            screen_y=self.top_nav.height + 3*GUIConstants.COMPONENT_PADDING
        ))


@dataclass
class NostrSignatureQRWholeQRScreen(WarningEdgesMixin, NostrButtonListScreen):
    qr_data: str = None
    # num_modules: int = None

    def __post_init__(self):
        self.title = "Nostr Signature"
        self.button_data = [f"Scan this into client"]
        self.is_bottom_list = True
        self.status_color = GUIConstants.DIRE_WARNING_COLOR
        super().__post_init__()

        qr_height = self.buttons[0].screen_y - self.top_nav.height - GUIConstants.COMPONENT_PADDING
        qr_width = qr_height

        qr = QR()
        qr_image = qr.qrimage(
            data=self.qr_data,
            width=qr_width,
            height=qr_height,
            border=1,
            style=QR.STYLE__ROUNDED
        ).convert("RGBA")

        self.paste_images.append((qr_image, (int((self.canvas_width - qr_width)/2), self.top_nav.height)))
