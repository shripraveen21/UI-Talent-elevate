import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { environment } from '../../../environments/environment';
import { HttpClient } from '@angular/common/http';
import { map } from 'rxjs/operators';

export interface TechStackParams {
  name: string;
  description:string;
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

  updateSelectedTopics(topicsData: any): Observable<any> {
    return this.http.post(environment.apiUrl + '/topics/update-selected', topicsData, {
      headers: { 'ngrok-skip-browser-warning': 'true' }
    });
  }

  // Get all collaborators for the current capability leader
  getCollaborators(): Observable<any[]> {
    const token = sessionStorage.getItem('token') || localStorage.getItem('token');
    return this.http.get<any[]>(
      environment.apiUrl + '/get-collaborators',
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'ngrok-skip-browser-warning': 'true'
        }
      }
    );
  }
  getTokenPayload(): any {
  const token = sessionStorage.getItem('token') || localStorage.getItem('token');
  if (!token) return null;
  try {
    const payload = token.split('.')[1];
    // Add padding if needed for base64 decoding
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(function (c) {
          return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        })
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}
getTopicsByLeader(leaderId: number): Observable<any[]> {
  const token = sessionStorage.getItem('token') || localStorage.getItem('token');
  return this.http.get<any[]>(
    environment.apiUrl + `/topics/by-leader-with-stack/${leaderId}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'ngrok-skip-browser-warning': 'true'
      }
    }
  );
}
getUserId(): number | null {
  const payload = this.getTokenPayload();
  // Try user_id, id, sub, userId, etc.
  if (payload) {
    if (payload.user_id) return Number(payload.user_id);
    if (payload.id) return Number(payload.id);
    if (payload.sub && !isNaN(Number(payload.sub))) return Number(payload.sub);
    if (payload.userId) return Number(payload.userId);
  }
  return null;
}

getCapabilityLeaderId(): Observable<number | null> {
  return this.http.get<any>(environment.apiUrl + `/rbac/get-cl`).pipe(
    map(response => {
      // Defensive: check if capability_leader and user_id exist
      if (response && response.capability_leader && response.capability_leader.user_id) {
        return response.capability_leader.user_id; // This is cl_id
      }
      return null; // Not assigned or error
    })
  );
}




getUserRole(): string | null {
  const payload = this.getTokenPayload();
  return payload && payload.role ? payload.role : null;
}

getUserEmail(): string | null {
  const payload = this.getTokenPayload();
  return payload && payload.sub ? payload.sub : null;
}

  // Update topic assignment for drag-and-drop functionality
  updateTopicAssignment(assignmentData: any): Observable<any> {
    return this.http.post(environment.apiUrl + '/topics/update-assignment', assignmentData, {
      headers: { 'ngrok-skip-browser-warning': 'true' }
    });
  }

}
