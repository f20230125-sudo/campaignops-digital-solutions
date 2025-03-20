export type Metric = {
  period: string; campaign: string; market: string;
  delivered: number; clicked: number; sessions: number; engaged: number; registrations: number;
  registrants: number; attendees: number; unmatched_attendees: number;
  email_click_rate: number | null; engagement_rate: number | null; registration_rate: number | null; attendance_rate: number | null;
};
export type MetricKey = 'email_click_rate' | 'engagement_rate' | 'registration_rate' | 'attendance_rate';
export type Campaign = { id: string; title: string; date: string; source: string; summary: string; provenance: string };
export type Asset = { asset_id: string; campaign_id: string; title: string; status: string; owner: string; review_date: string; mobile_ready: boolean; source?: string; provenance: string; id?: number; url?: string; edit_url?: string; revision_count?: number };
export type Issue = { id: string; title: string; severity: string; campaign: string; category: string; count: number; evidence: string; action: string; resolution: string };
export type Manifest = {version: string; data_hash: string; calculation_sha256: string; cutoff: string; report_timezone: string; provenance: string; accepted: number; rejected: number; quality: Record<string,number>; duplicate_events: number; orphan_registrations: number; imports: {file:string;sha256:string;duplicate:boolean}[]};
export type DashboardData = {campaigns: Campaign[]; assets: Asset[]; periods: {id:string;label:string;start:string;end:string;type:string}[]; metrics: Metric[]; registry: Record<MetricKey,{label:string;numerator:keyof Metric;denominator:keyof Metric;definition:string}>; manifest: Manifest; issues: Issue[]};
export type ObservedEvent = {event_id:string;kind:string;session_id:string;asset_id:string;campaign_id:string;market:string;device:string;timestamp:string;provenance:'observed_test'};
export const markets: Record<string,string>={all:'All markets',AE:'United Arab Emirates',SA:'Saudi Arabia',QA:'Qatar'};
export const pct=(n:number|null|undefined)=> n==null?'—':`${(n*100).toFixed(1)}%`;
export const num=(n:number)=>new Intl.NumberFormat('en').format(n);
export function download(name:string,contents:string,type='application/json') {
  const url=URL.createObjectURL(new Blob([contents],{type})); const a=document.createElement('a'); a.href=url; a.download=name; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
}
