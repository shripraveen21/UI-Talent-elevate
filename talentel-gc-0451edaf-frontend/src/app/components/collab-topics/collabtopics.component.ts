import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TechStackAgentService, Topic } from '../../services/techstack-agent/techstack-agent.service';
import { ToastService } from '../../services/toast/toast.service';
import { ToastComponent } from '../shared/toast/toast.component';
import { Toast } from '../../models/interface/toast';
import { Observable } from 'rxjs';
import { YourSuggestionService } from '../../services/suggestion/suggestion.service';

type Level = 'beginner' | 'intermediate' | 'advanced';

interface SelectableTopic extends Topic {
  techStackName?: string;
  techStackId?: number;
  selected: boolean;
}

@Component({
  selector: 'app-collab-topics',
  templateUrl: './collabtopics.component.html',
  standalone: true,
  imports: [CommonModule, FormsModule, ToastComponent]
})
export class CollabTopicsComponent implements OnInit {
  topics: SelectableTopic[] = [];
  toasts$: Observable<Toast[]>;
  userRole: string = '';
  userId: number | null = null;
  clId: number | null = null;
  techStackId: number | null = null;
  userName: string = '';
  reviewMessage: string = '';

  constructor(
    private agent: TechStackAgentService,
    private toastService: ToastService,
    private suggestionService: YourSuggestionService
  ) {
    this.toasts$ = this.toastService.toasts$;
  }

  ngOnInit(): void {
    // Get user info
    const userJson = localStorage.getItem('user');
    let userName: string = '';
    let userEmail: string = '';

    if (userJson) {
      try {
        const userObj = JSON.parse(userJson);
        this.userId = userObj.user_id;
        userName = userObj.name;
        userEmail = userObj.email;
      } catch (err) {
        console.error('[ngOnInit] Error parsing user from localStorage:', err);
      }
    }

    this.userName = userName;
    this.userRole = this.agent.getUserRole() || '';

    // Collaborator: Get assigned CL's ID and topics
    if (this.userId) {
      this.agent.getCapabilityLeaderId().subscribe({
        next: (clId: number | null) => {
          this.clId = clId;
          if (!clId) {
            this.topics = [];
            return;
          }
          this.agent.getTopicsByLeader(clId).subscribe({
            next: (topicsWithStack: any[]) => {
              if (!topicsWithStack || topicsWithStack.length === 0) {
                this.topics = [];
              } else {
                this.topics = topicsWithStack.map(t => ({
                  id: t.topic_id,
                  name: t.topic_name,
                  level: t.difficulty,
                  selected: false,
                  techStackName: t.tech_stack_name,
                  techStackId: t.tech_stack_id
                }));
                this.techStackId = topicsWithStack[0]?.tech_stack_id || null;
              }
            },
            error: () => {
              this.topics = [];
            }
          });
        },
        error: () => {
          this.topics = [];
        }
      });
    } else {
      this.topics = [];
    }
  }

  getTopicsByLevel(level: string): SelectableTopic[] {
    return this.topics.filter(topic => topic.level === level);
  }

  // Review box submission
  raiseReview() {
    if (!this.reviewMessage.trim()) {
      this.toastService.showWarning('Please enter a message before raising a review.');
      return;
    }
    if (!this.userId || !this.clId || !this.techStackId) {
      this.toastService.showError('Missing required information to raise a review.');
      return;
    }
    const suggestionPayload = {
      collaborator_id: this.userId,
      capability_leader_id: this.clId,
      tech_stack_id: this.techStackId,
      message: this.reviewMessage
    };
    this.suggestionService.raiseSuggestion(suggestionPayload).subscribe({
      next: () => {
        this.toastService.showSuccess('Suggestion sent successfully!');
        this.reviewMessage = '';
      },
      error: () => {
        this.toastService.showError('Failed to send suggestion. Please try again.');
      }
    });
  }

  onToastDismiss(toastId: string) {
    this.toastService.dismissToast(toastId);
  }
}
