import { UIAbility } from '@kit.AbilityKit';
import { window } from '@kit.ArkUI';
import { node } from '../pages/NodeController';

export default class EntryAbility extends UIAbility {
  onWindowStageCreate(stage: window.WindowStage): void { stage.loadContent('pages/Index'); }
  onBackground(): void { node.pause(); }
  onDestroy(): void { node.forget(); }
}
