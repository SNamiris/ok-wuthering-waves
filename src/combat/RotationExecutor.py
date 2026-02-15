import time

from ok import Logger

logger = Logger.get_logger(__name__)


class RotationStep:
    __slots__ = ('action', 'value', 'duration')

    def __init__(self, action, value=None, duration=0):
        self.action = action
        self.value = value
        self.duration = duration

    def __repr__(self):
        parts = [self.action]
        if self.value is not None:
            parts.append(str(self.value))
        if self.duration > 0:
            parts.append(f'{self.duration}s')
        return f'Step({" ".join(parts)})'


ACTIONS = {
    'e': 'resonance',
    'q': 'echo',
    'echo': 'echo',
    'lib': 'liberation',
    'a': 'attack',
    'ba': 'attack',
    'ha': 'heavy',
    'dodge': 'dodge',
    'jump': 'jump',
}


def parse_rotation(rotation_str):
    """Parse rotation string into list of RotationSteps.

    Format: space-separated tokens
        1, 2, 3         -> switch to character slot
        e                -> resonance skill
        q                -> echo skill
        lib              -> liberation
        a / ba           -> normal attack (click)
        ha               -> heavy attack (mouse hold)
        dodge            -> dodge
        jump             -> jump
        action:seconds   -> action with duration (e.g. a:1.2, ha:0.8)
    """
    steps = []
    if not rotation_str or not rotation_str.strip():
        return steps
    for token in rotation_str.strip().split():
        duration = 0
        base = token
        if ':' in token:
            base, dur_str = token.split(':', 1)
            try:
                duration = max(0, float(dur_str))
            except ValueError:
                logger.warning(f'Invalid duration in token: {token}')
                continue
        if base in ('1', '2', '3'):
            steps.append(RotationStep('switch', int(base), duration))
        elif base.lower() in ACTIONS:
            steps.append(RotationStep(ACTIONS[base.lower()], duration=duration))
        else:
            logger.warning(f'Unknown rotation token: {token}')
    return steps


class RotationExecutor:

    def __init__(self, task, rotation_str):
        self.task = task
        self.rotation_str = rotation_str
        self.steps = parse_rotation(rotation_str)
        if self.steps:
            logger.info(f'Rotation loaded: {len(self.steps)} steps')

    def execute_once(self):
        """Execute the full rotation sequence once (one cycle)."""
        for step in self.steps:
            if not self.task.in_combat():
                return
            self._execute_step(step)
            self.task.next_frame()

    def _execute_step(self, step):
        action = step.action
        if action == 'switch':
            self.task.send_key(str(step.value))
            self.task.sleep(max(step.duration, 0.15))
        elif action == 'resonance':
            self.task.send_key(self.task.get_resonance_key())
            if step.duration > 0:
                self.task.sleep(step.duration)
        elif action == 'echo':
            self.task.send_key(self.task.get_echo_key())
            if step.duration > 0:
                self.task.sleep(step.duration)
        elif action == 'liberation':
            self.task.send_key(self.task.get_liberation_key())
            if step.duration > 0:
                self.task.sleep(step.duration)
        elif action == 'attack':
            duration = step.duration or 0.1
            start = time.time()
            while time.time() - start < duration:
                if not self.task.in_combat():
                    return
                self.task.click()
                self.task.next_frame()
        elif action == 'heavy':
            duration = step.duration or 0.6
            try:
                self.task.mouse_down()
                self.task.sleep(duration)
            finally:
                self.task.mouse_up()
        elif action == 'dodge':
            self.task.send_key(self.task.key_config['Dodge Key'])
            if step.duration > 0:
                self.task.sleep(step.duration)
        elif action == 'jump':
            self.task.send_key(self.task.key_config['Jump Key'])
            if step.duration > 0:
                self.task.sleep(step.duration)
