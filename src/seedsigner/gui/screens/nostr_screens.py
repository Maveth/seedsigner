from dataclasses import dataclass
from datetime import datetime
from typing import List
from seedsigner.gui.components import Button, CheckboxButton, FontAwesomeIconConstants, GUIConstants, Icon, IconButton, TextArea

from seedsigner.gui.screens.screen import BaseTopNavScreen, ButtonListScreen, WarningEdgesMixin
from seedsigner.hardware.buttons import HardwareButtonsConstants



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
        self.button_data = [("Scan", FontAwesomeIconConstants.QRCODE)]

        super().__post_init__()

        self.components.append(TextArea(
            text="Scan the event hash",
            is_text_centered=True,
            screen_y=self.top_nav.height + 3*GUIConstants.COMPONENT_PADDING
        ))
