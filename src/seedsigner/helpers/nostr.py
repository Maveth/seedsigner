import json
from binascii import hexlify, unhexlify
from typing import List
from embit import bip32
from embit import ec
from hashlib import sha256
# import spec256k1
from seedsigner.helpers import bech32
from seedsigner.models.seed import Seed
# from seedsigner.models.nostr import Nostr



KIND__SET_METADATA = 0
KIND__TEXT_NOTE = 1
KIND__RECOMMEND_RELAY = 2
KIND__CONTACTS = 3
KIND__ENCRYPTED_DIRECT_MESSAGE = 4
KIND__DELETE = 5
KIND__REACTIONS = 7
KIND__LIST = 3000

KINDS = {
    KIND__SET_METADATA: "Set metadata",
    KIND__TEXT_NOTE: "Text note",
    KIND__RECOMMEND_RELAY: "Recommend relay",
    KIND__CONTACTS: "Contacts",
    KIND__ENCRYPTED_DIRECT_MESSAGE: "Encrypted DM",
    KIND__DELETE: "Delete",
    KIND__REACTIONS: "Reactions",
    KIND__LIST: "List",
}



class SerializedEventFields:
    # Nostr Events are serialized as (see NIP-01):
    #   [0, <sender_pubkey: str>, <created_at: int>, <kind: int>, <tags: List[List[str]]>, <content:str>]
    SENDER_PUBKEY = 1
    CREATED_AT = 2
    KIND = 3
    TAGS = 4
    CONTENT = 5



def derive_nostr_key(seed: Seed) -> bip32.HDKey:
    """ Derive the NIP-06 Nostr key at m/44'/1237'/0'/0/0 """
    """
        Note: You could derive sibling seeds (e.g. m/44h/1237h/0h/0/1) from the same root
        Seed, but so far Nostr use cases & best practices are limited to just a single
        direct path from mnemonic to npub/nsec. No sibling or child Nostr keys.
        
        Note: This would be a good way to do delegation via an external watchtower
    """
    root = bip32.HDKey.from_seed(seed.seed_bytes)
    return root.derive("m/44h/1237h/0h/0/0")


def get_nsec(seed: Seed) -> str:
    nostr_root = derive_nostr_key(seed=seed)
    converted_bits = bech32.convertbits(nostr_root.secret, 8, 5)
    return bech32.bech32_encode("nsec", converted_bits, bech32.Encoding.BECH32)


def get_npub(seed: Seed) -> str:
    nostr_root = derive_nostr_key(seed=seed)
    privkey = ec.PrivateKey(secret=nostr_root.secret)
    pubkey = privkey.get_public_key().xonly()
    converted_bits = bech32.convertbits(pubkey, 8, 5)
    return bech32.bech32_encode("npub", converted_bits, bech32.Encoding.BECH32)


def get_pubkey_hex(seed: Seed) -> str:
    nostr_root = derive_nostr_key(seed=seed)
    privkey = ec.PrivateKey(secret=nostr_root.secret)
    return hexlify(privkey.get_public_key().xonly()).decode()


def get_privkey_hex(seed: Seed) -> str:
    nostr_root = derive_nostr_key(seed=seed)
    return hexlify(nostr_root.secret).decode()



"""****************************************************************************
    Key format conversion
****************************************************************************"""
def pubkey_hex_to_npub(pubkey_hex: str) -> str:
    converted_bits = bech32.convertbits(unhexlify(pubkey_hex), 8, 5)
    return bech32.bech32_encode("npub", converted_bits, bech32.Encoding.BECH32)

#Since we will not always have a seed, we need to have the ability to do this directly
def privkey_hex_to_nsec(privkey_hex: str) -> str:
    converted_bits = bech32.convertbits(unhexlify(privkey_hex), 8, 5)
    return bech32.bech32_encode("nsec", converted_bits, bech32.Encoding.BECH32)


def npub_to_hex(npub: str) -> str:
    hrp, data, spec = bech32.bech32_decode(npub)
    raw_public_key = bech32.convertbits(data, 5, 8)[:-1]
    return bytes(raw_public_key).hex()


#Since we will not always have a seed, we need to have the ability to do this directly
def nsec_to_hex(nsec: str) -> str:
    hrp, data, spec = bech32.bech32_decode(bytes.fromhex(nsec))
    raw_priv_key = bech32.convertbits(data, 5, 8)[:-1]
    return bytes(raw_priv_key).hex()


    PK1= nsec_to_hex (nostr_add)  #convert nsec bech32 to HEX
    # PK1 = bytes.fromhex(PK1)  # Convert the hexadecimal string to bytes
    PK2= ec.PrivateKey(bytes.fromhex(PK1)) #get WIF format secret privatekey used by seedsigner ec import

def privkey_hex_to_pubkey_hex(privkey_hex: str) -> str:
    privkey = ec.PrivateKey(bytes.fromhex(privkey_hex))
    return hexlify(privkey.get_public_key().xonly()).decode()
    



##TODO we will need to have a method to do signing without a seed.
## many people do not have a seed, and created a privatekey without the bip32
"""****************************************************************************
    Signing an event ID only 
    (as Signing below, but sha256(full_message.encode()) IS the event_id for nostr)
****************************************************************************"""
def sign_event_id(nostr_add: str, nostr_add_type: str, nostr_event: str):
    """ signs a hash (event_ID), with privatekey """
    
    #TODO make this so it can take either nsec OR seed
    #or make 2 functions
    
    event_data = json.loads(nostr_event)
    event_id_hex = event_data.get("EVENT.ID", "") #strip out the event ID
    
    #run sanity checks
    if not event_id_hex:
        print("No EVENT.ID found in the JSON event.")
        return None
    
    if not nostr_add_type == "nsec":
        print("we expect nsec")
        return None
    
    PK1= nsec_to_hex (nostr_add)  #convert nsec bech32 to HEX
    # PK1 = bytes.fromhex(PK1)  # Convert the hexadecimal string to bytes
    PK2= ec.PrivateKey(bytes.fromhex(PK1)) #get WIF format secret privatekey used by seedsigner ec import
    
    sig = PK2.schnorr_sign(bytes.fromhex(event_id_hex))
    return sig

"""****************************************************************************
    Signing
****************************************************************************"""
def sign_message(seed: Seed, full_message: str):
    """ Hashes the full_message and then signs """
    nostr_root = derive_nostr_key(seed=seed)
    sig = nostr_root.schnorr_sign(sha256(full_message.encode()).digest())
    return sig


##TODO we are going to do signing of the event IDS not full messages.
"""****************************************************************************
    Events
****************************************************************************"""
def serialize_event(event_dict: dict) -> str:
    """ Serialize an Event from its json form """
    data = [0, event_dict["pubkey"], event_dict["created_at"], event_dict["kind"], event_dict["tags"], event_dict["content"]]
    data_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    return data_str


def sign_event(seed: Seed, serialized_event: str):
    return sign_message(seed=seed, full_message=serialized_event)


def sign_event_with_key(nostr_add: str, serialized_event: str):
    """ Hashes the full_message and then signs """
    print ("trying to sign message, we have")
    print ("nostr_add: ",nostr_add)
    print ("event",serialized_event)
    PK1= nsec_to_hex (nostr_add)  #convert nsec bech32 to HEX
    PK2= ec.PrivateKey(bytes.fromhex(PK1)) #get WIF format secret privatekey used by seedsigner ec import
    
    sig = PK2.schnorr_sign(sha256(serialized_event.encode()).digest())
    return sig


