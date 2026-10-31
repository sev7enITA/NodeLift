import { http } from '@kit.NetworkKit';
import { deviceInfo, thermal, systemDateTime } from '@kit.BasicServicesKit';
import { util } from '@kit.ArkTS';

interface Ticket {
  protocol: number; url: string; certificate: string; sha256: string;
  public_key_pin: string; invite: string; expires_at: number;
}
interface Caps {
  model: string; os: string; app_version: string; thermal: string;
  lifecycle: string; supported_jobs: string[];
}
interface PairRequest { invite: string; name: string; capabilities: Caps; }
interface PairResponse { node_id: string; token: string; }
interface Job { id: string; kind: string; }
interface Heartbeat { job: Job | null; }
interface Sample { kind: string; bytes: number; ms: number; }
interface Result { job_id: string; status: string; samples: Sample[]; note: string; }
interface Uploaded { bytes: number; }

// Credentials remain in memory in this first candidate. No plaintext persistence.
export class NodeController {
  status: string = 'Ready to pair';
  result: string = 'No measurements yet';
  running: boolean = false;
  changed: () => void = () => {};
  private ticket: Ticket | null = null;
  private token: string = '';
  private generation: number = 0;
  private request: http.HttpRequest | null = null;
  private timer: number = -1;

  private now(): number { return systemDateTime.getUptime(systemDateTime.TimeType.STARTUP, true) / 1000000; }
  private caps(): Caps {
    return { model: deviceInfo.productModel, os: deviceInfo.osFullName, app_version: '0.1.0',
      thermal: String(thermal.getLevel()), lifecycle: 'foreground-only', supported_jobs: ['network'] };
  }
  private ready(generation: number, start: number): void {
    if (!this.running || generation !== this.generation) throw new Error('cancelled');
    if (this.now() - start > 90000) throw new Error('Time limit exceeded');
    if (thermal.getLevel() >= 3) throw new Error('thermal_pause');
  }
  private async bytes(path: string, body?: string | ArrayBuffer, raw: boolean = false): Promise<ArrayBuffer> {
    const ticket = this.ticket;
    if (ticket === null) throw new Error('Pair your computer');
    const request = http.createHttp(); this.request = request;
    const headers: Record<string, string> = { 'Accept-Encoding': 'identity', 'Content-Type': raw ? 'application/octet-stream' : 'application/json' };
    if (this.token.length > 0) headers['Authorization'] = 'Bearer ' + this.token;
    const options: http.HttpRequestOptions = {
      method: body === undefined ? http.RequestMethod.GET : http.RequestMethod.POST,
      extraData: body, header: headers, expectDataType: http.HttpDataType.ARRAY_BUFFER,
      usingCache: false, usingProxy: false, usingProtocol: http.HttpProtocol.HTTP1_1,
      connectTimeout: 6000, readTimeout: 10000, maxLimit: 1048576, maxRedirects: 0,
      caData: ticket.certificate,
      certificatePinning: { publicKeyHash: ticket.public_key_pin, hashAlgorithm: 'SHA-256' }
    };
    try {
      const response = await request.request(ticket.url + path, options);
      if (response.responseCode !== 200) throw new Error('Request rejected: ' + response.responseCode);
      return response.result as ArrayBuffer;
    } finally { request.destroy(); if (this.request === request) this.request = null; }
  }
  private decode(data: ArrayBuffer): string { return new util.TextDecoder().decodeToString(new Uint8Array(data)); }
  async connect(text: string): Promise<void> {
    if (this.running) return;
    const generation = ++this.generation;
    try {
      const ticket = JSON.parse(text) as Ticket;
      const match = /^https:\/\/(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3}):(\d{1,5})$/.exec(ticket.url);
      if (match === null || ticket.protocol !== 1 || ticket.expires_at < Date.now() / 1000) throw new Error('Invalid or expired invitation');
      const octets = [Number(match[1]), Number(match[2]), Number(match[3]), Number(match[4])];
      if (octets.some((value: number) => value > 255) || !(octets[0] === 10 || octets[0] === 127 || octets[0] === 192 && octets[1] === 168 || octets[0] === 172 && octets[1] >= 16 && octets[1] <= 31)) throw new Error('Use your local network');
      if (!/^[A-Za-z0-9+/]{43}=$/.test(ticket.public_key_pin) || ticket.certificate.length > 16384 || !ticket.certificate.startsWith('-----BEGIN CERTIFICATE-----')) throw new Error('Invalid computer identity');
      this.ticket = ticket; this.token = ''; this.running = true; this.status = 'Pairing…'; this.changed();
      const body: PairRequest = { invite: ticket.invite, name: deviceInfo.productModel, capabilities: this.caps() };
      const reply = JSON.parse(this.decode(await this.bytes('/v1/pair', JSON.stringify(body)))) as PairResponse;
      if (generation !== this.generation) return;
      this.token = reply.token;
      await this.poll(generation);
    } catch (error) { if (generation === this.generation) { this.status = (error as Error).message; this.running = false; this.changed(); } }
  }
  resume(): void {
    if (!this.running && this.token.length > 0) { this.running = true; this.poll(++this.generation); }
  }
  private async poll(generation: number): Promise<void> {
    if (!this.running || generation !== this.generation) return;
    try {
      const reply = JSON.parse(this.decode(await this.bytes('/v1/heartbeat', JSON.stringify(this.caps())))) as Heartbeat;
      if (generation !== this.generation) return;
      this.status = 'Connected · waiting for a measurement'; this.changed();
      if (reply.job !== null) await this.network(reply.job, generation);
      if (this.running && generation === this.generation) this.timer = setTimeout(() => { this.poll(generation); }, 3000);
    } catch (error) { if (generation === this.generation) { this.running = false; this.status = (error as Error).message; this.changed(); } }
  }
  private async network(job: Job, generation: number): Promise<void> {
    const result: Result = { job_id: job.id, status: 'completed', samples: [], note: '' };
    const start = this.now();
    try {
      if (job.kind !== 'network') throw new Error('This HarmonyOS build supports only network testing');
      this.status = 'Measuring network…'; this.changed();
      await this.bytes('/v1/probe?size=64');
      for (let i = 0; i < 32; i++) {
        this.ready(generation, start);
        const t = this.now(); const data = await this.bytes('/v1/probe?size=64'); const elapsed = this.now() - t;
        if (data.byteLength !== 64) throw new Error('Incomplete payload');
        result.samples.push({ kind: 'rtt', bytes: 64, ms: elapsed });
      }
      for (const size of [16384, 1048576]) {
        const upload = new Uint8Array(size);
        for (let j = 0; j < size; j++) upload[j] = (j * 31 + 17) & 255;
        for (let i = 0; i < 4; i++) {
          this.ready(generation, start);
          let t = this.now(); const data = await this.bytes('/v1/probe?size=' + size); let elapsed = this.now() - t;
          if (data.byteLength !== size) throw new Error('Incomplete payload');
          result.samples.push({ kind: 'download', bytes: size, ms: elapsed });
          this.ready(generation, start);
          t = this.now(); const reply = await this.bytes('/v1/upload', upload.buffer as ArrayBuffer, true); elapsed = this.now() - t;
          if ((JSON.parse(this.decode(reply)) as Uploaded).bytes !== size) throw new Error('Incomplete upload');
          result.samples.push({ kind: 'upload', bytes: size, ms: elapsed });
        }
      }
      result.note = 'Application-level HTTPS measurement. Not an LLM benchmark.';
    } catch (error) {
      const message = (error as Error).message;
      result.status = message === 'thermal_pause' ? 'thermal_pause' : message === 'cancelled' ? 'cancelled' : 'failed';
      result.note = message;
    }
    if (generation === this.generation && this.running) {
      await this.bytes('/v1/result', JSON.stringify(result)); this.result = result.note; this.changed();
    }
  }
  pause(): void {
    this.generation++; this.running = false;
    if (this.timer !== -1) clearTimeout(this.timer);
    this.request?.destroy(); this.request = null;
    this.status = 'Paused · no delegated work'; this.changed();
  }
  forget(): void { this.pause(); this.token = ''; this.ticket = null; this.status = 'Computer forgotten'; this.changed(); }
}
export const node: NodeController = new NodeController();
