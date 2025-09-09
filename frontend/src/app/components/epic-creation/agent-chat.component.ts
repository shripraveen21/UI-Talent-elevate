import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { AgentChatService, EpicReviewMessage } from '../../services/epic-agent/agent-chat.service';

@Component({
  selector: 'app-agent-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './agent-chat.component.html',
  styleUrls: ['./agent-chat.component.css']
})
export class AgentChatComponent implements OnInit, OnDestroy {
  pocDetails: string = '';
  connected: boolean = false;
  reviewEpics: string = '';
  finalEpics: string = '';
  errorMsg: string = '';
  iteration: number = 0;
  awaitingReview: boolean = false;
  feedback: string = '';
  private connectionSub!: Subscription;

  constructor(public chatService: AgentChatService) {}

  ngOnInit(): void {
    this.chatService.connect();
    this.connectionSub = this.chatService.connectionStatus$.subscribe(status => {
      this.connected = status;
    });
  }

  ngDoCheck(): void {
    // Check for new messages in receivedData
    const lastMsg = this.chatService.receivedData[this.chatService.receivedData.length - 1];
    if (lastMsg) {
      if (lastMsg.type === 'review') {
        this.reviewEpics = lastMsg.content;
        this.iteration = lastMsg.iteration || 0;
        this.awaitingReview = true;
        this.finalEpics = '';
        this.errorMsg = '';
      } else if (lastMsg.type === 'final') {
        this.finalEpics = lastMsg.content;
        this.awaitingReview = false;
        this.errorMsg = '';
      } else if (lastMsg.type === 'error') {
        this.errorMsg = lastMsg.content;
        this.awaitingReview = false;
      }
    }
  }

  ngOnDestroy(): void {
    if (this.connectionSub) {
      this.connectionSub.unsubscribe();
    }
    this.chatService.close();
  }

  startReview(): void {
    if (this.pocDetails.trim()) {
      this.chatService.sendPocDetails(this.pocDetails.trim());
    }
  }

  sendDecision(decision: string): void {
    if (this.awaitingReview) {
      if (decision === 'FEEDBACK') {
        this.chatService.sendReviewDecision('FEEDBACK', this.feedback.trim());
        this.feedback = '';
      } else {
        this.chatService.sendReviewDecision(decision);
      }
      this.awaitingReview = false;
    }
  }
}
