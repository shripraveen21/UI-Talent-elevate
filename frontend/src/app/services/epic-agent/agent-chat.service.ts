import { Injectable } from '@angular/core';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { BehaviorSubject } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface EpicReviewMessage {
  type: string;
  content: string;
  iteration?: number;
  feedback?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AgentChatService {
  private socket$!: WebSocketSubject<any>;
  public receivedData: EpicReviewMessage[] = [];
  public connectionStatus$ = new BehaviorSubject<boolean>(false);

  public connect(): void {
    if (!this.socket$ || this.socket$.closed) {
      this.socket$ = webSocket(environment.websocketUrl + '/ws/epic-review');
      this.connectionStatus$.next(false);
      this.socket$.subscribe({
        next: (data: EpicReviewMessage) => {
          this.receivedData.push(data);
        },
        error: (err) => {
          this.connectionStatus$.next(false);
        },
        complete: () => {
          this.connectionStatus$.next(false);
        }
      });
      // Set connected to true when socket opens
      this.connectionStatus$.next(true);
    }
  }

  sendPocDetails(poc_details: string): void {
    if (this.socket$) {
      this.socket$.next({ poc_details });
    }
  }

  sendReviewDecision(decision: string, feedback?: string): void {
    if (this.socket$) {
      this.socket$.next({ decision, feedback });
    }
  }

  close(): void {
    if (this.socket$) {
      this.socket$.complete();
      this.connectionStatus$.next(false);
    }
  }
}
