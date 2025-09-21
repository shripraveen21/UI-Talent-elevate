import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { TechStackAgentService } from '../../services/techstack-agent/techstack-agent.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-collab-tech-stacks',
  templateUrl: './collab-tech-stacks.component.html',
  styleUrls: ['./collab-tech-stacks.component.css'],
  imports: [CommonModule]
})
export class CollabTechStacksComponent implements OnInit {
  techStacks: any[] = [];
  userId: number | null = null;

  constructor(
    private agent: TechStackAgentService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Get user info (assume userId is stored in localStorage as in other components)
    const userJson = localStorage.getItem('user');
    if (userJson) {
      try {
        const userObj = JSON.parse(userJson);
        this.userId = userObj.user_id;
      } catch (err) {
        console.error('[CollabTechStacks] Error parsing user from localStorage:', err);
      }
    }

    if (this.userId) {
      this.agent.getTechStacksByCollaborator(this.userId).subscribe({
        next: (stacks: any[]) => {
          this.techStacks = stacks;
        },
        error: () => {
          this.techStacks = [];
        }
      });
    }
  }

  goToTopics(techStackId: number) {
    // Navigate to collab_topics with techStackId as a route param
    this.router.navigate(['/collab-topics', techStackId]);
  }
}