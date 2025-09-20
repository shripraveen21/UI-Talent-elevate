import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { TechStackAgentService } from '../../services/techstack-agent/techstack-agent.service';
import { ToastService } from '../../services/toast/toast.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { BackButtonComponent } from '../shared/backbutton/backbutton.component';
type Level = 'beginner' | 'intermediate' | 'advanced';

interface Topic {
  id: string;
  name: string;
  difficulty?: string;
  level?: string;
}

@Component({
  selector: 'app-update-topics',
  templateUrl: './update-topics.component.html',
  styleUrls: ['./update-topics.component.css'],
  standalone: true,
  imports: [FormsModule, CommonModule, BackButtonComponent]
})
export class UpdateTopicsComponent implements OnInit {
  techStackId: string = '';
  techStackName: string = '';
  isLoading: boolean = false;

  assignedBeginnerTopics: Topic[] = [];
  assignedIntermediateTopics: Topic[] = [];
  assignedAdvancedTopics: Topic[] = [];

  beginnerInput: string = '';
  intermediateInput: string = '';
  advancedInput: string = '';

  constructor(
    private route: ActivatedRoute,
    private techStackAgentService: TechStackAgentService,
    private router: Router,
    private toastService: ToastService
  ) {}

  ngOnInit(): void {
    this.techStackId = this.route.snapshot.paramMap.get('techStackId') || '';
    this.techStackName = this.route.snapshot.queryParamMap.get('name') || '';
    this.isLoading = true;
    this.techStackAgentService.getTopics(this.techStackName).subscribe({
      next: (topics: Topic[]) => {
        // Ensure each topic has a unique id
        topics.forEach(t => {
          if (!t.id) {
            t.id = Math.random().toString(36).substr(2, 9);
          }
        });
        // Assign topics to their respective buckets based on difficulty
        this.assignedBeginnerTopics = topics.filter(t => t.difficulty === 'beginner' || t.level === 'beginner');
        this.assignedIntermediateTopics = topics.filter(t => t.difficulty === 'intermediate' || t.level === 'intermediate');
        this.assignedAdvancedTopics = topics.filter(t => t.difficulty === 'advanced' || t.level === 'advanced');
        this.isLoading = false;
      },
      error: () => {
        this.assignedBeginnerTopics = [];
        this.assignedIntermediateTopics = [];
        this.assignedAdvancedTopics = [];
        this.isLoading = false;
      }
    });
  }

  addTopic(level: Level): void {
    let inputValue = '';
    let assignedBucket: Topic[];

    if (level === 'beginner') {
      inputValue = this.beginnerInput.trim();
      assignedBucket = this.assignedBeginnerTopics;
    } else if (level === 'intermediate') {
      inputValue = this.intermediateInput.trim();
      assignedBucket = this.assignedIntermediateTopics;
    } else if (level === 'advanced') {
      inputValue = this.advancedInput.trim();
      assignedBucket = this.assignedAdvancedTopics;
    } else {
      return;
    }

    if (!inputValue) return;

    if (assignedBucket.some(t => t.name.toLowerCase() === inputValue.toLowerCase())) {
      return;
    }

    const newTopic: Topic = {
      id: Math.random().toString(36).substr(2, 9),
      name: inputValue,
      level: level
    };

    assignedBucket.push(newTopic);

    if (level === 'beginner') {
      this.beginnerInput = '';
    } else if (level === 'intermediate') {
      this.intermediateInput = '';
    } else if (level === 'advanced') {
      this.advancedInput = '';
    }
  }

  removeTopic(level: Level, topicId: string): void {
    let assignedBucket: Topic[];
    if (level === 'beginner') {
      assignedBucket = this.assignedBeginnerTopics;
    } else if (level === 'intermediate') {
      assignedBucket = this.assignedIntermediateTopics;
    } else {
      assignedBucket = this.assignedAdvancedTopics;
    }
    const idx = assignedBucket.findIndex(t => t.id === topicId);
    if (idx !== -1) {
      assignedBucket.splice(idx, 1);
    }
  }

  trackByTopicId(index: number, topic: Topic): string {
    return topic.id;
  }

  saveSelectedTopics() {
    const assignedTopics: Topic[] = [
      ...this.assignedBeginnerTopics.map(t => ({ ...t, level: 'beginner' })),
      ...this.assignedIntermediateTopics.map(t => ({ ...t, level: 'intermediate' })),
      ...this.assignedAdvancedTopics.map(t => ({ ...t, level: 'advanced' }))
    ];

    if (assignedTopics.length === 0) {
      this.toastService.showError('Please assign at least one topic to a skill level before updating.');
      return;
    }

    const topicsData = {
      topicName: this.techStackName,
      description: '',
      selectedTopics: assignedTopics.map(topic => ({
        name: topic.name,
        level: topic.level
      })),
      totalSelected: assignedTopics.length
    };

    this.techStackAgentService.updateSelectedTopics(topicsData).subscribe({
      next: () => {
        this.toastService.showSuccess('Topics updated successfully');
        this.router.navigate(['/capability-leader-dashboard']);
      },
      error: () => {
        this.toastService.showError('Failed to update topics');
      }
    });
  }

  // Navigation method for back button
  returnToDashboard(): void {
    window.history.back();
  }
}
