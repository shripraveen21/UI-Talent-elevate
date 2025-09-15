import { Component ,OnInit} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TechStackAgentService, TechStackParams, Topic, AgentMessage } from '../../services/techstack-agent/techstack-agent.service';
import { ToastService } from '../../services/toast/toast.service';
import { ToastComponent } from '../shared/toast/toast.component';
import { Toast } from '../../models/interface/toast';
import { Observable } from 'rxjs';

type Level = 'beginner' | 'intermediate' | 'advanced';

// Extended Topic interface with selection state
interface SelectableTopic extends Topic {
  selected: boolean;
}

@Component({
  selector: 'app-techstack-form',
  templateUrl: './techstack-form.component.html',
  styleUrls: ['./techstack-form.component.css'],
  standalone: true,
  imports: [CommonModule, FormsModule, ToastComponent]
})
export class TechStackFormComponent implements OnInit {
  params: TechStackParams = {
    name: '',
  };

  topicDescription: string = '';
  topics: SelectableTopic[] = [];
  log: string[] = [];
  reviewIteration = 0;
  wsConnected = false;
  showControls = false;
  feedback: string = '';
  toasts$: Observable<Toast[]>;
  
  // Topic selection properties - level-specific select all states
  selectAllBeginner = false;
  selectAllIntermediate = false;
  selectAllAdvanced = false;

  constructor(
    private agent: TechStackAgentService,
    private toastService: ToastService
  ) {
    this.toasts$ = this.toastService.toasts$;
  }

  connect() {
    this.log = [];
    this.topics = [];
    this.wsConnected = true;
    this.feedback = '';
    
    this.agent.connect(this.params).subscribe({
      next: (msg: AgentMessage) => {
        this.log.push(JSON.stringify(msg, null, 2));
        if (msg.type === 'review') {
          this.topics = this.addSelectionState(msg.content);
          this.reviewIteration = msg.iteration || 1;
          this.showControls = true;
        } else if (msg.type === 'final') {
          const finalTopics = msg.content.topics ? msg.content.topics : msg.content;
          this.topics = this.addSelectionState(finalTopics);
          this.showControls = false;
          this.wsConnected = false;
          this.toastService.showSuccess('Learning concepts generated successfully!');
        } else if (msg.type === 'error') {
          this.showControls = false;
          this.wsConnected = false;
          this.toastService.showError('Failed to generate learning concepts. Please try again.');
        }
      },
      error: (error) => {
        this.wsConnected = false;
        this.showControls = false;
        this.toastService.showError('Connection error. Please check your network and try again.');
      }
    });
  }

  sendDecision(decision: string, feedback?: string) {
    this.agent.sendDecision(decision, feedback);
    this.log.push(`Sent decision: ${decision}${feedback ? ' with feedback: ' + feedback : ''}`);
  }

  closeWs() {
    this.agent.close();
    this.wsConnected = false;
    this.showControls = false;
  }

  get formattedTopicsJson(): string {
    const grouped: { [key: string]: string[] } = {
      beginner: [],
      intermediate: [],
      advanced: []
    };
    for (const topic of this.topics) {
      const level = (topic.level || '').toLowerCase();
      if (grouped[level]) {
        grouped[level].push(topic.name);
      }
    }
    return JSON.stringify(grouped, null, 2);
  }

  // Helper method to add selection state to topics
  private addSelectionState(topics: Topic[]): SelectableTopic[] {
    return topics.map(topic => ({
      ...topic,
      selected: false
    }));
  }

  getTopicsByLevel(level: string): SelectableTopic[] {
    return this.topics.filter(topic => topic.level === level);
  }

  saveTopics() {
    try {
      // Only save selected topics, not all topics
      const selectedTopics = this.topics.filter(topic => topic.selected);
      
      if (selectedTopics.length === 0) {
        this.toastService.showWarning('Please select at least one topic to save.');
        return;
      }
      
      // Group selected topics by level for better organization
      const selectedByLevel = {
        beginner: selectedTopics.filter(topic => topic.level === 'beginner'),
        intermediate: selectedTopics.filter(topic => topic.level === 'intermediate'),
        advanced: selectedTopics.filter(topic => topic.level === 'advanced')
      };
      
      const topicsData = {
        topicName: this.params.name,
        description: this.topicDescription,
        selectedTopics: selectedTopics.map(topic => ({
          name: topic.name,
          level: topic.level
        })),
        selectedByLevel: selectedByLevel,
        totalSelected: selectedTopics.length,
        selectionSummary: {
          beginner: selectedByLevel.beginner.length,
          intermediate: selectedByLevel.intermediate.length,
          advanced: selectedByLevel.advanced.length
        },
        generatedAt: new Date().toISOString()
      };
      
      console.log('Saving only selected topics to DB:', topicsData);
      
      // Call API to save selected topics to database
      this.agent.saveSelectedTopics(topicsData).subscribe({
        next: (response) => {
          console.log('Topics saved successfully:', response);
          this.toastService.showSuccess(`Successfully saved ${response.saved_topics_count} new topics to database! (Total selected: ${selectedTopics.length})`);
        },
        error: (error) => {
          console.error('Error saving topics:', error);
          const errorMessage = error?.error?.detail || 'Failed to save topics to database';
          this.toastService.showError(errorMessage);
        }
      });
    } catch (error) {
      this.toastService.showError('Failed to save topics. Please try again.');
    }
  }

  approveTopics() {
    this.sendDecision('approve');
    this.showControls = false;
    this.toastService.showInfo('Topics approved. Generating final version...');
  }

  approveAndSaveTopics() {
    if (this.getSelectedTopicsCount() === 0) {
      this.toastService.showWarning('Please select at least one topic to save.');
      return;
    }

    // Save the selected topics first, before sending the decision
    this.saveSelectedTopicsToDatabase();

    // Then approve the topics
    this.sendDecision('approve');
    this.showControls = false;
    this.toastService.showInfo('Topics approved and saved successfully!');
  }

  private saveSelectedTopicsToDatabase() {
    const selectedTopics = this.topics.filter(topic => topic.selected);
    
    if (selectedTopics.length === 0) {
      this.toastService.showWarning('No topics selected to save.');
      return;
    }

    const topicsData = {
      topicName: this.params.name,
      description: this.topicDescription,
      selectedTopics: selectedTopics.map(topic => ({
        name: topic.name,
        level: topic.level
      })),
      totalSelected: selectedTopics.length
    };

    try {
      this.agent.saveSelectedTopics(topicsData).subscribe({
        next: (response: any) => {
          this.toastService.showSuccess(`Successfully saved ${response.saved_topics_count || selectedTopics.length} topics to database!`);
        },
        error: (error) => {
          console.error('Error saving topics:', error);
          this.toastService.showError('Failed to save topics to database. Please try again.');
        }
      });
    } catch (error) {
      this.toastService.showError('Failed to save topics. Please try again.');
    }
  }

  rejectTopics() {
    if (!this.feedback.trim()) {
      this.toastService.showWarning('Please provide feedback for rejection.');
      return;
    }
    this.sendDecision('reject', this.feedback);
    this.feedback = '';
    this.toastService.showInfo('Topics rejected. Regenerating with your feedback...');
  }

  regenerateTopics() {
    const feedbackText = this.feedback.trim() || 'Please regenerate the topics';
    this.sendDecision('regenerate', feedbackText);
    this.feedback = '';
    this.toastService.showInfo('Regenerating topics...');
  }

  onToastDismiss(toastId: string) {
    this.toastService.dismissToast(toastId);
  }

  // Topic selection methods - refactored for proper level-scoped selection
  onTopicSelectionChange(topic: SelectableTopic) {
    topic.selected = !topic.selected;
    this.updateSelectAllStates();
  }

  onSelectAllBeginner() {
    this.selectAllBeginner = !this.selectAllBeginner;
    const beginnerTopics = this.getTopicsByLevel('beginner');
    beginnerTopics.forEach(topic => {
      topic.selected = this.selectAllBeginner;
    });
  }

  onSelectAllIntermediate() {
    this.selectAllIntermediate = !this.selectAllIntermediate;
    const intermediateTopics = this.getTopicsByLevel('intermediate');
    intermediateTopics.forEach(topic => {
      topic.selected = this.selectAllIntermediate;
    });
  }

  onSelectAllAdvanced() {
    this.selectAllAdvanced = !this.selectAllAdvanced;
    const advancedTopics = this.getTopicsByLevel('advanced');
    advancedTopics.forEach(topic => {
      topic.selected = this.selectAllAdvanced;
    });
  }

  updateSelectAllStates() {
    const beginnerTopics = this.getTopicsByLevel('beginner');
    const intermediateTopics = this.getTopicsByLevel('intermediate');
    const advancedTopics = this.getTopicsByLevel('advanced');
    
    this.selectAllBeginner = beginnerTopics.length > 0 && beginnerTopics.every(topic => topic.selected);
    this.selectAllIntermediate = intermediateTopics.length > 0 && intermediateTopics.every(topic => topic.selected);
    this.selectAllAdvanced = advancedTopics.length > 0 && advancedTopics.every(topic => topic.selected);
  }

  isTopicSelected(topic: SelectableTopic): boolean {
    return topic.selected;
  }

  getSelectedTopicsCount(): number {
    return this.topics.filter(topic => topic.selected).length;
  }

  // Helper method to get selected topics by specific level
  getSelectedTopicsByLevel(level: Level): SelectableTopic[] {
    return this.topics.filter(topic => topic.level === level && topic.selected);
  }

  // Helper method to check if any topics are selected in a specific level
  hasSelectedTopicsInLevel(level: Level): boolean {
    return this.getSelectedTopicsByLevel(level).length > 0;
  }

  userName: string = '';

  ngOnInit(): void {
    this.userName = localStorage.getItem('username') || '';
  }
}
