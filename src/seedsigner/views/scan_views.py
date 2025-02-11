import re

from embit.descriptor import Descriptor

from seedsigner.gui.screens.screen import RET_CODE__BACK_BUTTON, WarningScreen
from seedsigner.models.decode_qr import DecodeQR
from seedsigner.models.seed import Seed
from seedsigner.models.settings import SettingsConstants
# from seedsigner.views.nostr_views import NostrMenuView
from seedsigner.views.settings_views import SettingsIngestSettingsQRView
from seedsigner.views.view import BackStackView, ErrorView, MainMenuView, NotYetImplementedView, OptionDisabledView, View, Destination



class ScanView(View):
    """
        The catch-all generic scanning View that will accept any of our supported QR
        formats and will route to the most sensible next step.

        Can also be used as a base class for more specific scanning flows with
        dedicated errors when an unexpected QR type is scanned (e.g. Scan PSBT was
        selected but a SeedQR was scanned).
    """
    instructions_text = "Scan a QR code"
    invalid_qr_type_message = "QRCode not recognized or not yet supported."


    def __init__(self):
        super().__init__()
        # Define the decoder here to make it available to child classes' is_valid_qr_type
        # checks and so we can inject data into it in the test suite's `before_run()`.
        self.wordlist_language_code = self.settings.get_value(SettingsConstants.SETTING__WORDLIST_LANGUAGE)
        self.decoder: DecodeQR = DecodeQR(wordlist_language_code=self.wordlist_language_code)


    @property
    def is_valid_qr_type(self):
        return True


    def run(self):
        from seedsigner.gui.screens.scan_screens import ScanScreen
        
        print("scan.views.line43")

        # Start the live preview and background QR reading
        self.run_screen(
            ScanScreen,
            instructions_text=self.instructions_text,
            decoder=self.decoder
        )

        print("scan.views.line53")
        
        # Handle the results
        if self.decoder.is_complete:
            
            print("decoder complete - scan.views.line58")
            if not self.is_valid_qr_type:
                # We recognized the QR type but it was not the type expected for the
                # current flow.
                # Report QR types in more human-readable text (e.g. QRType
                # `seed__compactseedqr` as "seed: compactseedqr").
                return Destination(ErrorView, view_args=dict(
                    title="Error",
                    status_headline="Wrong QR Type",
                    text=self.invalid_qr_type_message + f""", received "{self.decoder.qr_type.replace("__", ": ").replace("_", " ")}\" format""",
                    button_text="Back",
                    next_destination=Destination(BackStackView, skip_current_view=True),
                ))

            if self.decoder.is_seed:
                
                seed_mnemonic = self.decoder.get_seed_phrase()

                if not seed_mnemonic:
                    # seed is not valid, Exit if not valid with message
                    raise Exception("Not yet implemented!")
                else:
                    # Found a valid mnemonic seed! All new seeds should be considered
                    #   pending (might set a passphrase, SeedXOR, etc) until finalized.
                    from .seed_views import SeedFinalizeView
                    self.controller.storage.set_pending_seed(
                        Seed(mnemonic=seed_mnemonic, wordlist_language_code=self.wordlist_language_code)
                    )
                    if self.settings.get_value(SettingsConstants.SETTING__PASSPHRASE) == SettingsConstants.OPTION__REQUIRED:
                        from seedsigner.views.seed_views import SeedAddPassphraseView
                        return Destination(SeedAddPassphraseView)
                    else:
                        return Destination(SeedFinalizeView)
            
            elif self.decoder.is_psbt:
                from seedsigner.views.psbt_views import PSBTSelectSeedView
                psbt = self.decoder.get_psbt()
                self.controller.psbt = psbt
                self.controller.psbt_parser = None
                return Destination(PSBTSelectSeedView, skip_current_view=True)

            elif self.decoder.is_settings:
                data = self.decoder.get_settings_data()
                return Destination(SettingsIngestSettingsQRView, view_args=dict(data=data))
            
            elif self.decoder.is_wallet_descriptor:
                from seedsigner.views.seed_views import MultisigWalletDescriptorView
                descriptor_str = self.decoder.get_wallet_descriptor()

                try:
                    # We need to replace `/0/*` wildcards with `/{0,1}/*` in order to use
                    # the Descriptor to verify change, too.
                    orig_descriptor_str = descriptor_str
                    if len(re.findall (r'\[([0-9,a-f,A-F]+?)(\/[0-9,\/,h\']+?)\].*?(\/0\/\*)', descriptor_str)) > 0:
                        p = re.compile(r'(\[[0-9,a-f,A-F]+?\/[0-9,\/,h\']+?\].*?)(\/0\/\*)')
                        descriptor_str = p.sub(r'\1/{0,1}/*', descriptor_str)
                    elif len(re.findall (r'(\[[0-9,a-f,A-F]+?\/[0-9,\/,h,\']+?\][a-z,A-Z,0-9]*?)([\,,\)])', descriptor_str)) > 0:
                        p = re.compile(r'(\[[0-9,a-f,A-F]+?\/[0-9,\/,h,\']+?\][a-z,A-Z,0-9]*?)([\,,\)])')
                        descriptor_str = p.sub(r'\1/{0,1}/*\2', descriptor_str)
                except Exception as e:
                    print(repr(e))
                    descriptor_str = orig_descriptor_str

                descriptor = Descriptor.from_string(descriptor_str)

                if not descriptor.is_basic_multisig:
                    # TODO: Handle single-sig descriptors?
                    print(f"Received single sig descriptor: {descriptor}")
                    return Destination(NotYetImplementedView)

                self.controller.multisig_wallet_descriptor = descriptor
                return Destination(MultisigWalletDescriptorView, skip_current_view=True)
            
            elif self.decoder.is_address:
                from seedsigner.views.seed_views import AddressVerificationStartView
                address = self.decoder.get_address()
                (script_type, network) = self.decoder.get_address_type()

                return Destination(
                    AddressVerificationStartView,
                    skip_current_view=True,
                    view_args={
                        "address": address,
                        "script_type": script_type,
                        "network": network,
                    }
                )
                
            #nostr
            elif self.decoder.is_nostr_add:
                nostr_add = self.decoder.get_nostr_add()
                nostr_add_type = self.decoder.get_nostr_add_type()
                
                #TODO check if it is a nsec or a npub
                print("STARTS WITH : ",nostr_add.startswith('nsec')) 
                self.controller.storage.add_nsec(nostr_add)
                
                #TODO if we cscan a npub we might need to do something different.
                
                from seedsigner.views.nostr_views import NostrAddressStartView
                return Destination(
                    NostrAddressStartView,
                    skip_current_view=True,
                    view_args={
                        "nostr_add": nostr_add,
                        "nostr_add_type": nostr_add_type,
                    }
                )
                
                
            elif self.decoder.is_nostr_event_id:   # .qr_type == QRType.NOSTR__JSON_EVENT:
                from seedsigner.views.nostr_views import NostrSignEventIDReviewView
                nostr_event_id = self.decoder.get_nostr_event_id()
                
                try:
                    nostr_add = self.controller.storage.get_nsec()
                except IndexError:
                    #No Nsec is stored, goto nostr menu to add nsec
                    selected_menu_num = WarningScreen(
                        status_headline="No Nsec",
                        text="Scanned a nostr event id hash, we need a nsec loaded to sign it, Load Nsec from seed/scan/keyboard.",
                        button_data=["Continue"],
                    ).display()

                    if selected_menu_num == RET_CODE__BACK_BUTTON:
                        return Destination(BackStackView)

                    # Only one exit point
                    return Destination(
                        ScanNostrAddView,
                        skip_current_view=True,  # Prevent going BACK to WarningViews
                    )

                # TODO - maybe the decoder should return type as well?????
                # #TODO - might error but shouldnt, since its a valid nostr addr already stored
                if nostr_add.startswith('nsec'):
                # # print("addres strats with nsec: ",nostr_add.tostring().startswith('nsec'))
                #     print("address is:", nostr_add)
                    nostr_add_type = "nsec"
                elif nostr_add.startswith('npub'):
                    nostr_add_type = "npub"
                    print("Invalid")
                    raise Exception(f"expecting a nsec key")
                else: 
                    if nostr_add == "" :
                        print("I think we have no nsec, try and scan for one?")
                #         #THIS SHOULD NOT SHOW UP ANYMORE
                #         #TODO maybe we should ask first
                        Destination(ScanNostrAddView)
            
                
                return Destination(
                    NostrSignEventIDReviewView,
                    skip_current_view=True,
                    view_args={
                        "nostr_add": nostr_add,
                        "nostr_add_type": nostr_add_type,
                        "nostr_event_id" : nostr_event_id,
                    }
                )
                
            elif self.decoder.is_nostr_event:
                # from seedsigner.views.nostr_views import NostrSignEventReviewView
                print("this is the self.decode.is_nostr_json_event")
                nostr_event = self.decoder.get_json_event()
                print("WE ARE IN SCAN VIEWS")
                
                try:
                    nostr_add = self.controller.storage.get_nsec()
                except:
                    #No Nsec is stored, goto nostr menu to add nsec
                    selected_menu_num = WarningScreen(
                        status_headline="No Nsec",
                        text="Scanned a nostr event json, we need a nsec loaded to sign it, Load Nsec from seed/scan/keyboard.",
                        button_data=["Continue"],
                    ).display()

                    if selected_menu_num == RET_CODE__BACK_BUTTON:
                        return Destination(BackStackView)

                    # Only one exit point
                    return Destination(
                        ScanNostrAddView,
                        skip_current_view=True,  # Prevent going BACK to WarningViews
                    )

                # TODO - maybe the decoder should return type as well?????
                # #TODO - might error but shouldnt, since its a valid nostr addr already stored
                if nostr_add.startswith('nsec'):
                # # print("addres strats with nsec: ",nostr_add.tostring().startswith('nsec'))
                #     print("address is:", nostr_add)
                    nostr_add_type = "nsec"
                elif nostr_add.startswith('npub'):
                    nostr_add_type = "npub"
                    print("Invalid")
                    raise Exception(f"expecting a nsec key")
                else: 
                    if nostr_add == "" :
                        print("I think we have no nsec, try and scan for one?")
                #         #THIS SHOULD NOT SHOW UP ANYMORE
                #         #TODO maybe we should ask first
                        Destination(ScanNostrAddView)
            
                print("WE ARE ABOUT TO LOAD REVIEW OF JSON EVENT - THAT IS WHERE SIGNING HAPPENS")
                
                from seedsigner.views.nostr_views import NostrSignEventReviewView
                return Destination(
                    NostrSignEventReviewView,
                    skip_current_view=True,
                    view_args={
                        "nostr_add": nostr_add,
                        "nostr_add_type": nostr_add_type,
                        "nostr_event" : nostr_event,
                    }
                )
                
            elif self.decoder.is_nostr_event_serialized:
                # from seedsigner.views.nostr_views import NostrSignEventReviewView
                print("this is the self.decode.is_nostr_json_event_serialized")
                print("is serialized:", self.decoder.is_nostr_event_serialized)
                print("is normal:", self.decoder.is_nostr_event)
                nostr_event_serialized = self.decoder.get_serialized_event()
                print("WE ARE IN SCAN VIEWS")
                
                try:
                    nostr_add = self.controller.storage.get_nsec()
                except:
                    #No Nsec is stored, goto nostr menu to add nsec
                    selected_menu_num = WarningScreen(
                        status_headline="No Nsec",
                        text="Scanned a nostr serialized event , we need a nsec loaded to sign it, Load Nsec from seed/scan/keyboard.",
                        button_data=["Continue"],
                    ).display()

                    if selected_menu_num == RET_CODE__BACK_BUTTON:
                        return Destination(BackStackView)

                    # Only one exit point
                    return Destination(
                        ScanNostrAddView,
                        skip_current_view=True,  # Prevent going BACK to WarningViews
                    )

                # TODO - maybe the decoder should return type as well?????
                # #TODO - might error but shouldnt, since its a valid nostr addr already stored
                if nostr_add.startswith('nsec'):
                # # print("addres strats with nsec: ",nostr_add.tostring().startswith('nsec'))
                #     print("address is:", nostr_add)
                    nostr_add_type = "nsec"
                elif nostr_add.startswith('npub'):
                    nostr_add_type = "npub"
                    print("Invalid")
                    raise Exception(f"expecting a nsec key")
                else: 
                    if nostr_add == "" :
                        print("I think we have no nsec, try and scan for one?")
                #         #THIS SHOULD NOT SHOW UP ANYMORE
                #         #TODO maybe we should ask first
                        Destination(ScanNostrAddView)
            
                print("WE ARE ABOUT TO LOAD REVIEW OF SERIALIZED EVENT - THAT IS WHERE SIGNING HAPPENS")
                
                from seedsigner.views.nostr_views import NostrSignEventReviewView
                return Destination(
                    NostrSignEventReviewView,
                    skip_current_view=True,
                    view_args={
                        "nostr_add": nostr_add,
                        "nostr_add_type": nostr_add_type,
                        "nostr_event_serialized" : nostr_event_serialized,
                    }
                )
                
                

            ## THE CODE BELOW seems to have bug for get_qr_data - I might be missing something here.
            ## it might only trigger if it gets this far and never exits.
            
            elif self.decoder.is_sign_message:
                from seedsigner.views.seed_views import SeedSignMessageStartView
                qr_data = self.decoder.get_qr_data()

                return Destination(
                    SeedSignMessageStartView,
                    view_args=dict(
                        derivation_path=qr_data["derivation_path"],
                        message=qr_data["message"],
                    )
                )
                
           
            
            else:
                return Destination(NotYetImplementedView)

        elif self.decoder.is_invalid:
            # For now, don't even try to re-do the attempted operation, just reset and
            # start everything over.
            self.controller.resume_main_flow = None
            return Destination(ErrorView, view_args=dict(
                title="Error",
                status_headline="Unknown QR Type",
                text="QRCode is invalid or is a data format not yet supported.",
                button_text="Done",
                next_destination=Destination(MainMenuView, clear_history=True),
            ))

        return Destination(MainMenuView)



class ScanPSBTView(ScanView):
    instructions_text = "Scan PSBT"
    invalid_qr_type_message = "Expected a PSBT"

    @property
    def is_valid_qr_type(self):
        return self.decoder.is_psbt



class ScanSeedQRView(ScanView):
    instructions_text = "Scan SeedQR"
    invalid_qr_type_message = f"Expected a SeedQR"

    @property
    def is_valid_qr_type(self):
        return self.decoder.is_seed



class ScanWalletDescriptorView(ScanView):
    instructions_text = "Scan descriptor"
    invalid_qr_type_message = "Expected a wallet descriptor QR"

    @property
    def is_valid_qr_type(self):
        return self.decoder.is_wallet_descriptor



class ScanAddressView(ScanView):
    instructions_text = "Scan address QR"
    invalid_qr_type_message = "Expected an address QR"

    @property
    def is_valid_qr_type(self):
        return self.decoder.is_address
    
    
    
class ScanNostrAddView(ScanView):
    instructions_text = "Scan a Nostr address"
    invalid_qr_type_message = "Expected a Nostr Nsec Address"
        
    @property
    def is_valid_qr_type(self):
        return self.decoder.is_nostr_add
    
    
class ScanNostrJsonEventIDView(ScanView):
    instructions_text = "Scan an Event Id"
    invalid_qr_type_message = "Expected a Nostr Json Event Id"
        
    @property
    def is_valid_qr_type(self):
        return self.decoder.is_nostr_event_id
    
class ScanNostrJsonEventView(ScanView):
    instructions_text = "Scan an Event"
    invalid_qr_type_message = "Expected a Nostr Json Event"
        
    @property
    def is_valid_qr_type(self):
        return self.decoder.is_nostr_event

class ScanNostrSerializedEventView(ScanView):
    instructions_text = "Scan a Serialized Event"
    invalid_qr_type_message = "Expected a Nostr Serialized Event"
        
    @property
    def is_valid_qr_type(self):
        return self.decoder.is_nostr_event_serialized
