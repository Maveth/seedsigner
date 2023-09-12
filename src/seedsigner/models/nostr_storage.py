



#TODO this will be used to store the nostr nsec, just a like a seed is done.
##this is only becuase nostr users may have a nsec but no seed
##If a seed is used then this should never be touched.

#TODO maybe we should have a list of nsecs... for now we will only store one

class Nsec:
    def __init__(self):
        #nsec is a string
        self.nsec : str 

    def add_nsec(self, nsec):
        # Add a new root key to the storage
        self.nsec = nsec

    def remove_nsec(self):
        # make nsec null
        self.nsec = ""

    def get_nsec(self):
        #return the nsec string
        return self.nsec
    


