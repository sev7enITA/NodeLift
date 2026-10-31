import { node } from './NodeController';

@Entry
@Component
struct Index {
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
        Text('IL TUO DISPOSITIVO. UN NUOVO NODO.').fontSize(10).fontColor('#91F3CE').width('100%')
        Text('Collega. Misura.\nScegli quando partecipare.').fontSize(30).fontWeight(FontWeight.Medium).fontColor('#EDF5F8').width('100%').margin({ top: 18, bottom: 16 })
        Column({ space: 12 }) {
          Text(this.status).fontSize(20).fontColor('#91F3CE').width('100%')
          Text('HarmonyOS · sessione in primo piano').fontSize(14).fontColor('#9EB1BD').width('100%')
        }.padding(22).backgroundColor('#13232D').borderRadius(18).width('100%')
        Column({ space: 14 }) {
          Text('Associa il computer').fontSize(22).fontColor('#EDF5F8').width('100%')
          Text('Nella dashboard NodeLift crea un invito e incollalo qui. Vale 5 minuti e si usa una volta.').fontSize(14).fontColor('#9EB1BD')
          TextArea({ placeholder: 'Invito NodeLift', text: this.ticket }).height(110).fontSize(12).fontColor('#EDF5F8').backgroundColor('#0B151C').onChange((text: string) => { this.ticket = text; })
          Button('Associa e attiva nodo').width('100%').backgroundColor('#91F3CE').fontColor('#0B151C').enabled(!this.running).onClick(() => { const value = this.ticket; this.ticket = ''; node.connect(value); })
          Button('Riprendi sessione').width('100%').onClick(() => { node.resume(); })
        }.padding(22).backgroundColor('#13232D').borderRadius(18).width('100%')
        Column({ space: 12 }) {
          Text('Il controllo resta tuo').fontSize(22).fontColor('#EDF5F8').width('100%')
          Text('Tieni aperta l’app. Il passaggio in background mette in pausa il nodo. Questa build candidata misura la rete; CPU e LLM non sono abilitati. Le credenziali restano solo in memoria.').fontSize(14).fontColor('#9EB1BD')
          Button('Metti in pausa').width('100%').onClick(() => { node.pause(); })
          Button('Dimentica computer').width('100%').onClick(() => { node.forget(); })
          Text(this.result).fontSize(14).fontColor('#91F3CE')
        }.padding(22).backgroundColor('#13232D').borderRadius(18).width('100%')
        Text('0.1 · Candidato HarmonyOS da compilare e qualificare su dispositivo').fontSize(12).fontColor('#9EB1BD')
      }.padding(24).width('100%')
    }.width('100%').height('100%').backgroundColor('#0B151C')
  }
}
