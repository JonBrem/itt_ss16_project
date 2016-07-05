import utility_module as um


class UndoUtility():

    def __init__(self):
        self.action_history_ring = um.RingArray(12)
        self.current_index = 0

        self.first_state_at_undo = None
        self.currently_undoing = False
        self.currently_redoing = False

    def add_action(self, action, state):
        """ params: action = string description of the action
                    state = program state
        """
        # overwrite undo
        self.currently_undoing = False
        self.currently_redoing = False
        self.first_state_at_undo = None

        if self.current_index != len(self.action_history_ring) - 1 and\
           len(self.action_history_ring) != 0:
            old_action_ring = self.action_history_ring
            self.action_history_ring = um.RingArray(12)
            for i in range(0, self.current_index):
                self.action_history_ring.append(old_action_ring[i])

        self.action_history_ring.append({"action": action, "state": state})
        self.current_index = len(self.action_history_ring) - 1

    def undo(self):
        if self.current_index < 0 or self.current_index not in range(0, len(self.action_history_ring)):
            return None

        self.currently_redoing = False
        self.currently_undoing = True
        index = self.current_index
        self.current_index -= 1

        return self.action_history_ring[index]

    def set_first_state_at_undo(self, state):
        if not self.currently_undoing:
            self.first_state_at_undo = state

    def redo(self):
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
