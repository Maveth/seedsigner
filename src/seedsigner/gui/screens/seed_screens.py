import time

from dataclasses import dataclass

from .screen import BaseScreen, BaseTopNavScreen, ButtonListScreen, WarningScreenMixin
from ..components import Fonts, TextArea, GUIConstants, IconTextLine

from seedsigner.gui.keyboard import Keyboard, TextEntryDisplay
from seedsigner.helpers import B
from seedsigner.models.encode_qr import EncodeQR



@dataclass
class SeedValidScreen(ButtonListScreen):
    fingerprint: str = None
    title: str = "Seed Valid"
    is_bottom_list: bool = True

    def __post_init__(self):
        # Customize defaults
        self.button_data = [
            ("Scan a PSBT", "scan_inline"),
            "Seed Tools",
            ("Advanced", "settings_inline"),
        ]

        # Initialize the base class
        super().__post_init__()

        self.title_textarea = TextArea(
            text="Fingerprint:",
            is_text_centered=True,
            auto_line_break=False,
            screen_y=self.top_nav.height + int((self.buttons[0].screen_y - self.top_nav.height) / 2) - 30
        )

        self.fingerprint_icontl = IconTextLine(
            icon_name="fingerprint",
            value_text=self.fingerprint,
            font_size=GUIConstants.BODY_FONT_SIZE + 2,
            is_text_centered=True,
            screen_x = -4,
            screen_y=self.title_textarea.screen_y + self.title_textarea.height
        )

    def _render(self):
        super()._render()

        self.title_textarea.render()
        self.fingerprint_icontl.render()

        # self.renderer.canvas.paste(self.body_content, (self.body_content_x, self.body_content_y))

        # Write the screen updates
        self.renderer.show_image()



@dataclass
class SeedOptionsScreen(ButtonListScreen):
    # Customize defaults
    title: str = "Seed Options"
    is_bottom_list: bool = True
    fingerprint: str = None
    has_passphrase: bool = False

    def __post_init__(self):
        # Programmatically set up other args
        self.button_data = [
            "View Seed Words",
            "Export Xpub",
            "Export Seed as QR",
        ]

        # Initialize the base class
        super().__post_init__()

        self.fingerprint_icontextline = IconTextLine(
            icon_name="fingerprint",
            value_text=self.fingerprint,
            is_text_centered=True,
            screen_y=self.top_nav.height
        )


    def _render(self):
        super()._render()
        self.fingerprint_icontextline.render()



@dataclass
class SeedExportXpubCustomDerivationScreen(BaseTopNavScreen):
    title: str = "Custom Derivation"

    def __post_init__(self):
        super().__post_init__()

        # Set up the keyboard params
        right_panel_buttons_width = 60
        
        # Set up the live text entry display
        self.derivation = "m/"
        font = Fonts.get_font("RobotoCondensed-Regular", 28)
        tw, th = font.getsize("m/1234567890")  # All possible chars for max range
        text_entry_side_padding = 0
        text_entry_top_padding = 1
        text_entry_bottom_padding = 10
        text_entry_top_y = self.top_nav.height + text_entry_top_padding
        text_entry_bottom_y = text_entry_top_y + 3 + th + 3
        self.text_entry_display = TextEntryDisplay(
            canvas=self.renderer.canvas,
            rect=(text_entry_side_padding,text_entry_top_y, self.renderer.canvas_width - right_panel_buttons_width - 1, text_entry_bottom_y),
            font=font,
            font_color="orange",
            cursor_mode=TextEntryDisplay.CURSOR_MODE__BAR,
            is_centered=False,
            has_outline=True,
            cur_text=''.join(self.derivation)
        )

        keyboard_start_y = text_entry_bottom_y + text_entry_bottom_padding
        self.keyboard_digits = Keyboard(
            draw=self.renderer.draw,
            charset="/'0123456789",
            rows=3,
            cols=6,
            rect=(0, keyboard_start_y, self.renderer.canvas_width - right_panel_buttons_width, self.renderer.canvas_height),
            auto_wrap=[Keyboard.WRAP_LEFT, Keyboard.WRAP_RIGHT],
            render_now=False
        )
        self.keyboard_digits.set_selected_key(selected_letter="/")


    def _render(self):
        super()._render()

        self.keyboard_digits.render_keys()

        # Render the right button panel (only has a Key3 "Save" button)
        row_height = 28
        right_button_left_margin = 10
        right_button_width = 60
        font_padding_right = 2
        font_padding_top = 1
        key_x = self.renderer.canvas_width - right_button_width
        key_y = int(self.renderer.canvas_height - row_height) / 2 - 1 - 60
        font = Fonts.get_font("RobotoCondensed-Regular", 24)
        background_color = "#111"
        font_color = "orange"
        button3_text = "Save"
        tw, th = font.getsize(button3_text)
        key_y = int(self.renderer.canvas_height - row_height) / 2 - 1 + 60
        self.renderer.draw.rounded_rectangle((key_x, key_y, 250, key_y + row_height), outline="orange", fill=background_color, radius=5, width=1)
        self.renderer.draw.text((self.renderer.canvas_width - tw - font_padding_right, key_y + font_padding_top), font=font, text=button3_text, fill=font_color)

        self.text_entry_display.render(self.derivation)
        self.renderer.show_image()
    

    def _run(self):
        cursor_position = len(self.derivation)

        # Start the interactive update loop
        while True:
            input = self.hw_inputs.wait_for(
                [B.KEY_UP, B.KEY_DOWN, B.KEY_RIGHT, B.KEY_LEFT, B.KEY_PRESS, B.KEY3],
                check_release=True,
                release_keys=[B.KEY_PRESS, B.KEY3]
            )
    
            # Check our two possible exit conditions
            if input == B.KEY3:
                # Save!
                if len(self.derivation) > 0:
                    return self.derivation.strip()
    
            elif self.top_nav.is_selected and input == B.KEY_PRESS:
                # Prev button clicked; return empty string to signal cancel.
                return self.top_nav.selected_button
    
            # Process normal input
            if input in [B.KEY_UP, B.KEY_DOWN] and self.top_nav.is_selected:
                # We're navigating off the previous button
                self.top_nav.is_selected = False
                self.top_nav.render()
    
                # Override the actual input w/an ENTER signal for the Keyboard
                if input == B.KEY_DOWN:
                    input = Keyboard.ENTER_TOP
                else:
                    input = Keyboard.ENTER_BOTTOM
            elif input in [B.KEY_LEFT, B.KEY_RIGHT] and self.top_nav.is_selected:
                # ignore
                continue
    
            ret_val = self.keyboard_digits.update_from_input(input)
    
            # Now process the result from the keyboard
            if ret_val in Keyboard.EXIT_DIRECTIONS:
                self.top_nav.is_selected = True
                self.top_nav.render()
    
            elif ret_val in Keyboard.ADDITIONAL_KEYS and input == B.KEY_PRESS:
                if ret_val == Keyboard.KEY_BACKSPACE["code"]:
                    if len(self.derivation) <= 2:
                        pass
                    elif cursor_position == len(self.derivation):
                        self.derivation = self.derivation[:-1]
                        cursor_position -= 1
                    else:
                        self.derivation = self.derivation[:cursor_position - 1] + self.derivation[cursor_position:]
                        cursor_position -= 1
    
            elif input == B.KEY_PRESS and ret_val not in Keyboard.ADDITIONAL_KEYS:
                # User has locked in the current letter
                if cursor_position == len(self.derivation):
                    self.derivation += ret_val
                else:
                    self.derivation = self.derivation[:cursor_position] + ret_val + self.derivation[cursor_position:]
                cursor_position += 1
    
            elif input in [B.KEY_RIGHT, B.KEY_LEFT, B.KEY_UP, B.KEY_DOWN]:
                # Live joystick movement; haven't locked this new letter in yet.
                # Leave current spot blank for now. Only update the active keyboard keys
                # when a selection has been locked in (KEY_PRESS) or removed ("del").
                pass
    
            # Render the text entry display and cursor block
            self.text_entry_display.render(self.derivation)
    
            self.renderer.show_image()



@dataclass
class SeedExportXpubDetailsScreen(WarningScreenMixin, ButtonListScreen):
    # Customize defaults
    title: str = "Xpub Details"
    is_bottom_list: bool = True
    fingerprint: str = None
    has_passphrase: bool = False
    derivation_path: str = "m/84'/0'/0'"
    xpub: str = "zpub6r..."
    button_data=["Export Xpub"]

    def __post_init__(self):
        # Programmatically set up other args
        self.button_data = ["Export Xpub"]

        # Initialize the base class
        super().__post_init__()

        # Set up the fingerprint and passphrase displays
        self.fingerprint_line = IconTextLine(
            icon_name="fingerprint",
            label_text="Fingerprint",
            value_text=self.fingerprint,
            screen_x=8,
            screen_y=self.top_nav.height,
        )

        self.derivation_line = IconTextLine(
            icon_name="fingerprint",
            label_text="Derivation",
            value_text=self.derivation_path,
            screen_x=8,
            screen_y=self.fingerprint_line.screen_y + self.fingerprint_line.height + 8,
        )

        self.xpub_line = IconTextLine(
            icon_name="fingerprint",
            label_text="Xpub",
            value_text=self.xpub,
            screen_x=8,
            screen_y=self.derivation_line.screen_y + self.derivation_line.height + 8,
        )


    def _render(self):
        super()._render()

        self.fingerprint_line.render()
        self.derivation_line.render()
        self.xpub_line.render()

        self.render_warning_edges()

        # Write the screen updates
        self.renderer.show_image()



@dataclass
class SeedExportXpubQRDisplayScreen(BaseScreen):
    qr_encoder: EncodeQR = None

    def __post_init__(self):
        # Initialize the base class
        super().__post_init__()


    def _run(self):
        while self.qr_encoder.totalParts() > 1:
            image = self.qr_encoder.nextPartImage(240,240,2)
            self.renderer.show_image(image)
            time.sleep(0.1)
            if self.hw_inputs.check_for_low(B.KEY_RIGHT):
                break

        if self.qr_encoder.totalParts() == 1:
            image = self.qr_encoder.nextPartImage(240,240,1)
            self.renderer.show_image(image)
            self.hw_inputs.wait_for([B.KEY_RIGHT])

        # TODO: handle left as BACK
