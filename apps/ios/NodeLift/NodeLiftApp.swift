import SwiftUI

private let canvasColor=Color(red:0.043,green:0.082,blue:0.11)
private let panel=Color(red:0.075,green:0.137,blue:0.176)
private let mint=Color(red:0.57,green:0.953,blue:0.81)

@main struct NodeLiftApp: App {
    @StateObject private var model=NodeModel()
    @Environment(\.scenePhase) private var phase
    var body: some Scene {
        WindowGroup {
            ContentView(model:model).preferredColorScheme(.dark)
                .onChange(of:phase) { _,value in if value == .background { model.pause() } }
        }
    }
}
struct ContentView: View {
    @ObservedObject var model:NodeModel
    func card<Content:View>(@ViewBuilder content:()->Content)->some View {
        VStack(alignment:.leading,spacing:14,content:content).frame(maxWidth:.infinity,alignment:.leading).padding(22).background(panel,in:RoundedRectangle(cornerRadius:18))
    }
    var body:some View {
        ScrollView {
            VStack(alignment:.leading,spacing:18) {
                Text("◈ NodeLift").font(.system(size:30,weight:.bold))
                Text("IL TUO DISPOSITIVO. UN NUOVO NODO.").font(.system(size:10,weight:.bold)).tracking(2).foregroundStyle(mint)
                Text("Collega. Misura.\nScegli quando partecipare.").font(.system(size:32,weight:.semibold)).tracking(-1).padding(.vertical,14)
                card {
                    Label(model.running ? "NODO ATTIVO" : "SESSIONE",systemImage:model.running ? "circle.fill":"circle").font(.caption.weight(.bold)).foregroundStyle(mint)
                    Text(model.status).font(.title3.weight(.medium)).accessibilityIdentifier("session-status")
                    Text(model.telemetry).font(.footnote).foregroundStyle(.secondary)
                }
                card {
                    Text("Associa il computer").font(.title3.weight(.semibold))
                    Text("Nella dashboard NodeLift scegli “Aggiungi dispositivo”, poi incolla l’invito qui. Vale 5 minuti e si usa una volta.").font(.subheadline).foregroundStyle(.secondary)
                    TextEditor(text:$model.ticketText).font(.system(size:12,design:.monospaced)).frame(height:90).scrollContentBackground(.hidden).padding(8).background(canvasColor,in:RoundedRectangle(cornerRadius:8)).accessibilityLabel("Invito NodeLift").autocorrectionDisabled().textInputAutocapitalization(.never)
                    Button("Associa e attiva nodo") { model.connect(newTicket:true) }.buttonStyle(.borderedProminent).tint(mint).foregroundStyle(canvasColor).disabled(model.running || model.ticketText.isEmpty)
                    if model.hasSavedSession { Button("Riprendi sessione") { model.connect(newTicket:false) }.buttonStyle(.bordered).tint(mint).disabled(model.running) }
                }
                card {
                    Text("Il controllo resta tuo").font(.title3.weight(.semibold))
                    Text("Tieni aperta questa app durante le misure. Passando in background la sessione viene messa in pausa. Il computer può avviare brevi test di rete e CPU.").font(.subheadline).foregroundStyle(.secondary)
                    HStack { Button("Pausa") { model.pause() }.buttonStyle(.bordered).tint(mint);Button("Dimentica computer",role:.destructive) { model.forget() }.buttonStyle(.bordered) }
                }
                card {
                    Text("Ultima misura").font(.title3.weight(.semibold))
                    Text(model.lastResult).foregroundStyle(mint).font(.subheadline)
                    Text("La memoria rilevata non è RAM già condivisa. Il motore LLM distribuito non è ancora abilitato; i test sintetici non indicano token/s.").font(.footnote).foregroundStyle(.secondary)
                }
                Text("0.1 · Qualification build\nNessun account cloud richiesto").font(.caption).foregroundStyle(.secondary).padding(.top,8)
            }.padding(24).frame(maxWidth:700)
        }.frame(maxWidth:.infinity).background(canvasColor)
    }
}
