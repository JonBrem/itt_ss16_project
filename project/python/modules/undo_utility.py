from python.modules import utility_module as um

# number of states that can be undone
UNDO_LENGTH = 15


class UndoUtility:
    def __init__(self, max_steps=UNDO_LENGTH):
        self.action_history_ring = um.RingArray(max_steps)
        self.max_steps = max_steps

        # index of the currently active state in the RingArray of system
        # states. Usually the Array's length -1 (= the last state);
        # gets decreased by Undo and increased by Redo.
        self.current_index = 0

        # see "set_first_state_at_undo"
        self.first_state_at_undo = None

        # whether or not the user is currently in an "Undo/Redo Chain",
        # i.e. the last operation was either Undo or Redo.
        self.currently_undoing = False

    def reset(self):
        self.action_history_ring = um.RingArray(self.max_steps)
        self.current_index = 0

        self.first_state_at_undo = None
        self.currently_undoing = False

    def add_action(self, action, state):
        """ params: action = string description of the action
                    state = program state
        """
        # overwrite undo
        self.currently_undoing = False
        self.first_state_at_undo = None

        if self.current_index != len(self.action_history_ring) - 1 and\
           len(self.action_history_ring) != 0:
            # was currently undoing & now appended another action -->
            # the states that followed must be overwritten.
            old_action_ring = self.action_history_ring
            self.action_history_ring = um.RingArray(self.max_steps)
            for i in range(0, self.current_index):
                self.action_history_ring.append(old_action_ring[i])

        self.action_history_ring.append({"action": action, "state": state})
        self.current_index = len(self.action_history_ring) - 1

    def undo(self):
        """ Returns the state before the last change, or None. """
        if self.current_index not in range(0, len(self.action_history_ring)):
            return None

        self.currently_undoing = True
        index = self.current_index
        self.current_index -= 1

        return self.action_history_ring[index]

    def set_first_state_at_undo(self, state):
        """ In order to be able to Redo, the state of the app before the
            first undo operation must be stored using this method.
            This can be called more often in an Undo/Redo chain without
            overwriting the state.
        """
        if not self.currently_undoing:
            self.first_state_at_undo = state

    def redo(self):
        """ Returns the state before the last "undo", or None. """
        if not self.currently_undoing:
            return None

        if self.current_index == len(self.action_history_ring) - 2:
            state = self.first_state_at_undo
            self.current_index += 1
            return {"state": state, "action": "not identified"}
        elif self.current_index < len(self.action_history_ring) - 2:
            self.current_index += 1
            return self.action_history_ring[self.current_index + 1]
        else:
            return None

    def current_state(self, after_undo=True):
        """ Returns the state before "undo" or "redo" is applied.
            Must be called immediately _after_ one of these methods
            (undo / redo); else it might return the wrong state.

            The "current state" is used to identify changes that need to be
            made to reach the other state and is hence not required in a
            "full reload".
        """
        if len(self.action_history_ring) == 0:
            return None
        if after_undo:
            if self.current_index == len(self.action_history_ring) - 2:
                return {"state": self.first_state_at_undo,
                        "action": "not identified"}
            else:
                return self.action_history_ring[self.current_index + 2]
        else:
            return self.action_history_ring[self.current_index]
