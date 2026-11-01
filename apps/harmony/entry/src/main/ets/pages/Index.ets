import { node } from './NodeController';
import { translate } from './Localization';
import { bundleManager, common } from '@kit.AbilityKit';

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
  @State aboutExpanded: boolean = false;
  @State versionName: string = '-';
  @State versionCode: string = '-';
  @State aboutLinkError: boolean = false;
  private async readInstalledVersion(): Promise<void> {
    try {
      const info = await bundleManager.getBundleInfoForSelf(bundleManager.BundleFlag.GET_BUNDLE_INFO_DEFAULT);
      this.versionName = info.versionName;
      this.versionCode = info.versionCode.toString();
    } catch (_) { this.versionName = '-'; this.versionCode = '-'; }
  }
  private versionLabel(): string {
    return this.t('Version {0} · build {1}').replace('{0}', this.versionName).replace('{1}', this.versionCode);
  }
  private async openReference(url: string): Promise<void> {
    this.aboutLinkError = false;
    try {
      const context = this.getUIContext().getHostContext() as common.UIAbilityContext;
      await context.openLink(url, { appLinkingOnly: false });
    } catch (_) { this.aboutLinkError = true; }
  }
  @Builder aboutLink(label: string, url: string) {
    Button(this.t(label) + ' ↗').width('100%').constraintSize({ minHeight: 48 })
      .fontSize(15).fontColor('#91F3CE').backgroundColor('#13232D')
      .padding({ top: 12, bottom: 12, left: 0, right: 0 })
      .onClick(() => { this.openReference(url); })
  }
  @Builder aboutSection() {
    Column({ space: 12 }) {
      Image($r('app.media.nodelift_emblem')).width(80).height(80).objectFit(ImageFit.Contain)
      Text('NodeLift').fontSize(27).fontWeight(FontWeight.Bold).fontColor('#EDF5F8').width('100%')
      Text(this.versionLabel()).fontSize(13).fontColor('#91F3CE').width('100%')
      Text(this.t('HarmonyOS candidate · build and device qualification pending')).fontSize(13).fontColor('#9EB1BD').width('100%')
      Text(this.t('Created by Fabrizio Degni')).fontSize(21).fontColor('#EDF5F8').width('100%')
      Text(this.t('Original concept, research direction and development.')).fontSize(14).fontColor('#9EB1BD').width('100%')
      Text(this.t('Updates')).fontSize(19).fontColor('#EDF5F8').width('100%').margin({ top: 12 })
      Text(this.t('Open the official releases page and compare your installed version with the release notes. This is a manual check; no update is installed automatically.')).fontSize(14).fontColor('#9EB1BD').width('100%')
      this.aboutLink('Check releases on GitHub', 'https://github.com/sev7enITA/NodeLift/releases')
      this.aboutLink('Official downloads & installation', 'https://www.fabriziodegni.com/NodeLift/#downloads')
      Text(this.t('Project & author')).fontSize(19).fontColor('#EDF5F8').width('100%').margin({ top: 12 })
      this.aboutLink('Source repository', 'https://github.com/sev7enITA/NodeLift')
      this.aboutLink('Project website', 'https://www.fabriziodegni.com/NodeLift/')
      this.aboutLink('Author website', 'https://www.fabriziodegni.com/')
      this.aboutLink('LinkedIn', 'https://www.linkedin.com/in/fdegni/')
      Text(this.t('References & licenses')).fontSize(19).fontColor('#EDF5F8').width('100%').margin({ top: 12 })
      this.aboutLink('Architecture & technical documentation', 'https://github.com/sev7enITA/NodeLift/blob/main/docs/ARCHITECTURE.md')
      this.aboutLink('Research & comparison atlas', 'https://github.com/sev7enITA/NodeLift/blob/main/research/comparison-2026-10-31/README.md')
      this.aboutLink('Third-party acknowledgements', 'https://github.com/sev7enITA/NodeLift/blob/main/THIRD_PARTY_NOTICES.md')
      this.aboutLink('MIT license · original NodeLift code', 'https://github.com/sev7enITA/NodeLift/blob/main/LICENSE')
      Text(this.t('Dependencies and model weights retain their own licenses and authorship.')).fontSize(13).fontColor('#9EB1BD').width('100%')
      Text(this.t('This candidate measures the network only; a native LLM worker is not implemented.')).fontSize(13).fontColor('#9EB1BD').width('100%')
      Text(this.t('Links open in your browser. NodeLift does not attach pairing keys, model data or diagnostics.')).fontSize(13).fontColor('#9EB1BD').width('100%')
      Text(this.t('Opening a browser may pause this node. Return to NodeLift and resume when ready.')).fontSize(13).fontColor('#9EB1BD').width('100%')
      if (this.aboutLinkError) {
        Text(this.t('Unable to open this link. Open the official website in your browser.')).fontSize(14).fontColor('#FFD28A').width('100%')
      }
      Text('© 2026 Fabrizio Degni').fontSize(12).fontColor('#9EB1BD').width('100%')
      Button(this.t('Close')).width('100%').constraintSize({ minHeight: 48 })
        .backgroundColor('#91F3CE').fontColor('#0B151C').onClick(() => { this.aboutExpanded = false; })
    }.padding(22).backgroundColor('#13232D').borderRadius(18).width('100%')
  }
  aboutToAppear(): void { this.readInstalledVersion(); node.changed = () => { this.status = node.status; this.result = node.result; this.running = node.running; }; }
  aboutToDisappear(): void { node.pause(); node.changed = () => {}; }
  build() {
    Scroll() {
      Column({ space: 18 }) {
        Text('◈ NodeLift').fontSize(30).fontWeight(FontWeight.Bold).fontColor('#EDF5F8').width('100%')
        Button(this.t('About & References')).width('100%').constraintSize({ minHeight: 48 })
          .backgroundColor('#13232D').fontColor('#91F3CE')
          .onClick(() => { this.aboutExpanded = !this.aboutExpanded; })
        if (this.aboutExpanded) { this.aboutSection() }
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
        Text(this.versionLabel() + '\n' + this.t('HarmonyOS candidate · build and device qualification pending')).fontSize(12).fontColor('#9EB1BD')
      }.padding(24).width('100%')
    }.width('100%').height('100%').backgroundColor('#0B151C')
  }
}
