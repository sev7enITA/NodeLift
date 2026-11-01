import { node } from './NodeController';
import { translate } from './Localization';

PersistentStorage.persistProp('nodelift-language', 'en');

@Entry
@Component
struct Index {
  @StorageLink('nodelift-language') language: string = 'en';
  private t(key: string): string { return translate(key, this.language); }
  @State ticket: string = '';
  @State status: string = node.status;
  @State result: string = node.result;
  @State running: boolean = false;
  aboutToAppear(): void { node.changed = () => { this.status = node.status; this.result = node.result; this.running = node.running; }; }
  aboutToDisappear(): void { node.pause(); node.changed = () => {}; }
  build() {
    Scroll() {
      Column({ space: 18 }) {
        Text('◈ NodeLift').fontSize(30).fontWeight(FontWeight.Bold).fontColor('#EDF5F8').width('100%')
        Text(this.t('Language')).fontSize(14).fontColor('#9EB1BD').width('100%')
        Select([{ value: 'English' }, { value: '简体中文' }, { value: 'Italiano' }])
          .selected(this.language === 'zh-Hans' ? 1 : this.language === 'it' ? 2 : 0)
          .value(this.language === 'zh-Hans' ? '简体中文' : this.language === 'it' ? 'Italiano' : 'English')
          .onSelect((index: number) => { this.language = index === 1 ? 'zh-Hans' : index === 2 ? 'it' : 'en'; })
        Text(this.t('YOUR DEVICE. A NEW NODE.')).fontSize(10).fontColor('#91F3CE').width('100%')
        Text(this.t('Connect. Measure.\nChoose when to participate.')).fontSize(30).fontWeight(FontWeight.Medium).fontColor('#EDF5F8').width('100%').margin({ top: 18, bottom: 16 })
        Column({ space: 12 }) {
          Text(this.t(this.status)).fontSize(20).fontColor('#91F3CE').width('100%')
          Text(this.t('HarmonyOS · foreground session')).fontSize(14).fontColor('#9EB1BD').width('100%')
        }.padding(22).backgroundColor('#13232D').borderRadius(18).width('100%')
        Column({ space: 14 }) {
          Text(this.t('Pair your computer')).fontSize(22).fontColor('#EDF5F8').width('100%')
          Text(this.t('Create an invitation in the NodeLift dashboard and paste it here. It is valid for 5 minutes and can be used once.')).fontSize(14).fontColor('#9EB1BD')
          TextArea({ placeholder: this.t('NodeLift invitation'), text: this.ticket }).height(110).fontSize(12).fontColor('#EDF5F8').backgroundColor('#0B151C').onChange((text: string) => { this.ticket = text; })
          Button(this.t('Pair and activate node')).width('100%').backgroundColor('#91F3CE').fontColor('#0B151C').enabled(!this.running).onClick(() => { const value = this.ticket; this.ticket = ''; node.connect(value); })
          Button(this.t('Resume session')).width('100%').onClick(() => { node.resume(); })
        }.padding(22).backgroundColor('#13232D').borderRadius(18).width('100%')
        Column({ space: 12 }) {
          Text(this.t('You stay in control')).fontSize(22).fontColor('#EDF5F8').width('100%')
          Text(this.t('Keep the app open. Moving to the background pauses the node. This candidate build measures the network; CPU and LLM work are not enabled. Credentials remain in memory only.')).fontSize(14).fontColor('#9EB1BD')
          Button(this.t('Pause node')).width('100%').onClick(() => { node.pause(); })
          Button(this.t('Forget computer')).width('100%').onClick(() => { node.forget(); })
          Text(this.t(this.result)).fontSize(14).fontColor('#91F3CE')
        }.padding(22).backgroundColor('#13232D').borderRadius(18).width('100%')
        Text(this.t('0.1 · HarmonyOS candidate: build and device qualification required')).fontSize(12).fontColor('#9EB1BD')
      }.padding(24).width('100%')
    }.width('100%').height('100%').backgroundColor('#0B151C')
  }
}
