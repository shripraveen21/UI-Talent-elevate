import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { environment } from '../../../environments/environment';
import { HttpClient } from '@angular/common/http';

export interface TechStackParams {
  name: string;
}

export interface Topic {
  id: string;
  name: string;
  level: string; // or 'difficulty'
}

export interface AgentMessage {
  type: 'review' | 'final' | 'error';
  content: any;
  iteration?: number;
}

@Injectable({
  providedIn: 'root'
})
export class TechStackAgentService {
  private ws?: WebSocket;
  private messageSubject = new Subject<AgentMessage>();

  constructor(private http: HttpClient) {}

  getTechStacks(): Observable<any> {
    console.log("called in service")
    return this.http.get(environment.apiUrl + '/tech-stacks', {
      headers: { 'ngrok-skip-browser-warning': 'true' }
    });
  }

  getTopics(techStackName : string): Observable<any> {
    return this.http.get(environment.apiUrl + '/topics/'+techStackName, {
      headers: { 'ngrok-skip-browser-warning': 'true' }
    });
  }

  connect(params: TechStackParams): Observable<AgentMessage> {
    // Get JWT token from session storage
    const token = sessionStorage.getItem('token') || localStorage.getItem('token'); 

    // Build WebSocket URL with token as query param
    let wsUrl = environment.websocketUrl + '/ws/topic-generation';
    if (token) {
      wsUrl += `?token=${encodeURIComponent(token)}`;
    }
    if (this.ws) {
      this.ws.close();
    }
    this.ws = new WebSocket(wsUrl);
    this.ws.onopen = () => {
      this.ws?.send(JSON.stringify(params));
    };
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.messageSubject.next(data);
    };
    this.ws.onerror = () => {
      this.messageSubject.next({ type: 'error', content: 'WebSocket error' });
    };
    this.ws.onclose = () => {};
    return this.messageSubject.asObservable();
  }

  sendDecision(decision: string, feedback?: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ decision, feedback }));
    }
  }

  close() {
    if (this.ws) {
      this.ws.close();
      this.ws = undefined;
    }
  }

  saveSelectedTopics(topicsData: any): Observable<any> {
    return this.http.post(environment.apiUrl + '/topics/save-selected', topicsData, {
      headers: { 'ngrok-skip-browser-warning': 'true' }
    });
  }

}