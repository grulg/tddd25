# -----------------------------------------------------------------------------
# Distributed Systems (TDDD25)
# -----------------------------------------------------------------------------
# Author: Sergiu Rafiliu (sergiu.rafiliu@liu.se)
# Modified: 31 July 2013
#
# Copyright 2012 Linkoping University
# -----------------------------------------------------------------------------

"""Module for the distributed mutual exclusion implementation.

This implementation is based on the second Rikard-Agravara algorithm.
The implementation should satisfy the following requests:
    --  when starting, the peer with the smallest id in the peer list
        should get the token.
    --  access to the state of each peer (dictinaries: request, token,
        and peer_list) should be protected.
    --  the implementation should gratiously handle situations when a
        peer dies unexpectedly. All exceptions comming from calling
        peers that have died, should be handled such as the rest of the
        peers in the system are still working. Whenever a peer has been
        detected as dead, the token, request, and peer_list
        dictionaries should be updated acordingly.
    --  when the peer that has the token (either TOKEN_PRESENT or
        TOKEN_HELD) quits, it should pass the token to some other peer.
    --  For simplicity, we shall not handle the case when the peer
        holding the token dies unexpectedly.

"""

NO_TOKEN = 0
TOKEN_PRESENT = 1
TOKEN_HELD = 2


class DistributedLock(object):

    """Implementation of distributed mutual exclusion for a list of peers.

    Public methods:
        --  __init__(owner, peer_list)
        --  initialize()
        --  destroy()
        --  register_peer(pid)
        --  unregister_peer(pid)
        --  acquire()
        --  release()
        --  request_token(time, pid)
        --  obtain_token(token)
        --  display_status()

    """

    def __init__(self, owner, peer_list):
        self.peer_list = peer_list
        self.owner = owner
        self.time = 0
        self.token = None
        self.request = {}
        self.state = NO_TOKEN

    def _prepare(self, token):
        """Prepare the token to be sent as a JSON message.

        This step is necessary because in the JSON standard, the key to
        a dictionary must be a string whild in the token the key is
        integer.
        """
        return list(token.items())

    def _unprepare(self, token):
        """The reverse operation to the one above."""
        return dict(token)

    # Public methods

    def initialize(self):
        """ Initialize the state, request, and token dicts of the lock.

        Since the state of the distributed lock is linked with the
        number of peers among which the lock is distributed, we can
        utilize the lock of peer_list to protect the state of the
        distributed lock (strongly suggested).

        NOTE: peer_list must already be populated when this
        function is called.

        """
        self.request[self.owner.id] = 0

        self.peer_list.lock.acquire()

        for peer in self.peer_list.peers:
            self.request[peer.id] = 0

        if len(self.peer_list.peers) == 0:
            self.state = TOKEN_PRESENT
            self.token = {self.owner.id: 0}

        self.peer_list.lock.release()

    def destroy(self):
        """ The object is being destroyed.

        If we have the token (TOKEN_PRESENT or TOKEN_HELD), we must
        give it to someone else.

        """
        self.release()
        self.peer_list.lock.acquire()

        if self.state != NO_TOKEN and len(self.peer_list.peers) > 0:
            self.peer_list.peers.values()[0].obtain_token(self.token)

        self.peer_list.lock.release()

    def register_peer(self, pid):
        """Called when a new peer joins the system."""
        self.peer_list.lock.acquire()
        self.token[pid] = 0
        self.request[pid] = 0
        self.peer_list.lock.release()

    def unregister_peer(self, pid):
        """Called when a peer leaves the system."""
        self.peer_list.lock.acquire()
        del(self.token[pid])
        del(self.request[pid])
        self.peer_list.lock.release()

    def acquire(self):
        """Called when this object tries to acquire the lock."""
        print("Trying to acquire the lock...")
        self.peer_list.lock.acquire()
        if self.state == NO_TOKEN:
            for peer in self.peer_list.peers:
                peer.request_token(self.time, self.owner.id)

            while self.state == NO_TOKEN:
                pass

        self.peer_list.lock.release()
        self.state = TOKEN_HELD

    def release(self):
        """Called when this object releases the lock."""
        print("Releasing the lock...")
        self.state = TOKEN_PRESENT

        self.peer_list.lock.acquire()

        peers = sorted(self.peer_list.peers.iteritems())
        lower_peers = []
        found = False
        for peer in peers:
            if peer.id > self.owner.id:
                if self.can_has_tokenz(peer):
                    found = True
                    break

            else:
                lower_peers.append(peer)

        if not found:
            for peer in lower_peers:
                if peer.id > self.owner.id:
                    if self.can_has_tokenz(peer):
                        break

        self.peer_list.lock.release()
        self.token = None

    def can_has_tokenz(self, peer):
        if self.request[peer.id] > self.token[peer.id]:
            self.state = NO_TOKEN
            self.token[self.owner.id] = self.time   # TODO Fix this!
            peer.obtain_token(self._prepare(self.token))
            return True
        else:
            return False

    def request_token(self, time, pid):
        """Called when some other object requests the token from us."""
        # TODO Locks?
        self.request[pid] = max(self.request[pid], time)
        if self.state == TOKEN_PRESENT:
            self.release()

    def obtain_token(self, token):
        """Called when some other object is giving us the token."""
        print("Receiving the token...")
        self.token = self._unprepare(token)
        self.state = TOKEN_PRESENT

    def display_status(self):
        """Print the status of this peer."""
        self.peer_list.lock.acquire()
        try:
            nt = self.state == NO_TOKEN
            tp = self.state == TOKEN_PRESENT
            th = self.state == TOKEN_HELD
            print("State   :: no token      : {0}".format(nt))
            print("           token present : {0}".format(tp))
            print("           token held    : {0}".format(th))
            print("Request :: {0}".format(self.request))
            print("Token   :: {0}".format(self.token))
            print("Time    :: {0}".format(self.time))
        finally:
            self.peer_list.lock.release()
