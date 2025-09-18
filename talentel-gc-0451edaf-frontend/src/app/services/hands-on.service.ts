import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';

export interface AgentMessage {
  type: 'srs_review' | 'final' | 'error';
  content: any;
  regen_count?: number;
  max_regen?: number;
}

@Injectable({
  providedIn: 'root'
})
export class HandsonAgentService {
  private ws?: WebSocket;
  private messageSubject = new Subject<AgentMessage>();

  constructor(private http: HttpClient) {}

  connect(params: any): Observable<AgentMessage> {
    if (this.ws) {
      this.ws.close();
    }
    this.ws = new WebSocket(`${environment.websocketUrl}/ws/create-handson`);
    this.ws.onopen = () => {
      this.ws?.send(JSON.stringify({
        tech_stack: params.tech_stack[0].name,
        topics: params.topics,
        duration: params.duration
      }));
    };
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      // Normalize message structure for frontend
      if (data.type === 'srs_review') {
        this.messageSubject.next({
          type: 'srs_review',
          content: { srs_md: data.srs_md },
          regen_count: data.regen_count,
          max_regen: data.max_regen
        });
      } else if (data.type === 'final') {
        this.messageSubject.next({
          type: 'final',
          content: data.content
        });
      } else if (data.type === 'error') {
        this.messageSubject.next({
          type: 'error',
          content: data.content
        });
      }
    };
    this.ws.onerror = () => {
      this.messageSubject.next({ type: 'error', content: 'WebSocket error' });
    };
    this.ws.onclose = () => {};
    return this.messageSubject.asObservable();
  }

  sendFeedback(action: 'approve' | 'suggest', suggestions?: string[]) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action, suggestions }));
    }
  }

  close() {
    if (this.ws) {
      this.ws.close();
      this.ws = undefined;
    }
  }

  storeHandson(finalData: any): Observable<any> {
    return this.http.post(`${environment.apiUrl}/handson/store`, finalData);
  }
}

