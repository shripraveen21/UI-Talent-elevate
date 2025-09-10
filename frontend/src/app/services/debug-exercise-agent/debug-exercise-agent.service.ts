import { Injectable } from '@angular/core';
import { environment } from '../../../environments/environment';
import { Observable, Subject, from } from 'rxjs';

export interface AgentMessage {
  type: 'review' | 'final' | 'error';
  content: any;
  iteration?: number;
}

@Injectable({
  providedIn: 'root'
})
export class DebugExerciseAgentService {
  private ws: WebSocket | null = null;
  private messageSubject = new Subject<AgentMessage>();

  startDebugExercise(payload: any): Observable<AgentMessage> {
    console.log("in service")
    if (this.ws) {
      this.ws.close();
    }
    this.ws = new WebSocket(environment.websocketUrl + '/ws/debug-exercise');
    this.ws.onopen = () => {
      this.ws?.send(JSON.stringify(payload));
    };
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.messageSubject.next(data);
      console.log(data, "recieved in frontend")
    };
    this.ws.onerror = (event) => {
      this.messageSubject.next({ type: 'error', content: 'WebSocket error' });
    };
    this.ws.onclose = () => {
      // Optionally notify close
    };
    return this.messageSubject.asObservable();
  }

  sendDecision(decision: string, feedback: string = '') {
    console.log("Sending decision", decision, feedback)
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ decision, feedback }));
    }
  }

  async storeDebugExercise(payload: any, calibrationFeedback: string = ""): Promise<any> {
    const url = environment.apiUrl + '/debug-exercise/store';
    // Add calibration_feedback to payload if needed
    const finalPayload = {
      ...payload,
      calibration_feedback: calibrationFeedback
    };
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(finalPayload)
    });
    if (!response.ok) {
      throw new Error('Failed to store debug exercise');
    }
    return response.json();
  }

  // Fetch tech stacks from backend
  getTechStacks(): Observable<any[]> {
    const url = environment.apiUrl + '/tech-stacks';
    return from(
      fetch(url, {
        method: 'GET',
        headers: { 
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true'
        }
      }).then(response => {

        if (!response.ok) {
          throw new Error('Failed to fetch tech stacks');
        }
        return response.json();
      })
    );
  }

  // Fetch concepts for a given tech stack from backend
  getConcepts(techStackName: string): Observable<any[]> {
    const url = environment.apiUrl + `/topics/${encodeURIComponent(techStackName)}`;
    return from(
      fetch(url, {
        method: 'GET',
        headers: { 
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true'
        }
      }).then(response => {
        if (!response.ok) {
          throw new Error(`Failed to fetch concepts for ${techStackName}`);
        }
        return response.json();
      })
    );
  }
}
