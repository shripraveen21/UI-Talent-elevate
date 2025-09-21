import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
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
  public reviewText: string = '';

  public submitReview(): void {
    // TODO: Implement review submission logic
    console.log('Review submitted:', this.reviewText);
  }
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
    private suggestionService: YourSuggestionService,
    private router: Router
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

    // Get techStackId from route param
    let techStackId: number | null = null;
    if ((window as any).ng && (window as any).ng.router) {
      // Angular 17+ standalone router
      techStackId = Number((window as any).ng.router.currentRoute?.params?.techStackId);
    }
    // Fallback for classic router
    if (!techStackId && typeof window !== 'undefined') {
      const urlParts = window.location.pathname.split('/');
      const idx = urlParts.indexOf('collab-topics');
      if (idx !== -1 && urlParts.length > idx + 1) {
        techStackId = Number(urlParts[idx + 1]);
      }
    }

    this.techStackId = techStackId;

    // Fetch capability leader id (clId) from tech stack details
    if (this.techStackId) {
        this.agent.getTechStackById(this.techStackId).subscribe({
            next: (ts: any) => {
                console.log('TechStack response:', ts);
                this.clId = ts.created_by;
            },
            error: () => {
                this.clId = null;
            }
        });
    }

    // Collaborator: Get topics for selected tech stack only
    if (this.userId && this.techStackId) {
        this.agent.getTopicsByCollaborator(this.userId).subscribe({
            next: (topics: any[]) => {
                // Filter topics for this techStackId only
                const filtered = topics.filter(t => t.tech_stack_id === this.techStackId);
                if (!filtered || filtered.length === 0) {
                    this.topics = [];
                } else {
                    this.topics = filtered.map(t => ({
                        id: t.topic_id,
                        name: t.name,
                        level: t.difficulty,
                        selected: false,
                        techStackId: t.tech_stack_id
                    }));
                }
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
    console.log('raiseReview values:', {
      userId: this.userId,
      clId: this.clId,
      techStackId: this.techStackId,
      reviewMessage: this.reviewMessage
    });
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
        this.router.navigate(['/collab-tech-stacks']);
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