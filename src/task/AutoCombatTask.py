import time

from qfluentwidgets import FluentIcon

from ok import TriggerTask, Logger
from src.combat.RotationExecutor import RotationExecutor
from src.scene.WWScene import WWScene
from src.task.BaseCombatTask import BaseCombatTask, NotInCombatException, CharDeadException

logger = Logger.get_logger(__name__)


class AutoCombatTask(BaseCombatTask, TriggerTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_config = {'_enabled': True}
        self.trigger_interval = 0.1
        self.name = "Auto Combat"
        self.description = "Enable auto combat in Abyss, Game World etc"
        self.icon = FluentIcon.CALORIES
        self.last_is_click = False
        self.scene: WWScene | None = None
        self.default_config.update({
            'Auto Target': True,
            'Use Liberation': True,
            'Check Levitator': True,
            'Rotation Mode': False,
            'Rotation': '',
        })
        self.config_description = {
            'Auto Target': 'Turn off to enable auto combat only when manually target enemy using middle click',
            'Use Liberation': 'Do not use Liberation in Open World to Save Time',
            'Check Levitator': 'Toggle the levitator and verify if the character is floating',
            'Rotation Mode': 'Enable fixed rotation mode, execute predefined rotation instead of auto combat AI',
            'Rotation': 'Rotation sequence, e.g. "1 e q lib 2 e a:1.2 lib 3 e ha:0.8 lib"  '
                        '(1/2/3=switch char, e=skill, q=echo, lib=liberation, a=attack, ha=heavy, dodge, jump)',
        }
        self.rotation_executor = None
        self.op_index = 0

    def run(self):
        ret = False
        if not self.scene.in_team(self.in_team_and_world):
            return ret
        self.use_liberation = self.config.get('Use Liberation')
        if not self.use_liberation and not self.in_world():  # 仅大世界生效
            self.use_liberation = True
        combat_start = time.time()
        rotation_mode = self.config.get('Rotation Mode')
        if rotation_mode:
            rotation_str = self.config.get('Rotation', '')
            if rotation_str:
                if not self.rotation_executor or self.rotation_executor.rotation_str != rotation_str:
                    self.rotation_executor = RotationExecutor(self, rotation_str)
            else:
                rotation_mode = False
                logger.warning('Rotation Mode enabled but no rotation defined, falling back to auto combat')
        while self.in_combat():
            ret = True
            try:
                if rotation_mode and self.rotation_executor:
                    self.rotation_executor.execute_once()
                else:
                    self.get_current_char().perform()
            except CharDeadException:
                self.log_error(f'Characters dead', notify=True)
                break
            except NotInCombatException as e:
                logger.info(f'auto_combat_task_out_of_combat {int(time.time() - combat_start)} {e}')
                break
        if ret:
            self.combat_end()
        return ret

    def realm_perform(self):
        if not self.last_is_click:
            if self.op_index % 10 == 0:
                self.send_key_and_wait_animation('4', self.in_illusive_realm, enter_animation_wait=0.2)
            else:
                self.click()
        else:
            if self.available('liberation'):
                self.send_key_and_wait_animation(self.get_liberation_key(), self.in_illusive_realm)
            elif self.available('echo'):
                self.send_key(self.get_echo_key())
            elif self.available('resonance'):
                self.send_key(self.get_resonance_key())
            elif self.is_con_full() and self.in_team()[0]:
                self.send_key_and_wait_animation('2', self.in_illusive_realm)
        self.last_is_click = not self.last_is_click
        self.op_index += 1
        self.sleep(0.02)
